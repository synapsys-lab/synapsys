# Synapsys — Paleta de Cores

> **Fonte canônica:** `synapsys/viz/palette.py`  
> Todas as cores derivam de `website/src/css/custom.css` (dark mode).  
> **Regra:** nenhum arquivo de exemplo ou simulação deve hardcodar cores — importe sempre de `synapsys.viz.palette`.

---

## Importação

```python
from synapsys.viz.palette import Dark, mpl_theme
```

---

## Fundos e superfícies

| Token | Hex | Uso |
|---|---|---|
| `Dark.BG` | `#111111` | Fundo da janela / figura matplotlib |
| `Dark.SURFACE` | `#1a1a1a` | Cards, painéis, eixos matplotlib |
| `Dark.PANEL` | `#1e1e1e` | GroupBox Qt, camada intermediária |
| `Dark.BORDER` | `#2e2e2e` | Bordas padrão |
| `Dark.BORDER_LT` | `#222222` | Bordas sutis |

---

## Texto

| Token | Hex | Uso |
|---|---|---|
| `Dark.FG` | `#e2e8f0` | Texto principal |
| `Dark.MUTED` | `#999999` | Labels de eixo, texto secundário |
| `Dark.SUBTLE` | `#666666` | Dicas, texto terciário |
| `Dark.GRID` | `#2e2e2e` | Linhas de grade matplotlib |

---

## Brand (retiradas do CSS do website)

| Token | Hex | Variável CSS | Uso |
|---|---|---|---|
| `Dark.GOLD` | `#c8a870` | `--brand-gold` | Destaque principal, mola, haste |
| `Dark.GOLD_DIM` | `#987040` | `--ifm-color-primary-darkest` | Variante escura |
| `Dark.GOLD_LT` | `#d8b880` | `--ifm-color-primary-light` | Variante clara |
| `Dark.TEAL` | `#0d9488` | `--brand-teal` | Destaque secundário |

---

## Sinais de simulação

Cada canal de dado tem uma cor semântica fixa. Use sempre o mesmo canal para o mesmo tipo de grandeza física entre todos os exemplos.

| Token | Hex | Grandeza física |
|---|---|---|
| `Dark.SIG_POS` | `#3b82f6` | Posição / deslocamento (azul) |
| `Dark.SIG_POS_LT` | `#60a5fa` | Posição — segundo canal |
| `Dark.SIG_VEL` | `#f97316` | Velocidade / taxa (laranja) |
| `Dark.SIG_VEL_LT` | `#fb923c` | Velocidade — variante |
| `Dark.SIG_ANG` | `#f97316` | Ângulo (mesma família de velocidade) |
| `Dark.SIG_REF` | `#22c55e` | Setpoint / referência (verde) |
| `Dark.SIG_REF_DK` | `#16a34a` | Indicador visual do setpoint |
| `Dark.SIG_REF_LT` | `#4ade80` | Setpoint ativo / checked |
| `Dark.SIG_CTRL` | `#ef4444` | Força / torque de controle (vermelho) |
| `Dark.SIG_PHASE` | `#a78bfa` | Retrato de fase (violeta) |
| `Dark.SIG_TRAIL` | `#7c3aed` | Trilha 3D |
| `Dark.SIG_ALT` | `#facc15` | Altitude z (amarelo) |
| `Dark.SIG_CH1` | `#a78bfa` | Canal φ / roll (violeta) |
| `Dark.SIG_CH2` | `#fb923c` | Canal θ / pitch (laranja) |
| `Dark.SIG_CH3` | `#34d399` | Canal ψ / yaw (teal) |
| `Dark.SIG_CH4` | `#f59e0b` | 4.º canal (âmbar) |
| `Dark.SIG_CYAN` | `#38bdf8` | Ponto atual / dot marker |

---

## Objetos 3D (meshes PyVista)

| Token | Hex | Objeto |
|---|---|---|
| `Dark.MESH_BODY` | `#2563eb` | Corpo principal (massa, carrinho, drone) |
| `Dark.MESH_STRUCT` | `#334155` | Estrutura / chassis |
| `Dark.MESH_WALL` | `#334155` | Parede fixa |
| `Dark.MESH_FLOOR` | `#1a1a1a` | Chão / plano de referência |
| `Dark.MESH_SPRING` | `#c8a870` | Mola (brand-gold) |
| `Dark.MESH_DAMP` | `#64748b` | Amortecedor |
| `Dark.MESH_POLE` | `#c8a870` | Haste / braço (brand-gold) |
| `Dark.MESH_BOB` | `#f97316` | Bob / ponta da haste |
| `Dark.MESH_RAIL` | `#475569` | Trilho / guia |
| `Dark.MESH_STOP` | `#ef4444` | Batente / limite (vermelho) |
| `Dark.MESH_REF` | `#4ade80` | Esfera de referência (verde) |

---

## Status / badges

Espelham as classes `.badge--*` do CSS do website.

| Token | Hex | Significado |
|---|---|---|
| `Dark.STATUS_STABLE` | `#0d9488` | Estável (teal) |
| `Dark.STATUS_FUNCTIONAL` | `#c8a870` | Funcional (gold) |
| `Dark.STATUS_INTERFACE` | `#d97706` | Interface (âmbar) |
| `Dark.STATUS_PLANNED` | `#6b7280` | Planejado (cinza) |

---

## Feedback

| Token | Hex | Uso |
|---|---|---|
| `Dark.DANGER` | `#ef4444` | Erro, perturbação ativa, alerta crítico |
| `Dark.WARN` | `#f59e0b` | Aviso / saturação |
| `Dark.OK` | `#22c55e` | Sistema estabilizado / ok |

---

## Tema matplotlib global

```python
from synapsys.viz.palette import mpl_theme
mpl_theme()   # chamar antes de qualquer plt.figure()
```

O `mpl_theme()` configura automaticamente `figure.facecolor`, `axes.facecolor`, cores de grade, ticks, legenda e fonte (`JetBrains Mono`) — os mesmos tokens que o website usa.

---

## Exemplo completo

```python
import matplotlib.pyplot as plt
from synapsys.viz.palette import Dark, mpl_theme

mpl_theme()   # aplica o tema globalmente

fig, axes = plt.subplots(2, 1, figsize=(8, 6))

t = [0, 1, 2, 3, 4, 5]
q = [0, 0.3, 0.8, 1.4, 1.49, 1.5]
v = [0, 0.6, 0.9, 0.5, 0.1, 0.0]

axes[0].plot(t, q, color=Dark.SIG_POS,  lw=1.8, label="posição q")
axes[0].axhline(1.5, color=Dark.SIG_REF, ls="--", lw=1, label="setpoint")
axes[0].set_ylabel("m", color=Dark.MUTED)
axes[0].legend()

axes[1].plot(t, v, color=Dark.SIG_VEL, lw=1.8, label="velocidade q̇")
axes[1].set_xlabel("t (s)", color=Dark.MUTED)
axes[1].set_ylabel("m/s", color=Dark.MUTED)
axes[1].legend()

plt.tight_layout()
plt.show()
```

---

## Convenção de uso em simulações Qt

```python
# No topo do arquivo, em vez de hardcodar:
from synapsys.viz.palette import Dark

# Layout Qt
central.setStyleSheet(f"background:{Dark.BG};")
splitter.setStyleSheet(f"QSplitter::handle{{background:{Dark.BORDER};}}")

# Matplotlib
ax.set_facecolor(Dark.SURFACE)
ax.tick_params(colors=Dark.MUTED)
for sp in ax.spines.values():
    sp.set_edgecolor(Dark.BORDER)
ax.grid(True, color=Dark.GRID, linewidth=0.5, alpha=0.7)
```
