# Bills to Profile

Generates an hourly electrical load profile from monthly billing data.

## Quick Start

```bash
conda activate python-312-env
python run.py
```

The interactive launcher will prompt you for:
1. **Load pattern** — pick from the numbered list (e.g. `strip_mall`, `Office`, `Warehouse`)
2. **Mode** — Simple or Advanced
3. Optionally press `A` to tweak advanced controls before running

## Modes

### Simple
Enter a single max demand (kW). No CSV input required — useful for quick estimates.

### Advanced
Reads monthly data from `inputs/`:
- `Monthly Consumption.csv` — columns: `Month, Consumption` (kWh)
- `Monthly Demand.csv` — columns: `Month, Demand` (kW)
- Month names must be 3-letter abbreviations: `Jan, Feb, Mar …`

## Advanced Controls

| Parameter | Default | Effect |
|---|---|---|
| Year | 2025 | Target year for the profile |
| MD Multiplier | 1 | Scales all demand values up/down |
| Bandwidth | 0.1 | Random variability ±10% per hour |

## Outputs

Written to `outputs/`:
- `hourly_load_profile.csv` — 8760 rows of hourly kW with datetime and load factor columns
- `enriched_load_profile.csv` — above + TOU band (PK/STD/OP), season, and time columns
- `tou_summary.csv` — monthly energy split by TOU band with percentages

A weekly comparison chart also opens in the browser after each run.

## Load Patterns

CSV files in `inputs/load factor patterns/` with columns `Hour, WeekdayLoadFactor, WeekendLoadFactor`.

Available patterns: `Broadacres`, `Default`, `Fedex`, `Office`, `Warehouse`, `strip_mall`, `abagold_bergsig`, `abagold_generic`, `abagold_sulamanzi`, `fdx_building1`, `fdx_building2`, `fdx_warehouse`, `jan-celliers`, `laerskool-stellenbosch`, `Mandaryn`, `Talborne`, `ValDeVie`

## Other Scripts

| Script | Purpose |
|---|---|
| `python/profile_from_tou_ratio.py` | Optimises a profile so TOU energy fractions match billing targets (`inputs/time_of_use_ratios.csv`) |
| `python/loadfactor_calculator.py` | Derives load factor patterns from actual interval meter data (outputs Plotly charts) |
| `python/fedex_ev_load.py` | Generates a FedEx-style EV charging profile (weekday 9 pm–6 am only) |

## Dependencies

```bash
pip install pandas numpy scipy plotly
```
