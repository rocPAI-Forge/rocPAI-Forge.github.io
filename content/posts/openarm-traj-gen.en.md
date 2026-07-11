+++
title = "Feeding the VLA: Generating Expert Grasp Trajectories for OpenArm on AMD ROCm"
date = 2026-06-30
author = "rocPAI-Lab: Alex He, David Li, Andy Luo"
tags = ["ROCm", "VLA", "OpenArm"]
+++


> 📖 This is the **concise version** (~3 min). For the full engineering details (design decisions, algorithm / reward, diagnostics, reproduce commands), read the [**deep-dive →**](https://github.com/rocPAI-Forge/tech-blog-pub/blob/main/PhysicalAI/openarm-traj-gen-for-vla/README-details.md)

## Overview

VLA (Vision-Language-Action) models are data-hungry, and real-robot collection is slow
and expensive. So we flip it: on an **AMD Instinct MI300X + ROCm** box, we turn OpenArm's
pick-and-place into an in-sim **expert trajectory data engine** with
[`openarm_mp_labs`](https://github.com/alexhegit/openarm_mp_labs) — given an object and a
grasp pose, auto-solve a smooth, physically feasible, sub-mm-accurate demonstration
trajectory that's reproducible at scale.

Two key results:

1. With Cartesian waypoints + mink IK, a grasp splits into
   `approach→descend→close→lift→transport→place→retreat→home`, with **0.4–0.9 mm** IK
   error and **112–120 mm** simulated lifts for cube/ginger.
2. The grasp pose can be calibrated top-down *or* a **6-DOF grasp from GraspGenX** (run
   on AMD ROCm, generated for the OpenArm gripper) — many objects × many grasps = diverse
   demonstrations for a VLA.

<video src="/media/openarm-traj-gen/cube_pickplace_web.mp4" poster="/media/openarm-traj-gen/cube_pickplace.jpg" autoplay loop muted playsinline style="width:100%;border-radius:.6rem;"></video>
<p style="text-align:center;color:#888;font-size:.8rem;">cube pick-and-place replay: starting from a simple cube</p>

## Environment

- **Hardware**: AMD Instinct **MI300X**
- **Platform**: **ROCm 7.2** — measured `torch 2.7.1+rocm7.2`, `hip 7.2.26015`
- **Main project**: [`openarm_mp_labs`](https://github.com/alexhegit/openarm_mp_labs) (trajectory gen + MuJoCo replay)
- **Dependencies**: [`openarm_control`](https://github.com/enactic/openarm_control) (IK),
  [`openarm_mujoco`](https://github.com/enactic/openarm_mujoco) (model),
  [`GraspGenX`](https://github.com/NVlabs/GraspGenX) (6-DOF grasps),
  [`Scan2Sim`](https://github.com/alexhegit/Scan2Sim) (real scans → sim assets)

> Trajectory gen + MuJoCo is CPU; the GPU/ROCm value is in **GraspGenX grasp synthesis**
> and downstream **VLA training**.

## What we did

- **Trajectory gen is the data engine**: each phase lerps between poses, solves mink IK
  per frame, and appends a convergence step to minimize error; targets are the
  "fingertip midpoint + calibrated TCP offset" to fit OpenArm's curved fingertips.
- **From cube to real object**: swap in a Scan2Sim-converted ginger and GraspGenX's 50
  ranked 6-DOF grasps (confidence 0.97→0.77); `full` mode uses the diagonal orientation.
- **Making it stable**: settle-then-read coordinates, a calibrated grip angle, kinematic
  attach + closed-loop re-IK to suppress position-control drift.
- **AMD ROCm ecosystem**: enabled by 3 GraspGenX PRs of mine —
  [#1](https://github.com/NVlabs/GraspGenX/pull/1) adds ROCm support (inference on AMD),
  [#3](https://github.com/NVlabs/GraspGenX/pull/3) adds the OpenArm gripper (grasps for OpenArm),
  [#4](https://github.com/NVlabs/GraspGenX/pull/4) a mesh-visualization demo.

Key commands (full flow in the project repo):

```bash
uv run openarm-mp-demo --generate-only                       # trajectory only (IK error)
uv run openarm-mp-demo --simulate-only                       # physics check (lift test)
MUJOCO_GL=egl uv run openarm-mp-demo --object ginger \
  --grasp-mode full --record output/ginger_full.mp4         # GraspGenX 6-DOF + record
```

<video src="/media/openarm-traj-gen/ginger_full_web.mp4" poster="/media/openarm-traj-gen/ginger_full.jpg" autoplay loop muted playsinline style="width:100%;border-radius:.6rem;"></video>
<p style="text-align:center;color:#888;font-size:.8rem;">ginger 6-DOF pick-and-place replay: upgrading to a real scanned object</p>

## Results & takeaways

| Scene | Grasp source | Simulated lift |
| --- | --- | --- |
| cube | calibrated top-down | **112.0 mm** |
| ginger | GraspGenX topdown | **120.4 mm** |
| ginger | GraspGenX full (6-DOF, conf 0.97) | **112.4 mm** |

Three takeaways:

1. **Trajectory generation is underrated**: given good grasp poses, deterministic IK +
   physics validation reliably yields high-quality expert trajectories far cheaper than
   real robots.
2. **Diversity has two knobs**: GraspGenX (grippers) × Scan2Sim (objects) broaden the data.
3. **AMD ROCm carries Physical AI**: from GraspGenX inference to MuJoCo data generation,
   the chain runs on MI300X + ROCm.

## References / Reproduce it

- Main project: **[openarm_mp_labs](https://github.com/alexhegit/openarm_mp_labs)**
- Grasp generation: **[GraspGenX](https://github.com/NVlabs/GraspGenX)** (PRs [#1](https://github.com/NVlabs/GraspGenX/pull/1) / [#3](https://github.com/NVlabs/GraspGenX/pull/3) / [#4](https://github.com/NVlabs/GraspGenX/pull/4))
- Asset conversion: **[Scan2Sim](https://github.com/alexhegit/Scan2Sim)**

The projects above are all you need to reproduce this "generate VLA expert trajectories on
AMD ROCm" practice hands-on.

> 📖 Want more? Full engineering details in the [deep-dive](https://github.com/rocPAI-Forge/tech-blog-pub/blob/main/PhysicalAI/openarm-traj-gen-for-vla/README-details.md).