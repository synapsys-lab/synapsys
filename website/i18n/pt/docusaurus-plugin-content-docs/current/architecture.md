---
id: architecture
title: Arquitetura
sidebar_position: 3
---

# Arquitetura

O Synapsys é construído em **seis camadas**. Cada camada tem uma única responsabilidade e depende apenas das camadas abaixo. Isso significa que você pode usar o núcleo matemático isoladamente sem tocar na infraestrutura de agentes, ou trocar o transporte sem alterar nenhuma lógica de controle.

## Diagrama de camadas

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart TB
    subgraph UserAPI["1. API Pública — synapsys.api"]
        direction LR
        UI1["matlab_compat.py\ntf(), ss(), c2d(), step(), bode()"]
        UI2["agent_api.py\nPlantAgent(), ControllerAgent()"]
    end

    subgraph CoreMath["2. Núcleo Matemático — synapsys.core"]
        direction TB
        M1["LTIModel (ABC)"]
        M2["StateSpace"]
        M3["TransferFunction"]
        M5["TransferFunctionMatrix"]
        M4["NumPy / SciPy solvers"]
        M1 --> M2
        M1 --> M3
        M1 --> M5
        M2 --> M4
        M3 --> M4
        M5 --> M3
    end

    subgraph ControlLogic["3. Algoritmos — synapsys.algorithms"]
        direction LR
        C1["Clássico: PID, LQR"]
        C2["Avançado: MPC, Adaptativo (planejado)"]
        C3["Reconfiguração em tempo real (planejado)"]
    end

    subgraph MAS["4. Sistema Multiagente — synapsys.agents"]
        direction TB
        A1["FIPA ACL Messages\nINFORM, REQUEST, ..."]
        A2["SyncEngine\nWALL_CLOCK / LOCK_STEP"]
        A3["BaseAgent -> PlantAgent, ControllerAgent"]
    end

    subgraph Transport["5. Transporte — synapsys.transport"]
        direction TB
        T1{"TransportStrategy (ABC)"}
        T2["SharedMemoryTransport\nLatência zero-copy"]
        T3["ZMQTransport / ZMQReqRepTransport\nRede TCP"]
        T1 --> T2
        T1 --> T3
    end

    subgraph Hardware["6. Hardware — synapsys.hw"]
        direction LR
        H1["HardwareInterface (ABC)"]
        H2["FPGA / FPAA (planejado)"]
        H3["Microcontroladores (planejado)"]
    end

    UserAPI ==> CoreMath
    UserAPI ==> MAS
    CoreMath ==> ControlLogic
    MAS ==> Transport
    Transport -.-> Hardware
    ControlLogic -.-> MAS
```

## Decisões de projeto

### Separação API / Motor matemático

A camada `synapsys.api` é apenas um wrapper de conveniência. Toda a matemática vive em `synapsys.core`. Isso permite que a API evolua sem tocar no núcleo numérico.

### Operator overloading nas classes LTI

`G1 * G2` (série), `G1 + G2` (paralelo) e `G.feedback()` permitem compor sistemas com álgebra de blocos natural:

```python
T = (C * G).feedback()   # malha fechada: C em série com G
```

`TransferFunctionMatrix` estende essa álgebra para plantas MIMO: `*` realiza multiplicação matricial (série) e `+` é elemento a elemento (paralelo). Simulação e análise delegam para uma realização mínima em `StateSpace` construída de forma lazy por `to_state_space()`.

### Padrão Strategy no transporte

`PlantAgent` e `ControllerAgent` não sabem **como** os dados são enviados. Eles chamam `transport.write()` e `transport.read()`. A implementação concreta é injetada na construção — sem mudar lógica de controle.

### Ciclo de vida do transporte

O transporte é **gerenciado pelo chamador**, não pelo agente. O agente nunca chama `transport.close()`. Isso evita double-free quando múltiplos agentes compartilham visões do mesmo bloco de memória.

### Contínuo vs Discreto

`StateSpace(A, B, C, D, dt=0)` é contínuo. `dt > 0` é discreto. O mesmo objeto suporta ambos:

- `is_stable()` usa `Re(poles) < 0` para contínuo e `|poles| < 1` para discreto
- `step()` delega para `scipy.signal.step` ou `scipy.signal.dstep` automaticamente
- `evolve(x, u)` executa `x(k+1) = Ax + Bu` passo a passo para simulação em tempo real
