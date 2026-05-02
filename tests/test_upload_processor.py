"""Tests for upload_processor module."""

import sqlite3
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from emoji_counter.upload_processor import (
    extract_zip_file,
    process_uploaded_file,
    process_uploaded_file_from_path,
)


def create_signal_zip() -> BytesIO:
    """Create a test .zip file with Signal format data."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # Signal format message file
        signal_content = """Conversation: John Doe (phone-123)

From: You
Type: outgoing
Sent: Mon, 1 Jan 2024 10:00:00 +0200

Hey John! 😊

From: John Doe (phone-123)
Type: incoming
Sent: Mon, 1 Jan 2024 10:05:00 +0200
Received: Mon, 1 Jan 2024 10:05:01 +0200

Hello! How are you? 👋

"""
        zf.writestr("John Doe (phone-123).txt", signal_content)
    zip_buffer.seek(0)
    return zip_buffer


def create_whatsapp_zip() -> BytesIO:
    """Create a test .zip file with WhatsApp format data."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # WhatsApp format message file
        whatsapp_content = """2024-01-01 10:00 - Alice: Hi there! 😊
2024-01-01 10:05 - Bob: Hello Alice 👋
"""
        zf.writestr("WhatsApp-chatt med Alice.txt", whatsapp_content)
    zip_buffer.seek(0)
    return zip_buffer


def create_messenger_zip() -> BytesIO:
    """Create a test .zip file with Messenger format data."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # Messenger format - requires directory structure with both inbox and e2ee_cutover
        messenger_content = """{
  "title": "Alice",
  "messages": [
    {
      "timestamp_ms": 1704110400000,
      "sender_name": "You",
      "content": "Hey Alice! 😊"
    },
    {
      "timestamp_ms": 1704110700000,
      "sender_name": "Alice",
      "content": "Hi! 👋"
    }
  ]
}"""
        # Messenger requires both inbox and e2ee_cutover directories
        zf.writestr(
            "your_facebook_activity/messages/inbox/Alice_123/message_1.json",
            messenger_content,
        )
        zf.writestr(
            "your_facebook_activity/messages/e2ee_cutover/placeholder.txt",
            "placeholder",
        )
    zip_buffer.seek(0)
    return zip_buffer


class TestExtractZipFile:
    """Tests for extract_zip_file function."""

    def test_extract_valid_zip(self, tmp_path: Path) -> None:
        """Extract a valid .zip file."""
        zip_buffer = create_signal_zip()

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        extract_zip_file(zip_buffer.getvalue(), extract_dir)

        # Check that files were extracted
        extracted_files = list(extract_dir.glob("*.txt"))
        assert len(extracted_files) > 0
        assert any("John Doe" in f.name for f in extracted_files)

    def test_extract_invalid_zip(self, tmp_path: Path) -> None:
        """Extract invalid zip data raises error."""
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        with pytest.raises(zipfile.BadZipFile):
            extract_zip_file(b"not a zip file", extract_dir)


class TestProcessUploadedFile:
    """Tests for process_uploaded_file function."""

    def test_process_signal_format(self, tmp_path: Path) -> None:
        """Process Signal format upload creates database."""
        zip_buffer = create_signal_zip()
        output_db = tmp_path / "emojis.sql"

        result = process_uploaded_file(
            zip_buffer.getvalue(),
            "Signal",
            output_db,
        )

        assert result == output_db
        assert output_db.exists()

        # Verify database has emojis table
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "emojis" in tables

        # Verify data was extracted
        cursor.execute("SELECT COUNT(*) FROM emojis")
        count = cursor.fetchone()[0]
        assert count > 0

        conn.close()

    def test_process_whatsapp_format(self, tmp_path: Path) -> None:
        """Process WhatsApp format upload creates database."""
        zip_buffer = create_whatsapp_zip()
        output_db = tmp_path / "emojis.sql"

        result = process_uploaded_file(
            zip_buffer.getvalue(),
            "Whatsapp",
            output_db,
            your_name="Alice",
        )

        assert result == output_db
        assert output_db.exists()

        # Verify database has data
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emojis")
        count = cursor.fetchone()[0]
        assert count > 0
        conn.close()

    def test_process_messenger_format(self, tmp_path: Path) -> None:
        """Process Messenger format upload creates database."""
        zip_buffer = create_messenger_zip()
        output_db = tmp_path / "emojis.sql"

        result = process_uploaded_file(
            zip_buffer.getvalue(),
            "Messenger",
            output_db,
            your_name="You",
        )

        assert result == output_db
        assert output_db.exists()

        # Verify database has data
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emojis")
        count = cursor.fetchone()[0]
        assert count > 0
        conn.close()

    def test_invalid_format_raises_error(self, tmp_path: Path) -> None:
        """Invalid format raises ValueError."""
        zip_buffer = create_signal_zip()
        output_db = tmp_path / "emojis.sql"

        with pytest.raises(ValueError, match="Unknown format"):
            process_uploaded_file(
                zip_buffer.getvalue(),
                "InvalidFormat",
                output_db,
            )

    def test_invalid_zip_raises_error(self, tmp_path: Path) -> None:
        """Invalid zip file raises error."""
        output_db = tmp_path / "emojis.sql"

        with pytest.raises(zipfile.BadZipFile):
            process_uploaded_file(
                b"not a zip file",
                "Signal",
                output_db,
            )


class TestProcessUploadedFileFromPath:
    """Tests for process_uploaded_file_from_path function."""

    def test_process_from_file_path(self, tmp_path: Path) -> None:
        """Process upload from file path on disk."""
        # Create a zip file on disk
        zip_path = tmp_path / "test.zip"
        zip_buffer = create_signal_zip()
        zip_path.write_bytes(zip_buffer.getvalue())

        output_db = tmp_path / "emojis.sql"

        result = process_uploaded_file_from_path(
            zip_path,
            "Signal",
            output_db,
        )

        assert result == output_db
        assert output_db.exists()

        # Verify database
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emojis")
        count = cursor.fetchone()[0]
        assert count > 0
        conn.close()

    def test_database_schema(self, tmp_path: Path) -> None:
        """Verify created database has correct schema."""
        zip_buffer = create_signal_zip()
        output_db = tmp_path / "emojis.sql"

        process_uploaded_file(
            zip_buffer.getvalue(),
            "Signal",
            output_db,
        )

        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()

        # Check table schema
        cursor.execute("PRAGMA table_info(emojis)")
        columns = {row[1] for row in cursor.fetchall()}

        expected_columns = {"emoji", "timestamp", "username", "chat_name"}
        assert expected_columns.issubset(columns)

        conn.close()

    def test_emoji_extraction_in_database(self, tmp_path: Path) -> None:
        """Verify emojis are correctly extracted and stored."""
        zip_buffer = create_signal_zip()
        output_db = tmp_path / "emojis.sql"

        process_uploaded_file(
            zip_buffer.getvalue(),
            "Signal",
            output_db,
        )

        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()

        # Check for emojis
        cursor.execute("SELECT DISTINCT emoji FROM emojis")
        emojis = {row[0] for row in cursor.fetchall()}

        # Signal zip contains 😊 and 👋
        assert "😊" in emojis
        assert "👋" in emojis

        conn.close()
