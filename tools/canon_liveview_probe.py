from __future__ import annotations

import argparse
import ctypes
import platform
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from kiosk.services.camera.edsdk_liveview import EdsdkLiveViewClient


def log(msg: str) -> None:
    print(msg, flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Canon EDSDK liveview probe: save one EVF frame as JPEG."
    )
    parser.add_argument("--dll", required=True, help=r"Path to EDSDK.dll")
    parser.add_argument("--out", default=r"out\evf.jpg", help=r"Output JPEG path")
    parser.add_argument("--retries", type=int, default=200, help="Retry count")
    return parser.parse_args()


def run_probe(dll_path: Path, out_path: Path, retries: int) -> int:
    bits = ctypes.sizeof(ctypes.c_void_p) * 8
    log(f"[INFO] Python: {platform.python_version()} ({bits}-bit)")
    if bits != 64:
        log("[WARN] This probe is intended for 64-bit Python.")

    client = EdsdkLiveViewClient(
        dll_path=str(dll_path),
        retries=max(1, int(retries)),
        retry_sleep_sec=0.015,
    )

    try:
        log(f"[INFO] Opening camera session with DLL: {dll_path}")
        client.open()
        log("[OK] Camera session opened, EVF output set to PC")

        log("[INFO] Downloading one EVF frame...")
        data = client.get_frame_jpeg_bytes()
        if not data:
            raise RuntimeError("Empty EVF frame bytes returned.")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
        log(f"[OK] Saved EVF JPEG: {out_path} ({len(data)} bytes)")
        log("EDSDK/카메라 연결 OK")
        return 0
    except Exception as exc:
        log(f"[ERR] {exc}")
        msg = str(exc)
        if "bitness mismatch" in msg:
            log(
                "[HINT] WinError 193 often means Python/DLL bitness mismatch. "
                "Use matching 64-bit Python and EDSDK."
            )
        if "EdsOpenSession" in msg and "DEVICE_BUSY" in msg:
            log("[HINT] Camera is busy. Close EOS Utility and retry.")
        return 1
    finally:
        client.close()


def main() -> int:
    args = parse_args()
    dll_path = Path(args.dll)
    if not dll_path.is_file():
        log(f"[ERR] DLL not found: {dll_path}")
        return 2
    out_path = Path(args.out)
    return run_probe(dll_path=dll_path, out_path=out_path, retries=args.retries)


if __name__ == "__main__":
    raise SystemExit(main())
