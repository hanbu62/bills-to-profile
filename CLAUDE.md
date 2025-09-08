# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based hourly load profile generator that creates realistic electrical load patterns from monthly billing data. The application processes monthly consumption and demand data along with daily load patterns to generate hour-by-hour load profiles with realistic variability.

## Architecture

The project follows a simple single-script architecture with well-defined data flow:

1. **Input Processing** (`read_input_files()`): Reads CSV files from structured input directories
2. **Profile Generation** (`generate_hourly_load_profile()`): Core algorithm that applies load patterns, variability, and scaling
3. **Data Export** (`save_load_profile()`): Outputs processed hourly profiles to CSV

### Key Components

- **Main Script**: `Python/profile generator.py` - Contains all functionality in a single, well-documented file
- **Input Data Structure**:
  - `Inputs/Monthly Consumption.csv` - Monthly energy consumption in kWh
  - `Inputs/Monthly Demand.csv` - Monthly peak demand in kW  
  - `Inputs/load factor patterns/*.csv` - 24-hour load patterns with weekday/weekend differentiation
- **Output**: `Outputs/hourly_load_profile.csv` - Generated hourly load profile

### Load Pattern Selection

The script supports multiple predefined load patterns located in `Inputs/load factor patterns/`:
- Broadacres.csv (currently selected)
- Default.csv
- Fedex.csv
- Office.csv
- Strip_Mall.csv

Pattern selection is controlled by the `load_pattern` variable on line 55.

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

Key parameters can be modified directly in the script:

- **Load Pattern**: Change `load_pattern` variable (line 55)
- **Peak Multiplier**: Adjust `peak_multiplier` (line 58) to scale demand values
- **Target Year**: Modify year parameter in `main()` function (line 258)
- **Random Seed**: Fixed at 42 for reproducible results (line 51)
- **Variability**: 2% random variability applied to load factors (line 152)

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