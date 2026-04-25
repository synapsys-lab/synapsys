"""synapsys.viz.palette — Paleta de cores canônica do projeto Synapsys.

Todas as cores derivam do design system do website (website/src/css/custom.css).
Use sempre este módulo em exemplos, simulações e visualizações para garantir
consistência visual com a documentação.

Uso rápido
----------
>>> from synapsys.viz.palette import Dark
>>> Dark.BG          # fundo principal
>>> Dark.GOLD        # cor de destaque / brand
>>> Dark.SIG_POS     # sinal: posição / deslocamento

Matplotlib (aplica rcParams globais)
-------------------------------------
>>> from synapsys.viz.palette import mpl_theme
>>> mpl_theme()      # chamar antes de criar figures
"""

from __future__ import annotations


class Dark:
    """Tema escuro — espelho do design system do website (dark mode).

    Hierarquia de camadas
    ─────────────────────
    BG  →  SURFACE  →  PANEL  →  BORDER  (do mais escuro ao mais claro)

    Cores retiradas de :
      website/src/css/custom.css  [data-theme='dark']
    """

    # ── Fundos ────────────────────────────────────────────────────────────────
    BG = "#111111"  # fundo principal da janela / figura
    SURFACE = "#1a1a1a"  # superfície / card / panel
    PANEL = "#1e1e1e"  # painel interno (eixos matplotlib, grupbox Qt)
    BORDER = "#2e2e2e"  # borda padrão
    BORDER_LT = "#222222"  # borda sutil

    # ── Texto ─────────────────────────────────────────────────────────────────
    FG = "#e2e8f0"  # texto principal (foreground)
    MUTED = "#999999"  # texto secundário / labels de eixo
    SUBTLE = "#666666"  # texto terciário / dicas
    GRID = "#2e2e2e"  # linhas de grade matplotlib

    # ── Brand — retiradas diretamente do CSS do website ───────────────────────
    GOLD = "#c8a870"  # --brand-gold  (cor primária / destaque)
    GOLD_DIM = "#987040"  # --ifm-color-primary-darkest
    GOLD_LT = "#d8b880"  # --ifm-color-primary-light
    TEAL = "#0d9488"  # --brand-teal  (cor secundária)

    # ── Sinais de simulação — séries de dados / curvas ────────────────────────
    # Posição / deslocamento
    SIG_POS = "#3b82f6"  # azul médio   (posição, x, trajetória)
    SIG_POS_LT = "#60a5fa"  # azul claro   (variante ou segundo canal)

    # Velocidade / derivadas
    SIG_VEL = "#f97316"  # laranja       (velocidade, taxa)
    SIG_VEL_LT = "#fb923c"  # laranja claro (variante)

    # Referência / setpoint
    SIG_REF = "#22c55e"  # verde         (setpoint, referência)
    SIG_REF_DK = "#16a34a"  # verde escuro  (indicador visual)
    SIG_REF_LT = "#4ade80"  # verde claro   (checked/active)

    # Ângulo / rotação
    SIG_ANG = "#f97316"  # laranja (mesmo canal de derivada — ângulo)

    # Força / torque / controle
    SIG_CTRL = "#ef4444"  # vermelho      (força de controle, torque LQR)

    # Fase / trajetória no espaço de estados
    SIG_PHASE = "#a78bfa"  # violeta       (retrato de fase, trail)
    SIG_TRAIL = "#7c3aed"  # violeta escuro (trilha 3D)

    # Altitude / Z
    SIG_ALT = "#facc15"  # amarelo       (altitude z)

    # Canais adicionais (MIMO, Euler, etc.)
    SIG_CH1 = "#a78bfa"  # violeta  (canal φ / roll)
    SIG_CH2 = "#fb923c"  # laranja  (canal θ / pitch)
    SIG_CH3 = "#34d399"  # teal     (canal ψ / yaw)
    SIG_CH4 = "#f59e0b"  # âmbar    (4.º canal)
    SIG_CYAN = "#38bdf8"  # ciano    (ponto atual / dot marker)

    # ── Status / badges — espelham o CSS do website ───────────────────────────
    STATUS_STABLE = "#0d9488"  # .badge--stable
    STATUS_FUNCTIONAL = "#c8a870"  # .badge--functional
    STATUS_INTERFACE = "#d97706"  # .badge--interface
    STATUS_PLANNED = "#6b7280"  # .badge--planned

    # ── Danger / feedback ─────────────────────────────────────────────────────
    DANGER = "#ef4444"  # vermelho — erro, perturbação ativa
    WARN = "#f59e0b"  # âmbar   — aviso
    OK = "#22c55e"  # verde   — ok / estabilizado

    # ── Objetos 3D (meshes PyVista) ───────────────────────────────────────────
    MESH_BODY = "#2563eb"  # corpo principal (massa, carrinho, drone)
    MESH_STRUCT = "#334155"  # estrutura / trilho / base
    MESH_WALL = "#334155"  # parede
    MESH_FLOOR = "#1a1a1a"  # chão / plano
    MESH_SPRING = "#c8a870"  # mola (usa brand-gold)
    MESH_DAMP = "#64748b"  # amortecedor
    MESH_POLE = "#c8a870"  # haste (usa brand-gold)
    MESH_BOB = "#f97316"  # bob / ponta da haste
    MESH_RAIL = "#475569"  # trilho
    MESH_STOP = "#ef4444"  # batente final
    MESH_REF = "#4ade80"  # esfera de referência


def mpl_theme() -> None:
    """Aplica rcParams globais do tema Synapsys ao matplotlib.

    Deve ser chamado **antes** de criar qualquer Figure.

    Exemplo
    -------
    >>> from synapsys.viz.palette import mpl_theme
    >>> mpl_theme()
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()   # já com o tema aplicado
    """
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            # Figura
            "figure.facecolor": Dark.BG,
            "figure.edgecolor": Dark.BG,
            # Eixos
            "axes.facecolor": Dark.SURFACE,
            "axes.edgecolor": Dark.BORDER,
            "axes.labelcolor": Dark.MUTED,
            "axes.titlecolor": Dark.FG,
            "axes.grid": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            # Grade
            "grid.color": Dark.GRID,
            "grid.linewidth": 0.5,
            "grid.alpha": 0.7,
            # Ticks
            "xtick.color": Dark.MUTED,
            "ytick.color": Dark.MUTED,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            # Texto
            "text.color": Dark.FG,
            "font.family": ["JetBrains Mono", "Fira Code", "monospace"],
            "font.size": 9,
            # Legenda
            "legend.facecolor": Dark.SURFACE,
            "legend.edgecolor": Dark.BORDER,
            "legend.labelcolor": Dark.FG,
            "legend.fontsize": 7,
            # Linhas e marcadores
            "lines.linewidth": 1.5,
            "lines.markersize": 5,
            # Salvar
            "savefig.facecolor": Dark.BG,
            "savefig.edgecolor": Dark.BG,
        }
    )
