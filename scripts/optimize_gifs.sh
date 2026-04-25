#!/usr/bin/env bash
# optimize_gifs.sh — Re-otimiza os GIFs raw com configurações agressivas
# Alvo: < 3 MB por GIF  (de ~100+ MB raw)
#
# Estratégia:
#   - Reduz para 420px de largura (suficiente para cards da homepage)
#   - 8 fps (suficiente para movimentos suaves)
#   - 32 cores na paleta + diff_mode=rectangle (delta por regiões)
#   - Recorta os primeiros 10 s (já que 13 s é longo)

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR="/tmp/simview_gifs"
OUT_DIR="$REPO_ROOT/website/static/img/simview"

optimize() {
    local name="$1"
    local raw="$TMP_DIR/${name}_raw.gif"
    local out="$OUT_DIR/${name}.gif"

    [ -f "$raw" ] || { echo "  SKIP $name (raw não encontrado)"; return; }

    echo "  $name: $(du -sh "$raw" | cut -f1) raw → otimizando..."

    ffmpeg -y -i "$raw" \
        -vf "trim=duration=10,fps=8,scale=420:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=32:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" \
        "$out" 2>/dev/null

    local size
    size=$(du -sh "$out" | cut -f1)
    echo "  $name: $size  →  $out"
}

echo "Re-otimizando GIFs (alvo < 3 MB)..."
optimize cartpole
optimize pendulum
optimize msd

echo ""
echo "Resultado final:"
ls -lh "$OUT_DIR"/*.gif 2>/dev/null | awk '{print "  "$5"  "$9}'
