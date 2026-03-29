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

Now that you have Emoji Counter installed, you can:

1. [Convert your chat exports](message-conversion.md) to the supported format
2. [Extract emojis](emoji-extraction.md) from your messages
3. [Explore the data](dashboard.md) in the interactive dashboard

## Troubleshooting

### Python Version

Emoji Counter requires Python 3.14 or higher. Check your version:

```bash
python --version
```

If you have an older version, consider using [pyenv](https://github.com/pyenv/pyenv) to install a newer Python version.

### uv Not Found

If `uv` is not installed, follow the installation instructions at [docs.astral.sh/uv](https://docs.astral.sh/uv/).
