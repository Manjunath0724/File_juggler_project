"""Unit tests for client-side encryption and zero-storage security."""
import os
import tempfile
from pathlib import Path

from src.services.encryption_service import EncryptionService
from src.services.settings_service import SettingsService
from src.services.history_service import HistoryService
from src.models.operation_result import OperationResult, MoveRecord


def test_encryption_roundtrip():
    original_text = "C:\\Users\\SecretUser\\ImportantDownloads"
    token = EncryptionService.encrypt_string(original_text)
    assert token.startswith(EncryptionService.MAGIC_HEADER)
    assert token != original_text

    decrypted = EncryptionService.decrypt_string(token)
    assert decrypted == original_text


def test_encryption_dict_roundtrip():
    payload = {
        "folder": "D:\\Personal\\Photos",
        "nested": {"rules": [1, 2, 3]},
        "sensitive": True
    }
    cipher_token = EncryptionService.encrypt_data(payload)
    assert cipher_token.startswith(EncryptionService.MAGIC_HEADER)

    restored = EncryptionService.decrypt_data(cipher_token)
    assert restored == payload


def test_settings_encrypted_on_disk():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        settings_file = tmp_path / "settings.json"

        # Mock settings service to use temp file
        service = SettingsService()
        service.config_file = settings_file

        settings = service.load()
        settings["last_source_folder"] = "C:\\TopSecret\\Files"
        service.save(settings)

        # Verify disk file is encrypted and does not expose plain folder path
        disk_content = settings_file.read_text(encoding="utf-8")
        assert EncryptionService.is_encrypted(disk_content)
        assert "C:\\TopSecret\\Files" not in disk_content

        # Verify reload decrypts properly
        loaded = service.load()
        assert loaded["last_source_folder"] == "C:\\TopSecret\\Files"


def test_history_encrypted_on_disk():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        history_file = tmp_path / "history.json"

        service = HistoryService(config_dir=tmp_path)
        result = OperationResult(
            session_id="test-enc-001",
            mode="file_type",
            source_folder="C:\\Source",
            destination_folder="C:\\Dest",
            moves=[MoveRecord(
                source="C:\\Source\\tax_return.pdf",
                destination="C:\\Dest\\Documents\\tax_return.pdf",
                timestamp=1726200000.0,
                file_size=1024,
                category="Documents",
                original_name="tax_return.pdf",
                final_name="tax_return.pdf"
            )]
        )

        service.record_session(result)

        # Verify raw file content on disk is encrypted
        raw_disk = history_file.read_text(encoding="utf-8")
        assert EncryptionService.is_encrypted(raw_disk)
        assert "tax_return.pdf" not in raw_disk

        # Verify reading history decrypts correctly
        history = service.get_history()
        assert len(history) == 1
        assert history[0]["session_id"] == "test-enc-001"
        assert history[0]["moves"][0]["source"] == "C:\\Source\\tax_return.pdf"
