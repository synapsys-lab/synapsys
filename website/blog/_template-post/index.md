---
slug: SLUG-DO-POST
title: "Título do Post"
description: >
  Resumo curto e direto que aparece nos cards e no Open Graph.
authors: [oseias]
tags: [post, python]
content_type: post
image: /img/blog/SLUG-DO-POST-banner.png
hide_table_of_contents: false
---

Introdução direta: o que o leitor vai aprender neste post e em quanto tempo.

{/* truncate */}

## Pré-requisitos

- Synapsys instalado (`pip install synapsys`)
- Python 3.10+

## Passo 1 — Título do passo

Explicação curta. Foque no essencial.

```python
from synapsys.api import tf

G = tf([1], [1, 2, 1])
```

## Passo 2 — Título do passo

Continue o tutorial de forma sequencial e incremental.

```python
from synapsys.api import feedback, step

T    = feedback(G)
t, y = step(T)
```

## Resultado

Mostre o output esperado ou um gráfico.

## Próximos passos

Links para artigos relacionados ou exemplos mais avançados.
