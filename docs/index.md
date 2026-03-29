# 🎭 Emoji Counter 📊

Extract and visualize emoji usage from chat messages.

## Overview

Emoji Counter is a Python tool that helps you:

- Extract emojis from chat message files (Signal, WhatsApp)
- Store them in a SQLite database
- Explore patterns with an interactive dashboard
- Compare emoji usage across different platforms and chats

## Key Features

- **Multi-platform support**: Signal (via sigtop) and WhatsApp
- **Interactive dashboard**: Bar charts, pie charts, and time series visualizations
- **Smart filtering**: Dynamic user and chat filters that update based on each other
- **Multi-database**: Combine and compare data from different sources
- **Cumulative analysis**: Track emoji usage growth over time

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Prepare your chat exports** (see [Getting Started](getting-started.md))

3. **Extract emojis**:
   ```bash
   emoji-extract -i messages/ -o data/emojis.sql
   ```

4. **Explore the data**:
   ```bash
   emoji-explore data/emojis.sql
   ```

Open your browser to [http://127.0.0.1:8050](http://127.0.0.1:8050)

## Documentation

- [Getting Started](getting-started.md) - Installation and setup
- [Message Conversion](message-conversion.md) - Converting chat exports to the supported format
- [Emoji Extraction](emoji-extraction.md) - Extracting emojis to SQLite
- [Dashboard Usage](dashboard.md) - Using the interactive visualization dashboard
- [Database Schema](database-schema.md) - Understanding the data structure

## Project Links

- [GitHub Repository](https://github.com/simonthor/emoji-counter)
- [Issue Tracker](https://github.com/simonthor/emoji-counter/issues)
