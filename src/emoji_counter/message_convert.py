#!/usr/bin/env python3
"""
Convert chat exports from various formats to sigtop format for use with emoji-extract.

Supported formats:
- WhatsApp: YYYY-MM-DD HH:MM - Username: Message

Sigtop output format: Multi-line blocks with From:, Type:, Sent: headers.
"""

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

WHATSAPP_MSG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) - ([^:]+): (.*)$"
)
"""Regex pattern matching WhatsApp message lines."""


@dataclass
class Message:
    """
    Parsed chat message with timestamp, sender, and content.

    Attributes
    ----------
    timestamp : datetime
        Message timestamp.
    sender : str
        Display name of the message sender.
    content : str
        Message text content.
    """

    timestamp: datetime
    sender: str
    content: str


def parse_whatsapp_file(
    file_path: Path, your_name: str | None = None
) -> list[Message]:
    """
    Parse a WhatsApp chat export file into a list of messages.

    Handles multi-line messages by accumulating content until the next
    timestamp line. Skips system messages (lines without a sender).

    Parameters
    ----------
    file_path : Path
        Path to the WhatsApp export text file.
    your_name : str, optional
        Your display name in WhatsApp. If provided, messages from
        this sender will be marked as "You" in the output.

    Returns
    -------
    list of Message
        List of parsed messages in chronological order.
    """
    messages: list[Message] = []
    current_msg: Message | None = None

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            match = WHATSAPP_MSG_PATTERN.match(line)

            if match:
                # Save previous message if exists
                if current_msg is not None:
                    messages.append(current_msg)

                timestamp_str, sender, content = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")

                # Convert sender name to "You" if it matches your_name
                if your_name and sender == your_name:
                    sender = "You"

                current_msg = Message(
                    timestamp=timestamp,
                    sender=sender,
                    content=content,
                )
            elif current_msg is not None:
                # Continuation of previous message (multi-line)
                current_msg.content += "\n" + line

    # Don't forget the last message
    if current_msg is not None:
        messages.append(current_msg)

    return messages


def parse_messenger_file(
    file_path: Path, your_name: str | None = None
) -> tuple[str, str, list[Message]]:
    """
    Parse a Messenger JSON export file into chat metadata and messages.

    Parameters
    ----------
    file_path : Path
        Path to the Messenger message_1.json file.
    your_name : str, optional
        Your display name in Messenger. If provided, messages from this sender
        will be marked as "You" in the output.

    Returns
    -------
    tuple[str, str, list[Message]]
        (chat title, chat id, parsed messages)
    """
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    chat_title = _repair_messenger_text(data["title"])
    thread_name = file_path.parent.name
    chat_id = thread_name.rsplit("_", 1)[1] if "_" in thread_name else thread_name

    messages: list[Message] = []
    for raw_msg in data.get("messages", []):
        timestamp_ms = raw_msg.get("timestamp_ms")
        sender = raw_msg.get("sender_name")
        if timestamp_ms is None or sender is None:
            continue
        sender = _repair_messenger_text(sender)

        if your_name and sender == your_name:
            sender = "You"

        content = raw_msg.get("content")
        if content is None:
            content = ""
        else:
            content = _repair_messenger_text(content)

        messages.append(
            Message(
                timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
                sender=sender,
                content=content,
            )
        )

    messages.sort(key=lambda msg: msg.timestamp)
    return chat_title, chat_id, messages


def _repair_messenger_text(text: str) -> str:
    """
    Repair common UTF-8/Latin-1 mojibake found in some Messenger exports.

    Example: "FÃ¶r" -> "För".
    """
    mojibake_markers = ("Ã", "Â", "ð", "â", "€", "™")
    if not any(marker in text for marker in mojibake_markers):
        return text

    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text

    return repaired


def _safe_filename(value: str) -> str:
    """Normalize a user-facing name for use as a file name."""
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", value).strip()
    return cleaned or "unnamed_chat"


def process_messenger_input(
    input_path: Path,
    output_path: Path,
    your_name: str | None = None,
) -> None:
    """
    Process Messenger JSON exports from e2ee_cutover and inbox directories.
    """
    if input_path.is_file():
        raise ValueError("Messenger input must be a directory")
    if not input_path.exists():
        raise ValueError(f"Input path does not exist: {input_path}")
    if output_path.exists() and output_path.is_file():
        raise ValueError("Messenger output must be a directory")

    messages_root = input_path / "your_facebook_activity" / "messages"
    if not messages_root.is_dir():
        raise ValueError(
            "Messenger input must contain your_facebook_activity/messages"
        )

    cutover_dir = messages_root / "e2ee_cutover"
    inbox_dir = messages_root / "inbox"
    if not cutover_dir.is_dir() or not inbox_dir.is_dir():
        raise ValueError("Could not find Messenger e2ee_cutover and inbox folders")

    output_path.mkdir(parents=True, exist_ok=True)

    thread_files: dict[str, list[Path]] = {}
    for source_dir in (cutover_dir, inbox_dir):
        for message_file in source_dir.glob("*/message_1.json"):
            thread_key = message_file.parent.name
            thread_files.setdefault(thread_key, []).append(message_file)

    if not thread_files:
        print("No Messenger message_1.json files found")
        return

    converted_count = 0
    for thread_key in sorted(thread_files):
        chat_name: str | None = None
        chat_id: str | None = None
        merged_messages: list[Message] = []
        seen_entries: set[tuple[int, str, str]] = set()

        for message_file in thread_files[thread_key]:
            file_chat_name, file_chat_id, messages = parse_messenger_file(
                message_file, your_name
            )
            if chat_name is None:
                chat_name = file_chat_name
            if chat_id is None:
                chat_id = file_chat_id

            for msg in messages:
                dedup_key = (
                    int(msg.timestamp.timestamp() * 1000),
                    msg.sender,
                    msg.content,
                )
                if dedup_key in seen_entries:
                    continue
                seen_entries.add(dedup_key)
                merged_messages.append(msg)

        merged_messages.sort(key=lambda msg: msg.timestamp)
        if chat_name is None or chat_id is None:
            continue

        conversation_name = f"{chat_name} ({chat_id})"
        sigtop_content = convert_to_sigtop(merged_messages, conversation_name)
        out_file = output_path / f"{_safe_filename(conversation_name)}.txt"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(sigtop_content)
        converted_count += 1

    print(f"Converted {converted_count} Messenger chats")


def format_sigtop_timestamp(dt: datetime) -> str:
    """
    Format a datetime as sigtop-style timestamp.

    Produces format like 'Tue, 13 Aug 2024 09:30:41 +0200'.

    Parameters
    ----------
    dt : datetime
        Datetime to format.

    Returns
    -------
    str
        Formatted timestamp string with assumed +0200 timezone.
    """
    # WhatsApp exports don't include timezone, assume local (+0200)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0200")


def convert_to_sigtop(messages: list[Message], chat_name: str) -> str:
    """
    Convert parsed messages to sigtop format.

    Produces a complete sigtop-format document with conversation header
    and individual message blocks.

    Parameters
    ----------
    messages : list of Message
        List of parsed messages.
    chat_name : str
        Name to use in the 'Conversation:' header.

    Returns
    -------
    str
        Complete sigtop-format text ready to write to file.
    """
    lines: list[str] = []

    # Header
    lines.append(f"Conversation: {chat_name}")
    lines.append("")

    for msg in messages:
        # Determine message type based on sender
        msg_type = "outgoing" if msg.sender == "You" else "incoming"

        lines.append(f"From: {msg.sender}")
        lines.append(f"Type: {msg_type}")
        lines.append(f"Sent: {format_sigtop_timestamp(msg.timestamp)}")

        # Add Received line for incoming messages (same as Sent for simplicity)
        if msg_type == "incoming":
            lines.append(f"Received: {format_sigtop_timestamp(msg.timestamp)}")

        lines.append("")
        lines.append(msg.content)
        lines.append("")

    return "\n".join(lines)


def extract_chat_name(file_path: Path, name_pattern: str | None = None) -> str:
    """
    Extract chat name from chat export filename using a pattern.

    Uses '%s' as placeholder for the chat name in the pattern. For example,
    pattern "WhatsApp-chatt med %s" matches "WhatsApp-chatt med John.txt"
    and extracts "John".

    Parameters
    ----------
    file_path : Path
        Path to the chat export file.
    name_pattern : str, optional
        Pattern with '%s' placeholder for the name. If None,
        returns the entire filename stem.

    Returns
    -------
    str
        Extracted chat name.

    Raises
    ------
    ValueError
        If pattern is provided but doesn't match the filename,
        or if pattern doesn't contain '%s' placeholder.
    """
    stem = file_path.stem

    if name_pattern is None:
        return stem

    # Split pattern on %s to get prefix and suffix
    if "%s" not in name_pattern:
        raise ValueError(f"Pattern '{name_pattern}' must contain '%s' placeholder")

    parts = name_pattern.split("%s", 1)
    prefix = parts[0]
    suffix = parts[1] if len(parts) > 1 else ""

    # Check if stem matches the pattern
    if stem.startswith(prefix) and stem.endswith(suffix):
        # Extract the name between prefix and suffix
        start = len(prefix)
        end = len(stem) - len(suffix) if suffix else len(stem)
        return stem[start:end]

    raise ValueError(
        f"Filename '{file_path.name}' does not match pattern '{name_pattern}'"
    )


def convert_file(
    input_path: Path,
    output_path: Path,
    your_name: str | None = None,
    name_pattern: str | None = None,
) -> None:
    """
    Convert a single chat export file to sigtop format.

    Parameters
    ----------
    input_path : Path
        Path to input chat export file.
    output_path : Path
        Path where sigtop format output will be written.
    your_name : str, optional
        Your display name in the chat for sender identification.
    name_pattern : str, optional
        Pattern with '%s' for extracting chat name from filename.
    """
    chat_name = extract_chat_name(input_path, name_pattern)
    messages = parse_whatsapp_file(input_path, your_name)
    sigtop_content = convert_to_sigtop(messages, chat_name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sigtop_content)

    print(f"Converted: {input_path} -> {output_path}")


def process_input(
    input_path: Path,
    output_path: Path,
    your_name: str | None = None,
    name_pattern: str | None = None,
    chat_format: str = "Whatsapp",
) -> None:
    """
    Process input file or folder and write converted output.

    If input is a file, output must be a file. If input is a directory,
    output must be a directory. All '.txt' files in input directory
    are converted.

    Parameters
    ----------
    input_path : Path
        Path to input file or directory.
    output_path : Path
        Path to output file or directory.
    your_name : str, optional
        Your display name in the chat for sender identification.
    name_pattern : str, optional
        Pattern with '%s' for extracting chat name from filename.

    Raises
    ------
    ValueError
        If input/output path types don't match (file vs directory).
    """
    if chat_format == "Messenger":
        process_messenger_input(input_path, output_path, your_name)
        return

    if input_path.is_file():
        if output_path.is_dir():
            raise ValueError(
                "Input is a file but output is a directory. "
                "Both must be files or both must be directories."
            )
        convert_file(input_path, output_path, your_name, name_pattern)

    elif input_path.is_dir():
        if output_path.exists() and output_path.is_file():
            raise ValueError(
                "Input is a directory but output is a file. "
                "Both must be files or both must be directories."
            )

        output_path.mkdir(parents=True, exist_ok=True)

        txt_files = list(input_path.glob("*.txt"))
        if not txt_files:
            print(f"No .txt files found in {input_path}")
            return

        for txt_file in txt_files:
            chat_name = extract_chat_name(txt_file, name_pattern)
            out_file = output_path / f"{chat_name} (Whatsapp).txt"
            convert_file(txt_file, out_file, your_name, name_pattern)

        print(f"Converted {len(txt_files)} files")

    else:
        raise ValueError(f"Input path does not exist: {input_path}")


def main() -> int | None:
    """
    Parse arguments and run the chat format conversion.

    Returns
    -------
    int or None
        Exit code 1 on error, None on success.
    """
    parser = argparse.ArgumentParser(
        description="Convert chat exports to sigtop format"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Input file or folder containing chat exports",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output file or folder for sigtop format files",
    )
    parser.add_argument(
        "--your-name",
        type=str,
        default=None,
        help="Your display name in the chat (messages from this sender become 'You'). If not specified, the whole file name except for the extension is used as the chat name.",
    )
    parser.add_argument(
        "--name-pattern",
        type=str,
        default=None,
        help="Pattern to extract chat name from filename, with %%s as placeholder. Only used for WhatsApp exports."
        "(e.g., 'WhatsApp-chatt med %%s')",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="Whatsapp",
        choices=["Whatsapp", "Messenger"],
        help="Input format. Use 'Whatsapp' for existing .txt parsing or "
        "'Messenger' for Facebook Messenger JSON exports.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        process_input(
            input_path,
            output_path,
            args.your_name,
            args.name_pattern,
            args.format,
        )
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    return None


if __name__ == "__main__":
    main()
