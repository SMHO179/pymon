# pymon

Lightweight Linux system monitor with TUI.

## Features

- CPU usage monitoring
- RAM and Swap info
- Disk usage
- Network I/O
- Load average
- System uptime
- Process list

## Installation

No installation required. Ensure you have Python 3 and run:

```bash
python3 -m pymon
```

Or directly:

```bash
python3 pymon/__main__.py
```

## Usage

```bash
pymon [options]
```

Options:

- `-i, --interval` Refresh interval in seconds (default: 1.0)
- `-s, --sort` Initial sort column: `cpu` or `mem` (default: `cpu`)

## Controls

- `q` - Quit
- `r` - Refresh
- `c` - Sort by CPU
- `m` - Sort by Memory

## Requirements

This project uses only Python standard library. No external packages needed.