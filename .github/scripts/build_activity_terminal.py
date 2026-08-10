from __future__ import annotations

import re
import urllib.request
from pathlib import Path

GRAPH_URL = (
    "https://github-readme-activity-graph.vercel.app/graph"
    "?username=7sadakonr"
    "&bg_color=0D1117"
    "&color=E6EDF3"
    "&line=FF7777"
    "&point=FF7777"
    "&area=true"
    "&area_color=8B5CF6"
    "&hide_border=true"
    "&radius=12"
)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "7sadakonr-profile-readme/1.0",
            "Accept": "image/svg+xml,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def nested_svg(svg_text: str, *, x: int, y: int, width: int, height: int) -> str:
    start = svg_text.find("<svg")
    if start < 0:
        raise ValueError("SVG root not found")

    open_end = svg_text.find(">", start)
    close_start = svg_text.rfind("</svg>")
    if open_end < 0 or close_start < 0:
        raise ValueError("Invalid SVG document")

    opening = svg_text[start : open_end + 1]
    inner = svg_text[open_end + 1 : close_start]

    view_box = re.search(r'viewBox=["\']([^"\']+)["\']', opening)
    if view_box:
        viewport = view_box.group(1)
    else:
        width_match = re.search(r'width=["\']([0-9.]+)', opening)
        height_match = re.search(r'height=["\']([0-9.]+)', opening)
        source_w = width_match.group(1) if width_match else str(width)
        source_h = height_match.group(1) if height_match else str(height)
        viewport = f"0 0 {source_w} {source_h}"

    return (
        f'<svg x="{x}" y="{y}" width="{width}" height="{height}" '
        f'viewBox="{viewport}" preserveAspectRatio="xMidYMid meet">{inner}</svg>'
    )


def build_terminal(snake_svg: str, graph_svg: str) -> str:
    snake = nested_svg(snake_svg, x=58, y=112, width=1084, height=136)
    graph = nested_svg(graph_svg, x=46, y=340, width=1108, height=352)

    return f'''<svg width="1200" height="720" viewBox="0 0 1200 720" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="activityOuterClip"><rect x="1" y="1" width="1198" height="718" rx="28"/></clipPath>
  </defs>

  <g clip-path="url(#activityOuterClip)">
    <rect width="1200" height="720" fill="#0D1117"/>
    <rect x="1" y="1" width="1198" height="718" rx="28" fill="none" stroke="#30363D" stroke-width="2"/>

    <rect width="1200" height="56" fill="#111827"/>
    <line x1="0" y1="56" x2="1200" y2="56" stroke="#21262D"/>
    <circle cx="28" cy="28" r="7" fill="#FF5F57"/>
    <circle cx="51" cy="28" r="7" fill="#FEBC2E"/>
    <circle cx="74" cy="28" r="7" fill="#28C840"/>
    <text x="112" y="34" fill="#E6EDF3" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="17" font-weight="700">GitHub Activity</text>
    <text x="1150" y="34" text-anchor="end" fill="#8B949E" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12">~/activity/dashboard.sh</text>

    <rect x="24" y="78" width="1152" height="194" rx="18" fill="#0B1220" stroke="#30363D"/>
    <circle cx="46" cy="99" r="4.5" fill="#FF5F57"/>
    <circle cx="59" cy="99" r="4.5" fill="#FEBC2E"/>
    <circle cx="72" cy="99" r="4.5" fill="#28C840"/>
    <text x="92" y="103" fill="#8B949E" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10">contribution-snake.svg</text>
    {snake}

    <rect x="24" y="294" width="1152" height="402" rx="18" fill="#0B1220" stroke="#30363D"/>
    <circle cx="46" cy="315" r="4.5" fill="#FF5F57"/>
    <circle cx="59" cy="315" r="4.5" fill="#FEBC2E"/>
    <circle cx="72" cy="315" r="4.5" fill="#28C840"/>
    <text x="92" y="319" fill="#8B949E" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10">contribution-graph.svg</text>
    {graph}

    <rect x="1118" y="675" width="2" height="16" fill="#FF7777"/>
  </g>
</svg>'''


def main() -> None:
    dist = Path("dist")
    snake_path = dist / "github-contribution-grid-snake-dark.svg"
    if not snake_path.exists():
        raise SystemExit(f"Missing generated snake: {snake_path}")

    snake_svg = snake_path.read_text(encoding="utf-8")
    graph_svg = fetch_text(GRAPH_URL)
    output = build_terminal(snake_svg, graph_svg)
    (dist / "github-activity-terminal.svg").write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
