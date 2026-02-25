from __future__ import annotations

import argparse
import re
import time
from datetime import datetime
from pathlib import Path

try:
    import serial
    from serial import SerialException
except ImportError as exc:
    raise SystemExit(
        "pyserial is required. Install with: pip install pyserial"
    ) from exc


PARITY_MAP = {
    "N": serial.PARITY_NONE,
    "E": serial.PARITY_EVEN,
    "O": serial.PARITY_ODD,
}


def now_ts() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def normalize_port(port: str) -> str:
    p = port.strip()
    if p.upper().startswith("COM"):
        suffix = p[3:]
        if suffix.isdigit() and int(suffix) >= 10:
            return f"\\\\.\\{p.upper()}"
    return p


def format_hex(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def parse_hex_bytes(text: str) -> bytes:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("empty poll frame")
    tokens = re.split(r"[\s,]+", cleaned)
    out = bytearray()
    for token in tokens:
        if not token:
            continue
        token = token.lower().removeprefix("0x")
        if len(token) > 2:
            raise ValueError(f"invalid token '{token}'")
        out.append(int(token, 16))
    if not out:
        raise ValueError("empty poll frame")
    return bytes(out)


class LineLogger:
    def __init__(self, log_path: str | None) -> None:
        self._fp = None
        if log_path:
            path = Path(log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fp = path.open("a", encoding="utf-8")
            self.write(f"# bill_poller started {datetime.now().isoformat(timespec='seconds')}")

    def write(self, line: str) -> None:
        print(line, flush=True)
        if self._fp is not None:
            self._fp.write(line + "\n")
            self._fp.flush()

    def close(self) -> None:
        if self._fp is not None:
            self._fp.close()
            self._fp = None


def emit_line(logger: LineLogger, direction: str, chunk: bytes) -> int:
    total = 0
    for i in range(0, len(chunk), 32):
        part = chunk[i : i + 32]
        total += len(part)
        logger.write(f"{now_ts()} {direction}: {format_hex(part)}")
    return total


def open_serial(port: str, baud: int, parity: str, timeout: float):
    return serial.Serial(
        port=normalize_port(port),
        baudrate=int(baud),
        bytesize=serial.EIGHTBITS,
        parity=PARITY_MAP[parity],
        stopbits=serial.STOPBITS_ONE,
        timeout=timeout,
    )


def parse_poll_frames(args: argparse.Namespace) -> list[bytes]:
    if not args.poll:
        return [b"\x05"]  # ENQ default
    frames: list[bytes] = []
    for raw in args.poll:
        frames.append(parse_hex_bytes(raw))
    return frames


def run(args: argparse.Namespace) -> int:
    logger = LineLogger(args.log)
    tx_bytes = 0
    tx_frames = 0
    rx_bytes = 0
    rx_frames = 0

    try:
        poll_frames = parse_poll_frames(args)
    except ValueError as exc:
        logger.write(f"[ERR] invalid --poll: {exc}")
        logger.close()
        return 2

    logger.write(
        f"[OPEN] port={args.port} baud={args.baud} parity={args.parity} "
        f"interval_ms={args.interval_ms} read_window_ms={args.read_window_ms}"
    )
    logger.write(
        f"[INFO] poll_frames={len(poll_frames)} "
        + ", ".join(format_hex(frame) for frame in poll_frames)
    )
    if not args.poll:
        logger.write("[INFO] --poll not given; default ENQ(05) is used.")

    start = time.monotonic()
    try:
        with open_serial(args.port, args.baud, args.parity, args.timeout) as ser:
            logger.write("[INFO] Polling... Press Ctrl+C to stop.")
            idx = 0
            interval_sec = max(0.01, args.interval_ms / 1000.0)
            read_window_sec = max(0.0, args.read_window_ms / 1000.0)

            while True:
                frame = poll_frames[idx]
                ser.write(frame)
                ser.flush()
                tx_bytes += emit_line(logger, "TX", frame)
                tx_frames += 1

                deadline = time.monotonic() + read_window_sec
                got_rx = False
                while time.monotonic() < deadline:
                    chunk = ser.read(ser.in_waiting or 1)
                    if not chunk:
                        continue
                    rx_bytes += emit_line(logger, "RX", chunk)
                    rx_frames += 1
                    got_rx = True

                elapsed = time.monotonic() - (deadline - read_window_sec)
                remain = interval_sec - elapsed
                if remain > 0:
                    time.sleep(remain)

                idx = (idx + 1) % len(poll_frames)

                # Optional fast drain of delayed bytes.
                if not got_rx and ser.in_waiting:
                    chunk = ser.read(ser.in_waiting)
                    if chunk:
                        rx_bytes += emit_line(logger, "RX", chunk)
                        rx_frames += 1

    except KeyboardInterrupt:
        logger.write("[INFO] Stopped by user.")
    except SerialException as exc:
        logger.write(f"[ERR] Serial open/read failed: {exc}")
        return 2
    finally:
        elapsed = max(0.0, time.monotonic() - start)
        logger.write(
            f"[SUMMARY] tx_frames={tx_frames} tx_bytes={tx_bytes} "
            f"rx_frames={rx_frames} rx_bytes={rx_bytes} elapsed={elapsed:.2f}s"
        )
        if rx_bytes == 0:
            logger.write(
                "[INFO] No RX bytes. Check wiring/baud/parity or protocol-specific polling command."
            )
            logger.write(
                "[INFO] If sniffer also shows nothing, this device likely needs exact poll command."
            )
        logger.close()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RS232 poll sender + sniffer for bill acceptor testing."
    )
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM3")
    parser.add_argument("--baud", type=int, default=9600, help="Baud rate (default: 9600)")
    parser.add_argument(
        "--parity",
        choices=("N", "E", "O"),
        default="N",
        help="Parity (default: N)",
    )
    parser.add_argument(
        "--poll",
        action="append",
        help="HEX bytes to send periodically, e.g. --poll \"05\" or --poll \"02 10 03\". "
        "Can be repeated.",
    )
    parser.add_argument(
        "--interval-ms",
        type=int,
        default=200,
        help="Poll interval ms (default: 200)",
    )
    parser.add_argument(
        "--read-window-ms",
        type=int,
        default=120,
        help="RX listen window after each TX in ms (default: 120)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.05,
        help="Serial read timeout seconds (default: 0.05)",
    )
    parser.add_argument("--log", help="Optional log file path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.port = normalize_port(args.port)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
