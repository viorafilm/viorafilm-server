import os
import sys
from pathlib import Path


def main():
    project_dir = Path(__file__).resolve().parent
    project_dir_str = str(project_dir)
    repo_root = project_dir.parent.resolve()
    cwd_before = Path.cwd().resolve()

    cleaned_sys_path: list[str] = []
    for entry in sys.path:
        raw_entry = entry or str(cwd_before)
        try:
            resolved_entry = Path(raw_entry).resolve()
        except Exception:
            resolved_entry = None
        if resolved_entry == repo_root and resolved_entry != project_dir.resolve():
            continue
        if entry == project_dir_str:
            continue
        cleaned_sys_path.append(entry)

    os.chdir(project_dir)
    sys.path = [project_dir_str] + cleaned_sys_path

    try:
        from dotenv import load_dotenv

        root = project_dir.parent
        load_dotenv(root / ".env")
    except Exception:
        pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
