+++
title = "When a Robot Arm Invents Its Own Grip: An RL Practice with OpenArm"
date = 2026-07-06
author = "rocPAI-Lab: Alex He, David Li, Andy Luo"
tags = ["AMD ROCm", "PhysicalAI", "RL", "OpenArm", "UniLab"]
+++


<video src="/media/openarm-rl-grasp/play_overview_web.mp4" poster="/media/openarm-rl-grasp/play_overview.jpg" autoplay loop muted playsinline style="width:100%;border-radius:.6rem;"></video>
<p style="text-align:center;color:#888;font-size:.8rem;">总览回放 / Overview replay</p>

> 📖 This is the **concise version** (~3 min). For the full engineering details (design decisions, algorithm / reward, diagnostics, reproduce commands), read the [**deep-dive →**](https://github.com/alexhegit/tech-blog-pub/blob/main/PhysicalAI/openarm-rl-grasp/README-details.md)

## UniLab & Joint Release

[UniLab](https://github.com/unilabsim/UniLab) is a **heterogeneous robot-RL training
infrastructure**: **CPU-parallel physics simulation** (MuJoCo / Motrix) and **GPU policy
learning** are coupled through a unified runtime and shared memory — instead of pinning
physics, rollout collection, and learning on a single GPU-resident simulation path. Tasks,
rewards, and backend selection are expressed as Hydra owner YAMLs; training goes through a
unified `uv run train` / `uv run eval` CLI covering PPO, SAC, TD3, APPO, and more.

We are jointly releasing this practice alongside our system paper
[**UniLab: A Heterogeneous Architecture for Robot RL Beyond GPU-Dominant Paradigms**](https://arxiv.org/abs/2605.30313)
([arXiv:2605.30313](https://arxiv.org/abs/2605.30313)). The paper argues that efficient
training is not about *which processor runs physics*, but whether simulation throughput,
policy updates, and runtime synchronization form an efficient end-to-end loop — GPU
simulation is an effective path, but **not a necessary one**. On representative robot-control
tasks, UniLab improves end-to-end training efficiency by **3–10×** under the same hardware,
reduces dependence on the NVIDIA CUDA stack, and **natively supports AMD ROCm**, Intel XPU,
and Apple macOS.

On AMD platforms, ROCm is first-class: `make sync-rocm` sets up the environment; policy
learning runs on **CUDA / MPS / ROCm / XPU** accelerators while physics stays on
CPU-multithreaded simulation. This OpenArm grasp experiment is a rocPAI-Forge Physical AI
practice built on UniLab atop **Instinct MI300X / MI210 + ROCm**.

- **Code:** [github.com/unilabsim/UniLab](https://github.com/unilabsim/UniLab)
- **Paper:** [arXiv:2605.30313](https://arxiv.org/abs/2605.30313)
- **Docs:** [UniLab-doc](https://unilabsim.github.io/UniLab-doc/)

## Overview

On [UniLab](https://github.com/unilabsim/UniLab) we trained a PPO grasp policy for a single
**OpenArm**: pick a 3 cm cube off the table, lift it to an in-air goal, and hold it.

Final deterministic eval: **ever-success 100%, final-success 87.9%, drop rate 0%**.
But the interesting part is three moments along the way.

## Three interesting moments

**1. A gripper that actually closes is hard.** A binary snap-close gripper is easy
mode; switching to **continuous** control, the policy kept getting stuck in a
"grab but never lift" local optimum. Staged shaping (open-above → descend → close →
lift) plus one trick — `terminate_on_success=false` (don't end on success, keep
*paying it to hold*) — finally taught it the full motion.

**2. It learned to cradle, not clamp.** 🌟 At eval the policy **almost never closes
its fingers** (closure ≈ 0), yet lifts the cube 100% of the time — it *cradles* the
cube between two fingertips. We assumed a bug; then it clicked: for this
high-friction, small cube, a fingertip cradle leans on geometry + friction and is
**more robust** than precise clamping. The harder we forced clamping, the worse the
primary objective got. RL's most fascinating trait: **it doesn't solve the problem
you posed — it solves the easier, better one it discovered.**

![Gripper cradling the cube](/media/openarm-rl-grasp/openarm_pick_grasp_closeup.png)

**3. One wild curve, saved by one hyperparameter.** 🌟 Success plateaued around
iter ~600, but `action std` climbed to **39**. Why: after tanh saturation,
inflating the exploration noise barely changes the executed action, so PPO found a
"free entropy lunch" — inflate std, collect entropy bonus, reward doesn't drop.
Harmless to control, but it makes curves ugly and hides that the policy converged
long ago. The fix: lower `entropy_coef` from `0.01` to `0.003` (nothing else
changed):

| Metric | baseline `0.01` | lowent `0.003` |
| --- | --- | --- |
| ever success | 98.8% | **100.0%** |
| final success | 86.3% | **87.9%** |
| final reward | 2580 | **2800** |
| final action std | 39.08 | **1.35** |

Not a "trade success for clean curves" deal — a **net win**. And the change touched
no Python: just a new owner-variant YAML overriding a single field — UniLab's
"config-first, fix-at-owner-layer" principle (traceable, comparable, revertible).

## Three takeaways

1. **Config first**: express ideas as config, not code — cheap, traceable experiments.
2. **Validate near the risk**: "success didn't drop" isn't all-clear — watch every curve.
3. **Let evidence speak**: a counter-intuitive result is often evidence — understand before you judge.

> Training scale: 4096 parallel envs × 24 steps/iter × 1500 iter ≈ **147.5M** sim
> steps, ~1h49m per run (shared GPU, ~23k steps/s). To reproduce and see the full
> reward/curve analysis → [deep-dive](README-details.md).
> See also: UniLab PR [#640](https://github.com/unilabsim/UniLab/pull/640).

> 📖 Want more? Full engineering details in the [deep-dive](https://github.com/alexhegit/tech-blog-pub/blob/main/PhysicalAI/openarm-rl-grasp/README-details.md).