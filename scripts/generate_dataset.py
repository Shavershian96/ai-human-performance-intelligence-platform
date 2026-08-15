"""Generate the synthetic training dataset in data/sample_data.csv.

THE DATA THIS PRODUCES IS SYNTHETIC. It is not measured from real athletes and
must not be read as evidence about human physiology. It exists so the platform
has a dataset large enough for the model's metrics to mean something, and so
anyone cloning the repo can reproduce those metrics exactly.

The generator is deliberately not random noise: it encodes relationships taken
from training-load literature, so a model has real structure to recover rather
than memorising noise.

  - Load follows a weekly hard/easy pattern inside 3-week build blocks with a
    recovery week, which is how periodised training is usually scheduled.
  - Acute (7-day) and chronic (28-day) exponentially weighted loads give an
    acute:chronic workload ratio. Performance responds to ACWR as an inverted
    U: undertraining and spikes both cost, a ratio near 1.0 is best. This is
    the one genuinely non-linear relationship in the data.
  - Sleep, stress, resting heart rate and HRV are driven by recent load plus a
    per-athlete baseline, so the features are correlated the way real wearable
    data is - a model cannot treat them as independent.
  - Athletes differ in fitness, sleep need and cardiac baselines, so there is
    between-subject variance rather than one curve with noise.

Performance is a documented function of those latent factors plus Gaussian
noise, so there is an irreducible error floor: an honest model should land
short of R^2 = 1, and a suspiciously perfect score would indicate leakage.

Usage:
    python scripts/generate_dataset.py [--athletes N] [--days N] [--seed N]
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "sample_data.csv"
START = date(2025, 1, 6)  # a Monday, so the weekly pattern lines up

# Noise added to the latent performance score, in score points. Sets the error
# floor the model cannot beat.
PERFORMANCE_NOISE_SD = 3.5


def _clip(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return np.clip(x, lo, hi)


def _ewma(values: list[float], span: int) -> float:
    """Exponentially weighted mean of the history, most recent weighted most."""
    if not values:
        return 0.0
    alpha = 2.0 / (span + 1.0)
    out = values[0]
    for v in values[1:]:
        out = alpha * v + (1 - alpha) * out
    return out


def _athlete_rows(rng: np.random.Generator, athlete_id: str, days: int) -> list[dict]:
    # Per-athlete traits: between-subject variance.
    fitness = rng.normal(0.0, 1.0)
    sleep_need = rng.normal(7.6, 0.45)
    rhr_base = rng.normal(57.0, 4.5)
    hrv_base = rng.normal(68.0, 9.0)
    load_scale = rng.normal(1.0, 0.15)

    history: list[float] = []
    rows: list[dict] = []

    for day in range(days):
        week = day // 7
        dow = day % 7
        # 3 build weeks then a recovery week.
        block_factor = 0.62 if week % 4 == 3 else 1.0 + 0.05 * (week % 4)
        # Hard/easy alternation, Sunday off.
        dow_factor = [1.15, 0.55, 1.0, 0.6, 1.2, 0.85, 0.15][dow]

        load = 250.0 * block_factor * dow_factor * load_scale * rng.normal(1.0, 0.12)
        load = float(np.clip(load, 0.0, 600.0))

        acute = _ewma(history[-7:], 7)
        chronic = _ewma(history[-28:], 28)
        acwr = acute / chronic if chronic > 20 else 1.0
        acwr = float(np.clip(acwr, 0.4, 2.0))

        # Recent load and life stress push sleep and stress around.
        life_stress = rng.normal(0.0, 1.0)
        stress = 4.4 + 1.5 * (acwr - 1.0) + 0.9 * life_stress + 0.004 * (acute - 200)
        stress = float(np.clip(stress, 1.0, 10.0))

        sleep_hours = sleep_need - 0.22 * (stress - 4.4) + rng.normal(0.0, 0.55)
        sleep_hours = float(np.clip(sleep_hours, 4.0, 10.0))

        sleep_quality = 5.6 + 1.25 * (sleep_hours - sleep_need) - 0.42 * (stress - 4.4)
        sleep_quality = float(np.clip(sleep_quality + rng.normal(0.0, 0.6), 1.0, 10.0))

        # Cardiac markers respond to load and sleep debt.
        rhr = rhr_base + 0.022 * (acute - 200) + 0.9 * (stress - 4.4)
        rhr -= 0.8 * (sleep_hours - sleep_need)
        rhr = float(np.clip(rhr + rng.normal(0.0, 1.6), 30.0, 120.0))

        hrv = hrv_base - 0.030 * (acute - 200) - 2.1 * (stress - 4.4)
        hrv += 2.4 * (sleep_hours - sleep_need) + 4.5 * fitness
        hrv = float(np.clip(hrv + rng.normal(0.0, 3.5), 10.0, 160.0))

        recovery = 5.5 + 0.62 * (sleep_quality - 5.6) - 0.55 * (stress - 4.4)
        recovery += 0.028 * (hrv - hrv_base) - 0.055 * (rhr - rhr_base)
        recovery = float(np.clip(recovery + rng.normal(0.0, 0.5), 1.0, 10.0))

        # Latent performance. The ACWR term is the inverted U.
        acwr_penalty = -18.0 * (acwr - 1.0) ** 2
        perf = (
            72.0
            + 4.8 * fitness
            + 1.9 * (recovery - 5.5)
            + 1.15 * (sleep_quality - 5.6)
            + 0.9 * (sleep_hours - sleep_need)
            - 1.05 * (stress - 4.4)
            + 0.055 * (hrv - hrv_base)
            + acwr_penalty
            + 0.004 * chronic  # accumulated fitness from consistent training
        )
        perf = float(np.clip(perf + rng.normal(0.0, PERFORMANCE_NOISE_SD), 0.0, 100.0))

        history.append(load)
        rows.append(
            {
                "athlete_id": athlete_id,
                "record_date": (START + timedelta(days=day)).isoformat(),
                "sleep_hours": round(sleep_hours, 2),
                "sleep_quality": round(sleep_quality, 1),
                "training_load": round(load, 1),
                "stress_level": round(stress, 1),
                "recovery_score": round(recovery, 1),
                "resting_heart_rate": round(rhr, 1),
                "hrv": round(hrv, 1),
                "performance_score": round(perf, 2),
            }
        )

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--athletes", type=int, default=40)
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    rows: list[dict] = []
    for i in range(1, args.athletes + 1):
        rows.extend(_athlete_rows(rng, f"athlete_{i:03d}", args.days))

    df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)

    print(f"wrote {args.out}")
    print(f"  {len(df):,} rows, {df['athlete_id'].nunique()} athletes, {args.days} days each")
    print(f"  performance_score: mean {df.performance_score.mean():.1f}, "
          f"sd {df.performance_score.std():.1f}, "
          f"range {df.performance_score.min():.1f}-{df.performance_score.max():.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
