#!/usr/bin/env python3
"""Generate Hugo blog content from the tech-blog-pub source repo.

pub (source of truth) --> Hugo content (generated).

For each pub post `<category>/<slug>/` that has a `meta.toml` with `publish = true`:
  - split the bilingual README.md (## 中文 / ## English) into two Hugo files
    `content/posts/<slug>.md` and `content/posts/<slug>.en.md` with front matter
    taken from meta.toml;
  - rewrite media: `assets/gifs/x.gif` -> optimized looping `<video>` (mp4 + jpg
    poster) under `static/media/<slug>/`; `assets/images/x.png` -> `/media/<slug>/x.png`;
  - append a footer linking to the deep-dive (README-details.md) hosted on pub.

Only the CONCISE README.md is published to the site; the deep-dive stays on pub.

Usage:
  python3 scripts/sync_from_pub.py --pub /path/to/tech-blog-pub [--out .]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

PUB_REPO = "alexhegit/tech-blog-pub"
PUB_BRANCH = "main"

IMG_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>assets/[^)]+)\)")
VIDLINK_RE = re.compile(r"\[(?P<txt>[^\]]+)\]\((?P<path>assets/videos/[^)]+\.mp4)\)")


def parse_meta(path: Path) -> dict:
    """Minimal TOML-subset parser (string / bool / date / string-array)."""
    try:
        import tomllib  # py311+
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except ModuleNotFoundError:
        pass
    meta: dict = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip()
        if val.startswith("["):
            meta[key] = re.findall(r'"([^"]*)"', val)
        elif val.startswith('"'):
            meta[key] = val.strip('"')
        else:
            val = val.split("#", 1)[0].strip()
            if val in ("true", "false"):
                meta[key] = val == "true"
            else:
                meta[key] = val
    return meta


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def make_video(src: Path, web: Path, poster: Path) -> None:
    web.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-movflags", "+faststart", "-pix_fmt", "yuv420p",
         "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
         "-c:v", "libx264", "-crf", "26", "-an", str(web)])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(web),
         "-frames:v", "1", "-q:v", "3", str(poster)])


VIDEO_HTML = (
    '<video src="/media/{slug}/{name}_web.mp4" poster="/media/{slug}/{name}.jpg" '
    'autoplay loop muted playsinline style="width:100%;border-radius:.6rem;"></video>\n'
    '<p style="text-align:center;color:#888;font-size:.8rem;">{cap}</p>'
)


def transform_media(text: str, post_dir: Path, slug: str, static_media: Path) -> str:
    """Rewrite asset references; produce site media as a side effect."""
    def img_sub(m: re.Match) -> str:
        alt, rel = m.group("alt"), m.group("path")
        src = post_dir / rel
        name = Path(rel).stem
        ext = Path(rel).suffix.lower()
        if ext == ".gif":
            # prefer an mp4 counterpart in assets/videos/, else convert the gif
            mp4_src = post_dir / "assets" / "videos" / f"{name}.mp4"
            source = mp4_src if mp4_src.exists() else src
            web = static_media / slug / f"{name}_web.mp4"
            poster = static_media / slug / f"{name}.jpg"
            make_video(source, web, poster)
            return VIDEO_HTML.format(slug=slug, name=name, cap=alt)
        # images: copy through
        dst = static_media / slug / Path(rel).name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        return f"![{alt}](/media/{slug}/{Path(rel).name})"

    def vidlink_sub(m: re.Match) -> str:
        name = Path(m.group("path")).stem
        return f"[{m.group('txt')}](/media/{slug}/{name}_web.mp4)"

    text = IMG_RE.sub(img_sub, text)
    text = VIDLINK_RE.sub(vidlink_sub, text)
    return text


def split_sections(md: str) -> tuple[list[str], str, str]:
    lines = md.splitlines()

    def idx(header: str) -> int:
        for i, l in enumerate(lines):
            if l.strip() == header:
                return i
        return -1

    i_zh, i_en = idx("## 中文"), idx("## English")
    if i_zh < 0 or i_en < 0:
        raise SystemExit("README missing '## 中文' or '## English' section")

    preamble = lines[:i_zh]
    zh = lines[i_zh + 1:i_en]
    en = lines[i_en + 1:]

    # hero media that appears before the first language section
    hero = [l for l in preamble if IMG_RE.search(l)]

    def clean(block: list[str]) -> str:
        out = block[:]
        while out and out[-1].strip() in ("", "---"):
            out.pop()
        while out and out[0].strip() == "":
            out.pop(0)
        return "\n".join(out)

    return hero, clean(zh), clean(en)


def front_matter(title: str, meta: dict) -> str:
    tags = ", ".join('"' + t + '"' for t in meta.get("tags", []))
    author = meta.get("author", "")
    date = str(meta["date"])
    return (
        "+++\n"
        'title = "' + title + '"\n'
        "date = " + date + "\n"
        'author = "' + author + '"\n'
        "tags = [" + tags + "]\n"
        "+++\n"
    )


def build_post(post_dir: Path, meta: dict, content_dir: Path, static_media: Path) -> str:
    slug = meta["slug"]
    category = post_dir.parent.name
    readme = (post_dir / "README.md").read_text(encoding="utf-8")
    hero_lines, zh_body, en_body = split_sections(readme)
    hero = "\n".join(hero_lines)

    details_url = (
        f"https://github.com/{PUB_REPO}/blob/{PUB_BRANCH}/"
        f"{category}/{post_dir.name}/README-details.md"
    )
    # 显著的详解版入口:开头(hero 之后)引导 + 结尾兜底
    zh_lead = f"> 📖 本文为**精简版**（~3 分钟）。想深入完整工程细节（设计决策、算法 / reward、诊断、复现命令），请移步 [**技术详解版 →**]({details_url})"
    en_lead = f"> 📖 This is the **concise version** (~3 min). For the full engineering details (design decisions, algorithm / reward, diagnostics, reproduce commands), read the [**deep-dive →**]({details_url})"
    zh_footer = f"> 📖 想了解更多？完整工程细节见 [技术详解版]({details_url})。"
    en_footer = f"> 📖 Want more? Full engineering details in the [deep-dive]({details_url})."

    def assemble(title: str, body: str, lead: str, footer: str) -> str:
        # promote headings one level up (the '## 中文' wrapper is dropped)
        body = re.sub(r"(?m)^(#{2,5}) ", lambda m: m.group(1)[1:] + " ", body)
        parts = [front_matter(title, meta), ""]
        if hero:
            parts.append(hero)
            parts.append("")
        parts.append(lead)
        parts.append("")
        parts.append(body)
        parts.append("")
        parts.append(footer)
        raw = "\n".join(parts)
        return transform_media(raw, post_dir, slug, static_media)

    content_dir.mkdir(parents=True, exist_ok=True)
    (content_dir / f"{slug}.md").write_text(
        assemble(meta["title_zh"], zh_body, zh_lead, zh_footer), encoding="utf-8")
    (content_dir / f"{slug}.en.md").write_text(
        assemble(meta["title_en"], en_body, en_lead, en_footer), encoding="utf-8")
    return slug


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pub", required=True, help="path to tech-blog-pub repo")
    ap.add_argument("--out", default=".", help="Hugo site root (default: cwd)")
    args = ap.parse_args()

    pub = Path(args.pub).resolve()
    out = Path(args.out).resolve()
    content_dir = out / "content" / "posts"
    static_media = out / "static" / "media"

    metas = sorted(pub.glob("*/*/meta.toml"))
    if not metas:
        print(f"no meta.toml found under {pub}")
        return 1

    published = []
    for meta_path in metas:
        meta = parse_meta(meta_path)
        if not meta.get("publish", False):
            print(f"skip (publish=false): {meta_path.parent}")
            continue
        post_dir = meta_path.parent
        if not (post_dir / "README.md").exists():
            print(f"skip (no README.md): {post_dir}")
            continue
        slug = build_post(post_dir, meta, content_dir, static_media)
        published.append(slug)
        print(f"generated: {post_dir.name} -> posts/{slug}.{{md,en.md}} + media/{slug}/")

    print(f"done: {len(published)} post(s): {', '.join(published)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
