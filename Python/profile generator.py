"""
Hourly Load Profile Generator Based on Billing Data

Updates:
- 13/06/2025: Initial version with 2% random variability and reproducible seed.
- 13/06/2025: Added load factor bounds (0.1 to 1.0) to ensure realistic values.
- 24/06/2025: Added weekend vs weekday load factor differentiation.
- 24/06/2025: Added load pattern selection

##############################################################################

This script generates an hourly load profile on monthly consumption, demand
data, and daily load patterns. The script applies realistic variability and
differentiates between weekday and weekend patterns.

Steps performed:
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

Input CSV file formats:
- Monthly Consumption.csv: Columns ['Month', 'Consumption']
- Monthly Demand.csv: Columns ['Month', 'Demand']
- Load pattern.csv: Columns ['Hour', 'WeekdayLoadFactor', 'WeekendLoadFactor']

Notes:
- Load factors represent the percentage of monthly peak demand for each hour
- Weekend patterns typically show different consumption behaviors than weekdays
- Random variability (±2%) simulates real-world load fluctuations
- All power values are in kilowatts (kW) and energy values in kilowatt-hours (kWh)
- The script uses reproducible randomness (seed=42) for consistent results
- Output includes both base and adjusted load factors for analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from fedex_ev_load import create_ev_load 

# Set random seed for reproducible results
np.random.seed(42)


# ======= SCRIPT CONTROLS ======
# Set load factor file name
load_pattern = "Fedex"
# load_pattern = "Broadacres"

# Applied load factor multiplier
# peak_multiplier = 80 / 130 # For Broadacres
peak_multiplier = 1 

YEAR = 2025

NUM_CHARGERS = 20
# ==============================




def read_input_files(load_pattern="Default"):
    """Read the input CSV files from the input directory"""
    input_dir = "./inputs"
    pattern_dir = "./inputs/load factor patterns"

    # Read monthly consumption data
    consumption_df = pd.read_csv(os.path.join(input_dir, "Monthly Consumption.csv"))
    consumption_df.columns = consumption_df.columns.str.strip()  # Remove whitespace

    # Read monthly demand data
    demand_df = pd.read_csv(os.path.join(input_dir, "Monthly Demand.csv"))
    demand_df.columns = demand_df.columns.str.strip()  # Remove whitespace

    # Read load pattern data
    load_pattern_df = pd.read_csv(os.path.join(pattern_dir, f"{load_pattern}.csv"))
    load_pattern_df.columns = load_pattern_df.columns.str.strip()  # Remove whitespace

    return consumption_df, demand_df, load_pattern_df


def generate_hourly_load_profile(year=2025, peak_multiplier=1):
    """Generate hourly load profile for the specified year"""

    # Read input data
    consumption_df, demand_df, load_pattern_df = read_input_files(load_pattern)

    # Create month mapping
    month_map = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }

    # Convert month names to numbers and create dictionaries
    consumption_dict = {}
    demand_dict = {}

    for _, row in consumption_df.iterrows():
        month_num = month_map[row["Month"]]
        consumption_dict[month_num] = row["Consumption"]

    for _, row in demand_df.iterrows():
        month_num = month_map[row["Month"]]
        demand_dict[month_num] = row["Demand"]

    # Create load pattern dictionaries for weekday and weekend
    weekday_load_pattern = dict(
        zip(load_pattern_df["Hour"], load_pattern_df["WeekdayLoadFactor"])
    )
    weekend_load_pattern = dict(
        zip(load_pattern_df["Hour"], load_pattern_df["WeekendLoadFactor"])
    )

    # Generate date range for the year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    date_range = pd.date_range(
        start=start_date, end=end_date, freq="h", inclusive="left"
    )

    # Initialize results list
    results = []

    for dt in date_range:
        month = dt.month
        hour = dt.hour
        day_of_week = dt.weekday()  # Monday=0, Sunday=6
        is_weekend = day_of_week >= 5  # Saturday=5, Sunday=6

        # Get monthly values
        monthly_consumption = consumption_dict[month]  # kWh for the month
        monthly_demand = demand_dict[month]  # kW peak demand

        # Get hourly load factor based on weekday/weekend
        if is_weekend:
            base_load_factor = weekend_load_pattern[hour]
            day_type = "Weekend"
        else:
            base_load_factor = weekday_load_pattern[hour]
            day_type = "Weekday"

        # Apply random variability: ±2% of the base load factor
        variability = np.random.normal(0, 0.02 * base_load_factor)
        load_factor = max(
            0.1, min(1.0, base_load_factor + variability)
        )  # Ensure load factor stays between 10% and 100%

        # Calculate days in month
        if month == 2:  # February
            days_in_month = (
                29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
            )
        elif month in [4, 6, 9, 11]:
            days_in_month = 30
        else:
            days_in_month = 31

        # Calculate average hourly consumption for the month
        # Monthly consumption / (days in month * 24 hours)
        # avg_hourly_consumption = monthly_consumption / (days_in_month * 24)

        # Calculate hourly load based on peak demand scaled by load pattern
        hourly_load = monthly_demand * load_factor * peak_multiplier

        # Store result
        results.append(
            {
                "DateTime": dt,
                "Year": dt.year,
                "Month": dt.month,
                "Day": dt.day,
                "Hour": dt.hour,
                "DayOfWeek": day_of_week,
                "DayType": day_type,
                "MonthName": dt.strftime("%b"),
                "BaseLoadFactor": base_load_factor,
                "LoadFactor": round(load_factor, 4),
                "MonthlyConsumption_kWh": monthly_consumption,
                "MonthlyDemand_kW": monthly_demand,
                "HourlyLoad_kW": round(hourly_load, 2),
                "HourlyConsumption_kWh": round(
                    hourly_load, 2
                ),  # For hourly data, kW = kWh
            }
        )

    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Add EV load
    charger_df = create_ev_load(YEAR,NUM_CHARGERS)
    df['charger_load'] = charger_df['ev_power']
    df['combined_load'] = df['charger_load']+df['HourlyLoad_kW']

    # Calculate some summary statistics
    print(
        (
            f"Load Profile Generated for selected {load_pattern} profile in"
            f" {year} (with 2% random variability, seed=42)"
        )
    )
    print(f"Demand scaled by {peak_multiplier*100} %")
    print(f"Total Hours: {len(df)}")
    print(f"Total Consumption: {sum(df['HourlyLoad_kW'])}")
    print(f"Peak Load: {df['HourlyLoad_kW'].max():.2f} kW")
    print(f"Minimum Load: {df['HourlyLoad_kW'].min():.2f} kW")
    print(f"Average Load: {df['HourlyLoad_kW'].mean():.2f} kW")
    print(
        f"Load Factor Range: {df['LoadFactor'].min():.4f} to {df['LoadFactor'].max():.4f}"
    )

    # Weekday vs Weekend statistics
    print("\nWeekday vs Weekend Statistics:")
    day_type_stats = (
        df.groupby("DayType")
        .agg(
            {
                "HourlyLoad_kW": ["mean", "max", "min"],
                "LoadFactor": ["mean", "max", "min"],
            }
        )
        .round(3)
    )
    print(day_type_stats)

    # Verify monthly totals
    print("\nMonthly Verification:")
    monthly_summary = (
        df.groupby("Month")
        .agg({"HourlyLoad_kW": ["max", "mean"], "HourlyConsumption_kWh": "sum"})
        .round(2)
    )

    monthly_summary.columns = ["Peak_Load_kW", "Avg_Load_kW", "Total_Consumption_kWh"]
    print(monthly_summary)

    return df


def save_load_profile(df, filename="./outputs/hourly_load_profile.csv"):
    """Save the load profile to a CSV file"""
    # Ensure output directory exists
    os.makedirs("./outputs", exist_ok=True)

    df.to_csv(filename, index=False)
    print(f"\nLoad profile saved to: {filename}")


def main():
    """Main function to generate and save the hourly load profile"""
    try:
        # Generate hourly load profile
        load_profile_df = generate_hourly_load_profile(
            YEAR, peak_multiplier=peak_multiplier
        )

        # Save to CSV
        save_load_profile(load_profile_df)

        # Display first few rows
        print("\nFirst 24 hours of load profile:")
        print(
            load_profile_df.head(24)[
                [
                    "DateTime",
                    "Hour",
                    "DayType",
                    "BaseLoadFactor",
                    "LoadFactor",
                    "HourlyLoad_kW",
                ]
            ]
        )

        # Show variability examples
        print("\nVariability Examples:")
        sample_hours = load_profile_df.head(24)
        for i in range(0, 24, 6):
            row = sample_hours.iloc[i]
            variability_loadfactor = (
                (row["LoadFactor"] - row["BaseLoadFactor"]) / row["BaseLoadFactor"]
            ) * 100
            print(
                f"Hour {row['Hour']:2d} ({row['DayType']}): Base={row['BaseLoadFactor']:.3f}, Actual={row['LoadFactor']:.4f} ({variability_loadfactor:+.1f}%)"
            )

        # Display peak load hours
        peak_idx = load_profile_df["HourlyLoad_kW"].idxmax()
        min_idx = load_profile_df["HourlyLoad_kW"].idxmin()

        print(f"\nPeak load: {load_profile_df.loc[peak_idx, 'HourlyLoad_kW']:.2f} kW")
        print(
            f"Occurs at: {load_profile_df.loc[peak_idx, 'DateTime']} (Hour {load_profile_df.loc[peak_idx, 'Hour']}, {load_profile_df.loc[peak_idx, 'DayType']})"
        )

        print(f"\nMinimum load: {load_profile_df.loc[min_idx, 'HourlyLoad_kW']:.2f} kW")
        print(
            f"Occurs at: {load_profile_df.loc[min_idx, 'DateTime']} (Hour {load_profile_df.loc[min_idx, 'Hour']}, {load_profile_df.loc[min_idx, 'DayType']})"
        )

    except FileNotFoundError as e:
        print(
            "Error: Could not find input files. Please ensure the following files exist in './inputs/' directory:"
        )
        print("Monthly Consumption.csv")
        print("Monthly Demand.csv")
        print(
            f"{load_pattern}.csv (with columns: Hour, WeekdayLoadFactor, WeekendLoadFactor)"
        )
        print(f"Specific error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()

# %%
