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
| `ml` | `pip install synapsys torch` | PyTorch for Neural-LQR and RL controller examples |
| `viz` | `pip install synapsys pyvista imageio` | PyVista 3D visualisation and GIF export (quadcopter example) |

:::note
`ml` and `viz` are not packaged as PyPI extras because their wheel sizes and platform support vary widely. Install them separately as shown above.
:::

## Verify installation

```python
import synapsys
print(synapsys.__version__)
```
