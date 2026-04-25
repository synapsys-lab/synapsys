# Plano de Documentação — `synapsys.viz.simview`

> **Objetivo:** documentar completamente a feature de simuladores 3D plug-and-play,
> com GIFs demonstrativos, páginas de guia detalhadas, referência de API e
> grid de simuladores na homepage do website.
>
> **Status geral:** ✅ Etapas 1–4 concluídas · 🔲 Etapa 5 (simuladores futuros)

---

## Etapa 1 — Gravação dos GIFs ✅

### 1.1 Preparação do ambiente de gravação

- [x] Instalar ferramenta de gravação (`ffmpeg` disponível)
- [x] Criar diretório de destino `website/static/img/simview/`
- [x] Testar gravação de janela de exemplo (xprop + ffmpeg x11grab)

### 1.2 Gravar cada simulador

Script: `scripts/record_simview_gifs.sh`

- [x] **CartPole** — gravado 13 s via `viz3d_cartpole_qt.py`
- [x] **Pêndulo Invertido** — gravado 13 s via `viz3d_pendulum_qt.py`
- [x] **Mass-Spring-Damper** — gravado 13 s via `viz3d_msd_qt.py`

### 1.3 Otimizar GIFs

Script: `scripts/optimize_gifs.sh`
Configuração final: `fps=8, scale=420px, max_colors=32, trim=7s`

- [x] `cartpole.gif` → **1.5 MB** ✓
- [x] `pendulum.gif` → **1.5 MB** ✓
- [x] `msd.gif` → **1.7 MB** ✓
- [x] Todos abaixo de 3 MB (compatíveis com GitHub Pages)

---

## Etapa 2 — Páginas de documentação (Markdown) ✅

### 2.1 Estrutura de diretórios

- [x] `website/docs/guide/viz/` criado
- [x] `website/versioned_docs/version-0.2.3/guide/viz/` sincronizado

### 2.2 Página: Overview (`guide/viz/overview.md`)

- [x] Arquivo criado (`id: viz-overview`)
- [x] GIF hero do CartPole no topo
- [x] Diagrama ASCII da hierarquia `SimulatorBase → SimViewBase → CartPoleView`
- [x] Tabela comparativa: código standalone (~470 linhas) vs `CartPoleView().run()` (1 linha)
- [x] Seção de dependências com `pip install synapsys[viz]`
- [x] Tabela de simuladores disponíveis (CartPoleView / PendulumView / MSD)
- [x] Links para próximos passos

### 2.3 Página: Guia completo (`guide/viz/simview.md`)

- [x] Arquivo criado (`id: simview`)
- [x] GIF do CartPoleView embutido
- [x] GIF do PendulumView embutido
- [x] GIF do MassSpringDamperView embutido
- [x] Tabelas de parâmetros físicos para cada simulador
- [x] Seção: Anatomia da janela (diagrama ASCII anotado)
- [x] Seção: Controles de teclado (A/D/R/Space/Q/Esc/1/2/3)
- [x] Seção: Parâmetros físicos customizados (exemplos para os 3)
- [x] Seção: Gráficos de telemetria (tabs por simulador)
- [x] Seção: Perturbações (faixas e padrões por simulador)
- [x] Link para `api/viz#dark` (paleta de cores)

### 2.4 Página: Controlador customizado (`guide/viz/custom-controller.md`)

- [x] Arquivo criado (`id: custom-controller`)
- [x] Assinatura esperada do controller
- [x] Exemplo 1 — LQR projetado manualmente
- [x] Exemplo 2 — PID (`PIDController`)
- [x] Exemplo 3 — Rede neural (PyTorch)
- [x] Exemplo 4 — Agente RL (Stable-Baselines3)
- [x] Exemplo 5 — Neural-LQR residual
- [x] Seção: Thread-safety (modelos lentos com `queue.Queue`)
- [x] Seção: Verificar controlador antes de rodar

### 2.5 Página: API Reference (`api/viz.md`)

- [x] Arquivo criado (`id: viz`)
- [x] `SimViewBase` — tabela de 10 atributos de classe configuráveis
- [x] `SimViewBase` — tabela de hooks (`_lqr_u`, `_pert_vector`, `_build_extra_controls`, `_on_reset`)
- [x] `run()` — documentado com exemplos
- [x] `CartPoleView` — parâmetros, estado, LQR, perturbação
- [x] `PendulumView` — parâmetros, estado, polo instável, perturbação
- [x] `MassSpringDamperView` — parâmetros, estado, feed-forward, setpoints
- [x] `Dark` — tabela completa de tokens (fundos, texto, sinais, objetos 3D)
- [x] `mpl_theme()` — descrição e exemplo

---

## Etapa 3 — Componente React: Grid de simuladores ✅

### 3.1 Componente `SimulatorsShowcase.tsx`

- [x] Criado `website/src/components/SimulatorsShowcase/index.tsx`
- [x] Array `SIMULATORS` com cartpole / pendulum / msd
- [x] Layout grid 3 colunas (responsivo 3→2→1 via CSS)
- [x] Cards com: GIF, nome, estado, descrição, código 1 linha, link Docs
- [x] CSS adicionado em `website/src/css/custom.css`
- [x] `i18n/pt/code.json` atualizado com 12 novas entradas (`home.sims.*`)

### 3.2 Integração na homepage

- [x] `SimulatorsShowcase` importado em `website/src/pages/index.tsx`
- [x] `synapsys.viz` adicionado ao array `MODULES` (status: Functional)
- [x] Seção posicionada entre AI showcase e Blog
- [ ] Testar responsividade em 768px (mobile) — **pendente verificação visual**

---

## Etapa 4 — Atualizações em arquivos existentes ✅

### 4.1 Sidebar (`website/sidebars.ts`)

- [x] Categoria `Visualization` adicionada em User Guide:
  - `guide/viz/viz-overview`
  - `guide/viz/simview`
  - `guide/viz/custom-controller`
- [x] `api/viz` adicionado em API Reference
- [x] `versioned_sidebars/version-0.2.3-sidebars.json` atualizado

### 4.2 Homepage — tabela de módulos

- [x] `synapsys.viz` adicionado ao array `MODULES` em `index.tsx`

### 4.3 Intro (`website/docs/intro.md`)

- [x] Menção a `synapsys.viz.simview` adicionada
- [x] Linha na tabela de status do módulo

### 4.4 Roadmap (`website/docs/roadmap.md`)

- [x] Seção `v0.2.x ✅ — 3D Visualization` adicionada

---

## Etapa 5 — Novos simuladores futuros 🔲

> Cada simulador segue o padrão: criar em `synapsys/simulators/`, criar view em
> `synapsys/viz/simview/`, gravar GIF, adicionar à grid.

- [ ] Double Pendulum — `DoublePendulumView`
- [ ] Acrobot — `AcrobotView`
- [ ] Quadrotor MIMO — `QuadrotorView` (base: `examples/advanced/06c_unified_ui.py`)
- [ ] Ball and Beam — `BallBeamView`

---

## Checklist de revisão final

- [x] Sidebar mostra categoria **Visualization** no menu lateral ✓
- [x] Todos os GIFs carregam (1.5–1.7 MB, caminhos `/img/simview/` absolutos)
- [x] Nenhum GIF ultrapassa 3 MB
- [x] `api/viz.md` tem todas as classes documentadas
- [x] `i18n/pt/code.json` atualizado
- [x] Links internos verificados — sem links quebrados (`../../api/viz`, `../../api/viz#dark`)
- [x] Grid de simuladores: CSS 3→2col (996px) →1col (640px) ✓
- [x] Snippets corrigidos — `PIDController`→`PID`, `.update()`→`.compute()` (docs + versioned)

---

## Scripts criados

| Script | Função |
|---|---|
| `scripts/record_simview_gifs.sh` | Grava os 3 GIFs via xprop + ffmpeg x11grab |
| `scripts/optimize_gifs.sh` | Re-otimiza GIFs raw com configurações agressivas |
| `scripts/inject_gifs_into_docs.sh` | Substitui placeholders `:::info GIF em breve:::` pelos GIFs reais |
