#!/usr/bin/env python3
"""
Emoji extraction tool for chat message files.
Extracts emojis from text files and exports to SQLite database.
"""

import argparse
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import emoji
import pandas as pd


def extract_emojis(text: str) -> List[str]:
    """
    Extract all emojis from text using the emoji library.

    Parameters
    ----------
    text : str
        Input text to extract emojis from.

    Returns
    -------
    list of str
        List of emoji characters found in the text.
    """
    return [c.chars for c in emoji.analyze(text, join_emoji=True)]


def parse_message_file(file_path: Path) -> List[Tuple[str, str, str, str]]:
    """
    Parse a message file and extract emoji data.

    Parameters
    ----------
    file_path : Path
        Path to the message file to parse.

    Returns
    -------
    list of tuple
        List of tuples containing (emoji, timestamp, username, chat_name) for each
        emoji found in the file.
    """
    chat_name = file_path.stem
    # Remove text in parentheses from chat name
    chat_name = re.sub(r"\s*\([^)]*\)", "", chat_name).strip()

    results = []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into messages by "From:" markers
    messages = re.split(r"\n(?=From: )", content)

    for message in messages:
        if not message.strip():
            continue

        # Extract username from "From:" line
        from_match = re.search(r"^From:\s*(.+?)$", message, re.MULTILINE)
        if not from_match:
            continue
        username = from_match.group(1).strip()

        if "(" in username:
            username = username[: username.rfind("(")].strip()

        # Extract timestamp from "Sent:" line
        sent_match = re.search(r"^Sent:\s*(.+?)$", message, re.MULTILINE)
        if not sent_match:
            continue
        timestamp_str = sent_match.group(1).strip()

        # Parse timestamp
        try:
            # Try to parse the timestamp format: "Fri, 4 Oct 2024 10:25:51 +0200"
            timestamp = datetime.strptime(
                timestamp_str, "%a, %d %b %Y %H:%M:%S %z"
            ).isoformat()
        except ValueError:
            # If parsing fails, keep the original string
            timestamp = timestamp_str

        # Extract emojis from the message content
        emojis = extract_emojis(message)

        for em in emojis:
            results.append((em, timestamp, username, chat_name))

    return results


def process_input(input_path: Path) -> pd.DataFrame:
    """
    Process a file or directory of files to extract emoji data.

    Parameters
    ----------
    input_path : Path
        Path to a file or directory containing message files.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: emoji, timestamp, username, chat_name.

    Raises
    ------
    ValueError
        If input path does not exist.
    """
    all_data = []

    if input_path.is_file():
        all_data.extend(parse_message_file(input_path))
    elif input_path.is_dir():
        for file_path in input_path.glob("*.txt"):
            all_data.extend(parse_message_file(file_path))
    else:
        raise ValueError(f"Input path does not exist: {input_path}")

    df = pd.DataFrame(all_data, columns=["emoji", "timestamp", "username", "chat_name"])
    return df


def export_to_sqlite(df: pd.DataFrame, output_path: Path) -> None:
    """
    Export DataFrame to SQLite database.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing emoji data with columns: emoji, timestamp, username, chat_name.
    output_path : Path
        Path where the SQLite database file will be saved.
    """
    conn = sqlite3.connect(output_path)
    df.to_sql("emojis", conn, if_exists="replace", index=False)
    conn.close()


def main() -> None:
    """
    Parse command-line arguments and run the emoji extraction process.

    Extracts emojis from message files and exports them to a SQLite database.
    """
    parser = argparse.ArgumentParser(
        description="Extract emojis from chat message files and export to SQLite database"
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input file or directory containing message files",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="./emojis.sql",
        help="Output SQLite database file (default: ./emojis.sql)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Process input
    print(f"Processing: {input_path}")
    df = process_input(input_path)

    if len(df) == 0:
        print("No emojis found in the input files.")
        return

    # Export to SQLite
    print(f"Found {len(df)} emoji instances")
    print(f"Exporting to: {output_path}")
    export_to_sqlite(df, output_path)
    print("Done!")


if __name__ == "__main__":
    main()
