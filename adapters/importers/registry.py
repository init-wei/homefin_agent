from adapters.importers.base import StatementImporter
from adapters.importers.simple_bank_csv import SimpleBankCSVImporter
from adapters.importers.wechat_csv import WechatCSVImporter


class ImporterRegistry:
    def __init__(self, importers: list[StatementImporter]) -> None:
        self.importers = importers

    def pick(self, *, filename: str, mime_type: str, sample: bytes) -> StatementImporter:
        for importer in self.importers:
            if importer.can_handle(filename, mime_type, sample):
                return importer
        raise ValueError(f"No importer available for {filename}.")


def default_importer_registry() -> ImporterRegistry:
    return ImporterRegistry([WechatCSVImporter(), SimpleBankCSVImporter()])

