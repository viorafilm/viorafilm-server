from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Uploader(ABC):
    @abstractmethod
    def upload_print(self, session_id: str, print_path: Path) -> str:
        raise NotImplementedError
