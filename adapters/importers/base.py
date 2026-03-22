from __future__ import annotations

from abc import ABC, abstractmethod

from domain.value_objects.normalized_transaction import NormalizedTransaction


class StatementImporter(ABC):
    source_type: str

    @abstractmethod
    def can_handle(self, filename: str, mime_type: str, sample: bytes) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, file_bytes: bytes) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_record: dict) -> NormalizedTransaction:
        raise NotImplementedError

