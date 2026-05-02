# Getting Started

This guide will help you install and set up Emoji Counter.

## Prerequisites

- Python 3.14 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

### Using uv (Recommended)

Clone the repository and install dependencies:

```bash
git clone https://github.com/simonthor/emoji-counter.git
cd emoji-counter
uv sync
```

### Using pip

Alternatively, you can use a virtual environment and pip:

```bash
git clone https://github.com/simonthor/emoji-counter.git
cd emoji-counter
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install .
```

## Verify Installation

Check that the tools are installed correctly:

```bash
# Check emoji-extract
uv run emoji-extract --help

# Check message-convert
uv run message-convert --help

# Check emoji-explore
uv run emoji-explore --help
```

## Next Steps

Now that you have Emoji Counter installed, you have two options:

### Option 1: Web Interface (Recommended for Beginners)

The easiest way to get started is to use the built-in web interface:

1. Launch the dashboard:
   ```bash
   emoji-explore
   ```

2. Open [http://127.0.0.1:8050](http://127.0.0.1:8050) in your browser

3. Use the "Upload Chat Data" section to:
   - Select your chat format (Signal, WhatsApp, or Messenger)
   - Upload your `.zip` file
   - The data will be automatically processed and displayed

See [Dashboard Usage](dashboard.md) for more details on uploading and exploring your data.

### Option 2: Command-Line Tools (Advanced)

If you prefer more control or need to batch process multiple files:

1. [Convert your chat exports](message-conversion.md) to the supported format
2. [Extract emojis](emoji-extraction.md) from your messages
3. [Explore the data](dashboard.md) in the interactive dashboard

This approach gives you fine-grained control over the conversion and extraction process.

## Troubleshooting

### Python Version

Emoji Counter requires Python 3.14 or higher. Check your version:

```bash
python --version
```

If you have an older version, consider using [pyenv](https://github.com/pyenv/pyenv) to install a newer Python version.

### uv Not Found

If `uv` is not installed, follow the installation instructions at [docs.astral.sh/uv](https://docs.astral.sh/uv/).
