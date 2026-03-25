from __future__ import annotations

import numpy as np

from ml_service.domain.tablature import (
    build_rhythm_grid,
    build_tablature_data,
    format_ascii_from_tablature,
    quantize_hits_to_slots,
    render_tab_row,
)


def test_build_rhythm_grid_returns_expected_subdivisions() -> None:
    beat_times = np.array([0.0, 1.0], dtype=float)
    grid = build_rhythm_grid(beat_times, subdivisions=4)
    assert np.allclose(grid, np.array([0.0, 0.25, 0.5, 0.75], dtype=float))


def test_quantize_hits_to_slots_respects_tolerance() -> None:
    grid = np.array([0.0, 0.25, 0.5, 0.75], dtype=float)
    hits = np.array([0.02, 0.51, 1.4], dtype=float)
    slots = quantize_hits_to_slots(hits, grid, tolerance=0.06)
    assert slots == {0, 2}


def test_render_tab_row_marks_only_valid_slots() -> None:
    row = render_tab_row(slot_count=6, active_slots={0, 2, 8}, hit_char="x")
    assert row == "x-x---"


def test_build_tablature_data_returns_structured_payload() -> None:
    beat_times = np.array([0, 1, 2, 3, 4], dtype=float)
    events = {
        "hihat": [0.0, 0.5, 1.0, 1.5, 2.0],
        "snare": [1.0, 3.0],
        "kick": [0.0, 2.0],
    }
    tab = build_tablature_data(
        beat_times=beat_times,
        events=events,
        start_time=0.0,
        end_time=4.0,
        beats_per_bar=4,
        subdivisions=4,
        bars_per_line=1,
    )

    assert "meta" in tab
    assert tab["meta"]["beats_per_bar"] == 4
    assert len(tab["lines"]) == 1
    assert tab["lines"][0]["bars"][0]["instruments"]["hihat"]["pattern"]


def test_format_ascii_from_tablature_returns_readable_report() -> None:
    payload = {
        "lines": [
            {
                "line_number": 1,
                "first_bar": 1,
                "last_bar": 1,
                "start_sec": 0.0,
                "end_sec": 2.0,
                "bars": [
                    {
                        "instruments": {
                            "hihat": {"pattern": "x-x-"},
                            "snare": {"pattern": "--o-"},
                            "kick": {"pattern": "o---"},
                        }
                    }
                ],
            }
        ]
    }
    text = format_ascii_from_tablature(payload)
    assert "line 1 | bars 1-1" in text
    assert "hihat" in text
    assert "snare" in text
    assert "kick" in text

