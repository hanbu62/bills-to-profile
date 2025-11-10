# Hourly Load Profile Generator Based on Billing Data

## Updates:
- 13/06/2025: Initial version with 2% random variability and reproducible seed.
- 13/06/2025: Added load factor bounds (0.1 to 1.0) to ensure realistic values.
- 24/06/2025: Added weekend vs weekday load factor differentiation.
- 24/06/2025: Added load pattern selection
- 06/11/2025: Added monthly consumption multiplier to ensure energy totals match
- 06/11/2025: Improved load factor bounds (clamp after variability only)
- 06/11/2025: Removed EV charger functionality


##############################################################################

This script generates an hourly load profile on monthly consumption, demand
data, and daily load patterns. The script applies realistic variability and
differentiates between weekday and weekend patterns.

## Steps performed:
1. Load input data from CSV files in the './inputs/' directory:
    - 'Monthly Consumption.csv': Monthly energy consumption (kWh)
    - 'Monthly Demand.csv': Monthly peak demand (kW)
    - Load factor pattern selected from './inputs/load factor patterns':
        - 'Load pattern.csv': 24-hour load patterns with weekday and weekend
            factors
2. Generate hourly timestamps for the specified year
3. Apply monthly consumption and demand values to each hour
4. Apply daily load patterns with weekend/weekday differentiation
5. Add 2% random variability to load factors (with reproducible seed=42)
6. Ensure load factors remain within realistic bounds (0.1 to 1.0)
7. Calculate hourly loads based on monthly peak demand scaled by load factors
8. Export results to './outputs/hourly_load_profile.csv'

## Input CSV file formats:
- Monthly Consumption.csv: Columns ['Month', 'Consumption']
- Monthly Demand.csv: Columns ['Month', 'Demand']
- Load pattern.csv: Columns ['Hour', 'WeekdayLoadFactor', 'WeekendLoadFactor']

## Notes:
- Load factors represent the percentage of monthly peak demand for each hour
- Weekend patterns typically show different consumption behaviors than weekdays
- Random variability (±2%) simulates real-world load fluctuations
- All power values are in kilowatts (kW) and energy values in kilowatt-hours (kWh)
- The script uses reproducible randomness (seed=42) for consistent results
- Output includes both base and adjusted load factors for analysis
