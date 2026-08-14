# Carta de Carreira

Site estático de conteúdo sobre carreira, transição e LinkedIn. Cada edição
vira uma página com link próprio, feita para ser mandada no direct.

**O fluxo:**

```
post no Instagram  →  pessoa comenta a palavra-chave  →  ManyChat manda o link
                   →  ela lê a página  →  CTA no fim leva para a mentoria
```

Não existe lista de e-mail, não existe cadastro, não existe login. A pessoa
clica e lê. É de propósito: menos atrito, mais leitura.

## Por que site próprio e não Substack

Substack, beehiiv e Kit existem para gerenciar **lista de e-mail** — captura,
disparo, métrica de abertura. Como o e-mail não entra neste fluxo, essas
ferramentas só acrescentariam limitação de layout e um domínio que não é seu.

Aqui você tem controle total do visual, do CTA e do rastreamento, de graça.

## Como escrever uma edição

Peça ao Claude: **"escreve a parte 2 da série de LinkedIn"**. A skill em
`.claude/skills/edicao/` já conhece o formato, o tom e a estrutura.

Ou escreva à mão: crie `content/AAAA-MM-DD-slug.md` com o frontmatter:

```markdown
---
titulo: Seu LinkedIn não é um currículo
subtitulo: E é exatamente por isso que o seu não traz oportunidade nenhuma.
data: 2026-08-11
serie: LinkedIn
numero: 1
resumo: Aparece no card do índice e no preview do link no direct.
---

Texto da edição em markdown.
```

Adicione `rascunho: sim` ao frontmatter para manter fora do ar enquanto escreve.

### Blocos especiais

```markdown
::: destaque
Um aparte, uma objeção respondida.
:::

::: exercicio
A tarefa prática da edição.
:::
```

## Como publicar

```bash
python3 scripts/build.py    # gera docs/ a partir de content/
git add -A && git commit -m "Nova edição: ..." && git push
```

Sem dependências: só Python 3.8+ da própria máquina. O GitHub Pages atualiza
em 1–2 minutos.

Para conferir antes de subir, abra `docs/index.html` no navegador.

## Configuração inicial

### 1. Preencha o `config.json`

Os campos que **precisam** ser trocados antes da primeira publicação:

| Campo | O que é |
|---|---|
| `site.url` | A URL final do site. Sem ela, o preview do link no direct sai quebrado. |
| `cta.link` | Para onde o botão leva: WhatsApp, Calendly, formulário. |
| `rodape.instagram` / `rodape.linkedin` | Seus perfis. |

O resto (`cta.titulo`, `cta.texto`, `cta.botao`) muda o CTA de **todas** as
edições de uma vez. Bom para testar chamadas diferentes.

### 2. Ligue o GitHub Pages

No repositório: **Settings → Pages → Source: Deploy from a branch →
branch `main`, pasta `/docs` → Save**.

Em um minuto o site está em `https://<usuário>.github.io/<repo>/`. Cole essa
URL em `site.url` no `config.json`, rode o build de novo e publique.

> O GitHub Pages é gratuito em repositórios **públicos**. Como o conteúdo vai
> ser público de qualquer forma, isso não é problema — só não guarde nada
> privado aqui.

### 3. Domínio próprio (opcional, recomendado)

`carta.somostakai.com.br` passa muito mais confiança no direct do que
`github.io`. Crie um registro CNAME no seu DNS apontando para
`<usuário>.github.io`, e informe o domínio em Settings → Pages.

### 4. Monte o fluxo no ManyChat

1. Gatilho: comentário no post com a palavra-chave (ex.: "LINKEDIN")
2. Resposta automática no direct com o link da edição
3. Uma pergunta de confirmação antes do link aumenta muito a entrega do
   Instagram ("quer que eu te mande?" → botão "quero")

Mande sempre o link **da edição**, não o do índice. A pessoa veio por um
assunto específico; fazer ela procurar perde leitura.

## Como saber qual edição converteu

O CTA aponta para um Google Formulário, e aí tem uma pegadinha: **UTM não
funciona.** O `forms.gle` é um encurtador e descarta a query no redirect, e o
Forms não reporta origem de tráfego. Sem tratamento, todas as respostas
chegam iguais e você não sabe qual edição trouxe cada pessoa.

O jeito que funciona é o formulário se autopreencher. Configuração, uma vez só:

1. No formulário, crie uma pergunta de resposta curta: **"Como você chegou
   até aqui?"** (pode deixar por último, e não obrigatória)
2. Menu de três pontos → **Obter link pré-preenchido** → escreva qualquer
   coisa nessa pergunta → **Obter link**
3. O link copiado tem um trecho `entry.123456789=qualquercoisa`. Copie só o
   `entry.123456789`
4. Cole em `cta.parametro_origem` no `config.json`
5. Troque `cta.link` pela **URL longa** do formulário
   (`docs.google.com/forms/d/e/.../viewform`) — o `forms.gle` curto descarta
   o preenchimento

Feito isso, cada edição passa a mandar o próprio slug na resposta, e a aba de
respostas mostra em qual texto a pessoa estava quando decidiu te procurar.

Enquanto `parametro_origem` estiver vazio, o build avisa e deixa o link
intacto — nada quebra, você só fica sem a atribuição.

> Se um dia o CTA apontar para WhatsApp ou Calendly em vez do Forms, o build
> volta a anexar UTMs sozinho (`utm_campaign=<slug-da-edição>`). Não precisa
> mexer em nada.

Para número de visitas, cole um script no campo `analytics` do `config.json`
(o [Plausible](https://plausible.io) e o [Umami](https://umami.is) são leves
e não precisam de aviso de cookie).

## Estrutura

```
config.json                 # marca, CTA e links — mexa aqui primeiro
content/*.md                # as edições, uma por arquivo
templates/estilo.css        # todo o visual do site
templates/edicao.html       # template de uma edição
templates/index.html        # template do índice
scripts/build.py            # gera docs/ (sem dependências externas)
assets/                     # logo e imagens
docs/                       # site gerado — é o que o Pages publica
plano-serie-linkedin.md     # roteiro das 4 edições de LinkedIn
```

`docs/` é regerado do zero a cada build. Não edite nada lá dentro — a mudança
some no próximo `build.py`.
