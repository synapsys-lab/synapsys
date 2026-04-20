---
slug: welcome-to-synapsys-blog
title: "Welcome to the Synapsys Blog"
description: >
  Introducing the Synapsys Blog — a space for tutorials, research insights,
  and practical guides for control systems engineers and researchers.
authors: [oseias]
tags: [post, release, python, control-theory]
content_type: post
hide_table_of_contents: false
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Welcome to the **Synapsys Blog** — a space dedicated to practical control systems
engineering, academic research, and real-world applications of the Synapsys library.

{/* truncate */}

## What you'll find here

This blog is aimed at **researchers, graduate students, and engineers** who work at the
intersection of classical control theory and modern software. Each post will focus on
a concrete problem and show how to solve it end-to-end using Synapsys.

### Series planned

| Series | What it covers |
|--------|----------------|
| **Control Theory in Practice** | Modelling, analysis and design from first principles |
| **From Simulation to Hardware** | MIL → SIL → HIL step by step |
| **AI-Augmented Control** | Neural-LQR, RL policies and PyTorch integration |
| **Research Snippets** | Short posts connecting library features to published papers |
| **Release Notes** | What's new in each version with worked examples |

---

## Quick taste: step response in 5 lines

```python
from synapsys.api import tf, feedback, step

G = tf([1], [1, 2, 1])   # G(s) = 1 / (s² + 2s + 1)
T = feedback(G)           # unity negative feedback
t, y = step(T)            # simulate step response
```

The closed-loop DC gain converges to **1.0**, and the natural frequency $\omega_n = 1$ rad/s
with $\zeta = 1$ (critically damped) — as expected from the denominator.

:::tip Install
```bash
pip install synapsys   # or: uv add synapsys
```
:::

---

## Why Synapsys?

Most Python control libraries focus on analysis. Synapsys adds a **simulation and
deployment layer** on top: agents that run in real time, a transport-agnostic
communication bus, and a hardware abstraction that makes MIL/SIL/HIL a configuration
change rather than a rewrite.

It was built alongside graduate research in multi-agent control systems and is
designed to be readable, testable, and academically citable.

---

## Stay connected

- Watch the repo on [GitHub](https://github.com/synapsys-lab/synapsys) for new releases
- Open an [issue](https://github.com/synapsys-lab/synapsys/issues) if you have a topic you'd like covered

The first technical post — **Stabilising an Inverted Pendulum with LQR** — is coming up next.
