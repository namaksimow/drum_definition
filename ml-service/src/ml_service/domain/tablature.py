from __future__ import annotations

import json

import numpy as np


def build_rhythm_grid(beat_times: np.ndarray, subdivisions: int = 4) -> np.ndarray:
    beat_times = np.asarray(beat_times, dtype=float)
    if len(beat_times) < 2:
        return np.array([])

    grid = []
    for i in range(len(beat_times) - 1):
        start = beat_times[i]
        end = beat_times[i + 1]
        step = (end - start) / subdivisions
        for s in range(subdivisions):
            grid.append(start + s * step)
    return np.array(grid, dtype=float)


def quantize_hits_to_slots(hit_times: np.ndarray, grid_times: np.ndarray, tolerance: float = 0.06) -> set[int]:
    hit_times = np.asarray(hit_times, dtype=float)
    grid_times = np.asarray(grid_times, dtype=float)

    slots: set[int] = set()
    if len(grid_times) == 0 or len(hit_times) == 0:
        return slots

    for hit in hit_times:
        idx = int(np.argmin(np.abs(grid_times - hit)))
        if abs(grid_times[idx] - hit) <= tolerance:
            slots.add(idx)
    return slots


def render_tab_row(slot_count: int, active_slots: set[int], hit_char: str) -> str:
    row = ["-"] * slot_count
    for s in active_slots:
        if 0 <= s < slot_count:
            row[s] = hit_char
    return "".join(row)


def build_tablature_data(
    beat_times: np.ndarray,
    events: dict[str, list[float]],
    start_time: float,
    end_time: float,
    beats_per_bar: int = 4,
    subdivisions: int = 4,
    bars_per_line: int = 4,
    tolerance_by_instrument: dict[str, float] | None = None,
) -> dict:
    if tolerance_by_instrument is None:
        tolerance_by_instrument = {"hihat": 0.05, "snare": 0.06, "kick": 0.06}

    beat_times = np.asarray(beat_times, dtype=float)
    fragment_beats = beat_times[(beat_times >= start_time) & (beat_times <= end_time)]

    if len(fragment_beats) < beats_per_bar + 1:
        return {"meta": {"error": "Not enough beats for a full bar"}, "lines": []}

    bars = []
    i = 0
    bar_num = 1
    symbols = {"hihat": "x", "snare": "o", "kick": "o"}

    while i + beats_per_bar < len(fragment_beats):
        bar_beats = fragment_beats[i : i + beats_per_bar + 1]
        bar_start = float(bar_beats[0])
        bar_end = float(bar_beats[-1])
        grid = build_rhythm_grid(bar_beats, subdivisions=subdivisions)
        slot_count = int(len(grid))

        bar_data = {
            "bar_number": bar_num,
            "start_sec": bar_start,
            "end_sec": bar_end,
            "slot_count": slot_count,
            "instruments": {},
        }

        for instrument in ("hihat", "snare", "kick"):
            hits = np.asarray(events.get(instrument, []), dtype=float)
            hits = hits[(hits >= bar_start) & (hits < bar_end)]
            slots = sorted(
                quantize_hits_to_slots(
                    hit_times=hits,
                    grid_times=grid,
                    tolerance=tolerance_by_instrument[instrument],
                )
            )
            bar_data["instruments"][instrument] = {
                "symbol": symbols[instrument],
                "slots": slots,
                "pattern": render_tab_row(slot_count, set(slots), symbols[instrument]),
            }

        bars.append(bar_data)
        i += beats_per_bar
        bar_num += 1

    lines = []
    line_idx = 1
    for j in range(0, len(bars), bars_per_line):
        chunk = bars[j : j + bars_per_line]
        lines.append(
            {
                "line_number": line_idx,
                "first_bar": chunk[0]["bar_number"],
                "last_bar": chunk[-1]["bar_number"],
                "start_sec": chunk[0]["start_sec"],
                "end_sec": chunk[-1]["end_sec"],
                "bars": chunk,
            }
        )
        line_idx += 1

    return {
        "meta": {
            "start_time_sec": float(start_time),
            "end_time_sec": float(end_time),
            "beats_per_bar": int(beats_per_bar),
            "subdivisions": int(subdivisions),
            "bars_per_line": int(bars_per_line),
            "instruments": ["hihat", "snare", "kick"],
        },
        "lines": lines,
    }


def format_ascii_from_tablature(tab_data: dict) -> str:
    if not tab_data.get("lines"):
        return "No tablature data"

    out = []
    for line in tab_data["lines"]:
        out.append(
            f"line {line['line_number']} | bars {line['first_bar']}-{line['last_bar']} "
            f"| {line['start_sec']:.3f}s - {line['end_sec']:.3f}s"
        )
        for instrument in ("hihat", "snare", "kick"):
            row = "".join(f"|{bar['instruments'][instrument]['pattern']}|" for bar in line["bars"])
            out.append(f"{instrument:<5}{row}")
        out.append("")
    return "\n".join(out).rstrip()


def save_tablature_json(tab_data: dict, out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tab_data, f, ensure_ascii=False, indent=2)

