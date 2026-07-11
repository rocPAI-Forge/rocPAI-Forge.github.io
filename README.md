# rocPAI-Forge.github.io

组织主站（Hugo + PaperMod），发布于 <https://rocpai-forge.github.io/>。中英双语。
板块：技术全景 Overview（含功能架构图）、博客 Blog、路线规划 Roadmap。

> **内容来源**：博客文章的唯一真源是 [`rocPAI-Forge/tech-blog-pub`](https://github.com/rocPAI-Forge/tech-blog-pub)，
> 本仓库的 `content/posts/` 与 `static/media/` 由脚本从 pub **单向生成**。
> **发布流程与规则（写什么、怎么发、详解版入口规则）以 pub 的 `AGENTS.md` 为准**；
> 本 README 只讲**站点构建内部**。

## 技术选型

Astro / 纯 HTML+Tailwind / Hugo+PaperMod 三方案对比后选 **Hugo + PaperMod**：内容扩展性最好
（丢一个 Markdown 即成文章，标签/分页/RSS/搜索开箱即用）、模板一致、环境便携（单二进制，无
Node 运行时）。唯一注意点：**Hugo 与主题版本强耦合，必须锁版本**（见下）。

## 目录结构

```
hugo.toml                      # baseURL、i18n(zh/en)、菜单;defaultContentLanguage=en
content/
  overview.md / overview.en.md   # 技术全景 + mermaid 架构图（手写）
  roadmap.md  / roadmap.en.md     # 路线规划（手写，当前占位）
  posts/<slug>.md(.en.md)         # ← 由 pub 生成,勿手改
static/media/<slug>/             # ← 由 pub 生成的 mp4 + jpg 海报（正文 /media/<slug>/xxx 引用）
scripts/sync_from_pub.py         # 内容生成器：tech-blog-pub → content/ + static/
layouts/shortcodes/mermaid.html  # 自定义 mermaid 渲染（绕开代码高亮器）
themes/PaperMod/                 # vendored（直接提交，非 submodule）
.github/workflows/deploy.yml     # CI: checkout pub → 生成器 → 构建 + 部署 Pages
```

> **`posts/` 与 `static/media/` 是生成产物**，会被下一次生成覆盖，不要手改。
> `overview` / `roadmap` 是本仓库手写（非生成），front matter 用 Hugo TOML `+++ ... +++`。

### i18n / 默认语言
文件名后缀：`xxx.md`(默认语言) / `xxx.en.md`(英文)；`defaultContentLanguageInSubdir=true` →
URL 带 `/zh/`、`/en/`。**默认语言为 `en`**（`hugo.toml` 的 `defaultContentLanguage="en"`），
根 `/` 静态跳转到 `/en/`；中文在 `/zh/`，右上角手动切换（纯静态,不做浏览器语言探测）。

### 架构图 / 图表
用 mermaid shortcode：`{{</* mermaid */>}} ... {{</* /mermaid */>}}`。shortcode 强制
`theme:'dark'`，flowchart 用 **TB 纵向**（横向 LR 在正文单列会被压得文字看不清）。

## 内容生成器（sync_from_pub.py）

pub → Hugo 单向转换。**为什么需要**：pub 面向 GitHub 阅读（单文件双语 + 相对 gif），Hugo
面向网站（分语言文件 + front matter + `/media` 下 mp4）——格式天然不同，中间必有一层转换。

做的事：
1. 拆 pub `README.md` 的 `## 中文` / `## English` → `posts/<slug>.md` / `<slug>.en.md`；
2. front matter 取自 pub 每篇 `meta.toml`（`slug/date/author/tags/title_zh/title_en/publish`）；
3. 正文标题上提一级（去掉 `## 中文` 外层）；
4. 媒体改写：`assets/gifs/*.gif` → 循环 `<video>`（优先用 pub `assets/videos/` 同名 mp4，
   ffmpeg 转 `_web.mp4` + `.jpg` 海报 → `static/media/<slug>/`）；`assets/images/*` 直接拷贝；
5. **详解版入口**（发布规则，见 pub `AGENTS.md`）：hero 后 + 文末各插一个指回 pub
   `README-details.md` 的入口。只发精简版，详解版不上站只链接。

只处理带 `meta.toml` 且 `publish=true` 的文件夹。

## 本地预览

需 Hugo **extended v0.148.2**（与 CI 对齐）：

```bash
# 1) 从 pub 生成内容(需 ffmpeg)
python3 scripts/sync_from_pub.py --pub ../tech-blog-pub --out .
# 2) 预览
hugo server -D          # http://localhost:1313/
```

没有对应版本时下载单二进制：

```bash
HV=0.148.2
wget https://github.com/gohugoio/hugo/releases/download/v${HV}/hugo_extended_${HV}_linux-amd64.tar.gz
tar xzf hugo_extended_${HV}_linux-amd64.tar.gz hugo && ./hugo server -D
```

## 版本锁定（重要）

Hugo ↔ PaperMod 版本耦合，当前锁定：
- **Hugo extended 0.148.2**（`deploy.yml` 的 `HUGO_VERSION`）。
- **PaperMod：master**（2026-07 验证可用），vendored 在 `themes/PaperMod/`。

> 历史坑：Hugo 0.135 + 旧 PaperMod v7.0 会让文章 meta 行输出裸 `<span>`；旧主题用了 Hugo
> 0.124 已移除的 `.Site.Social`，新 Hugo 直接构建报错。升级任一方前务必本地验证构建。

## 构建与部署（CI）

`.github/workflows/deploy.yml`：触发（push `main` / `workflow_dispatch` / 来自 pub 的
`repository_dispatch:pub-updated`）→ 装固定版 Hugo → checkout `rocPAI-Forge/tech-blog-pub` 到
`_pub/` → 装 ffmpeg → `python3 scripts/sync_from_pub.py --pub _pub --out .` → `hugo --gc
--minify --baseURL <pages_url>` → `upload-pages-artifact` → `deploy-pages`。只提交源码，
**不提交 `public/`**。

pub 改稿自动触发官网重建需 pub 仓库配 secret `SITE_DISPATCH_TOKEN`（详见 pub `AGENTS.md`）；
未配置时可在本仓库手动 `workflow_dispatch`。

### 首次启用踩坑
- 仓库 **Settings → Pages → Source 选 “GitHub Actions”**（API：
  `gh api -X PUT repos/<org>/<repo>/pages -f build_type=workflow`）。
- 新建 `*.github.io` 仓库时 GitHub 会**默认跑一次 Jekyll 构建**把 `README.md` 当首页（导致
  Hugo 子页 404）；切成 GitHub Actions 源并重新触发部署即由 Hugo 产物接管。

## 后续可做
- 绑定自定义域名（加 `CNAME`）。
- 补全 Roadmap 内容。
- 媒体变大可考虑 Git LFS / Cloudflare Pages（当前 <1.5MB，Pages 免费额度足够）。
