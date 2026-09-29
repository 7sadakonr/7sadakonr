from __future__ import annotations

import json
import math
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "7sadakonr"
ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "profile-views.json"
SVG_FILE = ROOT / "assets" / "profile-views-history.svg"
COUNTER_URL = (
    "https://komarev.com/ghpvc/"
    f"?username={USERNAME}&label=views&color=8B5CF6&style=flat"
)


def fetch_view_count() -> int:
    req = urllib.request.Request(
        COUNTER_URL,
        headers={"User-Agent": "Mozilla/5.0 GitHub-Profile-Views-History"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        svg = response.read().decode("utf-8")

    values = []
    for value in re.findall(r">\s*([0-9][0-9,.]*[kKmM]?)\s*<", svg):
        raw = value.replace(",", "").lower()
        multiplier = 1
        if raw.endswith("k"):
            multiplier, raw = 1_000, raw[:-1]
        elif raw.endswith("m"):
            multiplier, raw = 1_000_000, raw[:-1]
        try:
            values.append(int(float(raw) * multiplier))
        except ValueError:
            pass

    if not values:
        raise RuntimeError("Could not parse visitor count from counter SVG.")
    return max(values)


def load_history() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"username": USERNAME, "started_at": None, "entries": []}


def save_history(history: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(history, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def update_history(history: dict, today: str, views: int) -> dict:
    history["username"] = USERNAME
    if not history.get("started_at"):
        history["started_at"] = today

    entries = history.setdefault("entries", [])
    existing = next((item for item in entries if item["date"] == today), None)
    if existing:
        existing["views"] = views
    else:
        entries.append({"date": today, "views": views})

    entries.sort(key=lambda item: item["date"])
    return history


def make_svg(history: dict) -> str:
    entries = history.get("entries", [])[-30:]
    width, height = 900, 300
    left, right, top, bottom = 72, 38, 102, 58
    chart_w = width - left - right
    chart_h = height - top - bottom

    if not entries:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" rx="18" fill="#24292F"/>
<text x="42" y="58" fill="#FF7777" font-family="monospace" font-size="18">7sadakonr@github:~$ visitors --history 30d</text>
<text x="42" y="148" fill="#C9D1D9" font-family="monospace" font-size="16">Collecting the first visitor snapshot...</text>
</svg>
"""

    values = [int(item["views"]) for item in entries]
    dates = [item["date"] for item in entries]
    minimum = min(values)
    maximum = max(values)
    spread = max(1, maximum - minimum)
    pad = max(1, math.ceil(spread * 0.18))
    y_min = max(0, minimum - pad)
    y_max = maximum + pad
    y_span = max(1, y_max - y_min)

    def x_pos(index: int) -> float:
        if len(entries) == 1:
            return left + chart_w / 2
        return left + (index / (len(entries) - 1)) * chart_w

    def y_pos(value: int) -> float:
        return top + (1 - ((value - y_min) / y_span)) * chart_h

    points = " ".join(
        f"{x_pos(i):.1f},{y_pos(value):.1f}" for i, value in enumerate(values)
    )
    total = values[-1]
    delta = values[-1] - values[0]
    days = len(entries)
    start_label = datetime.strptime(dates[0], "%Y-%m-%d").strftime("%b %d")
    end_label = datetime.strptime(dates[-1], "%Y-%m-%d").strftime("%b %d")
    delta_text = f"+{delta:,}" if delta >= 0 else f"{delta:,}"

    grid = []
    y_labels = []
    for i in range(4):
        ratio = i / 3
        y = top + ratio * chart_h
        value = round(y_max - ratio * y_span)
        grid.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#30363D" stroke-width="1"/>'
        )
        y_labels.append(
            f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" fill="#8B949E" font-family="monospace" font-size="12">{value:,}</text>'
        )

    circles = "".join(
        f'<circle cx="{x_pos(i):.1f}" cy="{y_pos(value):.1f}" r="4" fill="#FF7777"/>'
        for i, value in enumerate(values)
    )

    subtitle = escape(f"{days} day{'s' if days != 1 else ''} collected · daily snapshots")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" rx="18" fill="#24292F"/>
<text x="42" y="46" fill="#FF7777" font-family="monospace" font-size="18">7sadakonr@github:~$ visitors --history 30d</text>
<text x="42" y="76" fill="#C9D1D9" font-family="monospace" font-size="14">{subtitle}</text>
<text x="{width-42}" y="46" text-anchor="end" fill="#8B5CF6" font-family="monospace" font-weight="700" font-size="22">{total:,} total</text>
<text x="{width-42}" y="76" text-anchor="end" fill="#8B949E" font-family="monospace" font-size="13">{delta_text} in displayed period</text>
{"".join(grid)}
{"".join(y_labels)}
<polyline points="{points}" fill="none" stroke="#8B5CF6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
{circles}
<text x="{left}" y="{height-25}" fill="#8B949E" font-family="monospace" font-size="12">{start_label}</text>
<text x="{width-right}" y="{height-25}" text-anchor="end" fill="#8B949E" font-family="monospace" font-size="12">{end_label}</text>
</svg>
"""


def main() -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    views = fetch_view_count()
    history = update_history(load_history(), today, views)
    save_history(history)
    SVG_FILE.parent.mkdir(parents=True, exist_ok=True)
    SVG_FILE.write_text(make_svg(history), encoding="utf-8")
    print(f"Recorded {views} profile views for {today}")


if __name__ == "__main__":
    main()
