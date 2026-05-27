# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based hourly load profile generator that creates realistic electrical load patterns from monthly billing data. The application processes monthly consumption and demand data along with daily load patterns to generate hour-by-hour load profiles with realistic variability. It also includes tools for fitting profiles to TOU billing ratios and calculating load factors from actual interval data.

## Architecture

The project follows a multi-script architecture with well-defined data flow:

1. **Input Processing** (`read_input_files()`): Reads CSV files from structured input directories
2. **Profile Generation** (`generate_hourly_load_profile()`): Core algorithm that applies load patterns, variability, and scaling
3. **Consumption Scaling** (`apply_monthly_consumption_multipliers()`): Post-processing to ensure hourly sums match monthly consumption targets
4. **TOU Enrichment** (`enrich_data()`): Merges TOU schedule onto the hourly profile, classifying each hour as PK/STD/OP
5. **TOU Summary** (`calculate_time_of_use_ratios()`): Aggregates energy by TOU band per month
6. **Data Export** (`save_load_profile()`): Outputs processed hourly profiles to CSV

### Key Components

- **Main Script**: `python/profile_generator.py` - Main load profile generation with TOU enrichment
- **TOU Profile Fitter**: `python/profile_from_tou_ratio.py` - Fits a load factor profile so TOU energy fractions match billing-derived target ratios (uses scipy optimisation)
- **Load Factor Calculator**: `python/loadfactor_calculator.py` - Derives load factor profiles from actual interval meter data with Plotly visualisation
- **EV Load Script**: `python/fedex_ev_load.py` - Generates FedEx-style EV charging profile with weekday 9pm-6am restrictions (standalone, not called from main script)
- **Input Data Structure**:
  - `inputs/Monthly Consumption.csv` - Monthly energy consumption in kWh
  - `inputs/Monthly Demand.csv` - Monthly peak demand in kW
  - `inputs/time_of_use_25-26.csv` - TOU schedule: columns `['season', 'DayType', 'time', 'TOU']`
  - `inputs/time_of_use_ratios.csv` - Target TOU energy ratios: columns `['period', 'ratio']`
  - `inputs/load factor patterns/*.csv` - 24-hour load patterns with weekday/weekend differentiation
- **Outputs**:
  - `outputs/hourly_load_profile.csv` - Generated hourly load profile
  - `outputs/enriched_load_profile.csv` - Hourly profile with TOU band, season, and time columns added
  - `outputs/tou_summary.csv` - Monthly energy split by TOU band with percentages

### Load Pattern Selection

The script supports multiple predefined load patterns located in `inputs/load factor patterns/`:
- Broadacres.csv
- Default.csv
- Fedex.csv
- Office.csv
- Warehouse.csv
- strip_mall.csv (currently selected)
- abagold_bergsig.csv, abagold_generic.csv, abagold_sulamanzi.csv
- fdx_building1.csv, fdx_building2.csv, fdx_warehouse.csv
- jan-celliers.csv, laerskool-stellenbosch.csv, Mandaryn.csv, Talborne.csv, ValDeVie.csv

Pattern selection is controlled by the `LOAD_PATTERN` variable on line 18.

## Development Commands

### Running the Application
```bash
python run.py
# or directly:
python python/profile_generator.py
```

### Dependencies
- Python 3.12+ (tested with 3.12.4)
- pandas 2.2.2+
- numpy 1.26.4+
- scipy (required by `profile_from_tou_ratio.py`)
- plotly (required by `loadfactor_calculator.py`)

Install dependencies manually as no requirements.txt exists:
```bash
pip install pandas numpy scipy plotly
```

## Configuration

Key parameters can be modified directly in `python/profile generator.py`:

- **Load Pattern**: Change `LOAD_PATTERN` variable (line 18 of `python/profile_generator.py`) - currently set to `"strip_mall"`
- **Demand Multiplier**: Adjust `MD_MULTIPLIER` (line 21) to scale demand values
- **Target Year**: Modify `YEAR` constant (line 22) - currently set to 2025
- **Variability Bandwidth**: Adjust `BANDWIDTH` (line 23) - currently `0.1` (10% random variability)
- **Random Seed**: Fixed at 42 for reproducible results (line 14)

### EV Load Configuration

EV charging parameters in `python/fedex_ev_load.py`:
- **Charging Schedule**: Weekdays only, 9pm-6am (hours 22-23, 0-5)
- **Charger Power**: Each charger assumed to be 5 kW capacity
- **Weekend Charging**: Disabled (no charging on weekends)

## Input File Formats

All CSV files must follow exact column naming:

- **Monthly Consumption.csv**: Columns `['Month', 'Consumption']`
- **Monthly Demand.csv**: Columns `['Month', 'Demand']`
- **Load Pattern files**: Columns `['Hour', 'WeekdayLoadFactor', 'WeekendLoadFactor']`
- **time_of_use_25-26.csv**: Columns `['season', 'DayType', 'time', 'TOU']` — DayType values: `Weekday`, `Sat`, `Sun`; TOU values: `PK`, `STD`, `OP`
- **time_of_use_ratios.csv**: Columns `['period', 'ratio']` — period values: `PK`, `STD`, `OP`

Month names must be 3-letter abbreviations (Jan, Feb, Mar, etc.).

## Output Structure

`hourly_load_profile.csv` includes:
- DateTime, temporal components (Year, Month, Day, Hour)
- Day classification (DayOfWeek, DayType, MonthName)
- Load factors (BaseLoadFactor, LoadFactor with variability)
- Monthly reference values (MonthlyConsumption_kWh, MonthlyDemand_kW)
- Hourly load (HourlyLoad_kW)

`enriched_load_profile.csv` adds TOU columns (TOU, season, time) merged from the TOU schedule.

`tou_summary.csv` shows monthly energy (kWh) split by PK/STD/OP with percentage columns.

## Key Features

- **Weekend/Weekday Differentiation**: Different load patterns for weekdays vs weekends
- **Realistic Variability**: Random variation (controlled by `BANDWIDTH`, default 10%) with bounds checking (0.1–1.0 load factor range)
- **Dual Scaling**: Peak demand is matched first, then a consumption multiplier scales each month's total to match the input kWh
- **TOU Analysis**: Each hour is tagged with its TOU band (PK/STD/OP) and monthly breakdowns are exported
- **TOU Profile Fitting**: `profile_from_tou_ratio.py` uses scipy L-BFGS-B optimisation to reshape a base profile so its TOU energy fractions match billing targets
- **Leap Year Handling**: Proper calculation of days per month including leap years
- **Reproducible Results**: Fixed random seed ensures consistent output
