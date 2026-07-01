+++
title = "Overview"
date = 2026-07-01
+++

**rocPAI-Forge** is dedicated to forging **Physical AI** on **AMD ROCm**. We organize our work as a closed **simulation ↔ real-world** loop, with every stage running on the ROCm acceleration stack.

## Solution Architecture

{{< mermaid >}}
flowchart TB
    subgraph REAL["Real World"]
        RR["Real robots / arms / mobile platforms"]
        SEN["Sensor data capture"]
    end

    subgraph SIM["Simulation"]
        ENG["Sim engines<br/>MuJoCo / Genesis, etc."]
        TWIN["Digital twins / scenes"]
    end

    subgraph LEARN["Learning"]
        RL["Reinforcement Learning<br/>locomotion / manipulation"]
        WM["World Models"]
        VLA["VLA models<br/>Vision-Language-Action"]
    end

    ASSET["3D assets & scene reconstruction<br/>meshes / environments / twins"]

    SEN -- "Real2Sim: reconstruct dynamics/scenes" --> ASSET
    ASSET --> TWIN
    TWIN --> ENG

    ENG --> RL
    ENG --> WM
    ENG --> VLA
    RL --> POLICY["Policies / models"]
    WM --> POLICY
    VLA --> POLICY

    ENG -. "Sim2Sim: cross-simulator validation/transfer" .-> ENG

    POLICY -- "Sim2Real: deploy" --> INF["Real-robot inference<br/>low-latency ROCm deploy"]
    INF --> RR
    RR --> SEN

    ROCM["AMD ROCm acceleration (train / sim / inference)"]
    ROCM --- SIM
    ROCM --- LEARN
    ROCM --- INF
{{< /mermaid >}}

## Focus Areas

| Area | What We Explore |
| --- | --- |
| **Sim2Real** | Closing the gap between simulation and real robots — domain randomization, calibration, and deployment |
| **Sim2Sim** | Cross-simulator validation and transfer (e.g. MuJoCo ↔ Genesis, etc.) for robust policies |
| **Real2Sim** | Reconstructing scenes and dynamics from real data to improve simulation fidelity |
| **3D Assets & Scene Reconstruction** | Meshes, environments, and digital twins for robotics and RL |
| **Reinforcement Learning** | Locomotion, manipulation, and task-specific RL on ROCm-accelerated stacks |
| **World Models** | Predictive models of environment dynamics for planning and control |
| **VLA Models** | Vision–Language–Action models for generalist robot policies |
| **Real Robot Inference** | Low-latency deployment on manipulators and mobile platforms with ROCm |

## Principles

- **Open by default** — code, configs, and learnings shared with the community
- **ROCm-first** — optimize and validate on AMD hardware and software stack
- **End-to-end** — from data and sim to train, eval, and real-world inference
- **Evidence over hype** — reproducible benchmarks, clear contracts, and honest trade-offs
