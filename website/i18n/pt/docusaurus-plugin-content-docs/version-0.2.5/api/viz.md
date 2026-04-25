---
id: viz
title: synapsys.viz
sidebar_label: synapsys.viz
---

# `synapsys.viz`

Módulo de visualização: paleta de cores canônica e janelas de simulação 3D plug-and-play.

```python
from synapsys.viz import (
    Dark, mpl_theme,
    CartPoleView, PendulumView, MassSpringDamperView,
)
```

---

## `SimViewBase`

Classe base de todas as views. Herda de `QMainWindow`.
**Não instanciar diretamente** — use as subclasses concretas.

### Atributos de classe (configuráveis nas subclasses)

| Atributo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `_title` | `str` | `"Synapsys Simulator"` | Título da janela Qt |
| `_mpl_title` | `str` | `"Telemetria"` | Título do painel matplotlib |
| `_dt` | `float` | `0.02` | Passo de simulação em segundos |
| `_hist_len` | `int` | `500` | Comprimento do deque de histórico |
| `_mpl_skip` | `int` | `3` | Renderizar matplotlib a cada N ticks |
| `_pert_max_default` | `float` | `20.0` | Magnitude padrão da perturbação |
| `_slider_range` | `tuple` | `(1, 50)` | Faixa do slider de magnitude |
| `_slider_unit` | `str` | `"N"` | Unidade exibida no label do slider |
| `_splitter_w` | `tuple` | `(770, 630)` | Largura inicial dos painéis (3D, mpl) |
| `_u_clip` | `float` | `50.0` | Saturação do controlador |
| `_u_clip_total` | `float` | `80.0` | Saturação após adição da perturbação |

### Método público

#### `run() -> None`

Cria `QApplication` (se não existir), inicializa `QMainWindow`, constrói a UI
completa e entra no event loop Qt. **Não retorna** (chama `sys.exit`).

```python
CartPoleView().run()
CartPoleView(controller=fn).run()
```

### Hooks (override opcional nas subclasses)

| Método | Assinatura | Descrição |
|---|---|---|
| `_lqr_u(x)` | `(ndarray) → ndarray` | Lei de controle LQR. Padrão: `−K@x`. Override para setpoint tracking. |
| `_pert_vector()` | `() → ndarray` | Converte `_pert` escalar para vetor de entrada. |
| `_build_extra_controls(hb)` | `(QHBoxLayout) → None` | Injeta widgets extras na barra de controles. |
| `_on_reset()` | `() → None` | Chamado após `sim.reset()` — útil para resetar estado extra. |
| `_post_tick(x, u)` | `(ndarray, ndarray) → None` | Chamado ao final de cada tick. Usado para lógica de auto-reset (ex: limite do trilho no CartPole). |

---

## `CartPoleView`

```python
CartPoleView(
    controller: Callable | None = None,
    m_c: float = 1.0,              # massa do carrinho [kg]
    m_p: float = 0.1,              # massa do bob [kg]
    l:   float = 0.5,              # comprimento da haste [m]
    g:   float = 9.81,             # gravidade [m/s²]
    x0:  np.ndarray | None = None, # estado inicial (4,) — padrão [0,0,0.18,0]
)
```

**Sistema:** carrinho sobre trilho com pêndulo invertido articulado.

**Estado:** `x = [posição carrinho (m), velocidade (m/s), ângulo θ (rad), vel. angular (rad/s)]`

**Entrada:** força horizontal no carrinho (N).

**LQR padrão:** `Q = diag([1, 0.1, 100, 10])`, `R = 0.01·I`

**Perturbação:** botões ◀/▶ e teclas A/D — força horizontal (1–80 N, padrão 30 N).

**Auto-reset:** o carrinho é resetado automaticamente ao atingir 92% do comprimento do trilho (`_LIMIT_FRAC = 0.92`). Entre 72% e 92% o carrinho muda de cor para âmbar como aviso.

---

## `PendulumView`

```python
PendulumView(
    controller: Callable | None = None,
    m:  float = 1.0,              # massa do bob [kg]
    l:  float = 1.0,              # comprimento da haste [m]
    g:  float = 9.81,             # gravidade [m/s²]
    b:  float = 0.1,              # amortecimento viscoso
    x0: np.ndarray | None = None, # estado inicial (2,) — padrão [0.18, 0]
)
```

**Sistema:** pêndulo invertido de 1 elo com base fixa.

**Estado:** `x = [ângulo θ (rad), velocidade angular θ̇ (rad/s)]`

**Entrada:** torque na junta (N·m).

**Polo instável:** `λ = +√(g/l)` ≈ `+3.13 rad/s` nos parâmetros padrão.

**LQR padrão:** `Q = diag([80, 5])`, `R = I`

**Perturbação:** botões ↺/↻ e teclas A/D — torque (1–40 N·m, padrão 20 N·m).
Setas vermelhas aparecem na ponta da haste indicando direção e magnitude.

---

## `MassSpringDamperView`

```python
MassSpringDamperView(
    controller: Callable | None = None,
    m:         float = 1.0,              # massa [kg]
    c:         float = 0.5,              # amortecimento [N·s/m]
    k:         float = 2.0,              # constante da mola [N/m]
    x0:        np.ndarray | None = None, # estado inicial (2,) — padrão [0, 0]
    setpoints: list | None = None,       # lista de (label, valor_m) — padrão 3 pontos
)
```

**Sistema:** massa-mola-amortecedor 1D com rastreamento de setpoint.

**Estado:** `x = [posição q (m), velocidade q̇ (m/s)]`

**Entrada:** força externa (N).

**LQR com feed-forward:** `u = −K·(x − x_ref) + k·sp`

**Setpoints padrão:** `[("0 m", 0.0), ("+1.5 m", 1.5), ("−1.5 m", -1.5)]` (botões ou teclas 1/2/3).
Setpoints customizados:

```python
MassSpringDamperView(setpoints=[("0", 0.0), ("+2m", 2.0), ("-2m", -2.0)]).run()
```

**Perturbação:** botões ◀/▶ e teclas A/D — força (1–30 N, padrão 15 N).

---

## `Dark`

Classe de tokens de cor do design system Synapsys (espelho do website dark mode).

```python
from synapsys.viz.palette import Dark
```

### Fundos

| Token | Hex | Uso |
|---|---|---|
| `Dark.BG` | `#111111` | Fundo da janela / figura matplotlib |
| `Dark.SURFACE` | `#1a1a1a` | Cards, painéis, eixos matplotlib |
| `Dark.PANEL` | `#1e1e1e` | GroupBox Qt |
| `Dark.BORDER` | `#2e2e2e` | Bordas padrão |
| `Dark.BORDER_LT` | `#222222` | Borda sutil |

### Texto

| Token | Hex | Uso |
|---|---|---|
| `Dark.FG` | `#e2e8f0` | Texto principal |
| `Dark.MUTED` | `#999999` | Labels de eixo, texto secundário |
| `Dark.SUBTLE` | `#666666` | Texto terciário / dicas |
| `Dark.GRID` | `#2e2e2e` | Linhas de grade matplotlib |

### Marca

| Token | Hex | Uso |
|---|---|---|
| `Dark.GOLD` | `#c8a870` | Cor primária / destaque |
| `Dark.GOLD_DIM` | `#987040` | Variante escura |
| `Dark.GOLD_LT` | `#d8b880` | Variante clara |
| `Dark.TEAL` | `#0d9488` | Cor secundária |

### Estado / alerta

| Token | Hex | Uso |
|---|---|---|
| `Dark.DANGER` | `#ef4444` | Erro, limite atingido, perturbação ativa |
| `Dark.WARN` | `#f59e0b` | Aviso (ex: carrinho se aproximando do limite) |
| `Dark.OK` | `#22c55e` | Estabilizado / ok |

### Sinais

| Token | Hex | Grandeza física |
|---|---|---|
| `Dark.SIG_POS` | `#3b82f6` | Posição / deslocamento |
| `Dark.SIG_POS_LT` | `#60a5fa` | Posição (variante clara / segundo canal) |
| `Dark.SIG_VEL` | `#f97316` | Velocidade / taxa |
| `Dark.SIG_VEL_LT` | `#fb923c` | Velocidade (variante clara) |
| `Dark.SIG_ANG` | `#f97316` | Ângulo |
| `Dark.SIG_REF` | `#22c55e` | Setpoint / referência |
| `Dark.SIG_REF_DK` | `#16a34a` | Referência (variante escura — linha tracejada) |
| `Dark.SIG_REF_LT` | `#4ade80` | Referência (variante clara — checked/active) |
| `Dark.SIG_CTRL` | `#ef4444` | Força / torque de controle |
| `Dark.SIG_PHASE` | `#a78bfa` | Retrato de fase |
| `Dark.SIG_TRAIL` | `#7c3aed` | Trilha 3D |
| `Dark.SIG_ALT` | `#facc15` | Altitude z |
| `Dark.SIG_CYAN` | `#38bdf8` | Ponto atual (dot marker) |

### Objetos 3D

| Token | Hex | Objeto |
|---|---|---|
| `Dark.MESH_BODY` | `#2563eb` | Corpo principal (massa, carrinho) |
| `Dark.MESH_POLE` | `#c8a870` | Haste / braço |
| `Dark.MESH_BOB` | `#f97316` | Bob / ponta da haste |
| `Dark.MESH_SPRING` | `#c8a870` | Mola |
| `Dark.MESH_DAMP` | `#64748b` | Amortecedor |
| `Dark.MESH_STRUCT` | `#334155` | Estrutura / base |
| `Dark.MESH_WALL` | `#334155` | Parede de ancoragem |
| `Dark.MESH_FLOOR` | `#1a1a1a` | Chão / plano |
| `Dark.MESH_RAIL` | `#475569` | Trilho |
| `Dark.MESH_STOP` | `#ef4444` | Batente final |
| `Dark.MESH_REF` | `#4ade80` | Esfera de referência (setpoint) |

---

## `mpl_theme()`

```python
from synapsys.viz.palette import mpl_theme
mpl_theme()
```

Aplica rcParams globais do tema Synapsys ao matplotlib.
Deve ser chamado **antes** de criar qualquer `Figure`.

Configura automaticamente: `figure.facecolor`, `axes.facecolor`, grade, ticks,
legenda e fonte (`JetBrains Mono`).
