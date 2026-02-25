from __future__ import annotations

import argparse
import ctypes
import os
import queue
import time
from pathlib import Path

EDS_ERR_OK = 0x00000000
EDS_ERR_DEVICE_BUSY = 0x00000081

K_EDS_PROP_ID_SAVE_TO = 0x0000000B
K_EDS_SAVE_TO_HOST = 2
K_EDS_SAVE_TO_BOTH = 3

K_EDS_OBJECT_EVENT_ALL = 0x00000200
K_EDS_OBJECT_EVENT_DIR_ITEM_REQUEST_TRANSFER = 0x00000208

K_EDS_CAMERA_COMMAND_TAKE_PICTURE = 0x00000000

K_EDS_FILE_CREATE_DISPOSITION_CREATE_ALWAYS = 1
K_EDS_ACCESS_READ_WRITE = 2

OBJECT_EVENT_HANDLER = ctypes.WINFUNCTYPE(
    ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p
)


class EdsCapacity(ctypes.Structure):
    _fields_ = [
        ("numberOfFreeClusters", ctypes.c_int32),
        ("bytesPerSector", ctypes.c_int32),
        ("reset", ctypes.c_int32),
    ]


class EdsDirectoryItemInfo(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_uint64),
        ("isFolder", ctypes.c_int32),
        ("groupID", ctypes.c_uint32),
        ("option", ctypes.c_uint32),
        ("szFileName", ctypes.c_char * 256),
        ("format", ctypes.c_uint32),
        ("dateTime", ctypes.c_uint32),
    ]


def log(msg: str) -> None:
    print(msg, flush=True)


def hex_err(code: int) -> str:
    return f"0x{code:08X}"


def describe_error(code: int) -> str:
    if code == EDS_ERR_OK:
        return "EDS_ERR_OK"
    if code == EDS_ERR_DEVICE_BUSY:
        return "EDS_ERR_DEVICE_BUSY"
    return "UNKNOWN_ERROR"


class CanonCaptureProbe:
    def __init__(self, dll_path: Path, out_path: Path | None, timeout_ms: int) -> None:
        self.dll_path = Path(dll_path)
        self.out_path = Path(out_path) if out_path else None
        self.timeout_ms = max(1000, int(timeout_ms))

        self.sdk = None
        self._dll_dir_handle = None

        self.camera_list = ctypes.c_void_p()
        self.camera = ctypes.c_void_p()
        self.session_opened = False
        self.sdk_initialized = False

        self._object_handler_ref: OBJECT_EVENT_HANDLER | None = None
        self._transfer_queue: queue.Queue[tuple[ctypes.c_void_p, bool]] = queue.Queue()

    def _bind_api(self) -> None:
        if self.sdk is None:
            raise RuntimeError("EDSDK is not loaded.")

        c_void_pp = ctypes.POINTER(ctypes.c_void_p)
        c_uint32_p = ctypes.POINTER(ctypes.c_uint32)

        self.sdk.EdsInitializeSDK.restype = ctypes.c_uint32
        self.sdk.EdsInitializeSDK.argtypes = []

        self.sdk.EdsTerminateSDK.restype = ctypes.c_uint32
        self.sdk.EdsTerminateSDK.argtypes = []

        self.sdk.EdsGetCameraList.restype = ctypes.c_uint32
        self.sdk.EdsGetCameraList.argtypes = [c_void_pp]

        self.sdk.EdsGetChildCount.restype = ctypes.c_uint32
        self.sdk.EdsGetChildCount.argtypes = [ctypes.c_void_p, c_uint32_p]

        self.sdk.EdsGetChildAtIndex.restype = ctypes.c_uint32
        self.sdk.EdsGetChildAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_int32, c_void_pp]

        self.sdk.EdsOpenSession.restype = ctypes.c_uint32
        self.sdk.EdsOpenSession.argtypes = [ctypes.c_void_p]

        self.sdk.EdsCloseSession.restype = ctypes.c_uint32
        self.sdk.EdsCloseSession.argtypes = [ctypes.c_void_p]

        self.sdk.EdsSetPropertyData.restype = ctypes.c_uint32
        self.sdk.EdsSetPropertyData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_int32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]

        self.sdk.EdsSetCapacity.restype = ctypes.c_uint32
        self.sdk.EdsSetCapacity.argtypes = [ctypes.c_void_p, EdsCapacity]

        self.sdk.EdsSetObjectEventHandler.restype = ctypes.c_uint32
        self.sdk.EdsSetObjectEventHandler.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            OBJECT_EVENT_HANDLER,
            ctypes.c_void_p,
        ]

        self.sdk.EdsSendCommand.restype = ctypes.c_uint32
        self.sdk.EdsSendCommand.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32]

        self.sdk.EdsGetEvent.restype = ctypes.c_uint32
        self.sdk.EdsGetEvent.argtypes = []

        self.sdk.EdsRetain.restype = ctypes.c_uint32
        self.sdk.EdsRetain.argtypes = [ctypes.c_void_p]

        self.sdk.EdsRelease.restype = ctypes.c_uint32
        self.sdk.EdsRelease.argtypes = [ctypes.c_void_p]

        self.sdk.EdsGetDirectoryItemInfo.restype = ctypes.c_uint32
        self.sdk.EdsGetDirectoryItemInfo.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(EdsDirectoryItemInfo),
        ]

        self.sdk.EdsDownload.restype = ctypes.c_uint32
        self.sdk.EdsDownload.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]

        self.sdk.EdsDownloadComplete.restype = ctypes.c_uint32
        self.sdk.EdsDownloadComplete.argtypes = [ctypes.c_void_p]

        self.sdk.EdsCreateFileStreamEx.restype = ctypes.c_uint32
        self.sdk.EdsCreateFileStreamEx.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            c_void_pp,
        ]

        if hasattr(self.sdk, "EdsCreateFileStream"):
            self.sdk.EdsCreateFileStream.restype = ctypes.c_uint32
            self.sdk.EdsCreateFileStream.argtypes = [
                ctypes.c_char_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                c_void_pp,
            ]

    def _ensure_ok(self, err: int, stage: str) -> None:
        if err != EDS_ERR_OK:
            raise RuntimeError(
                f"{stage} failed: {hex_err(err)} {describe_error(err)}"
            )

    def _release_ref(self, ref: ctypes.c_void_p, name: str) -> None:
        if self.sdk is None or not ref or not ref.value:
            return
        err = self.sdk.EdsRelease(ref)
        if err != EDS_ERR_OK:
            log(f"[WARN] EdsRelease({name}) -> {hex_err(err)} {describe_error(err)}")

    def _event_handler(
        self,
        event: int,
        in_ref,
        in_context,
    ) -> int:
        ref_value = 0
        if in_ref:
            try:
                ref_value = int(in_ref)
            except Exception:
                ref_value = 0

        if event == K_EDS_OBJECT_EVENT_DIR_ITEM_REQUEST_TRANSFER and ref_value:
            log(f"[EVENT] DirItemRequestTransfer received ref=0x{ref_value:016X}")
            dir_item = ctypes.c_void_p(ref_value)
            err = self.sdk.EdsRetain(dir_item)
            if err == EDS_ERR_OK:
                self._transfer_queue.put((dir_item, True))
                log(
                    f"[EVENT] DirItemRequestTransfer queued ref=0x{ref_value:016X}"
                )
            else:
                log(
                    "[WARN] EdsRetain(dirItem) failed, queue raw ref fallback: "
                    f"{hex_err(err)} {describe_error(err)}"
                )
                self._transfer_queue.put((dir_item, False))
        return EDS_ERR_OK

    def _decode_filename(self, raw_name: bytes) -> str:
        raw = raw_name.split(b"\x00", 1)[0]
        if not raw:
            return "capture.jpg"
        for encoding in ("utf-8", "mbcs", "cp932", "latin1"):
            try:
                return raw.decode(encoding)
            except Exception:
                continue
        return "capture.jpg"

    def _resolve_output_path(self, suggested_name: str) -> Path:
        if self.out_path is not None:
            target = self.out_path
        else:
            ts = time.strftime("%Y%m%d_%H%M%S")
            suffix = Path(suggested_name).suffix.lower()
            if suffix not in (".jpg", ".jpeg"):
                suffix = ".jpg"
            target = Path("out") / f"capture_{ts}{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def _download_dir_item(self, dir_item: ctypes.c_void_p) -> Path:
        info = EdsDirectoryItemInfo()
        err = self.sdk.EdsGetDirectoryItemInfo(dir_item, ctypes.byref(info))
        self._ensure_ok(err, "EdsGetDirectoryItemInfo")
        size = int(info.size)
        file_name = self._decode_filename(bytes(info.szFileName))
        target = self._resolve_output_path(file_name)
        log(f"[INFO] Download target: {target} size={size}")

        stream = ctypes.c_void_p()
        try:
            if hasattr(self.sdk, "EdsCreateFileStreamEx"):
                err = self.sdk.EdsCreateFileStreamEx(
                    str(target),
                    K_EDS_FILE_CREATE_DISPOSITION_CREATE_ALWAYS,
                    K_EDS_ACCESS_READ_WRITE,
                    ctypes.byref(stream),
                )
                self._ensure_ok(err, "EdsCreateFileStreamEx")
            else:
                path_bytes = str(target).encode("mbcs", errors="replace")
                err = self.sdk.EdsCreateFileStream(
                    path_bytes,
                    K_EDS_FILE_CREATE_DISPOSITION_CREATE_ALWAYS,
                    K_EDS_ACCESS_READ_WRITE,
                    ctypes.byref(stream),
                )
                self._ensure_ok(err, "EdsCreateFileStream")

            if size > 0xFFFFFFFF:
                log("[WARN] file size exceeds 32-bit range, truncating read size")
                read_size = 0xFFFFFFFF
            else:
                read_size = size

            err = self.sdk.EdsDownload(dir_item, ctypes.c_uint32(read_size), stream)
            self._ensure_ok(err, "EdsDownload")
            err = self.sdk.EdsDownloadComplete(dir_item)
            self._ensure_ok(err, "EdsDownloadComplete")
            log("[OK] Download complete")
        finally:
            self._release_ref(stream, "stream")

        if not target.is_file() or target.stat().st_size <= 0:
            raise RuntimeError("Output file missing or empty after download.")
        return target

    def _drain_queue_refs(self) -> None:
        while True:
            try:
                ref, retained = self._transfer_queue.get_nowait()
            except queue.Empty:
                break
            if retained:
                self._release_ref(ref, "queued_dir_item")

    def run(self) -> int:
        try:
            if hasattr(os, "add_dll_directory"):
                self._dll_dir_handle = os.add_dll_directory(str(self.dll_path.parent))

            log(f"[STEP] load dll: {self.dll_path}")
            self.sdk = ctypes.WinDLL(str(self.dll_path))
            self._bind_api()

            self._ensure_ok(self.sdk.EdsInitializeSDK(), "EdsInitializeSDK")
            self.sdk_initialized = True
            log("[OK] SDK initialized")

            self._ensure_ok(
                self.sdk.EdsGetCameraList(ctypes.byref(self.camera_list)),
                "EdsGetCameraList",
            )
            count = ctypes.c_uint32(0)
            self._ensure_ok(
                self.sdk.EdsGetChildCount(self.camera_list, ctypes.byref(count)),
                "EdsGetChildCount",
            )
            log(f"[INFO] camera count={count.value}")
            if count.value < 1:
                raise RuntimeError("No camera detected.")

            self._ensure_ok(
                self.sdk.EdsGetChildAtIndex(self.camera_list, 0, ctypes.byref(self.camera)),
                "EdsGetChildAtIndex(0)",
            )
            err = self.sdk.EdsOpenSession(self.camera)
            if err == EDS_ERR_DEVICE_BUSY:
                raise RuntimeError(
                    "EdsOpenSession failed: camera busy. Close EOS Utility and retry."
                )
            self._ensure_ok(err, "EdsOpenSession")
            self.session_opened = True
            log("[OK] session opened")

            save_to = ctypes.c_uint32(K_EDS_SAVE_TO_HOST)
            err = self.sdk.EdsSetPropertyData(
                self.camera,
                K_EDS_PROP_ID_SAVE_TO,
                0,
                ctypes.sizeof(save_to),
                ctypes.byref(save_to),
            )
            log(
                "[INFO] SaveTo Host set result: "
                f"{hex_err(err)} {describe_error(err)}"
            )
            if err != EDS_ERR_OK:
                save_to = ctypes.c_uint32(K_EDS_SAVE_TO_BOTH)
                err2 = self.sdk.EdsSetPropertyData(
                    self.camera,
                    K_EDS_PROP_ID_SAVE_TO,
                    0,
                    ctypes.sizeof(save_to),
                    ctypes.byref(save_to),
                )
                log(
                    "[INFO] SaveTo Both fallback result: "
                    f"{hex_err(err2)} {describe_error(err2)}"
                )
                self._ensure_ok(err2, "EdsSetPropertyData(SaveTo=Both)")
            else:
                log("[OK] SaveTo=Host configured")

            capacity = EdsCapacity(
                numberOfFreeClusters=0x7FFFFFFF,
                bytesPerSector=4096,
                reset=1,
            )
            err = self.sdk.EdsSetCapacity(self.camera, capacity)
            log(f"[INFO] SetCapacity result: {hex_err(err)} {describe_error(err)}")
            self._ensure_ok(err, "EdsSetCapacity")
            log("[OK] SetCapacity configured")

            self._object_handler_ref = OBJECT_EVENT_HANDLER(self._event_handler)
            self._ensure_ok(
                self.sdk.EdsSetObjectEventHandler(
                    self.camera,
                    K_EDS_OBJECT_EVENT_ALL,
                    self._object_handler_ref,
                    None,
                ),
                "EdsSetObjectEventHandler",
            )
            log("[OK] object event handler set")

            self._ensure_ok(
                self.sdk.EdsSendCommand(
                    self.camera,
                    K_EDS_CAMERA_COMMAND_TAKE_PICTURE,
                    0,
                ),
                "EdsSendCommand(TakePicture)",
            )
            log("[OK] take picture command sent")

            deadline = time.perf_counter() + (self.timeout_ms / 1000.0)
            while time.perf_counter() < deadline:
                err = self.sdk.EdsGetEvent()
                if err != EDS_ERR_OK:
                    log(
                        "[WARN] EdsGetEvent: "
                        f"{hex_err(err)} {describe_error(err)}"
                    )

                try:
                    dir_item, retained = self._transfer_queue.get_nowait()
                except queue.Empty:
                    time.sleep(0.015)
                    continue

                try:
                    out_file = self._download_dir_item(dir_item)
                finally:
                    if retained:
                        self._release_ref(dir_item, "dir_item")

                log(f"[OK] capture downloaded: {out_file}")
                return 0

            raise TimeoutError(
                f"Timeout waiting for DirItemRequestTransfer ({self.timeout_ms}ms)."
            )

        except Exception as exc:
            log(f"[ERR] {exc}")
            return 1
        finally:
            self._drain_queue_refs()
            if self.sdk is not None:
                if self.session_opened and self.camera and self.camera.value:
                    err = self.sdk.EdsCloseSession(self.camera)
                    if err != EDS_ERR_OK:
                        log(
                            "[WARN] EdsCloseSession: "
                            f"{hex_err(err)} {describe_error(err)}"
                        )
                self.session_opened = False

                self._release_ref(self.camera, "camera")
                self._release_ref(self.camera_list, "camera_list")

                if self.sdk_initialized:
                    err = self.sdk.EdsTerminateSDK()
                    if err != EDS_ERR_OK:
                        log(
                            "[WARN] EdsTerminateSDK: "
                            f"{hex_err(err)} {describe_error(err)}"
                        )

            self.camera = ctypes.c_void_p()
            self.camera_list = ctypes.c_void_p()
            self.sdk = None
            self._object_handler_ref = None
            self.sdk_initialized = False

            if self._dll_dir_handle is not None:
                try:
                    self._dll_dir_handle.close()
                except Exception:
                    pass
                self._dll_dir_handle = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Canon EDSDK capture probe: take picture and download to PC."
    )
    parser.add_argument("--dll", required=True, help=r"Path to EDSDK.dll")
    parser.add_argument(
        "--out",
        default=None,
        help=r'Output file path (e.g. "out\capture.jpg"). If omitted, timestamp name is used.',
    )
    parser.add_argument("--timeout_ms", type=int, default=15000, help="Event wait timeout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dll = Path(args.dll)
    if not dll.is_file():
        log(f"[ERR] DLL not found: {dll}")
        return 2

    out_path = Path(args.out) if args.out else None
    probe = CanonCaptureProbe(dll_path=dll, out_path=out_path, timeout_ms=args.timeout_ms)
    return probe.run()


if __name__ == "__main__":
    raise SystemExit(main())
