---
id: installation
title: Installation
sidebar_position: 1
---

# Installation

## Requirements

- Python **3.10** or newer
- pip or [uv](https://docs.astral.sh/uv/) (recommended)

## Install from PyPI

```bash
pip install synapsys
```

```bash
uv add synapsys
```

## Install from source

```bash
git clone https://github.com/synapsys-lab/synapsys.git
cd synapsys
uv sync --extra dev
```

## Optional dependencies

| Extra | Command | What it adds |
|-------|---------|--------------|
| `dev` | `uv sync --extra dev` | pytest, ruff, mypy, matplotlib |

## Verify installation

```python
import synapsys
print(synapsys.__version__)
```
