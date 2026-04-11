---
id: installation
title: Instalação
sidebar_position: 1
---

# Instalação

## Requisitos

- Python **3.10** ou superior
- pip ou [uv](https://docs.astral.sh/uv/) (recomendado)

## Instalar do PyPI

```bash
pip install synapsys
```

```bash
uv add synapsys
```

## Instalar do código-fonte

```bash
git clone https://github.com/synapsys/synapsys.git
cd synapsys
uv sync --extra dev
```

## Dependências opcionais

| Extra | Comando | O que adiciona |
|-------|---------|----------------|
| `dev` | `uv sync --extra dev` | pytest, ruff, mypy, matplotlib |

## Verificar instalação

```python
import synapsys
print(synapsys.__version__)
```
