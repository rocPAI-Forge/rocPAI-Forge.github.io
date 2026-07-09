+++
title = "当机械臂自己发明了一种抓法：OpenArm 抓取强化学习实践"
date = 2026-07-06
author = "rocPAI-Lab: Alex He, David Li, Andy Luo"
tags = ["AMD ROCm", "PhysicalAI", "RL", "OpenArm", "UniLab"]
+++


<video src="/media/openarm-rl-grasp/play_overview_web.mp4" poster="/media/openarm-rl-grasp/play_overview.jpg" autoplay loop muted playsinline style="width:100%;border-radius:.6rem;"></video>
<p style="text-align:center;color:#888;font-size:.8rem;">总览回放 / Overview replay</p>

> 📖 本文为**精简版**（~3 分钟）。想深入完整工程细节（设计决策、算法 / reward、诊断、复现命令），请移步 [**技术详解版 →**](https://github.com/alexhegit/tech-blog-pub/blob/main/PhysicalAI/openarm-rl-grasp/README-details.md)

## UniLab 与联合发布

[UniLab](https://github.com/unilabsim/UniLab) 是面向机器人强化学习的**异构训练基础设施**：
**CPU 侧并行物理仿真**（MuJoCo / Motrix）与 **GPU 侧策略学习**通过统一 runtime 与共享内存
衔接，而不是把物理、rollout 采集与学习全部绑死在 GPU 仿真路径上。任务、奖励与后端切换由
Hydra owner YAML 表达；训练入口统一为 `uv run train` / `uv run eval`，覆盖 PPO、SAC、TD3、
APPO 等算法。

我们同期联合发布了系统论文
[**UniLab: A Heterogeneous Architecture for Robot RL Beyond GPU-Dominant Paradigms**](https://arxiv.org/abs/2605.30313)
（[arXiv:2605.30313](https://arxiv.org/abs/2605.30313)）。论文的核心观点是：高效训练的关键
不在于「物理必须在 GPU 上跑」，而在于仿真吞吐、策略更新与运行时同步能否形成高效的端到端
闭环——GPU 仿真是有效路径，但**不是唯一路径**。在代表性机器人控制任务上，UniLab 在相同硬件
配置下将端到端训练效率提升 **3–10×**，同时减少对 NVIDIA CUDA 软件栈的依赖，并**原生支持
AMD ROCm**、Intel XPU 与 Apple macOS。

对 AMD 平台，ROCm 是一等公民：`make sync-rocm` 即可装好环境，策略学习走
**CUDA / MPS / ROCm / XPU** 统一加速器路径，物理仿真留在 CPU 多线程并行。本文的 OpenArm
抓取实验，正是 rocPAI-Forge 在 **Instinct MI300X / MI210 + ROCm** 上用 UniLab 落地的一条
Physical AI 实践。

- **代码**：[github.com/unilabsim/UniLab](https://github.com/unilabsim/UniLab)
- **论文**：[arXiv:2605.30313](https://arxiv.org/abs/2605.30313)
- **文档**：[UniLab-doc](https://unilabsim.github.io/UniLab-doc/)

## 概要

我们在 [UniLab](https://github.com/unilabsim/UniLab) 上用 PPO 给 **OpenArm** 的一条手臂
训练了一个抓取策略：把桌面上的 3cm 方块抓起、抬到空中目标点并稳稳保持。

最终确定性评估：**ever success 100%、final success 87.9%、掉落率 0%**。但真正有意思的
是过程里的三个瞬间。

## 三个有意思的瞬间

**1. 会"捏"的夹爪比想象中难。** 一键开合（binary）的夹爪是作弊版；换成**连续控制**后，
策略最初总在"夹住却不抬"的局部最优里打转。我们用分阶段塑形（先到方块上方→下探→闭合→
抬起）+ 一招 `terminate_on_success=false`（成功后不结束、持续"付费保持"）才让它学会完整
动作。

**2. 它学会了"托"，而不是"夹"。** 🌟 评估时发现策略**几乎从不闭合手指**（闭合度≈0），
却能 100% 抬起方块——它用两根指尖把方块**兜住托起**。一开始以为是 bug，后来才懂：对这个
高摩擦、小尺寸的方块，指尖托举靠几何兜底 + 摩擦，比精确夹紧**更鲁棒**。我们越逼它夹紧，
主目标反而越差。RL 最迷人之处：**它不解你出的题，而是解它发现的、更好解的那道题。**

![夹爪托举方块特写](/media/openarm-rl-grasp/openarm_pick_grasp_closeup.png)

**3. 一条失控的曲线，被一个超参救回。** 🌟 成功率在 ~600 iter 就封顶，但 `action std`
一路涨到 **39**。原因：动作经 tanh 饱和压缩后，把探索噪声推大几乎不改变真正执行的动作，
于是 PPO 发现了"薅熵奖励的免费午餐"——把 std 推大白拿熵奖励、reward 不掉。它对控制无害，
却让曲线难看、掩盖了"其实早已收敛"。诊断清楚后，只把 `entropy_coef` 从 `0.01` 降到
`0.003`（其它全不变），曲线立刻变干净：

| 指标 | baseline `0.01` | lowent `0.003` |
| --- | --- | --- |
| ever success | 98.8% | **100.0%** |
| final success | 86.3% | **87.9%** |
| 最终 reward | 2580 | **2800** |
| 最终 action std | 39.08 | **1.35** |

这不是"用成功率换干净曲线"，而是**净改进**。而且改动没碰 Python——只新增一个覆盖单字段的
owner 变体 YAML，体现 UniLab "配置优先、在 owner 层修正"的理念（可追溯、可对照、可回滚）。

## 三条方法论

1. **配置优先**：把想法表达成配置而非代码，让对照实验廉价、可追溯。
2. **在最接近风险处验证**：成功率没退化 ≠ 万事大吉，盯住每一条曲线。
3. **让证据说话**：反直觉现象往往是策略给的证据，先理解再判断。

> 训练规模：4096 并行环境 × 24 步/iter × 1500 iter ≈ **1.47 亿步**仿真，单次约 1h49m
> （共享 GPU，~23k steps/s）。想复现、看完整 reward/曲线分析 → [技术详解版](README-details.md)。
> 相关：UniLab PR [#640](https://github.com/unilabsim/UniLab/pull/640)。

> 📖 想了解更多？完整工程细节见 [技术详解版](https://github.com/alexhegit/tech-blog-pub/blob/main/PhysicalAI/openarm-rl-grasp/README-details.md)。