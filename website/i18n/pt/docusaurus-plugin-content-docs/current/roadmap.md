---
id: roadmap
title: Roadmap
sidebar_position: 99
---

# Roadmap

## Estado atual — v0.2.0

A biblioteca está completa e testada (184 testes, Python 3.10–3.12, cobertura 90 %).

| Módulo | Status |
|--------|--------|
| `synapsys.core` — TransferFunction, StateSpace, TransferFunctionMatrix (contínuo + discreto) | Concluído |
| `synapsys.algorithms` — PID (anti-windup), LQR (Q/R validados) | Concluído |
| `synapsys.agents` — PlantAgent, ControllerAgent, FIPA ACL, SyncEngine | Concluído |
| `synapsys.transport` — SharedMemory (zero-copy), ZMQ (PUB/SUB, REQ/REP) | Concluído |
| `synapsys.api` — tf(), ss(), c2d(), step(), bode(), feedback() (SISO + MIMO) | Concluído |
| `synapsys.hw` — Interface definida, sem implementações concretas | Pendente |

---

## v0.1.0 ✅ — Fundação

- LTI SISO (`TransferFunction`, `StateSpace`), PID, LQR, multi-agente, memória compartilhada, ZMQ, abstração de hardware.

## v0.2.0 ✅ — MIMO

- `TransferFunctionMatrix` — matriz de funções de transferência MIMO com álgebra de operadores, `to_state_space()`, polos/zeros/estabilidade.
- `feedback()` MIMO — malha fechada em espaço de estados para plantas `StateSpace` e `TransferFunctionMatrix`.
- Zeros de transmissão via matriz de Rosenbrock.
- Validação de semi-definição positiva de Q no `lqr()`.
- Anotações de tipo covariantes no `LTIModel` para mypy/pyright.

---

## v0.3 — Análise avançada

- [ ] **Atraso de transporte** — aproximação de Pade `pade(T, n)`
- [ ] **Margem de fase e ganho** — `margin(G)`
- [ ] **Root locus** — `rlocus(G)`
- [ ] **Alocação de polos** — `place(A, B, poles)`
- [ ] **LQI** — LQR com ação integral
- [ ] **Observadores** — filtro de Kalman e Luenberger

---

## v0.4 — Controle avançado

- [ ] **MPC** — Model Predictive Control com restrições
- [ ] **Controle adaptativo** — MRAC para plantas com parâmetros variantes
- [ ] **Reconfiguração em tempo real** — troca de lei sem parar a simulação

---

## v0.4 — Infraestrutura distribuída

- [ ] **Semáforos OS** — proteger `SharedMemoryTransport` em multi-process
- [ ] **Barreira lock-step entre processos** — `multiprocessing.Barrier`
- [ ] **Protocolo de clock distribuído** — coordenar agentes em máquinas diferentes
- [ ] **Tolerância a falhas** — ZOH quando o par desconecta

---

## v0.5 — Hardware

- [ ] **Serial/UART** — ESP32, STM32
- [ ] **OPC-UA** — PLCs e sistemas SCADA
- [ ] **FPGA/FPAA** — co-simulação analógico-digital
- [ ] **ROS 2 bridge** — integração com robótica

---

## v1.0 — Interface gráfica

- [ ] **JSON netlist parser** — diagrama de blocos via JSON/YAML
- [ ] **REST API** — FastAPI expondo o motor de simulação
- [ ] **Editor visual web** — React + React Flow drag-and-drop
- [ ] **Scope em tempo real** — WebSocket para streaming no browser

---

## Ideias de longo prazo

- **Antifragilidade** — algoritmos que melhoram sob perturbações
- **Digital twins** — sincronização com planta física
- **Compilação para C** — exportar lei de controle para embarcado
- **Integração com Julia** — solvers de EDOs de alta performance
