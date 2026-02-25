from __future__ import annotations

import argparse
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

SCAN_BAUDS = (9600, 19200, 38400)
SCAN_PARITIES = ("N", "E", "O")


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


class LineLogger:
    def __init__(self, log_path: str | None) -> None:
        self._fp = None
        if log_path:
            path = Path(log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fp = path.open("a", encoding="utf-8")
            self.write(f"# bill_sniffer started {datetime.now().isoformat(timespec='seconds')}")

    def write(self, line: str) -> None:
        print(line, flush=True)
        if self._fp is not None:
            self._fp.write(line + "\n")
            self._fp.flush()

    def close(self) -> None:
        if self._fp is not None:
            self._fp.close()
            self._fp = None


def emit_rx(logger: LineLogger, chunk: bytes) -> int:
    if not chunk:
        return 0
    total = 0
    for i in range(0, len(chunk), 32):
        part = chunk[i : i + 32]
        total += len(part)
        logger.write(f"{now_ts()} RX: {format_hex(part)}")
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


def sniff_once(ser, duration_sec: float, logger: LineLogger) -> int:
    total_bytes = 0
    deadline = time.monotonic() + duration_sec
    while time.monotonic() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if not chunk:
            continue
        total_bytes += emit_rx(logger, chunk)
    return total_bytes


def run_scan(args: argparse.Namespace, logger: LineLogger) -> int:
    logger.write(
        f"[SCAN] port={args.port} duration={args.scan_seconds:.1f}s "
        f"combos={len(SCAN_BAUDS) * len(SCAN_PARITIES)}"
    )
    results: list[tuple[int, int, str]] = []
    any_opened = False

    for baud in SCAN_BAUDS:
        for parity in SCAN_PARITIES:
            logger.write(f"[SCAN] listen baud={baud} parity={parity} ...")
            try:
                with open_serial(args.port, baud, parity, args.timeout) as ser:
                    any_opened = True
                    count = sniff_once(ser, args.scan_seconds, logger)
            except SerialException as exc:
                logger.write(f"[SCAN] open failed baud={baud} parity={parity}: {exc}")
                continue

            logger.write(f"[SCAN] result baud={baud} parity={parity} bytes={count}")
            results.append((count, baud, parity))

    if not any_opened:
        logger.write("[ERR] Could not open serial port in scan mode.")
        return 2

    matched = [item for item in results if item[0] > 0]
    if not matched:
        logger.write(
            "[INFO] No RX bytes detected in scan mode. Polling may be required by the bill acceptor."
        )
        return 0

    matched.sort(reverse=True)
    logger.write("[SCAN] Recommended combinations (highest RX bytes first):")
    for count, baud, parity in matched[:3]:
        logger.write(f"[SCAN] baud={baud} parity={parity} bytes={count}")
    return 0


def run_sniffer(args: argparse.Namespace, logger: LineLogger) -> int:
    total_bytes = 0
    start = time.monotonic()
    try:
        with open_serial(args.port, args.baud, args.parity, args.timeout) as ser:
            logger.write(
                f"[OPEN] port={args.port} baud={args.baud} parity={args.parity} "
                f"timeout={args.timeout:.3f}s"
            )
            logger.write("[INFO] Listening... Press Ctrl+C to stop.")
            while True:
                chunk = ser.read(ser.in_waiting or 1)
                if not chunk:
                    continue
                total_bytes += emit_rx(logger, chunk)
    except KeyboardInterrupt:
        logger.write("[INFO] Stopped by user.")
    except SerialException as exc:
        logger.write(f"[ERR] Serial open/read failed: {exc}")
        return 2
    finally:
        elapsed = max(0.0, time.monotonic() - start)
        logger.write(f"[SUMMARY] total_bytes={total_bytes} elapsed={elapsed:.2f}s")
        if total_bytes == 0:
            logger.write(
                "[INFO] No RX bytes detected. Polling may be required by the bill acceptor."
            )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RS232 sniffer for bill acceptor signal discovery."
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
        "--timeout",
        type=float,
        default=0.1,
        help="Read timeout seconds (default: 0.1)",
    )
    parser.add_argument("--log", help="Optional log file path")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan baud/parity combinations (9600/19200/38400 x N/E/O)",
    )
    parser.add_argument(
        "--scan-seconds",
        type=float,
        default=3.0,
        help="Listen seconds per scan combination (default: 3.0)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.port = normalize_port(args.port)
    logger = LineLogger(args.log)
    try:
        if args.scan:
            return run_scan(args, logger)
        return run_sniffer(args, logger)
    finally:
        logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
