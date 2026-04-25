#!/usr/bin/env bash
# record_simview_gifs.sh — Grava e otimiza os GIFs dos simuladores
# Dependências: ffmpeg, xwininfo, xprop  (sem xdotool)

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$REPO_ROOT/website/static/img/simview"
TMP_DIR="/tmp/simview_gifs"
PYTHON="python3"
DISP="${DISPLAY:-:0}"
WIN_W=1400
WIN_H=720
DURATION=13   # segundos de gravação por simulador

mkdir -p "$OUT_DIR" "$TMP_DIR"

# ── helpers ───────────────────────────────────────────────────────────────────

# Espera a janela cujo nome contém $1 aparecer; devolve o Window ID hex
wait_for_window() {
    local pat="$1"
    local timeout=25
    local wid=""
    echo "  aguardando janela '$pat'..."
    for _ in $(seq 1 $((timeout * 2))); do
        wid=$(xprop -root _NET_CLIENT_LIST 2>/dev/null \
            | grep -oP '0x[0-9a-f]+' \
            | while read -r id; do
                name=$(xprop -id "$id" WM_NAME 2>/dev/null | grep -oP '(?<=")[^"]+' | head -1)
                echo "$id $name"
              done \
            | grep -i "$pat" \
            | awk '{print $1}' \
            | head -1)
        [ -n "$wid" ] && { echo "$wid"; return 0; }
        sleep 0.5
    done
    echo "ERRO: janela '$pat' não apareceu em ${timeout}s" >&2
    return 1
}

# Move e redimensiona janela para 0,0 usando xprop/xdotool alternativo via X11
position_window() {
    local wid="$1"
    # Usa _NET_MOVERESIZE_WINDOW via xprop (X11 EWMH)
    xprop -id "$wid" -f _NET_WM_STATE 32a \
          -set _NET_WM_STATE _NET_WM_STATE_FULLSCREEN 2>/dev/null || true
    # Fallback: envia evento de resize via python-xlib se disponível
    python3 - "$wid" "$WIN_W" "$WIN_H" <<'PYEOF' 2>/dev/null || true
import sys, subprocess
wid, w, h = sys.argv[1], sys.argv[2], sys.argv[3]
# wmctrl-style via xdotool alternative: use xte if available
subprocess.run(['xte', f'windowfocus {wid}'], capture_output=True)
PYEOF
    sleep 1
}

# Detecta posição atual da janela via xwininfo
get_win_geometry() {
    local wid="$1"
    xwininfo -id "$wid" 2>/dev/null \
        | awk '/Absolute upper-left X:/{x=$NF} /Absolute upper-left Y:/{y=$NF} END{print x" "y}'
}

optimize_gif() {
    local input="$1"
    local output="$2"
    echo "  otimizando: $(basename "$output")"
    ffmpeg -y -i "$input" \
        -vf "fps=15,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" \
        "$output" 2>/dev/null
    echo "  tamanho: $(du -sh "$output" | cut -f1)  →  $output"
}

record_sim() {
    local name="$1"
    local script="$2"
    local title_pat="$3"
    local raw="$TMP_DIR/${name}_raw.gif"
    local final="$OUT_DIR/${name}.gif"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  [$name]  $script"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Abre o simulador
    DISPLAY=$DISP $PYTHON "$REPO_ROOT/$script" &
    local sim_pid=$!
    sleep 3   # aguarda Qt inicializar

    # Localiza a janela
    local wid
    wid=$(wait_for_window "$title_pat") || { kill $sim_pid 2>/dev/null; return 1; }
    echo "  window id: $wid"
    sleep 1

    # Posição atual da janela
    local geom
    geom=$(get_win_geometry "$wid")
    local win_x win_y
    win_x=$(echo "$geom" | awk '{print $1}')
    win_y=$(echo "$geom" | awk '{print $2}')
    echo "  posição da janela: x=$win_x y=$win_y"

    # Se a janela estiver fora da tela, usar 0,0
    [ -z "$win_x" ] && win_x=0
    [ -z "$win_y" ] && win_y=0
    [ "$win_x" -lt 0 ] 2>/dev/null && win_x=0
    [ "$win_y" -lt 0 ] 2>/dev/null && win_y=0

    # Grava a região da janela
    echo "  gravando ${DURATION}s em ${WIN_W}x${WIN_H}+${win_x},${win_y}..."
    ffmpeg -y \
        -f x11grab -r 30 \
        -s "${WIN_W}x${WIN_H}" \
        -i "${DISP}+${win_x},${win_y}" \
        -t "$DURATION" \
        "$raw" 2>/dev/null
    echo "  gravação concluída"

    # Fecha o simulador
    kill $sim_pid 2>/dev/null || true
    wait $sim_pid 2>/dev/null || true
    sleep 1

    optimize_gif "$raw" "$final"
}

# ── main ──────────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Gravação de GIFs — synapsys.viz.simview        ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "ROTEIRO — durante cada gravação:"
echo "  CartPole  → segure D ~3s → solte → aguarde estabilizar → segure A ~3s"
echo "  Pêndulo   → clique 'Torque dir.' ~3s → solte → aguarde → clique esq."
echo "  MSD       → tecla 2 → aguarde → tecla 3 → aguarde → tecla 1"
echo ""
echo "Iniciando em 5 s  (posicione as janelas no campo de visão)..."
sleep 5

record_sim "cartpole" \
    "examples/simulators/viz3d_cartpole_qt.py" \
    "Cart-Pole"

record_sim "pendulum" \
    "examples/simulators/viz3d_pendulum_qt.py" \
    "Pêndulo"

record_sim "msd" \
    "examples/simulators/viz3d_msd_qt.py" \
    "Mass-Spring-Damper"

# ── relatório ─────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  GIFs gerados em $OUT_DIR:"
ls -lh "$OUT_DIR"/*.gif 2>/dev/null | awk '{print "  "$5"  "$9}' || echo "  (nenhum)"
echo ""
echo "  Próximo passo:"
echo "  ./scripts/inject_gifs_into_docs.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
