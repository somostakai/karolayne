#!/usr/bin/env python3
"""Gera o site estático da Carta de carreira a partir dos markdowns em content/.

Sem dependências externas: só a biblioteca padrão do Python 3.8+.

    python3 scripts/build.py

Lê  : config.json, content/*.md, templates/*.html, assets/
Grava: docs/  (pasta servida pelo GitHub Pages)
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

RAIZ = Path(__file__).resolve().parent.parent
CONTENT = RAIZ / "content"
TEMPLATES = RAIZ / "templates"
ASSETS = RAIZ / "assets"
SAIDA = RAIZ / "docs"

MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

PALAVRAS_POR_MINUTO = 200


# --------------------------------------------------------------------------
# Frontmatter
# --------------------------------------------------------------------------

def separar_frontmatter(texto: str) -> tuple[dict, str]:
    """Divide '---\\nchave: valor\\n---\\ncorpo' em (metadados, corpo)."""
    if not texto.startswith("---"):
        return {}, texto

    partes = texto.split("\n")
    if partes[0].strip() != "---":
        return {}, texto

    try:
        fim = partes.index("---", 1)
    except ValueError:
        return {}, texto

    meta: dict[str, str] = {}
    for linha in partes[1:fim]:
        linha = linha.strip()
        if not linha or linha.startswith("#") or ":" not in linha:
            continue
        chave, valor = linha.split(":", 1)
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        meta[chave.strip()] = valor

    return meta, "\n".join(partes[fim + 1:]).lstrip("\n")


# --------------------------------------------------------------------------
# Markdown (subconjunto)
# --------------------------------------------------------------------------

RE_CODIGO = re.compile(r"`([^`]+)`")
RE_IMAGEM = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
RE_NEGRITO = re.compile(r"\*\*([^*]+)\*\*")
RE_ITALICO = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
RE_RISCADO = re.compile(r"~~([^~]+)~~")


def _inline(texto: str) -> str:
    """Aplica formatação inline num trecho já sem marcação de bloco."""
    texto = html.escape(texto, quote=False)

    # Protege trechos de código antes de qualquer outra substituição.
    guardados: list[str] = []

    def guardar(m: re.Match) -> str:
        guardados.append(f"<code>{m.group(1)}</code>")
        return f"\x00{len(guardados) - 1}\x00"

    texto = RE_CODIGO.sub(guardar, texto)

    texto = RE_IMAGEM.sub(
        lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}" loading="lazy" />',
        texto,
    )
    texto = RE_LINK.sub(_link_html, texto)
    texto = RE_NEGRITO.sub(r"<strong>\1</strong>", texto)
    texto = RE_RISCADO.sub(r"<del>\1</del>", texto)
    texto = RE_ITALICO.sub(r"<em>\1</em>", texto)

    for i, bloco in enumerate(guardados):
        texto = texto.replace(f"\x00{i}\x00", bloco)

    return texto


def _link_html(m: re.Match) -> str:
    rotulo, destino = m.group(1), m.group(2)
    externo = destino.startswith(("http://", "https://"))
    extra = ' target="_blank" rel="noopener"' if externo else ""
    return f'<a href="{destino}"{extra}>{rotulo}</a>'


def renderizar_markdown(texto: str) -> str:
    """Converte o subconjunto de markdown usado nas edições em HTML."""
    linhas = texto.split("\n")
    saida: list[str] = []
    i = 0

    while i < len(linhas):
        linha = linhas[i]
        despida = linha.strip()

        if not despida:
            i += 1
            continue

        # Bloco de destaque:  ::: destaque ... :::
        if despida.startswith(":::"):
            variante = despida[3:].strip() or "destaque"
            corpo: list[str] = []
            i += 1
            while i < len(linhas) and linhas[i].strip() != ":::":
                corpo.append(linhas[i])
                i += 1
            i += 1
            interno = renderizar_markdown("\n".join(corpo))
            saida.append(f'<aside class="callout callout--{variante}">{interno}</aside>')
            continue

        # Regra horizontal
        if re.fullmatch(r"-{3,}|\*{3,}", despida):
            saida.append("<hr />")
            i += 1
            continue

        # Títulos
        cabecalho = re.match(r"(#{1,4})\s+(.*)", despida)
        if cabecalho:
            nivel = len(cabecalho.group(1))
            saida.append(f"<h{nivel}>{_inline(cabecalho.group(2))}</h{nivel}>")
            i += 1
            continue

        # Citação
        if despida.startswith(">"):
            corpo = []
            while i < len(linhas) and linhas[i].strip().startswith(">"):
                corpo.append(linhas[i].strip()[1:].strip())
                i += 1
            saida.append(f"<blockquote><p>{_inline(' '.join(corpo))}</p></blockquote>")
            continue

        # Lista não ordenada
        if re.match(r"[-*]\s+", despida):
            itens = []
            while i < len(linhas) and re.match(r"[-*]\s+", linhas[i].strip()):
                itens.append(_inline(re.sub(r"^[-*]\s+", "", linhas[i].strip())))
                i += 1
            corpo = "".join(f"<li>{item}</li>" for item in itens)
            saida.append(f"<ul>{corpo}</ul>")
            continue

        # Lista ordenada
        if re.match(r"\d+[.)]\s+", despida):
            itens = []
            while i < len(linhas) and re.match(r"\d+[.)]\s+", linhas[i].strip()):
                itens.append(_inline(re.sub(r"^\d+[.)]\s+", "", linhas[i].strip())))
                i += 1
            corpo = "".join(f"<li>{item}</li>" for item in itens)
            saida.append(f"<ol>{corpo}</ol>")
            continue

        # Parágrafo: junta linhas até uma linha em branco ou um novo bloco.
        corpo = []
        while i < len(linhas) and linhas[i].strip():
            atual = linhas[i].strip()
            if atual.startswith((":::", ">", "#")) or re.match(r"[-*]\s+|\d+[.)]\s+", atual):
                break
            corpo.append(atual)
            i += 1
        if corpo:
            saida.append(f"<p>{_inline(' '.join(corpo))}</p>")

    return "\n".join(saida)


# --------------------------------------------------------------------------
# Edições
# --------------------------------------------------------------------------

class Edicao:
    def __init__(self, caminho: Path, meta: dict, corpo_md: str):
        self.caminho = caminho
        self.meta = meta
        self.corpo_md = corpo_md

        self.slug = meta.get("slug") or self._slug_do_arquivo()
        self.titulo = meta.get("titulo", "Sem título")
        self.subtitulo = meta.get("subtitulo", "")
        self.serie = meta.get("serie", "")
        self.numero = meta.get("numero", "")
        self.resumo = meta.get("resumo", "")
        self.rascunho = meta.get("rascunho", "").lower() in ("sim", "true", "1")
        self.data = self._parse_data(meta.get("data", ""))
        self.corpo_html = renderizar_markdown(corpo_md)
        self.minutos = max(1, round(len(corpo_md.split()) / PALAVRAS_POR_MINUTO))

    def _slug_do_arquivo(self) -> str:
        nome = self.caminho.stem
        return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", nome)

    @staticmethod
    def _parse_data(valor: str) -> date | None:
        try:
            return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    @property
    def data_legivel(self) -> str:
        if not self.data:
            return ""
        return f"{self.data.day} de {MESES[self.data.month - 1]} de {self.data.year}"

    @property
    def etiqueta(self) -> str:
        """Ex.: 'LinkedIn · parte 2'."""
        partes = [p for p in (self.serie, f"parte {self.numero}" if self.numero else "") if p]
        return " · ".join(partes)

    @property
    def url(self) -> str:
        return f"{self.slug}/"


def carregar_edicoes() -> list[Edicao]:
    edicoes = []
    for caminho in sorted(CONTENT.glob("*.md")):
        meta, corpo = separar_frontmatter(caminho.read_text(encoding="utf-8"))
        if not meta:
            print(f"  aviso: {caminho.name} sem frontmatter, ignorado")
            continue
        edicao = Edicao(caminho, meta, corpo)
        if edicao.rascunho:
            print(f"  rascunho (não publicado): {caminho.name}")
            continue
        edicoes.append(edicao)

    # Mais recentes primeiro; sem data vai para o fim.
    edicoes.sort(key=lambda e: (e.data is not None, e.data or date.min), reverse=True)
    return edicoes


# --------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------

def preencher(template: str, valores: dict[str, str]) -> str:
    """Substituição simples de {{ chave }}, sem motor de template externo."""
    def trocar(m: re.Match) -> str:
        return str(valores.get(m.group(1).strip(), ""))

    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", trocar, template)


_AVISOS: set[str] = set()


def _avisar(msg: str) -> None:
    """Avisa uma vez só, mesmo com várias edições."""
    if msg not in _AVISOS:
        _AVISOS.add(msg)
        print(f"  aviso: {msg}")


def link_cta(link: str, campanha: str, cta: dict) -> str:
    """Marca o link do CTA com a edição de origem.

    Google Forms ignora UTM: o `forms.gle` é encurtador e descarta a query
    no redirect, e o Forms não reporta origem de tráfego. O que funciona é
    preencher campos do próprio formulário pela URL:

    - `cta.parametro_origem`: o `entry.NNNNN` de uma pergunta de **resposta
      curta**, que recebe o slug da edição. Precisa ser resposta curta,
      lista suspensa e múltipla escolha só aceitam valor idêntico a uma das
      opções cadastradas, e descartam qualquer outro.
    - `cta.prefill`: pares `entry.NNNNN: valor` fixos, para já deixar
      respondidas perguntas de opção (ex.: o canal "Newsletter"). O valor
      tem que ser idêntico à opção no formulário, acento inclusive.
    """
    if not link or link.startswith(("#", "mailto:", "tel:")):
        return link

    partes = urlsplit(link)
    query = dict(parse_qsl(partes.query, keep_blank_values=True))
    eh_forms = "forms.gle" in partes.netloc or "/forms/" in partes.path
    parametro = cta.get("parametro_origem", "").strip()
    fixos = {k: v for k, v in (cta.get("prefill") or {}).items() if k and v}

    if parametro or fixos:
        if "forms.gle" in partes.netloc:
            _avisar(
                "cta.link é um forms.gle (encurtador) e descarta o prefill. "
                "Troque pela URL longa do formulário (docs.google.com/forms/...)."
            )
        query["usp"] = "pp_url"
        query.update(fixos)
        if parametro:
            query[parametro] = campanha
    elif eh_forms:
        # Sem parâmetro configurado o link vai limpo: o formulário já pergunta
        # o canal de origem, e a atribuição por edição é opcional (ver README).
        return link
    else:
        query.setdefault("utm_source", "carta-de-carreira")
        query.setdefault("utm_medium", "cta")
        query.setdefault("utm_campaign", campanha)

    return urlunsplit(partes._replace(query=urlencode(query)))


def bloco_cta(cfg: dict, campanha: str) -> str:
    cta = cfg.get("cta", {})
    if not cta.get("link"):
        return ""

    nota = f'<p class="cta__nota">{html.escape(cta.get("nota", ""))}</p>' if cta.get("nota") else ""
    return f"""<section class="cta">
  <h2 class="cta__titulo">{html.escape(cta.get("titulo", ""))}</h2>
  <p class="cta__texto">{html.escape(cta.get("texto", ""))}</p>
  <a class="cta__botao" href="{link_cta(cta["link"], campanha, cta)}" target="_blank" rel="noopener">{html.escape(cta.get("botao", "Saber mais"))}</a>
  {nota}
</section>"""


def bloco_rodape_links(cfg: dict) -> str:
    """Só entra no rodapé o que estiver preenchido no config."""
    rodape = cfg.get("rodape", {})
    rotulos = {"instagram": "Instagram", "linkedin": "LinkedIn", "site": "takai"}

    itens = [
        f'<a href="{url}" target="_blank" rel="noopener">{rotulo}</a>'
        for chave, rotulo in rotulos.items()
        if (url := rodape.get(chave, "").strip())
    ]
    return f'<p class="rodape__links">{"".join(itens)}</p>' if itens else ""


def bloco_relacionadas(atual: Edicao, todas: list[Edicao]) -> str:
    """Outras edições da mesma série, para manter a pessoa lendo."""
    if not atual.serie:
        return ""

    irmas = [e for e in todas if e.serie == atual.serie and e.slug != atual.slug]
    if not irmas:
        return ""

    irmas.sort(key=lambda e: int(e.numero) if e.numero.isdigit() else 99)
    itens = "".join(
        f'<li><a href="../{e.slug}/"><span class="rel__num">{e.numero or "·"}</span>'
        f'<span class="rel__titulo">{html.escape(e.titulo)}</span></a></li>'
        for e in irmas
    )
    return f"""<section class="relacionadas">
  <h2 class="relacionadas__titulo">Outras partes da série {html.escape(atual.serie)}</h2>
  <ul class="rel">{itens}</ul>
</section>"""


def construir_edicao(edicao: Edicao, todas: list[Edicao], cfg: dict, template: str) -> str:
    site = cfg.get("site", {})
    rodape = cfg.get("rodape", {})
    base_url = site.get("url", "").rstrip("/")

    descricao = edicao.resumo or site.get("descricao", "")
    og_image = site.get("og_image") or (f"{base_url}/{site.get('logo', '')}" if base_url else "")

    return preencher(template, {
        "titulo": html.escape(edicao.titulo),
        "subtitulo": html.escape(edicao.subtitulo),
        "etiqueta": html.escape(edicao.etiqueta),
        "data_legivel": edicao.data_legivel,
        "minutos": str(edicao.minutos),
        "corpo": edicao.corpo_html,
        "cta": bloco_cta(cfg, edicao.slug),
        "relacionadas": bloco_relacionadas(edicao, todas),
        "site_nome": html.escape(site.get("nome", "")),
        "autora": html.escape(site.get("autora", "")),
        "autora_bio": html.escape(site.get("autora_bio", "")),
        "descricao": html.escape(descricao),
        "url_canonica": f"{base_url}/{edicao.url}" if base_url else "",
        "og_image": og_image,
        "rodape_links": bloco_rodape_links(cfg),
        "ano": str(date.today().year),
        "analytics": cfg.get("analytics", ""),
        "prefixo": "../",
        "logo": "../" + site.get("logo", ""),
    })


def construir_indice(edicoes: list[Edicao], cfg: dict, template: str) -> str:
    site = cfg.get("site", {})
    rodape = cfg.get("rodape", {})
    base_url = site.get("url", "").rstrip("/")

    cartoes = []
    for e in edicoes:
        etiqueta = f'<span class="card__etiqueta">{html.escape(e.etiqueta)}</span>' if e.etiqueta else ""
        cartoes.append(f"""<li class="card">
  <a class="card__link" href="{e.url}">
    {etiqueta}
    <h2 class="card__titulo">{html.escape(e.titulo)}</h2>
    <p class="card__resumo">{html.escape(e.resumo or e.subtitulo)}</p>
    <p class="card__meta">{e.data_legivel} · {e.minutos} min de leitura</p>
  </a>
</li>""")

    vazio = '<p class="vazio">Primeira edição chegando.</p>' if not cartoes else ""

    return preencher(template, {
        "site_nome": html.escape(site.get("nome", "")),
        "tagline": html.escape(site.get("tagline", "")),
        "descricao": html.escape(site.get("descricao", "")),
        "autora": html.escape(site.get("autora", "")),
        "autora_bio": html.escape(site.get("autora_bio", "")),
        "cartoes": "\n".join(cartoes),
        "vazio": vazio,
        "cta": bloco_cta(cfg, "index"),
        "url_canonica": f"{base_url}/" if base_url else "",
        "og_image": site.get("og_image") or (f"{base_url}/{site.get('logo', '')}" if base_url else ""),
        "rodape_links": bloco_rodape_links(cfg),
        "ano": str(date.today().year),
        "analytics": cfg.get("analytics", ""),
        "logo": site.get("logo", ""),
    })


# --------------------------------------------------------------------------

def main() -> int:
    cfg = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))

    tpl_edicao = (TEMPLATES / "edicao.html").read_text(encoding="utf-8")
    tpl_indice = (TEMPLATES / "index.html").read_text(encoding="utf-8")

    print("Lendo edições...")
    edicoes = carregar_edicoes()
    if not edicoes:
        print("  nenhuma edição publicável encontrada em content/")

    # Domínio próprio: ao configurar em Settings > Pages, o GitHub grava um
    # arquivo docs/CNAME. Como o build recria docs/ do zero, sem resgatar esse
    # arquivo antes o domínio cairia no primeiro build seguinte.
    dominio = cfg.get("site", {}).get("dominio", "").strip()
    cname = SAIDA / "CNAME"
    if not dominio and cname.is_file():
        dominio = cname.read_text(encoding="utf-8").strip()

    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir(parents=True)

    if dominio:
        (SAIDA / "CNAME").write_text(dominio + "\n", encoding="utf-8")
        print(f"  domínio próprio preservado: {dominio}")

    # GitHub Pages não serve pastas iniciadas por "_" sem isto.
    (SAIDA / ".nojekyll").write_text("", encoding="utf-8")

    if ASSETS.exists():
        shutil.copytree(ASSETS, SAIDA / "assets")

    shutil.copy2(TEMPLATES / "estilo.css", SAIDA / "estilo.css")

    for edicao in edicoes:
        destino = SAIDA / edicao.slug
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "index.html").write_text(
            construir_edicao(edicao, edicoes, cfg, tpl_edicao), encoding="utf-8"
        )
        print(f"  → docs/{edicao.slug}/index.html  ({edicao.minutos} min)")

    (SAIDA / "index.html").write_text(
        construir_indice(edicoes, cfg, tpl_indice), encoding="utf-8"
    )
    print(f"  → docs/index.html  ({len(edicoes)} edição/edições)")
    print("\nPronto. Abra docs/index.html no navegador para conferir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
