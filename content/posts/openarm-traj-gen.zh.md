+++
title = "给 VLA 喂饭：在 AMD ROCm 上用 OpenArm 生成抓取专家轨迹"
date = 2026-06-30
author = "rocPAI-Lab: Alex He, David Li, Andy Luo"
tags = ["ROCm", "VLA", "OpenArm"]
+++


> 📖 本文为**精简版**（~3 分钟）。想深入完整工程细节（设计决策、算法 / reward、诊断、复现命令），请移步 [**技术详解版 →**](https://github.com/alexhegit/tech-blog-pub/blob/main/PhysicalAI/openarm-traj-gen-for-vla/README-details.md)

## 概要

VLA（Vision-Language-Action）模型很能吃数据，而真机采集又贵又慢。我们换个思路：在
**AMD Instinct MI300X + ROCm** 平台上，用 [`openarm_mp_labs`](https://github.com/alexhegit/openarm_mp_labs)
把 OpenArm 的「抓-放」动作变成一台 **sim 内的专家轨迹数据引擎**——给定物体和抓取位姿，自动
解出一条平滑、物理可行、亚毫米精度的示范轨迹，可批量复现。

两个关键结果：

1. 用 Cartesian 路点 + mink IK，把抓取拆成 `approach→descend→close→lift→transport→place→retreat→home`，
   末端 IK 误差 **0.4–0.9 mm**，cube/ginger 物理仿真抬升 **112–120 mm**。
2. 抓取位姿既能是标定 top-down，也能直接吃 **GraspGenX 的 6-DOF 抓取**（在 AMD ROCm 上、
   为 OpenArm 夹爪生成）——多物体 × 多抓取 = 给 VLA 的多样化示范。

<video src="/media/openarm-traj-gen/cube_pickplace_web.mp4" poster="/media/openarm-traj-gen/cube_pickplace.jpg" autoplay loop muted playsinline style="width:100%;border-radius:.6rem;"></video>
<p style="text-align:center;color:#888;font-size:.8rem;">cube 抓-放回放：从简单方块起步</p>

## 实践环境

- **硬件**：AMD Instinct **MI300X**
- **平台**：**ROCm 7.2**——容器内实测 `torch 2.7.1+rocm7.2`、`hip 7.2.26015`
- **主项目**：[`openarm_mp_labs`](https://github.com/alexhegit/openarm_mp_labs)（轨迹生成 + MuJoCo 回放）
- **依赖**：[`openarm_control`](https://github.com/enactic/openarm_control)（IK）、
  [`openarm_mujoco`](https://github.com/enactic/openarm_mujoco)（模型）、
  [`GraspGenX`](https://github.com/NVlabs/GraspGenX)（6-DOF 抓取）、
  [`Scan2Sim`](https://github.com/alexhegit/Scan2Sim)（真实扫描件转 sim 资产）

> 轨迹生成 + MuJoCo 是 CPU 计算；GPU/ROCm 的价值在 **GraspGenX 抓取合成**与下游 **VLA 训练**。

## 实践过程概要

- **轨迹生成是数据引擎**：每个阶段在起止位姿间插值、逐帧解 mink IK，阶段末加一步收敛把
  误差压到最小；以"两指尖中点 + 标定 TCP 偏移"为目标，适配 OpenArm 弯曲指尖。
- **从方块到真实物体**：换上 Scan2Sim 转换的 ginger，抓取改用 GraspGenX 的 50 个排序 6-DOF
  抓取（置信度 0.97→0.77），`full` 模式直接采用斜向朝向。
- **让抓取稳**：先 settle 再取坐标、标定夹合角、运动学吸附 + 闭环重 IK，压住位控漂移。
- **AMD ROCm 生态**：靠我提的 3 个 GraspGenX PR——
  [#1](https://github.com/NVlabs/GraspGenX/pull/1) 加 ROCm 支持（能在 AMD 上推理）、
  [#3](https://github.com/NVlabs/GraspGenX/pull/3) 加 OpenArm 夹爪（能为 OpenArm 出抓取）、
  [#4](https://github.com/NVlabs/GraspGenX/pull/4) 网格可视化 demo。

关键命令（完整流程见项目仓库）：

```bash
uv run openarm-mp-demo --generate-only                       # 只生成轨迹(IK 误差)
uv run openarm-mp-demo --simulate-only                       # 物理校验(抬升判定)
MUJOCO_GL=egl uv run openarm-mp-demo --object ginger \
  --grasp-mode full --record output/ginger_full.mp4         # GraspGenX 6-DOF + 录制
```

<video src="/media/openarm-traj-gen/ginger_full_web.mp4" poster="/media/openarm-traj-gen/ginger_full.jpg" autoplay loop muted playsinline style="width:100%;border-radius:.6rem;"></video>
<p style="text-align:center;color:#888;font-size:.8rem;">ginger 6-DOF 抓取-放置回放：升级到真实扫描物体</p>

## 实践结果与结论

| 场景 | 抓取来源 | 仿真抬升 |
| --- | --- | --- |
| cube | 标定 top-down | **112.0 mm** |
| ginger | GraspGenX topdown | **120.4 mm** |
| ginger | GraspGenX full（6-DOF，conf 0.97） | **112.4 mm** |

三条带得走的经验：

1. **轨迹生成被低估**：有了好抓取位姿，确定性 IK + 物理校验就能稳定产出高质量专家轨迹，
   成本远低于真机。
2. **多样性靠两个旋钮**：GraspGenX（夹爪）× Scan2Sim（物体），把数据做"广"。
3. **AMD ROCm 能扛 Physical AI**：从 GraspGenX 推理到 MuJoCo 数据生成，整条链路在 MI300X +
   ROCm 上跑得通。

## 项目引用 / 动手复现

- 主项目：**[openarm_mp_labs](https://github.com/alexhegit/openarm_mp_labs)**
- 抓取生成：**[GraspGenX](https://github.com/NVlabs/GraspGenX)**（PR [#1](https://github.com/NVlabs/GraspGenX/pull/1) / [#3](https://github.com/NVlabs/GraspGenX/pull/3) / [#4](https://github.com/NVlabs/GraspGenX/pull/4)）
- 资产转换：**[Scan2Sim](https://github.com/alexhegit/Scan2Sim)**

按上面的项目就能复现这套"在 AMD ROCm 上为 VLA 造专家轨迹"的实践。

> 📖 想了解更多？完整工程细节见 [技术详解版](https://github.com/alexhegit/tech-blog-pub/blob/main/PhysicalAI/openarm-traj-gen-for-vla/README-details.md)。