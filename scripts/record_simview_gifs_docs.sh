#!/usr/bin/env bash
# record_simview_gifs_docs.sh — Grava GIFs de tela INTEIRA para documentação
#
# Diferença dos GIFs da homepage:
#   homepage → recorte da cena 3D, 720px, < 2 MB
#   docs     → janela completa (3D + matplotlib), 1100px, < 6 MB
#
# Dependências: ffmpeg, xwininfo, xprop

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$REPO_ROOT/website/static/img/simview/docs"
TMP_DIR="/tmp/simview_gifs_docs"
PYTHON="python3"
DISP="${DISPLAY:-:0}"
DURATION=14   # segundos de gravação

mkdir -p "$OUT_DIR" "$TMP_DIR"

# ── helpers ───────────────────────────────────────────────────────────────────

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

# Retorna: x y width height
get_win_geometry() {
    local wid="$1"
    xwininfo -id "$wid" 2>/dev/null | awk '
        /Absolute upper-left X:/ { x=$NF }
        /Absolute upper-left Y:/ { y=$NF }
        /Width:/                 { w=$NF }
        /Height:/                { h=$NF }
        END { print x, y, w, h }
    '
}

optimize_docs_gif() {
    local input="$1"
    local output="$2"
    echo "  otimizando para docs: $(basename "$output")"
    # 1100px largura, 10 fps, 128 cores — janela inteira legível
    ffmpeg -y -i "$input" \
        -vf "fps=10,scale=1100:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" \
        "$output" 2>/dev/null
    echo "  tamanho: $(du -sh "$output" | cut -f1)  →  $output"
}

record_sim() {
    local name="$1"
    local script="$2"
    local title_pat="$3"
    local raw="$TMP_DIR/${name}_raw.mp4"
    local final="$OUT_DIR/${name}.gif"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  [$name]  $script"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    DISPLAY=$DISP $PYTHON "$REPO_ROOT/$script" &
    local sim_pid=$!
    sleep 4   # aguarda Qt + PyVista inicializarem completamente

    local wid
    wid=$(wait_for_window "$title_pat") || { kill $sim_pid 2>/dev/null; return 1; }
    echo "  window id: $wid"
    sleep 1

    local geom win_x win_y win_w win_h
    geom=$(get_win_geometry "$wid")
    win_x=$(echo "$geom" | awk '{print $1}')
    win_y=$(echo "$geom" | awk '{print $2}')
    win_w=$(echo "$geom" | awk '{print $3}')
    win_h=$(echo "$geom" | awk '{print $4}')

    [ -z "$win_x" ] && win_x=0
    [ -z "$win_y" ] && win_y=0
    [ -z "$win_w" ] && win_w=1400
    [ -z "$win_h" ] && win_h=720

    # Garante dimensões pares (exigência do ffmpeg)
    win_w=$(( (win_w / 2) * 2 ))
    win_h=$(( (win_h / 2) * 2 ))

    echo "  geometria: ${win_w}x${win_h} @ (${win_x}, ${win_y})"
    echo "  gravando ${DURATION}s da janela completa..."

    # Grava em MP4 (mais eficiente que GIF raw para arquivo temporário)
    ffmpeg -y \
        -f x11grab -r 30 \
        -s "${win_w}x${win_h}" \
        -i "${DISP}+${win_x},${win_y}" \
        -t "$DURATION" \
        -c:v libx264 -preset ultrafast -crf 18 \
        "$raw" 2>/dev/null
    echo "  gravação concluída"

    kill $sim_pid 2>/dev/null || true
    wait $sim_pid 2>/dev/null || true
    sleep 1

    optimize_docs_gif "$raw" "$final"
}

# ── main ──────────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   GIFs para Docs — janela COMPLETA               ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "ROTEIRO — durante cada gravação:"
echo "  CartPole  → segure D ~3s → solte → aguarde estabilizar → segure A ~3s"
echo "  Pêndulo   → clique 'Torque dir.' ~3s → solte → aguarde → clique esq."
echo "  MSD       → tecla 2 → aguarde → tecla 3 → aguarde → tecla 1"
echo ""
echo "Os GIFs serão salvos em: $OUT_DIR"
echo ""
echo "Iniciando em 5 s  (redimensione a janela para o tamanho desejado)..."
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
echo "  GIFs de docs gerados em $OUT_DIR:"
ls -lh "$OUT_DIR"/*.gif 2>/dev/null | awk '{print "  "$5"  "$9}' || echo "  (nenhum)"
echo ""
echo "  Próximo passo: atualizar as docs para usar /img/simview/docs/*.gif"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
