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


class Light:
    """Tema claro — para ambientes com fundo branco (apresentações, relatórios).

    Hierarquia de camadas
    ─────────────────────
    BG  →  SURFACE  →  PANEL  →  BORDER  (do mais claro ao mais escuro)
    """

    # ── Fundos ────────────────────────────────────────────────────────────────
    BG = "#ffffff"
    SURFACE = "#f8fafc"
    PANEL = "#f1f5f9"
    BORDER = "#e2e8f0"
    BORDER_LT = "#f1f5f9"

    # ── Texto ─────────────────────────────────────────────────────────────────
    FG = "#0f172a"
    MUTED = "#475569"
    SUBTLE = "#94a3b8"
    GRID = "#e2e8f0"

    # ── Brand ─────────────────────────────────────────────────────────────────
    GOLD = "#92671e"
    GOLD_DIM = "#6b4a15"
    GOLD_LT = "#c8a870"
    TEAL = "#0d9488"

    # ── Sinais ────────────────────────────────────────────────────────────────
    SIG_POS = "#1d4ed8"
    SIG_POS_LT = "#3b82f6"
    SIG_VEL = "#c2410c"
    SIG_VEL_LT = "#ea580c"
    SIG_REF = "#15803d"
    SIG_REF_DK = "#166534"
    SIG_REF_LT = "#22c55e"
    SIG_ANG = "#c2410c"
    SIG_CTRL = "#b91c1c"
    SIG_PHASE = "#7c3aed"
    SIG_TRAIL = "#6d28d9"
    SIG_ALT = "#b45309"
    SIG_CH1 = "#7c3aed"
    SIG_CH2 = "#c2410c"
    SIG_CH3 = "#0f766e"
    SIG_CH4 = "#b45309"
    SIG_CYAN = "#0284c7"

    # ── Status ────────────────────────────────────────────────────────────────
    STATUS_STABLE = "#0d9488"
    STATUS_FUNCTIONAL = "#92671e"
    STATUS_INTERFACE = "#d97706"
    STATUS_PLANNED = "#6b7280"

    # ── Danger / feedback ─────────────────────────────────────────────────────
    DANGER = "#dc2626"
    WARN = "#d97706"
    OK = "#16a34a"

    # ── Objetos 3D ────────────────────────────────────────────────────────────
    MESH_BODY = "#1d4ed8"
    MESH_STRUCT = "#64748b"
    MESH_WALL = "#94a3b8"
    MESH_FLOOR = "#e2e8f0"
    MESH_SPRING = "#92671e"
    MESH_DAMP = "#64748b"
    MESH_POLE = "#92671e"
    MESH_BOB = "#c2410c"
    MESH_RAIL = "#94a3b8"
    MESH_STOP = "#dc2626"
    MESH_REF = "#15803d"


def mpl_theme(theme: str = "dark") -> None:
    """Aplica rcParams globais do tema Synapsys ao matplotlib.

    Parameters
    ----------
    theme:
        ``"dark"`` (padrão) ou ``"light"``.

    Exemplo
    -------
    >>> from synapsys.viz.palette import mpl_theme
    >>> mpl_theme()           # dark
    >>> mpl_theme("light")    # light
    """
    import matplotlib as mpl

    p = Light if theme == "light" else Dark
    mpl.rcParams.update(
        {
            "figure.facecolor": p.BG,
            "figure.edgecolor": p.BG,
            "axes.facecolor": p.SURFACE,
            "axes.edgecolor": p.BORDER,
            "axes.labelcolor": p.MUTED,
            "axes.titlecolor": p.FG,
            "axes.grid": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": p.GRID,
            "grid.linewidth": 0.5,
            "grid.alpha": 0.7,
            "xtick.color": p.MUTED,
            "ytick.color": p.MUTED,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "text.color": p.FG,
            "font.family": ["JetBrains Mono", "Fira Code", "monospace"],
            "font.size": 9,
            "legend.facecolor": p.SURFACE,
            "legend.edgecolor": p.BORDER,
            "legend.labelcolor": p.FG,
            "legend.fontsize": 7,
            "lines.linewidth": 1.5,
            "lines.markersize": 5,
            "savefig.facecolor": p.BG,
            "savefig.edgecolor": p.BG,
        }
    )
