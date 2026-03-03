from __future__ import annotations

import matplotlib.pyplot as plt

BLOCK_GAP_UNITS = 0.9


def _line_weight(line: str) -> float:
    s = line.rstrip()
    if not s:
        return 0.22
    if s.startswith(("hihat", "snare", "kick")):
        return 0.70
    if s.startswith("line "):
        return 1.35
    return 0.70


def save_ascii_tab_report(text: str, out_path: str, title: str = "Drum ASCII Tab") -> None:
    lines = text.splitlines()
    max_len = max((len(line) for line in lines), default=40)

    fig_w = max(8.0, max_len * 0.11)
    top_pad = 0.10 if title else 0.04
    bottom_pad = 0.04
    total_weight = sum(_line_weight(line) for line in lines) or 1.0
    fig_h = max(4.0, total_weight * 0.23 + 1.0)

    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    y = 1.0 - top_pad

    if title:
        ax.text(
            0.02,
            0.985,
            title,
            va="top",
            ha="left",
            fontsize=14,
            family="monospace",
            weight="bold",
        )

    available = 1.0 - top_pad - bottom_pad
    unit = available / total_weight

    for line in lines:
        stripped = line.rstrip()
        ax.text(0.02, y, line, va="top", ha="left", fontsize=11, family="monospace")
        y -= _line_weight(line) * unit
        if stripped.startswith("kick"):
            y -= BLOCK_GAP_UNITS * unit

    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

