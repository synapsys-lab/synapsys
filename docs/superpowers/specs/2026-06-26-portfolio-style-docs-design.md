# Design: Aplicar estilo do portfólio à documentação Synapsys

**Data:** 2026-06-26  
**Escopo:** Website Docusaurus em `website/`  
**Referência visual:** `/home/osfarias/workspace/sites_blogs/oseias-farias-portfolio/`

---

## Objetivo

Migrar a identidade visual da documentação Synapsys para corresponder ao portfólio pessoal do autor, mantendo a legibilidade de documentação técnica longa e a estrutura Docusaurus intacta.

---

## Decisões de design

| Dimensão | Decisão |
|---|---|
| Escopo | Todo o site (docs, blog, navbar, homepage) |
| Modo padrão | Dark-first, toggle disponível |
| Fonte corpo | Inter (legibilidade técnica) |
| Fonte código | IBM Plex Mono |
| Fonte títulos | IBM Plex Mono (consistência mono com portfólio) |
| Accent | `#e8513a` (laranja-vermelho, igual ao portfólio) |
| Estratégia | CSS tokens + homepage redesign (sem swizzle de componentes) |

---

## Paleta de cores

### Dark (padrão)

```
--bg:        #0d0c0b   (fundo principal)
--bg2:       #131210   (superfícies/cards)
--panel:     #121110   (sidebar/navbar)
--line:      rgba(236,233,225,.13)  (bordas sutis)
--line-2:    rgba(236,233,225,.32)  (bordas de destaque)
--grid:      rgba(236,233,225,.04)  (grade de fundo)
--fg:        #ece9e1   (texto principal)
--fg-muted:  #a39d90   (texto secundário)
--fg-soft:   #6f695c   (texto terciário/placeholders)
--accent:    #e8513a   (links, botões, badges ativos)
```

### Light

```
--bg:        #f3efe6
--bg2:       #ebe6d9
--panel:     #f8f5ee
--line:      rgba(20,17,13,.14)
--line-2:    rgba(20,17,13,.34)
--grid:      rgba(20,17,13,.045)
--fg:        #17130d
--fg-muted:  #5b5446
--fg-soft:   #8a8273
--accent:    #e8513a
```

---

## Arquitetura de implementação

### Tarefa 1 — CSS tokens (`website/src/css/custom.css`)

Reescrever completamente o arquivo com:
- Importação das fontes via Google Fonts: `IBM Plex Mono` + `Inter`
- Mapeamento de todos os tokens do portfólio para variáveis `--ifm-*` do Docusaurus
- Variantes dark e light
- Animação `livedot` (do portfólio) para uso nos componentes
- Estilos globais: scrollbar customizada, seleção de texto com accent, links com underline accent

Variáveis Docusaurus afetadas:
- `--ifm-color-primary` → `#e8513a`
- `--ifm-background-color` → `--bg`
- `--ifm-navbar-background-color` → `--panel` com blur
- `--ifm-font-family-base` → Inter
- `--ifm-font-family-monospace` → IBM Plex Mono
- `--ifm-heading-font-family` → IBM Plex Mono
- `--ifm-toc-border-color` → `--line`
- `--ifm-sidebar-*` → variantes de `--bg2`

### Tarefa 2 — Homepage (`website/src/pages/index.tsx`)

Reescrever a homepage com 4 blocos:

**Hero:**
- Grade sutil de fundo via CSS (`background-image: linear-gradient`)
- Headline em IBM Plex Mono com badge de versão
- Subtítulo em Inter
- Dois CTAs: "Get Started" (accent fill) e "GitHub" (border)
- Fade-in via framer-motion (já disponível como dependência do Docusaurus não — verificar ou usar CSS animation)

**Stats bar:**
- Linha horizontal com separadores `|`
- 4 métricas: módulos, transports, algoritmos, cobertura de testes
- Contador animado via CSS ou hook simples

**Feature cards:**
- Grid 3 colunas (responsivo 1 em mobile)
- Borda `1px solid var(--line)`, fundo `var(--bg2)`
- Ícone lucide + título mono + descrição Inter
- Hover: borda `var(--line-2)`

**Module status table:**
- Reutilizar a tabela existente de módulos
- Badges reestilizados: Stable=verde, Functional=accent, Planned=muted

Componentes existentes mantidos e reestilizados via CSS:
- `LibraryMap` — herda tokens automaticamente
- `HomeBlogSection` — herda tokens automaticamente  
- `SimulatorsShowcase` — herda tokens automaticamente

### Tarefa 3 — `docusaurus.config.ts`

- Confirmar `defaultMode: 'dark'` (já está correto)
- Adicionar `respectPrefersColorScheme: false` (já está correto)
- Sem outras mudanças

---

## Dependências

- **framer-motion:** Não será adicionado. Usar CSS animations puras (`@keyframes`, `animation`) para fade-in e transições — evita bundle extra no Docusaurus.
- **lucide-react:** Já disponível em `website/package.json` (`^1.8.0`). Usar normalmente.

---

## O que NÃO muda

- Estrutura de docs, blog e sidebars
- Conteúdo de qualquer página
- Internacionalização (i18n pt/en)
- Componentes `LibraryMap`, `HomeBlogSection`, `SimulatorsShowcase` (internamente)
- Plugins (search, mermaid, zoom)
- `docusaurus.config.ts` além do colorMode

---

## Critérios de sucesso

1. `npm run build` passa sem erros
2. Visual dark é idêntico em paleta ao portfólio
3. Toggle light/dark funciona em todas as páginas
4. Homepage tem os 4 blocos descritos
5. Docs, blog e navbar herdam os tokens corretamente
6. Legibilidade em páginas longas de API reference é boa (Inter 16px, line-height 1.7)
