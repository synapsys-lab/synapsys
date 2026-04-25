#!/usr/bin/env bash
# inject_gifs_into_docs.sh — Substitui blocos :::info GIF em breve pelos GIFs reais
#
# Uso: ./scripts/inject_gifs_into_docs.sh
# Pré-condição: os 3 GIFs já devem existir em website/static/img/simview/

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIMVIEW_DOC="$REPO_ROOT/website/docs/guide/viz/simview.md"
GIF_DIR="$REPO_ROOT/website/static/img/simview"
MISSING=0

check_gif() {
    local name="$1"
    if [ ! -f "$GIF_DIR/${name}.gif" ]; then
        echo "  FALTANDO: $GIF_DIR/${name}.gif"
        MISSING=$((MISSING + 1))
    else
        local size
        size=$(du -sh "$GIF_DIR/${name}.gif" | cut -f1)
        echo "  OK ($size): ${name}.gif"
    fi
}

echo "Verificando GIFs..."
check_gif cartpole
check_gif pendulum
check_gif msd

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "ERRO: $MISSING GIF(s) faltando. Rode primeiro:"
    echo "  ./scripts/record_simview_gifs.sh"
    exit 1
fi

echo ""
echo "Injetando GIFs em $SIMVIEW_DOC ..."

# Substituir bloco cartpole
python3 - <<'EOF'
import re, pathlib

doc = pathlib.Path("website/docs/guide/viz/simview.md")
text = doc.read_text()

replacements = {
    "cartpole": (
        r":::info GIF em breve\n_Gravação da janela CartPole.*?:::",
        "![CartPole — simulação 3D em tempo real](../../../static/img/simview/cartpole.gif)"
    ),
    "pendulum": (
        r":::info GIF em breve\n_Gravação da janela PendulumView.*?:::",
        "![Pêndulo Invertido — simulação 3D em tempo real](../../../static/img/simview/pendulum.gif)"
    ),
    "msd": (
        r":::info GIF em breve\n_Gravação da janela MassSpringDamperView.*?:::",
        "![Mass-Spring-Damper — simulação 3D em tempo real](../../../static/img/simview/msd.gif)"
    ),
}

for name, (pattern, replacement) in replacements.items():
    new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    if new_text == text:
        print(f"  AVISO: padrão '{name}' não encontrado (já substituído?)")
    else:
        text = new_text
        print(f"  substituído: {name}")

doc.write_text(text)
print("  salvo:", doc)
EOF

echo ""
echo "Feito. Reinicie o servidor para ver as mudanças:"
echo "  cd website && npm run start -- --port 3001"
