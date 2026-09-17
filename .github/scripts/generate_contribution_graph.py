#!/usr/bin/env python3
"""
Generates a standalone purple line/area contribution graph SVG,
matching a minimal "just the chart" look (no card, no border/box).
"""

import os
import sys
import json
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

USERNAME = os.environ.get("GITHUB_USERNAME", "alinazeeshan")
TOKEN = os.environ.get("GITHUB_TOKEN")
DAYS = int(os.environ.get("DAYS", "30"))  # last N days, like the screenshot
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "contribution-line-graph.svg")
LINE_COLOR = os.environ.get("LINE_COLOR", "#B983FF")

QUERY = """
query($userName: String!) {
  user(login: $userName) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_contributions(username, token):
    headers = {"Authorization": f"bearer {token}"}
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"userName": username}},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append((datetime.strptime(d["date"], "%Y-%m-%d"), d["contributionCount"]))
    days.sort(key=lambda x: x[0])
    return days


def make_mock_data(n=30):
    import random
    from datetime import timedelta
    today = datetime.utcnow()
    days = []
    for i in range(n):
        d = today - timedelta(days=n - 1 - i)
        c = random.choice([0, 0, 0, 1, 2, 3, 5, 8])
        days.append((d, c))
    return days


def plot(days, output_path, line_color):
    dates = [d for d, _ in days]
    counts = [c for _, c in days]

    fig, ax = plt.subplots(figsize=(9, 3.2), dpi=150)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    ax.plot(dates, counts, color=line_color, linewidth=2.2, marker="o",
            markersize=4, markerfacecolor=line_color, markeredgecolor=line_color, zorder=3)
    ax.fill_between(dates, counts, color=line_color, alpha=0.15, zorder=1)

    ax.grid(True, which="major", axis="both", color="#888888", alpha=0.15, linewidth=0.6, linestyle="-")
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="x", colors="#B983FF", labelsize=8)
    ax.tick_params(axis="y", colors="#B983FF", labelsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.xticks(rotation=0)

    ax.set_ylim(bottom=0)
    ax.margins(x=0.01)

    plt.tight_layout(pad=0.6)
    plt.savefig(output_path, transparent=True, format="svg")
    plt.close(fig)


def main():
    if TOKEN:
        try:
            days = fetch_contributions(USERNAME, TOKEN)
            days = days[-DAYS:]
        except Exception as e:
            print(f"Failed to fetch live data ({e}); falling back to mock data.", file=sys.stderr)
            days = make_mock_data(DAYS)
    else:
        print("No GITHUB_TOKEN set; using mock data for preview.", file=sys.stderr)
        days = make_mock_data(DAYS)

    plot(days, OUTPUT_PATH, LINE_COLOR)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
