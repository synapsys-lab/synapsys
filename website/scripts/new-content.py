#!/usr/bin/env python3
"""
Scaffold a new blog post from template.

Usage:
    python scripts/new-content.py artigo "Título do Artigo"
    python scripts/new-content.py post   "Título do Post"
"""

import re
import sys
from datetime import date
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent / "blog"

VALID_TYPES = ("artigo", "post")


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[àáâãä]", "a", slug)
    slug = re.sub(r"[èéêë]", "e", slug)
    slug = re.sub(r"[ìíîï]", "i", slug)
    slug = re.sub(r"[òóôõö]", "o", slug)
    slug = re.sub(r"[ùúûü]", "u", slug)
    slug = re.sub(r"[ç]", "c", slug)
    slug = re.sub(r"[ñ]", "n", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug


def main() -> None:
    if len(sys.argv) != 3:
        print('Uso: python scripts/new-content.py <artigo|post> "Título"')
        sys.exit(1)

    content_type = sys.argv[1].lower()
    title = sys.argv[2]

    if content_type not in VALID_TYPES:
        print(f"Tipo inválido: '{content_type}'. Use 'artigo' ou 'post'.")
        sys.exit(1)

    today = date.today().isoformat()
    slug = slugify(title)
    folder_name = f"{today}-{slug}"
    dest = BLOG_DIR / folder_name

    if dest.exists():
        print(f"Já existe: {dest}")
        sys.exit(1)

    template = BLOG_DIR / f"_template-{content_type}" / "index.md"
    if not template.exists():
        print(f"Template não encontrado: {template}")
        sys.exit(1)

    dest.mkdir()
    content = template.read_text(encoding="utf-8")
    content = content.replace("SLUG-DO-ARTIGO", slug)
    content = content.replace("SLUG-DO-POST", slug)
    content = content.replace('title: "Título do Artigo"', f'title: "{title}"')
    content = content.replace('title: "Título do Post"', f'title: "{title}"')

    out = dest / "index.md"
    out.write_text(content, encoding="utf-8")

    sys.stdout.buffer.write(
        f"[OK] Criado: website/blog/{folder_name}/index.md\n".encode("utf-8")
    )
    sys.stdout.buffer.write(f"     slug:         {slug}\n".encode("utf-8"))
    sys.stdout.buffer.write(f"     content_type: {content_type}\n".encode("utf-8"))
    sys.stdout.buffer.write(
        f"     banner:       website/static/img/blog/{slug}-banner.png\n".encode(
            "utf-8"
        )
    )
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
