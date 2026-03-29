# 🎭 Emoji Counter 📊

Extract and visualize emoji usage from chat messages.
![Dashboard Screenshot](./banner.png)

## Features

- **Extract emojis** from chat message files into a SQLite database
- **Interactive dashboard** to explore emoji usage patterns
- **Multiple visualizations**: Bar chart, Pie chart, and Time series
- **Filter by user or chat** to analyze specific conversations
- **Cumulative time series** showing emoji usage growth over time

## Installation
Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/simonthor/emoji-counter.git
cd emoji-counter
```

The easiest way to install it is using [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Otherwise, you can create a virtual environment and install the dependencies manually:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install .
```

## Usage

### 1. Prepare Message Files

The format that the current program supports is the output format from [sigtop](https://github.com/tbvdm/sigtop/), which is a tool to extract messages from Signal desktop. To install and run `sigtop`, follow the instructions in their repository. Other output formats are planned to be supported in the future.

`sigtop` will create a directory with text files containing the messages from each chat. This will be of the format
```
messages/
├── FirstName1 LastName1 (phone number or unique ID).txt
├── FirstName2 LastName2 (phone number or unique ID).txt
├── Group Chat (unique ID).txt
...
```
The format of the messages in these files is as follows:
```
Conversation: FirstName1 LastName1 (unique ID)

From: FirstName1 LastName1 (unique ID)
Type: incoming
Sent: Tue, 13 Aug 2024 09:30:41 +0200
Received: Tue, 13 Aug 2024 14:45:13 +0200

Lorem ipsum... 😄

From: FirstName1 LastName1 (unique ID)
Type: incoming
Sent: Tue, 13 Aug 2024 09:31:00 +0200
Received: Tue, 13 Aug 2024 14:45:13 +0200

Dorot sit amet... 😂
```

The only fields that the extractor uses are `From:`, `Sent:`, chat name (derived from the filename), and the message text itself. Therefore, it should be relatively easy to convert other chat message formats to this format if needed.

### 2. Extract Emojis

Once you have the message files in the correct format, you can use the `emoji-extract` command to extract emojis from these files and save them to a SQLite database. This can be done on either a single file or an entire directory:

```bash
mkdir -p data # Not necessary, but recommended to keep things organized

# From a single file
emoji-extract -i messages/chat.txt -o data/emojis.sql

# From a directory of files
emoji-extract -i messages/ -o data/emojis.sql
```

**Options:**
- `-i, --input` (required): Input file or directory containing message files
- `-o, --output` (default: `./emojis.sql`): Output SQLite database file


### 3. Explore Data

Launch the interactive dashboard to visualize emoji usage:

```bash
emoji-explore data/emojis.sql
```

The first argument is the path to the SQLite database created by the extractor. You can also specify additional options:

**Options:**
- `--port` (default: 8050): Port to run the Dash app on
- `--no-debug`: Disable debug mode

Then open your browser to http://127.0.0.1:8050

## Dashboard Features

### Chart Types

- **Bar Chart**: Shows total count for each emoji with individual colors
- **Pie Chart**: Shows proportional distribution of emoji usage
- **Time Series**: Shows cumulative emoji usage over time

### Filters

- **User**: Filter by a specific user or view everyone's emojis
- **Chat**: Filter by a specific chat or view all chats

### Interactive Controls

- **Show All / Hide All**: Toggle visibility of all traces (unfortunately there is a bug in Plotly that prevents this from working properly for pie charts, but it works for the other charts)
- **Legend**: Click to toggle individual emoji visibility
- **Hover**: View detailed information for each data point

## Database Schema

The SQLite database contains a single `emojis` table:

| Column | Type | Description |
|--------|------|-------------|
| `emoji` | TEXT | The emoji character |
| `timestamp` | TEXT | ISO 8601 timestamp of the message |
| `username` | TEXT | Name of the user who sent the emoji |
| `chat_name` | TEXT | Name of the chat/conversation |

## Development

### Running Tests

```bash
uv run pytest
```

### Linting

```bash
uv run ruff check .
```

### Type Checking

```bash
uv run ty check .
```
