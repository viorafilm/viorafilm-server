from __future__ import annotations

import ctypes
import os
import time
from pathlib import Path
from typing import Optional

EDS_ERR_OK = 0x00000000
EDS_ERR_DEVICE_BUSY = 0x00000081
EDS_ERR_OBJECT_NOTREADY = 0x0000A102

K_EDS_PROP_ID_EVF_OUTPUT_DEVICE = 0x00000500
K_EDS_EVF_OUTPUT_DEVICE_PC = 0x00000002


def _hex_err(code: int) -> str:
    return f"0x{code:08X}"


def _describe_error(code: int) -> str:
    if code == EDS_ERR_OK:
        return "EDS_ERR_OK"
    if code == EDS_ERR_OBJECT_NOTREADY:
        return "EDS_ERR_OBJECT_NOTREADY"
    if code == EDS_ERR_DEVICE_BUSY:
        return "EDS_ERR_DEVICE_BUSY"
    return "UNKNOWN_ERROR"


class EdsdkLiveViewClient:
    def __init__(
        self,
        dll_path: str,
        retries: int = 200,
        retry_sleep_sec: float = 0.015,
        stream_size: int = 8 * 1024 * 1024,
    ) -> None:
        self.dll_path = Path(dll_path)
        self.retries = max(1, int(retries))
        self.retry_sleep_sec = max(0.01, float(retry_sleep_sec))
        self.stream_size = max(1024 * 1024, int(stream_size))

        self._sdk = None
        self._dll_dir_handle = None

        self._camera_list = ctypes.c_void_p()
        self._camera = ctypes.c_void_p()
        self._stream = ctypes.c_void_p()
        self._evf = ctypes.c_void_p()

        self._sdk_initialized = False
        self._session_opened = False
        self._opened = False

    def _load_sdk(self) -> None:
        if not self.dll_path.is_file():
            raise FileNotFoundError(f"EDSDK DLL not found: {self.dll_path}")

        if hasattr(os, "add_dll_directory"):
            self._dll_dir_handle = os.add_dll_directory(str(self.dll_path.parent))

        try:
            self._sdk = ctypes.WinDLL(str(self.dll_path))
        except OSError as exc:
            if getattr(exc, "winerror", None) == 193:
                raise RuntimeError(
                    "EDSDK DLL bitness mismatch (WinError 193). "
                    "Use matching Python and EDSDK bitness."
                ) from exc
            raise

        self._bind_api()

    def _bind_api(self) -> None:
        if self._sdk is None:
            raise RuntimeError("EDSDK DLL is not loaded.")

        c_void_pp = ctypes.POINTER(ctypes.c_void_p)
        c_uint32_p = ctypes.POINTER(ctypes.c_uint32)

        self._sdk.EdsInitializeSDK.restype = ctypes.c_uint32
        self._sdk.EdsInitializeSDK.argtypes = []

        self._sdk.EdsTerminateSDK.restype = ctypes.c_uint32
        self._sdk.EdsTerminateSDK.argtypes = []

        self._sdk.EdsGetCameraList.restype = ctypes.c_uint32
        self._sdk.EdsGetCameraList.argtypes = [c_void_pp]

        self._sdk.EdsGetChildCount.restype = ctypes.c_uint32
        self._sdk.EdsGetChildCount.argtypes = [ctypes.c_void_p, c_uint32_p]

        self._sdk.EdsGetChildAtIndex.restype = ctypes.c_uint32
        self._sdk.EdsGetChildAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_int32, c_void_pp]

        self._sdk.EdsOpenSession.restype = ctypes.c_uint32
        self._sdk.EdsOpenSession.argtypes = [ctypes.c_void_p]

        self._sdk.EdsCloseSession.restype = ctypes.c_uint32
        self._sdk.EdsCloseSession.argtypes = [ctypes.c_void_p]

        self._sdk.EdsGetPropertyData.restype = ctypes.c_uint32
        self._sdk.EdsGetPropertyData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_int32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]

        self._sdk.EdsSetPropertyData.restype = ctypes.c_uint32
        self._sdk.EdsSetPropertyData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_int32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]

        self._sdk.EdsCreateMemoryStream.restype = ctypes.c_uint32
        self._sdk.EdsCreateMemoryStream.argtypes = [ctypes.c_uint32, c_void_pp]

        self._sdk.EdsCreateEvfImageRef.restype = ctypes.c_uint32
        self._sdk.EdsCreateEvfImageRef.argtypes = [ctypes.c_void_p, c_void_pp]

        self._sdk.EdsDownloadEvfImage.restype = ctypes.c_uint32
        self._sdk.EdsDownloadEvfImage.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        self._sdk.EdsGetLength.restype = ctypes.c_uint32
        self._sdk.EdsGetLength.argtypes = [ctypes.c_void_p, c_uint32_p]

        self._sdk.EdsGetPointer.restype = ctypes.c_uint32
        self._sdk.EdsGetPointer.argtypes = [ctypes.c_void_p, c_void_pp]

        self._sdk.EdsRelease.restype = ctypes.c_uint32
        self._sdk.EdsRelease.argtypes = [ctypes.c_void_p]

    def _ensure_ok(self, err: int, stage: str) -> None:
        if err == EDS_ERR_OK:
            return

        msg = f"{stage} failed: {_hex_err(err)} {_describe_error(err)}"
        if err == EDS_ERR_DEVICE_BUSY:
            msg += " (close EOS Utility and other camera apps)"
        raise RuntimeError(msg)

    def _release_ref(self, ref: ctypes.c_void_p) -> None:
        if self._sdk is None:
            return
        if ref and ref.value:
            self._sdk.EdsRelease(ref)

    def _set_liveview_output_to_pc(self) -> None:
        if self._sdk is None:
            raise RuntimeError("EDSDK DLL is not loaded.")

        current_output = ctypes.c_uint32(0)
        err = self._sdk.EdsGetPropertyData(
            self._camera,
            K_EDS_PROP_ID_EVF_OUTPUT_DEVICE,
            0,
            ctypes.sizeof(current_output),
            ctypes.byref(current_output),
        )

        if err == EDS_ERR_OK:
            target_output = ctypes.c_uint32(current_output.value | K_EDS_EVF_OUTPUT_DEVICE_PC)
        else:
            target_output = ctypes.c_uint32(K_EDS_EVF_OUTPUT_DEVICE_PC)

        self._ensure_ok(
            self._sdk.EdsSetPropertyData(
                self._camera,
                K_EDS_PROP_ID_EVF_OUTPUT_DEVICE,
                0,
                ctypes.sizeof(target_output),
                ctypes.byref(target_output),
            ),
            "EdsSetPropertyData(Evf_OutputDevice=PC)",
        )

    def open(self) -> None:
        if self._opened:
            return

        try:
            self._load_sdk()
            self._ensure_ok(self._sdk.EdsInitializeSDK(), "EdsInitializeSDK")
            self._sdk_initialized = True

            self._ensure_ok(
                self._sdk.EdsGetCameraList(ctypes.byref(self._camera_list)),
                "EdsGetCameraList",
            )

            count = ctypes.c_uint32(0)
            self._ensure_ok(
                self._sdk.EdsGetChildCount(self._camera_list, ctypes.byref(count)),
                "EdsGetChildCount",
            )
            if count.value < 1:
                raise RuntimeError("No camera detected.")

            self._ensure_ok(
                self._sdk.EdsGetChildAtIndex(self._camera_list, 0, ctypes.byref(self._camera)),
                "EdsGetChildAtIndex(0)",
            )

            self._ensure_ok(self._sdk.EdsOpenSession(self._camera), "EdsOpenSession")
            self._session_opened = True

            self._set_liveview_output_to_pc()

            self._ensure_ok(
                self._sdk.EdsCreateMemoryStream(self.stream_size, ctypes.byref(self._stream)),
                "EdsCreateMemoryStream",
            )
            self._ensure_ok(
                self._sdk.EdsCreateEvfImageRef(self._stream, ctypes.byref(self._evf)),
                "EdsCreateEvfImageRef",
            )
            self._opened = True
        except Exception:
            self.close()
            raise

    def get_frame_jpeg_bytes(self) -> bytes:
        if not self._opened or self._sdk is None:
            raise RuntimeError("EdsdkLiveViewClient is not open.")

        last_err = EDS_ERR_OK
        for _ in range(self.retries):
            err = self._sdk.EdsDownloadEvfImage(self._camera, self._evf)
            last_err = err
            if err == EDS_ERR_OK:
                break
            if err == EDS_ERR_OBJECT_NOTREADY:
                time.sleep(self.retry_sleep_sec)
                continue
            raise RuntimeError(
                "EdsDownloadEvfImage failed: "
                f"{_hex_err(err)} {_describe_error(err)}"
            )
        else:
            raise RuntimeError(
                "EdsDownloadEvfImage retries exhausted: "
                f"{_hex_err(last_err)} {_describe_error(last_err)}"
            )

        length = ctypes.c_uint32(0)
        self._ensure_ok(self._sdk.EdsGetLength(self._stream, ctypes.byref(length)), "EdsGetLength")
        if length.value <= 0:
            raise RuntimeError("EVF data length is 0.")

        ptr = ctypes.c_void_p()
        self._ensure_ok(
            self._sdk.EdsGetPointer(self._stream, ctypes.byref(ptr)),
            "EdsGetPointer",
        )
        if not ptr.value:
            raise RuntimeError("EVF pointer is null.")

        return ctypes.string_at(ptr.value, length.value)

    def close(self) -> None:
        if self._sdk is not None:
            self._release_ref(self._evf)
            self._release_ref(self._stream)

            if self._session_opened and self._camera and self._camera.value:
                self._sdk.EdsCloseSession(self._camera)
            self._session_opened = False

            self._release_ref(self._camera)
            self._release_ref(self._camera_list)

            if self._sdk_initialized:
                self._sdk.EdsTerminateSDK()
            self._sdk_initialized = False

        self._evf = ctypes.c_void_p()
        self._stream = ctypes.c_void_p()
        self._camera = ctypes.c_void_p()
        self._camera_list = ctypes.c_void_p()
        self._sdk = None
        self._opened = False

        if self._dll_dir_handle is not None:
            try:
                self._dll_dir_handle.close()
            except Exception:
                pass
            self._dll_dir_handle = None

    def __enter__(self) -> "EdsdkLiveViewClient":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
