---
name: edicao
description: Escreve, revisa ou publica uma edição da Carta de carreira. Use quando a Karol pedir para escrever uma nova edição, continuar uma série (LinkedIn, transição, posicionamento), revisar um rascunho existente em content/, ou publicar o site. Também use para pedidos como "escreve a parte 2", "nova carta sobre X", "publica o site".
---

# Escrever uma edição da Carta de carreira

Este repositório publica páginas de conteúdo sobre carreira. O fluxo real é:
post no Instagram → a pessoa comenta → o ManyChat manda o link → ela lê a página
→ o CTA no fim leva para a mentoria.

Isso define tudo: **quem chega já demonstrou interesse, está no celular, e veio
de uma promessa específica feita no post.** A edição precisa entregar essa
promessa rápido e provar competência sem vender no meio do texto.

## Antes de escrever

1. Leia `content/` para ver as edições já publicadas: tom, tamanho, estrutura.
2. Leia `plano-serie-linkedin.md` se o pedido for de uma série em andamento.
3. Se for continuação, confirme qual `numero` da série está livre.

Se a Karol não disse o tema, **pergunte** antes de escrever. Nunca invente o
tema de uma edição.

## Formato do arquivo

Crie `content/AAAA-MM-DD-slug-curto.md`. O slug vira a URL, então mantenha
curto, sem acento e sem data: `linkedin-headline`, não `parte-1-como-fazer-um-otimo-headline`.

```
---
titulo: Frase curta e afiada, sem dois-pontos se der
subtitulo: Uma linha que complementa o título, não que o repete
data: 2026-08-11
serie: LinkedIn
numero: 1
resumo: Duas frases. Aparece no card do índice E no preview do link no direct.
rascunho: sim
---
```

Campos:

- `serie` e `numero` são opcionais, use só em conteúdo sequencial. Eles geram
  a etiqueta ("LINKEDIN · PARTE 1") e o bloco "outras partes da série".
- `resumo` é o texto que aparece **no preview do link no Instagram**. É o que
  decide se a pessoa clica. Trate como copy, não como resumo burocrático.
- `rascunho: sim` mantém fora do site. Remova a linha para publicar.

## Como escrever

**Tom.** Direta, sem rodeio, sem jargão de LinkedIn ("sinergia", "mindset
vencedor", "fora da caixa"). Segunda pessoa ("você"), presente. Frases curtas.
Pode discordar do senso comum, que é o que diferencia de conteúdo genérico.

**Nunca use travessão.** Nada de `—` nem `–`, em nenhum lugar: título,
subtítulo, resumo, corpo, config. A Karol não gosta e é regra firme. Onde a
tentação aparecer, o certo é uma destas saídas:

- vírgula, quando é aposto: *o headline, aquela linha embaixo do seu nome, é...*
- dois-pontos, quando o que vem depois explica ou lista o que veio antes
- ponto final, quando na verdade são duas frases
- parênteses, quando é mesmo um aparte dispensável

Para intervalo de números, escreva "de 4 a 7", não "4–7".

**Escreva em linguagem neutra.** Quem lê pode ser de qualquer gênero, e o
texto não pode presumir. Nada de "sozinha", "encontrada", "criadora",
"preparada", "a leitora". Saídas que funcionam sem travar a frase:

- fale direto com a pessoa em segunda pessoa, que em português já é neutra:
  *você consegue*, *você vai perceber*
- troque o adjetivo por substantivo ou verbo: ~~fica perdida~~ → *fica sem
  contexto*; ~~ser encontrada~~ → *ser encontrado pelas oportunidades* só se
  não houver saída melhor, e prefira *aparecer para as oportunidades*
- use "quem": *quem faz bem o que faz*, *quem está em transição*
- "pessoa", "profissional" e "gente" resolvem a maior parte dos casos

Isso vale também para `config.json` e para os resumos, não só para o corpo.

**Abertura.** Comece por uma observação concreta da prática de mentoria ("toda
semana eu abro dezenas de perfis e vejo o mesmo padrão"), nunca por definição de
dicionário nem por "no mundo atual do mercado de trabalho".

**Estrutura que funciona:**

1. O padrão/erro que a pessoa provavelmente está cometendo
2. Por que ele acontece, a lógica por trás, não só o "não faça isso"
3. O que fazer no lugar, com exemplo antes → depois de verdade
4. As objeções ("mas eu faço muita coisa", "tenho medo de me limitar")
5. Um exercício que dá para fazer em 5 minutos
6. Uma ponte para a próxima edição da série

**Exemplos são obrigatórios.** Toda afirmação abstrata precisa de um exemplo
concreto com cargo real. Use áreas variadas entre as edições (RH, financeiro,
dados, marketing, operações) para quem lê se enxergar.

**Tamanho.** 4 a 7 minutos de leitura (de 800 a 1400 palavras). Menos que isso não
prova competência; mais que isso não termina no celular.

**Não venda no meio do texto.** O CTA final é injetado automaticamente pelo
build a partir de `config.json`. Escrever "e na minha mentoria eu..." no meio
do conteúdo queima a confiança que o texto acabou de construir. O conteúdo
vende sozinho ao ser bom.

## Markdown disponível

O build usa um renderizador próprio, com um subconjunto de markdown:

- `##` e `###` para seções (o `#` já é o título do frontmatter, não use)
- `**negrito**`, `*itálico*`, `~~riscado~~`, `` `código` ``
- listas com `-` ou `1.`
- `> citação` para destacar um exemplo ruim/bom isolado
- `---` para uma quebra antes da ponte final
- blocos de destaque:

```
::: destaque
Para um aparte, uma objeção respondida, um caso particular.
:::

::: exercicio
Para a tarefa prática. Sempre inclua um por edição.
:::
```

Tabelas, HTML solto e imagens remotas **não** são suportados.

## Publicar

```bash
python3 scripts/build.py
```

Confira `docs/` e então:

```bash
git add -A && git commit -m "Nova edição: <título>" && git push
```

O site atualiza sozinho pelo GitHub Pages em 1 a 2 minutos.

Depois de publicar, ofereça à Karol as **legendas do post do Instagram** que
vão levar até essa edição: o texto do post e a resposta automática do
ManyChat. Uma edição publicada sem o post que leva até ela não serve para nada.
