#!/usr/bin/env python3
"""Gera versões autocontidas das páginas, para ver o site sem servidor.

O site em docs/ usa CSS e imagens em arquivos separados, então abrir uma
página solta pelo celular ou mandar por WhatsApp mostra o texto sem estilo
nenhum. Este script embute CSS e imagens dentro do próprio HTML: cada
arquivo gerado abre sozinho, em qualquer lugar.

    python3 scripts/build.py && python3 scripts/previa.py

Grava em previa/. É só para conferência. O que vai para o ar é docs/.
"""

from __future__ import annotations

import base64
import mimetypes
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
SAIDA = RAIZ / "previa"


def embutir(pagina: Path) -> str:
    html = pagina.read_text(encoding="utf-8")
    base = pagina.parent

    # 1. folha de estilo -> <style> inline
    def trocar_css(m: re.Match) -> str:
        alvo = (base / m.group(1)).resolve()
        if not alvo.is_file():
            return m.group(0)
        return f"<style>\n{alvo.read_text(encoding='utf-8')}\n</style>"

    html = re.sub(r'<link rel="stylesheet" href="([^"]+)"\s*/?>', trocar_css, html)

    # 2. imagens -> data: URI
    def trocar_img(m: re.Match) -> str:
        atributo, caminho = m.group(1), m.group(2)
        if caminho.startswith(("data:", "http://", "https://")):
            return m.group(0)
        alvo = (base / caminho).resolve()
        if not alvo.is_file():
            return m.group(0)
        tipo = mimetypes.guess_type(alvo.name)[0] or "application/octet-stream"
        dados = base64.b64encode(alvo.read_bytes()).decode()
        return f'{atributo}="data:{tipo};base64,{dados}"'

    html = re.sub(r'(src|href)="([^"]+\.(?:png|jpg|jpeg|gif|svg|webp))"', trocar_img, html)

    # 3. o ícone da aba não faz falta na prévia e pesaria o arquivo de novo
    html = re.sub(r'<link rel="icon"[^>]*/?>', "", html)

    # 4. a prévia é uma pasta plana, então a navegação do site (pastas por
    #    edição) precisa virar nome de arquivo, senão os links não abrem
    html = re.sub(r'href="(?:\.\./|\./)"', 'href="index.html"', html)
    html = re.sub(r'href="\.\./([\w-]+)/"', r'href="\1.html"', html)
    html = re.sub(r'href="([\w-]+)/"', r'href="\1.html"', html)

    return html


def main() -> int:
    if not DOCS.is_dir():
        print("docs/ não existe. Rode antes: python3 scripts/build.py")
        return 1

    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir()

    paginas = sorted(DOCS.rglob("index.html"))
    for pagina in paginas:
        relativo = pagina.parent.relative_to(DOCS)
        nome = "index.html" if relativo == Path(".") else f"{'-'.join(relativo.parts)}.html"
        destino = SAIDA / nome
        destino.write_text(embutir(pagina), encoding="utf-8")
        print(f"  → previa/{nome}  ({destino.stat().st_size / 1024:.0f} KB)")

    print(f"\n{len(paginas)} página(s). Abra qualquer uma direto no navegador.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
