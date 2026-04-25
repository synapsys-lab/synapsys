---
id: viz-overview
title: Visualização 3D — Visão Geral
sidebar_label: Visão Geral
sidebar_position: 1
---

# Simuladores 3D — Visão Geral

![Cart-Pole — simulação 3D em tempo real](/img/simview/docs/cartpole.gif)

`synapsys.viz.simview` fornece janelas de simulação **plug-and-play** que combinam
renderização 3D em tempo real (PyVista) e telemetria (matplotlib) em uma única
interface PySide6 — pronta para receber qualquer controlador que você projetar.

---

## O que você obtém com uma linha

```python
from synapsys.viz import CartPoleView
CartPoleView().run()
```

Uma janela completa com:

- **Painel 3D** — animação física em tempo real (PyVista + VTK)
- **Painel de telemetria** — 4 gráficos matplotlib sincronizados (posição, ângulo, controle, retrato de fase)
- **Barra de controles** — botões de perturbação hold-to-apply, slider de magnitude, pausa/reset
- **LQR automático** — se nenhum controlador for passado, a lib lineariza o simulador e projeta um LQR internamente
- **Captura de teclado global** — A/D (perturbação), R (reset), Espaço (pausa), Q (fechar)

---

## Arquitetura

```
SimulatorBase          ← synapsys.simulators
│  dynamics(), step(), linearize()
│
SimViewBase            ← synapsys.viz.simview._base  (QMainWindow)
│  • cria janela Qt (splitter 3D + matplotlib)
│  • QTimer loop → _on_tick()
│  • auto-LQR via linearize() + lqr()
│  • teclado, perturbações, pausa, reset
│  • _build_all() chamado em run()
│
├── CartPoleView        ← state: [x, ẋ, θ, θ̇]
├── PendulumView        ← state: [θ, θ̇]
└── MassSpringDamperView ← state: [q, q̇]  + setpoint tracking
```

Cada subclasse implementa apenas o que é específico do seu sistema físico
(cena 3D, gráficos, HUD, parâmetros LQR). Todo o boilerplate Qt é herdado da base.

---

## Simuladores disponíveis

| Classe | Sistema físico | Estado | Entradas | Perturbação |
|---|---|---|---|---|
| `CartPoleView` | Carrinho + pêndulo | `[x, ẋ, θ, θ̇]` | Força no carrinho (N) | ◀/▶ força horizontal |
| `PendulumView` | Pêndulo invertido | `[θ, θ̇]` | Torque na junta (N·m) | ↺/↻ torque angular |
| `MassSpringDamperView` | Massa-mola-amortecedor | `[q, q̇]` | Força externa (N) | ◀/▶ força + setpoints 1/2/3 |

---

## Comparação: código standalone vs. módulo da lib

<table>
<thead><tr><th>Abordagem</th><th>Linhas de código</th><th>Requer conhecimento de Qt?</th></tr></thead>
<tbody>
<tr>
<td>Arquivo <code>viz3d_cartpole_qt.py</code> (standalone)</td>
<td>~470 linhas</td>
<td>Sim — layout, QTimer, splitter, canvas</td>
</tr>
<tr>
<td><code>CartPoleView().run()</code></td>
<td>1 linha</td>
<td>Não</td>
</tr>
<tr>
<td><code>CartPoleView(controller=minha_rede).run()</code></td>
<td>1 linha + sua função</td>
<td>Não</td>
</tr>
</tbody>
</table>

Os arquivos standalone em `examples/simulators/` continuam disponíveis como
referência didática para quem quiser entender a implementação interna ou criar
UIs altamente customizadas além do que a lib oferece.

---

## Dependências

```bash
pip install synapsys[viz]
# ou individualmente:
pip install pyside6 pyvistaqt matplotlib numpy
```

> **Nota:** `pyvistaqt` requer uma instalação de VTK compatível com Qt.
> Em ambientes headless (servidores sem display), use `pyvista` com backend offscreen.

---

## Próximos passos

- [Guia completo de uso →](./simview)
- [Conectar seu próprio controlador →](./custom-controller)
- [Referência da API →](../../api/viz)
