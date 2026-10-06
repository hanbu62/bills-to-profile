#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / "python"))

DEFAULTS = {"year": 2025, "md_multiplier": 1, "bandwidth": 0.1}

WIDTH = 42


def list_patterns():
    pattern_dir = project_root / "inputs" / "load factor patterns"
    return sorted(p.stem for p in pattern_dir.glob("*.csv"))


def prompt_pattern(patterns, tou_option=False, label="Available load patterns:"):
    print(f"\n{label}")
    print("-" * WIDTH)
    if tou_option:
        print(f"    0. [Generate new profile from TOU ratios]")
    for i, name in enumerate(patterns, 1):
        print(f"  {i:3d}. {name}")
    print("-" * WIDTH)
    n = len(patterns)
    lo = 0 if tou_option else 1
    while True:
        raw = input(f"Select pattern [{lo}-{n}]: ").strip()
        try:
            val = int(raw)
            if tou_option and val == 0:
                return None
            if 1 <= val <= n:
                return patterns[val - 1]
        except ValueError:
            pass
        print(f"  Please enter a number between {lo} and {n}.")


def run_tou_fit(patterns):
    print("\n--- Generate Profile from TOU Ratios ---")
    base = prompt_pattern(patterns, label="Select base pattern to fit:")

    default_name = f"fitted_{base}"
    raw = input(f"\n  Output profile name [{default_name}]: ").strip()
    output_name = raw if raw else default_name

    ratios_path   = str(project_root / "inputs" / "time_of_use_ratios.csv")
    schedule_path = str(project_root / "inputs" / "time_of_use_25-26.csv")
    base_path     = str(project_root / "inputs" / "load factor patterns" / f"{base}.csv")
    output_path   = str(project_root / "inputs" / "load factor patterns" / f"{output_name}.csv")

    print("\n" + "=" * WIDTH)

    import profile_from_tou_ratio as fitter
    fitter.fit_load_profile(
        tou_ratios_path=ratios_path,
        tou_schedule_path=schedule_path,
        base_profile_path=base_path,
        output_path=output_path,
        verbose=True,
    )

    print("=" * WIDTH)
    raw = input(f"\nContinue to generate hourly profile with '{output_name}'? [Y/n]: ").strip().lower()
    if raw in ("", "y"):
        return output_name
    return None


def check_pattern_format(pattern):
    """Return (possibly updated) pattern name after checking for Sat/Sun columns."""
    path = project_root / "inputs" / "load factor patterns" / f"{pattern}.csv"
    df = pd.read_csv(path)
    if "SaturdayLoadFactor" in df.columns:
        return pattern

    print(f"\nPattern '{pattern}' uses a single WeekendLoadFactor for both Saturday and Sunday.")
    print("The TOU schedule distinguishes them — separate factors give more accurate results.")
    print()
    print("  [1] Generate a new Sat/Sun profile  (saves a new CSV, uses it for this run)")
    print("  [2] Use as-is                        (Saturday and Sunday share the same factors)")

    while True:
        raw = input("\nYour choice [1/2]: ").strip()
        if raw == "1":
            break
        if raw == "2":
            return pattern
        print("  Please enter 1 or 2.")

    default_name = f"{pattern}_sat_sun"
    raw = input(f"\n  Output profile name [{default_name}]: ").strip()
    output_name = raw if raw else default_name

    new_df = df.copy()
    new_df["SaturdayLoadFactor"] = new_df["WeekendLoadFactor"]
    new_df["SundayLoadFactor"]   = new_df["WeekendLoadFactor"]
    new_df = new_df.drop(columns=["WeekendLoadFactor"])

    out_path = project_root / "inputs" / "load factor patterns" / f"{output_name}.csv"
    new_df.to_csv(out_path, index=False)
    print(f"  Saved → {out_path}")

    return output_name


def prompt_mode():
    print("\nMode:")
    print("  [1] Simple    — enter a single max demand (kW)")
    print("  [2] Advanced  — use Monthly Demand & Consumption data")
    while True:
        raw = input("\nSelect mode [1/2]: ").strip()
        if raw in ("1", ""):
            return "simple"
        if raw == "2":
            return "advanced"
        print("  Please enter 1 or 2.")


def prompt_float(label, default):
    while True:
        raw = input(f"  {label} [{default}]: ").strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            print("  Invalid — please enter a number.")


def prompt_int(label, default):
    while True:
        raw = input(f"  {label} [{default}]: ").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            print("  Invalid — please enter a whole number.")


def advanced_controls_simple(year, bandwidth):
    print("\n--- Advanced Controls ---")
    year = prompt_int("Year", year)
    bandwidth = prompt_float("Bandwidth", bandwidth)
    return year, bandwidth


def advanced_controls(year, md_mult, bandwidth):
    print("\n--- Advanced Controls ---")
    year = prompt_int("Year", year)
    md_mult = prompt_float("MD Multiplier", md_mult)
    bandwidth = prompt_float("Bandwidth", bandwidth)
    return year, md_mult, bandwidth


def run_simple(pattern):
    year = DEFAULTS["year"]
    bandwidth = DEFAULTS["bandwidth"]

    while True:
        raw = input("\nMax demand (kW): ").strip()
        try:
            max_demand = float(raw)
            if max_demand > 0:
                break
        except ValueError:
            pass
        print("  Please enter a positive number.")

    print(f"\nSelected : {pattern}  (simple)")
    print(f"Settings : max demand={max_demand} kW  |  year={year}  |  bandwidth={bandwidth}")
    print()
    print("  [A] Advanced Controls    (year, bandwidth)")
    print("  [Enter] Run")

    if input("\nYour choice: ").strip().upper() == "A":
        year, bandwidth = advanced_controls_simple(year, bandwidth)
        print(f"\nRunning  : pattern={pattern}  max demand={max_demand} kW  year={year}  bandwidth={bandwidth}")

    print("\n" + "=" * WIDTH)

    import profile_generator as gen
    gen.LOAD_PATTERN = pattern
    gen.MODE = "simple"
    gen.MAX_DEMAND = max_demand
    gen.YEAR = year
    gen.BANDWIDTH = bandwidth
    df = gen.main()
    gen.plot_weekly_comparison(df)


def run_advanced(pattern):
    year = DEFAULTS["year"]
    md_mult = DEFAULTS["md_multiplier"]
    bandwidth = DEFAULTS["bandwidth"]

    print(f"\nSelected : {pattern}  (advanced)")
    print(f"Settings : year={year}  |  MD multiplier={md_mult}  |  bandwidth={bandwidth}")
    print()
    print("  [A] Advanced Controls    (year, MD multiplier, bandwidth)")
    print("  [Enter] Run")

    if input("\nYour choice: ").strip().upper() == "A":
        year, md_mult, bandwidth = advanced_controls(year, md_mult, bandwidth)
        print(f"\nRunning  : pattern={pattern}  year={year}  MD multiplier={md_mult}  bandwidth={bandwidth}")

    print("\n" + "=" * WIDTH)

    import profile_generator as gen
    gen.LOAD_PATTERN = pattern
    gen.MODE = "advanced"
    gen.YEAR = year
    gen.MD_MULTIPLIER = md_mult
    gen.BANDWIDTH = bandwidth
    df = gen.main()
    gen.plot_weekly_comparison(df)


def main():
    patterns = list_patterns()
    if not patterns:
        print("Error: no load pattern files found in inputs/load factor patterns/")
        sys.exit(1)

    print("=" * WIDTH)
    print("  Load Profile Generator")
    print("=" * WIDTH)

    pattern = prompt_pattern(patterns, tou_option=True)

    if pattern is None:
        pattern = run_tou_fit(patterns)
        if pattern is None:
            return

    pattern = check_pattern_format(pattern)

    mode = prompt_mode()

    if mode == "simple":
        run_simple(pattern)
    else:
        run_advanced(pattern)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
