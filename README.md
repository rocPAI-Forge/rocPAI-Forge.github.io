# rocPAI-Forge.github.io

组织主站（Hugo + PaperMod），发布于 <https://rocpai-forge.github.io/>。

板块：技术全景 Overview（含功能架构图）、博客 Blog、路线规划 Roadmap。中英双语。

## 本地预览

需要 Hugo **extended v0.148.2**（与 CI 一致，务必对齐版本以免主题不兼容）：

```bash
hugo server -D
# 打开 http://localhost:1313/
```

若本机没有对应版本，可下载单二进制：

```bash
HV=0.148.2
wget https://github.com/gohugoio/hugo/releases/download/v${HV}/hugo_extended_${HV}_linux-amd64.tar.gz
tar xzf hugo_extended_${HV}_linux-amd64.tar.gz hugo
./hugo server -D
```

## 写文章

在 `content/posts/` 放 Markdown：

- 中文（默认语言）：`my-post.md`
- 英文：`my-post.en.md`

front matter 示例：

```toml
+++
title = "标题"
date = 2026-07-01
author = "Your Name"
tags = ["AMD ROCm", "PhysicalAI"]
+++
```

图片/视频放 `static/media/`，正文用 `/media/xxx.mp4` 引用。

## 架构图 / 图表

用 `mermaid` shortcode（见 `layouts/shortcodes/mermaid.html`）：

```
{{</* mermaid */>}}
flowchart LR
  A --> B
{{</* /mermaid */>}}
```

## 发布

推到 `main` 分支后，`.github/workflows/deploy.yml` 会用固定版本 Hugo 构建并发布到 GitHub Pages。
首次需在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。

## 版本约定（重要）

Hugo 与 PaperMod 主题版本耦合。当前锁定：

- Hugo extended **0.148.2**（`.github/workflows/deploy.yml` 中的 `HUGO_VERSION`）
- PaperMod：vendored 在 `themes/PaperMod/`（master，2026-07 验证可用）

升级任一方前请本地验证构建，避免线上白屏。
