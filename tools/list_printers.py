#!/usr/bin/env python
"""List installed Windows printer queue names and the default printer."""

from __future__ import annotations

import sys

try:
    import win32print
except ImportError:
    print("pywin32 is required. Install with: pip install pywin32")
    sys.exit(1)


def _printer_names() -> list[str]:
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = win32print.EnumPrinters(flags)
    names = [entry[2] for entry in printers if len(entry) > 2 and entry[2]]
    return sorted(set(names), key=str.casefold)


def main() -> int:
    names = _printer_names()
    default_printer = win32print.GetDefaultPrinter()

    print("Installed printers:")
    if names:
        for name in names:
            marker = " (default)" if name == default_printer else ""
            print(f"- {name}{marker}")
    else:
        print("- (none)")

    print(f"Default printer: {default_printer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
