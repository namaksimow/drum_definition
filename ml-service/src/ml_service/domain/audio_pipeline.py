from __future__ import annotations

from pathlib import Path
from typing import Any

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

BANDS = {
    "kick": (30, 150),
    "snare": (200, 4000),
    "hihat": (5000, 12000),
}

GAP_BY_INSTRUMENT = {
    "kick": 0.09,
    "snare": 0.08,
    "hihat": 0.045,
}


def separate_to_4stems(song_path: str | Path, stems_root_dir: str | Path) -> dict[str, Any]:
    try:
        from spleeter.separator import Separator
    except ImportError as exc:
        raise RuntimeError("Spleeter is not installed. Install dependency: spleeter") from exc

    song_path = Path(song_path)
    stems_root_dir = Path(stems_root_dir)
    stems_root_dir.mkdir(parents=True, exist_ok=True)

    separator = Separator("spleeter:4stems")
    separator.separate_to_file(str(song_path), str(stems_root_dir), codec="wav")

    track_dir = stems_root_dir / song_path.stem
    if not track_dir.exists():
        raise FileNotFoundError(f"Spleeter output dir not found: {track_dir}")

    stems: dict[str, str] = {}
    for stem in ("vocals", "drums", "bass", "other"):
        candidate = track_dir / f"{stem}.wav"
        if candidate.exists():
            stems[stem] = str(candidate)

    if "drums" not in stems:
        raise FileNotFoundError(f"Drums stem was not created in: {track_dir}")

    return {
        "track_dir": str(track_dir),
        "stems": stems,
    }


def bandpass_signal(y: np.ndarray, sr: int, low_freq: int, high_freq: int, n_fft: int = 2048, hop_length: int = 256) -> np.ndarray:
    d = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    spectrum = np.abs(d)
    phase = np.angle(d)

    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    mask = (freqs >= low_freq) & (freqs <= high_freq)

    filtered = np.zeros_like(spectrum)
    filtered[mask, :] = spectrum[mask, :]
    d_filtered = filtered * np.exp(1j * phase)
    return librosa.istft(d_filtered, hop_length=hop_length)


def get_beats(y: np.ndarray, sr: int, hop_length: int = 256) -> tuple[float, np.ndarray]:
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
    return float(tempo), beat_times


def detect_hits_from_onset_env(
    y: np.ndarray,
    sr: int,
    hop_length: int = 256,
    delta: float = 0.25,
    prominence: float = 0.12,
    min_gap_sec: float = 0.06,
    smooth_frames: int = 5,
) -> np.ndarray:
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    if onset_env.size == 0:
        return np.array([])

    onset_env = onset_env.astype(np.float32)
    onset_env /= onset_env.max() + 1e-9

    if smooth_frames > 1:
        kernel = np.ones(smooth_frames, dtype=np.float32) / smooth_frames
        onset_env = np.convolve(onset_env, kernel, mode="same")

    med = np.median(onset_env)
    mad = np.median(np.abs(onset_env - med)) + 1e-9
    height = med + delta * mad
    min_distance_frames = max(1, int(min_gap_sec * sr / hop_length))

    peaks, _ = find_peaks(
        onset_env,
        height=height,
        prominence=prominence,
        distance=min_distance_frames,
    )

    if peaks.size > 1:
        keep = [int(peaks[0])]
        for p in peaks[1:]:
            p = int(p)
            if p - keep[-1] < min_distance_frames:
                if onset_env[p] > onset_env[keep[-1]]:
                    keep[-1] = p
            else:
                keep.append(p)
        peaks = np.array(keep, dtype=int)

    return librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)


def _build_chunks(start_sec: float, end_sec: float, chunk_sec: float) -> list[tuple[float, float]]:
    chunks: list[tuple[float, float]] = []
    t = start_sec
    while t < end_sec:
        chunk_start = t
        chunk_end = min(t + chunk_sec, end_sec)
        chunks.append((chunk_start, chunk_end))
        t = chunk_end
    return chunks


def _save_part_plot(
    out_path: Path,
    y_band: np.ndarray,
    sr: int,
    beat_times: np.ndarray,
    hit_times_local: np.ndarray,
    chunk_start: float,
    chunk_end: float,
    instrument: str,
    low: int,
    high: int,
    tempo: float,
    part_idx: int,
    total_parts: int,
) -> None:
    plt.figure(figsize=(14, 4))
    librosa.display.waveshow(y_band, sr=sr, alpha=0.8)

    beat_times_fragment = beat_times[(beat_times >= chunk_start) & (beat_times <= chunk_end)] - chunk_start
    plt.vlines(
        beat_times_fragment,
        ymin=-1,
        ymax=1,
        color="black",
        linestyle="dashed",
        alpha=0.6,
        label="Beats",
    )

    for t_local in hit_times_local:
        plt.axvline(t_local, color="red", alpha=0.7)

    plt.title(
        f"{instrument} band-pass ({low}-{high} Hz) | BPM ≈ {int(tempo)} | "
        f"part {part_idx}/{total_parts} | {chunk_start:.1f}-{chunk_end:.1f}s"
    )
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude (normalized)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def analyze_audio_file(
    audio_path: str | Path,
    output_dir: str | Path,
    *,
    start_time: float = 0.0,
    duration: float | None = None,
    plot: bool = True,
    plot_chunk_sec: float = 8.0,
) -> dict[str, Any]:
    audio_path = Path(audio_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    y_full, sr = librosa.load(str(audio_path), sr=None, mono=True)
    total_audio_sec = len(y_full) / sr
    analysis_start = max(0.0, float(start_time))
    analysis_end = total_audio_sec if duration is None else min(analysis_start + float(duration), total_audio_sec)
    if analysis_end <= analysis_start:
        raise ValueError("Empty analysis range")

    if plot_chunk_sec <= 0:
        plot_chunk_sec = analysis_end - analysis_start
    chunks = _build_chunks(analysis_start, analysis_end, plot_chunk_sec)

    tempo, beat_times = get_beats(y_full, sr)
    parts_root = output_dir / "parts"
    parts_root.mkdir(parents=True, exist_ok=True)

    events: dict[str, list[float]] = {name: [] for name in BANDS}
    part_files: dict[str, list[str]] = {name: [] for name in BANDS}

    for instrument, (low, high) in BANDS.items():
        instrument_parts_dir = parts_root / instrument
        instrument_parts_dir.mkdir(parents=True, exist_ok=True)
        min_gap = GAP_BY_INSTRUMENT[instrument]

        total_parts = len(chunks)
        for part_idx, (chunk_start, chunk_end) in enumerate(chunks, start=1):
            start_sample = int(chunk_start * sr)
            end_sample = int(chunk_end * sr)
            y = y_full[start_sample:end_sample]
            if y.size == 0:
                continue

            y_band = bandpass_signal(y, sr, low, high)
            max_amp = np.max(np.abs(y_band))
            if max_amp > 0:
                y_band = y_band / max_amp

            hit_times_local = detect_hits_from_onset_env(
                y_band,
                sr,
                hop_length=256,
                delta=0.25,
                prominence=0.12,
                min_gap_sec=min_gap,
                smooth_frames=5,
            )
            hit_times_global = hit_times_local + chunk_start
            events[instrument].extend(hit_times_global.tolist())

            if plot:
                out_name = f"band_{low}-{high}Hz_part{part_idx:03d}_{chunk_start:.1f}-{chunk_end:.1f}s.png"
                out_path = instrument_parts_dir / out_name
                _save_part_plot(
                    out_path=out_path,
                    y_band=y_band,
                    sr=sr,
                    beat_times=beat_times,
                    hit_times_local=hit_times_local,
                    chunk_start=chunk_start,
                    chunk_end=chunk_end,
                    instrument=instrument,
                    low=low,
                    high=high,
                    tempo=tempo,
                    part_idx=part_idx,
                    total_parts=total_parts,
                )
                part_files[instrument].append(str(out_path))

    return {
        "sample_rate": int(sr),
        "tempo_bpm": float(tempo),
        "audio_duration_sec": float(total_audio_sec),
        "analysis_start_sec": float(analysis_start),
        "analysis_end_sec": float(analysis_end),
        "beat_times_sec": beat_times.tolist(),
        "events": events,
        "parts": part_files,
    }


def run_song_pipeline(
    song_path: str | Path,
    output_dir: str | Path,
    *,
    start_time: float = 0.0,
    duration: float | None = None,
    plot: bool = True,
    plot_chunk_sec: float = 8.0,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stems_root_dir = output_dir / "stems"
    separation = separate_to_4stems(song_path=song_path, stems_root_dir=stems_root_dir)
    drums_path = Path(separation["stems"]["drums"])

    drums_analysis = analyze_audio_file(
        audio_path=drums_path,
        output_dir=output_dir,
        start_time=start_time,
        duration=duration,
        plot=plot,
        plot_chunk_sec=plot_chunk_sec,
    )

    return {
        "input_song": str(song_path),
        "drums_stem": str(drums_path),
        "stems": separation["stems"],
        **drums_analysis,
    }
