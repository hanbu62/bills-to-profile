"""
Debug script to break down the hourly load formula into component parts.
Creates a dataframe showing each variable in the calculation.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# Set random seed for reproducible results
np.random.seed(42)

# ======= SCRIPT CONTROLS ======
LOAD_PATTERN = "Broadacres"
MD_MULTIPLIER = 1 
YEAR = 2025
# ==============================


def read_input_files(load_pattern="Default"):
    """Read the input CSV files from the input directory"""
    input_dir = "./inputs"
    pattern_dir = "./inputs/load factor patterns"

    consumption_df = pd.read_csv(os.path.join(input_dir, "Monthly Consumption.csv"))
    consumption_df.columns = consumption_df.columns.str.strip()

    demand_df = pd.read_csv(os.path.join(input_dir, "Monthly Demand.csv"))
    demand_df.columns = demand_df.columns.str.strip()

    load_pattern_df = pd.read_csv(os.path.join(pattern_dir, f"{load_pattern}.csv"))
    load_pattern_df.columns = load_pattern_df.columns.str.strip()

    return consumption_df, demand_df, load_pattern_df


def main():
    consumption_df, demand_df, load_pattern_df = read_input_files(LOAD_PATTERN)

    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }

    demand_dict = {}
    for _, row in demand_df.iterrows():
        month_num = month_map[row["Month"]]
        demand_dict[month_num] = row["Demand"]

    # Calculate monthly demand multipliers
    max_demand = demand_df["Demand"].max()
    monthly_demand_multipliers = {
        month_num: max_demand / demand_dict[month_num] 
        for month_num in range(1, 13)
    }

    weekday_load_pattern = dict(
        zip(load_pattern_df["Hour"], load_pattern_df["WeekdayLoadFactor"])
    )
    weekend_load_pattern = dict(
        zip(load_pattern_df["Hour"], load_pattern_df["WeekendLoadFactor"])
    )

    # Generate date range for the year
    start_date = datetime(YEAR, 1, 1)
    end_date = datetime(YEAR + 1, 1, 1)
    date_range = pd.date_range(
        start=start_date, end=end_date, freq="h", inclusive="left"
    )

    # Initialize results list
    results = []

    for dt in date_range:
        month = dt.month
        hour = dt.hour
        day_of_week = dt.weekday()
        is_weekend = day_of_week >= 5

        monthly_demand = demand_dict[month]

        if is_weekend:
            base_load_factor = weekend_load_pattern[hour]
        else:
            base_load_factor = weekday_load_pattern[hour]

        variability = np.random.normal(0, 0.02 * base_load_factor)
        load_factor = max(0.1, min(1.0, base_load_factor + variability))

        monthly_multiplier = monthly_demand_multipliers[month]
        peak_multiplier = MD_MULTIPLIER

        hourly_load = (
            monthly_demand
            * load_factor
            * monthly_multiplier
            * peak_multiplier
        )

        results.append({
            "DateTime": dt,
            "Month": month,
            "Hour": hour,
            "monthly_demand": round(monthly_demand, 2),
            "load_factor": round(load_factor, 4),
            "monthly_multiplier": round(monthly_multiplier, 4),
            "peak_multiplier": peak_multiplier,
            "hourly_load": round(hourly_load, 2),
        })

    df = pd.DataFrame(results)
    
    # Save to CSV
    os.makedirs("./outputs", exist_ok=True)
    df.to_csv("./outputs/load_profile_debug.csv", index=False)
    print("Debug dataframe saved to: ./outputs/load_profile_debug.csv")
    
    # Print sample rows
    print("\nFirst 24 hours:")
    print(df.head(24))
    
    print("\nFebruary sample (month 2):")
    print(df[df["Month"] == 2].head(24))
    
    print("\nPeak loads by month:")
    peak_by_month = df.groupby("Month")["hourly_load"].max()
    print(peak_by_month)


if __name__ == "__main__":
    main()