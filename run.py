#!/usr/bin/env python3
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / "python"))

DEFAULTS = {"year": 2025, "md_multiplier": 1, "bandwidth": 0.1}

WIDTH = 42


def list_patterns():
    pattern_dir = project_root / "inputs" / "load factor patterns"
    return sorted(p.stem for p in pattern_dir.glob("*.csv"))


def prompt_pattern(patterns):
    print("\nAvailable load patterns:")
    print("-" * WIDTH)
    for i, name in enumerate(patterns, 1):
        print(f"  {i:3d}. {name}")
    print("-" * WIDTH)
    n = len(patterns)
    while True:
        raw = input(f"Select pattern [1-{n}]: ").strip()
        try:
            val = int(raw)
            if 1 <= val <= n:
                return patterns[val - 1]
        except ValueError:
            pass
        print(f"  Please enter a number between 1 and {n}.")


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

    pattern = prompt_pattern(patterns)
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
