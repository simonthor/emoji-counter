# 🎭 Emoji Counter 📊

Extract and visualize emoji usage from chat messages.

## Overview

Emoji Counter is a Python tool that helps you:

- Upload and process chat exports directly from the web dashboard
- Extract emojis from chat message files (Signal, WhatsApp, Messenger)
- Store them in a SQLite database
- Explore patterns with an interactive dashboard
- Compare emoji usage across different platforms and chats

## Key Features

- **Web-based upload**: Process chat exports directly from the dashboard without command-line tools
- **Multi-platform support**: Signal (via sigtop), WhatsApp, and Messenger
- **Interactive dashboard**: Bar charts, pie charts, and time series visualizations
- **Smart filtering**: Dynamic user and chat filters that update based on each other
- **Multi-database**: Combine and compare data from different sources
- **Cumulative analysis**: Track emoji usage growth over time

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Launch the dashboard**:
   ```bash
   emoji-explore
   ```

3. **Open your browser** to [http://127.0.0.1:8050](http://127.0.0.1:8050)

4. **Upload chat data**: Use the "Upload Chat Data" section to upload your `.zip` file
   - Select your chat format (Signal, WhatsApp, or Messenger)
   - Drag and drop or select your file
   - The data will be automatically processed and displayed in the chart

**Alternative (Command-line workflow):**

If you prefer using command-line tools, see [Getting Started](getting-started.md) for detailed instructions on converting and extracting emoji data manually.

## Documentation

- [Getting Started](getting-started.md) - Installation and setup
- [Web-Based Upload](web-upload.md) - Upload chat data directly from the dashboard
- [Message Conversion](message-conversion.md) - Converting chat exports to the supported format
- [Emoji Extraction](emoji-extraction.md) - Extracting emojis to SQLite
- [Dashboard Usage](dashboard.md) - Using the interactive visualization dashboard
- [Database Schema](database-schema.md) - Understanding the data structure

## Project Links

- [GitHub Repository](https://github.com/simonthor/emoji-counter)
- [Issue Tracker](https://github.com/simonthor/emoji-counter/issues)
