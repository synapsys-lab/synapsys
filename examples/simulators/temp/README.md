# Exemplos — SimView (módulo da biblioteca)

Versões reescritas dos exemplos usando as views prontas da biblioteca.
Cada arquivo mostra várias variações; descomente o bloco desejado.

| Arquivo | View | Destaque |
|---------|------|----------|
| `01_msd_view.py` | `MassSpringDamperView` | LQR auto, PD, setpoints, parâmetros, x0 |
| `02_pendulum_view.py` | `PendulumView` | LQR auto, swing-up, queda livre |
| `03_cartpole_view.py` | `CartPoleView` | LQR auto, PD, params, instabilidade |
| `04_custom_controllers.py` | `CartPoleView` | PID com estado, rede neural, feedback lin. |
| `05_msd_setpoints.py` | `MassSpringDamperView` | Setpoints customizados, LQR externo |

## Como executar

```bash
# da raiz do projeto
python examples/simulators/temp/01_msd_view.py
```

## Teclas de atalho (em todas as views)

| Tecla | Ação |
|-------|------|
| `Space` | Pausar / retomar |
| `R` | Reset |
| `A` / `D` | Perturbação esquerda / direita |
| `Q` | Fechar |
| `1` / `2` / `3` | Setpoints (MSD) |
