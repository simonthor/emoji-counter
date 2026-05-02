#!/usr/bin/env python3
"""
Process uploaded .zip files containing chat exports.

Handles extraction, format conversion, and emoji extraction from uploaded
chat data in various formats (Signal, WhatsApp, Messenger).
"""

import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

from emoji_counter.emoji_extract import export_to_sqlite
from emoji_counter.emoji_extract import process_input as extract_emoji_process
from emoji_counter.message_convert import process_input as convert_messages_process


def extract_zip_file(zip_bytes: bytes, output_dir: Path) -> None:
    """
    Extract a zip file from bytes into the specified directory.

    Parameters
    ----------
    zip_bytes : bytes
        Raw bytes of the zip file.
    output_dir : Path
        Directory where the contents will be extracted.

    Raises
    ------
    zipfile.BadZipFile
        If the provided bytes are not a valid zip file.
    """
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        zf.extractall(output_dir)


def process_uploaded_file(
    zip_bytes: bytes,
    chat_format: str,
    output_db_path: Path,
    your_name: str | None = None,
    name_pattern: str | None = None,
) -> Path:
    """
    Process an uploaded .zip file and generate an emoji database.

    Handles extraction, optional message conversion, and emoji extraction
    for the uploaded data. Returns the path to the generated SQLite database.

    For WhatsApp and Messenger formats, automatically runs message-convert
    before emoji extraction. Signal format data is assumed to be pre-converted
    to sigtop format.

    Parameters
    ----------
    zip_bytes : bytes
        Raw bytes of the uploaded zip file.
    chat_format : str
        Format of the chat data. One of: 'Signal', 'Whatsapp', 'Messenger'.
    output_db_path : Path
        Path where the output SQLite database will be created.
    your_name : str, optional
        Your display name in the chat (used during conversion).
    name_pattern : str, optional
        Pattern to extract chat name from filename (used for WhatsApp).

    Returns
    -------
    Path
        Path to the created SQLite database.

    Raises
    ------
    ValueError
        If chat_format is not recognized.
    zipfile.BadZipFile
        If the uploaded file is not a valid zip file.
    """
    if chat_format not in ("Signal", "Whatsapp", "Messenger"):
        raise ValueError(
            f"Unknown format: {chat_format}. "
            "Must be one of: Signal, Whatsapp, Messenger"
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_dir = temp_path / "extracted"
        extract_dir.mkdir()

        # Extract the zip file
        extract_zip_file(zip_bytes, extract_dir)

        # Handle case where zip extracts to a subdirectory
        # (e.g., Signal.zip extracts to "extracted/Signal/")
        # (e.g., WhatsApp.zip extracts to "extracted/Whatsapp original/")
        # (e.g., Messenger.zip extracts to "extracted/Messenger original/")
        contents = list(extract_dir.iterdir())
        messages_source = extract_dir

        # Only descend into subdirectory if:
        # 1. There's exactly one subdirectory, AND
        # 2. There are no .txt files at the root level (for Signal/WhatsApp), AND
        # 3. The required structure is NOT at the root level
        if (
            len(contents) == 1
            and contents[0].is_dir()
            and not list(extract_dir.glob("*.txt"))
        ):
            # Check if the structure we're looking for is already at root
            # For Messenger, check for your_facebook_activity
            # For Signal/WhatsApp, they don't have this structure requirement
            has_required_structure = False
            if chat_format == "Messenger":
                has_required_structure = (
                    extract_dir / "your_facebook_activity" / "messages"
                ).is_dir()

            # If structure is not at root, try the subdirectory
            if not has_required_structure:
                messages_source = contents[0]

        # Create conversion directory for non-Signal formats
        if chat_format != "Signal":
            converted_dir = temp_path / "converted"
            converted_dir.mkdir()

            # Convert messages to sigtop format
            convert_messages_process(
                messages_source,
                converted_dir,
                your_name=your_name,
                name_pattern=name_pattern,
                chat_format=chat_format,
            )
            messages_dir = converted_dir
        else:
            messages_dir = messages_source

        # Extract emojis from the messages
        df = extract_emoji_process(messages_dir)
        export_to_sqlite(df, output_db_path)

    return output_db_path


def process_uploaded_file_from_path(
    uploaded_file_path: Path,
    chat_format: str,
    output_db_path: Path,
    your_name: str | None = None,
    name_pattern: str | None = None,
) -> Path:
    """
    Process an uploaded file from disk and generate an emoji database.

    This is a convenience wrapper for process_uploaded_file that reads from disk
    instead of accepting raw bytes. Useful for testing.

    Parameters
    ----------
    uploaded_file_path : Path
        Path to the uploaded zip file on disk.
    chat_format : str
        Format of the chat data. One of: 'Signal', 'Whatsapp', 'Messenger'.
    output_db_path : Path
        Path where the output SQLite database will be created.
    your_name : str, optional
        Your display name in the chat (used during conversion).
    name_pattern : str, optional
        Pattern to extract chat name from filename (used for WhatsApp).

    Returns
    -------
    Path
        Path to the created SQLite database.
    """
    with open(uploaded_file_path, "rb") as f:
        zip_bytes = f.read()

    return process_uploaded_file(
        zip_bytes,
        chat_format,
        output_db_path,
        your_name=your_name,
        name_pattern=name_pattern,
    )
