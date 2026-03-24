#!/usr/bin/env python
import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    src_manage = base_dir / "src" / "manage.py"
    if src_manage.exists():
        os.chdir(src_manage.parent)
        sys.argv[0] = str(src_manage)
        runpy.run_path(str(src_manage), run_name="__main__")
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your "
            "PYTHONPATH environment variable? Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
