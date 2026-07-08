+++
title = "技术全景 Overview"
date = 2026-07-01
+++

**rocPAI-Forge** 专注于在 **AMD ROCm** 上锻造物理智能（Physical AI）。我们把工作组织成一个「仿真 ↔ 真机」的闭环，所有环节都跑在 ROCm 加速底座上。

## 功能解决架构

{{< mermaid >}}
flowchart TB
    subgraph REAL["真实世界 Real World"]
        RR["真机 / 机械臂 / 移动平台"]
        SEN["传感数据 采集"]
    end

    subgraph SIM["仿真世界 Simulation"]
        ENG["仿真引擎<br/>MuJoCo / Genesis 等"]
        TWIN["数字孪生 / 场景"]
    end

    subgraph LEARN["学习与建模 Learning"]
        RL["强化学习 RL<br/>运动 / 操作"]
        WM["世界模型 World Models"]
        VLA["VLA 模型<br/>视觉-语言-动作"]
    end

    ASSET["3D 资产 & 场景重建<br/>网格 / 环境 / 数字孪生"]

    SEN -- "Real2Sim 重建动力学/场景" --> ASSET
    ASSET --> TWIN
    TWIN --> ENG

    ENG --> RL
    ENG --> WM
    ENG --> VLA
    RL --> POLICY["策略 / 模型"]
    WM --> POLICY
    VLA --> POLICY

    ENG -. "Sim2Sim 跨仿真器验证/迁移" .-> ENG

    POLICY -- "Sim2Real 部署" --> INF["真机推理<br/>低延迟 ROCm 部署"]
    INF --> RR
    RR --> SEN

    ROCM["AMD ROCm 加速底座（训练 / 仿真 / 推理）"]
    ROCM --- SIM
    ROCM --- LEARN
    ROCM --- INF
{{< /mermaid >}}

## 重点方向

| 方向 | 探索内容 |
| --- | --- |
| **Sim2Real** | 缩小仿真与真机差距——域随机化、标定与部署 |
| **Sim2Sim** | 跨仿真器验证与迁移（如 MuJoCo ↔ Genesis 等），提升策略鲁棒性 |
| **Real2Sim** | 从真实数据重建场景与动力学，提升仿真保真度 |
| **3D 资产与场景重建** | 网格、环境与数字孪生，服务机器人与强化学习 |
| **强化学习** | 在 ROCm 加速栈上的运动、操作与任务型 RL |
| **世界模型** | 环境动力学预测模型，用于规划与控制 |
| **VLA 模型** | 视觉–语言–动作模型，面向通用机器人策略 |
| **真机推理** | 机械臂与移动平台上的低延迟 ROCm 部署 |

## 原则

- **默认开源** — 代码、配置与经验向社区开放
- **ROCm 优先** — 在 AMD 软硬件栈上优化与验证
- **端到端** — 从数据与仿真到训练、评测与真机推理
- **用结果说话** — 可复现基准、清晰契约、坦诚的技术取舍
