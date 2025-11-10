# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based hourly load profile generator that creates realistic electrical load patterns from monthly billing data. The application processes monthly consumption and demand data along with daily load patterns to generate hour-by-hour load profiles with realistic variability. It also includes functionality to add a complementary EV charging load profile.

## Architecture

The project follows a dual-script architecture with well-defined data flow:

1. **Input Processing** (`read_input_files()`): Reads CSV files from structured input directories
2. **Profile Generation** (`generate_hourly_load_profile()`): Core algorithm that applies load patterns, variability, and scaling
3. **EV Load Generation** (`create_ev_load()`): Creates complementary EV charging load profile with FedEx-style restrictions
4. **Data Export** (`save_load_profile()`): Outputs processed hourly profiles to CSV

### Key Components

- **Main Script**: `Python/profile generator.py` - Main load profile generation with EV load integration
- **EV Load Script**: `Python/fedex_ev_load.py` - Generates FedEx-style EV charging profile with weekday 9pm-6am restrictions
- **Input Data Structure**:
  - `inputs/Monthly Consumption.csv` - Monthly energy consumption in kWh
  - `inputs/Monthly Demand.csv` - Monthly peak demand in kW  
  - `inputs/load factor patterns/*.csv` - 24-hour load patterns with weekday/weekend differentiation
- **Output**: `outputs/hourly_load_profile.csv` - Generated hourly load profile

### Load Pattern Selection

The script supports multiple predefined load patterns located in `inputs/load factor patterns/`:
- Broadacres.csv
- Default.csv
- Fedex.csv (currently selected)
- Office.csv
- Strip_Mall.csv

Pattern selection is controlled by the `load_pattern` variable on line 57.

## Development Commands

### Running the Application
```bash
python "Python/profile generator.py"
```

### Dependencies
- Python 3.12+ (tested with 3.12.4)
- pandas 2.2.2+
- numpy 1.26.4+

Install dependencies manually as no requirements.txt exists:
```bash
pip install pandas numpy
```

## Configuration

Key parameters can be modified directly in `Python/profile generator.py`:

- **Load Pattern**: Change `load_pattern` variable (line 57) - currently set to "Fedex"
- **Peak Multiplier**: Adjust `peak_multiplier` (line 62) to scale demand values
- **Target Year**: Modify `YEAR` constant (line 64) - currently set to 2025
- **Number of EV Chargers**: Adjust `NUM_CHARGERS` constant (line 66) - currently set to 15
- **Random Seed**: Fixed at 42 for reproducible results (line 52)
- **Variability**: 2% random variability applied to load factors

### EV Load Configuration

EV charging parameters in `Python/fedex_ev_load.py`:
- **Charging Schedule**: Weekdays only, 9pm-6am (hours 22-23, 0-5)
- **Charger Power**: Each charger assumed to be 5 kW capacity
- **Weekend Charging**: Disabled (no charging on weekends)

## Input File Formats

All CSV files must follow exact column naming:

- **Monthly Consumption.csv**: Columns `['Month', 'Consumption']`
- **Monthly Demand.csv**: Columns `['Month', 'Demand']`  
- **Load Pattern files**: Columns `['Hour', 'WeekdayLoadFactor', 'WeekendLoadFactor']`

Month names must be 3-letter abbreviations (Jan, Feb, Mar, etc.).

## Output Structure

Generated CSV includes comprehensive hourly data:
- DateTime, temporal components (Year, Month, Day, Hour)
- Day classification (DayOfWeek, DayType)
- Load factors (BaseLoadFactor, LoadFactor with variability)
- Consumption and demand values (kWh, kW)

## Key Features

- **Weekend/Weekday Differentiation**: Different load patterns for weekdays vs weekends
- **Realistic Variability**: ±2% random variation with bounds checking (0.1-1.0 load factor range)
- **Leap Year Handling**: Proper calculation of days per month including leap years
- **Comprehensive Validation**: Built-in verification and summary statistics
- **Reproducible Results**: Fixed random seed ensures consistent output