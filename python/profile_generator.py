#%%
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys
from pathlib import Path

# Get the project root (parent of src/)
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / "python"))

np.random.seed(42)

# ======= SCRIPT CONTROLS ======
# Set load factor file name
LOAD_PATTERN = "strip_mall"

# Applied load factor multiplier
MD_MULTIPLIER = 1
YEAR = 2025
BANDWIDTH = 0.1

# "simple" uses MAX_DEMAND only; "advanced" uses monthly CSV data
MODE = "advanced"
MAX_DEMAND = 100        # kW — used only in simple mode
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


def apply_monthly_consumption_multipliers(df):
    """
    Apply monthly multipliers to ensure hourly loads sum to monthly consumption.

    This post-processing step scales all hourly loads in each month so that
    the total equals the target monthly consumption.
    """
    df_adjusted = df.copy()
    consumption_dict = {}

    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }

    # Build consumption dict from the original input
    consumption_df, _, _ = read_input_files(LOAD_PATTERN)

    for _, row in consumption_df.iterrows():
        month_num = month_map[row["Month"]]
        consumption_dict[month_num] = row["Consumption"]

    # Apply monthly consumption multipliers
    multipliers = []
    for month in range(1, 13):
        month_data = df_adjusted[df_adjusted["Month"] == month]
        if len(month_data) == 0:
            continue

        current_consumption = month_data["HourlyLoad_kW"].sum()
        target_consumption = consumption_dict[month]

        if current_consumption > 0:
            multiplier = target_consumption / current_consumption
        else:
            multiplier = 1.0

        multipliers.append({
            "Month": month,
            "MonthName": month_data.iloc[0]["MonthName"],
            "TargetConsumption_kWh": target_consumption,
            "CalculatedConsumption_kWh": round(current_consumption, 2),
            "Multiplier": round(multiplier, 4),
        })

        # Apply multiplier to all hours in this month
        df_adjusted.loc[df_adjusted["Month"] == month, "HourlyLoad_kW"] = (
            month_data["HourlyLoad_kW"] * multiplier
        ).round(2)

    multipliers_df = pd.DataFrame(multipliers)
    return df_adjusted, multipliers_df

def generate_hourly_load_profile(year=2025, peak_multiplier=1):
    """Generate hourly load profile for the specified year"""
    consumption_df, demand_df, load_pattern_df = read_input_files(LOAD_PATTERN)

    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }

    consumption_dict = {}
    demand_dict = {}

    for _, row in consumption_df.iterrows():
        month_num = month_map[row["Month"]]
        consumption_dict[month_num] = row["Consumption"]

    for _, row in demand_df.iterrows():
        month_num = month_map[row["Month"]]
        demand_dict[month_num] = row["Demand"]

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
        variability = np.random.normal(0, BANDWIDTH * base_load_factor)
        load_factor = max(
            0.1, min(1.0, base_load_factor + variability)
        )  # Ensure load factor stays between 10% and 100%

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
            }
        )

    df = pd.DataFrame(results)

    # Scale each month's loads so peak matches input monthly demand
    for month in range(1, 13):
        month_mask = df["Month"] == month
        month_data = df.loc[month_mask, "HourlyLoad_kW"]

        current_peak = month_data.max()
        target_peak = demand_dict[month]

        if current_peak > 0:
            scale_factor = target_peak / current_peak
            df.loc[month_mask, "HourlyLoad_kW"] = (month_data * scale_factor).round(2)

    # Apply monthly consumption multipliers
    df, multipliers_df = apply_monthly_consumption_multipliers(df)
    # multipliers_df = pd.DataFrame({
    #     "Month": range(1, 13),
    #     "MonthName": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    #     "TargetConsumption_kWh": [0] * 12,
    #     "CalculatedConsumption_kWh": [0] * 12,
    #     "Multiplier": [1.0] * 12,
    # })

    # Calculate some summary statistics
    print(
        (
            f"Load Profile Generated for selected {LOAD_PATTERN} profile in"
            f" {year} (with {BANDWIDTH*100}% random variability, seed=42)"
        )
    )
    print(f"Demand scaled by {peak_multiplier*100:.0f}%")
    print(f"Total Hours: {len(df)}")
    print(f"Total Consumption: {sum(df['HourlyLoad_kW']):.2f} kWh")
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

    print("\nMonthly Verification (after consumption scaling):")
    print(multipliers_df.to_string(index=False))

    # Verify monthly totals
    print("\nMonthly Load Statistics:")
    monthly_summary = (
        df.groupby("Month")
        .agg({
            "HourlyLoad_kW": ["max", "mean", "sum"]
        })
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

def enrich_data(df):
    df = df.copy()

    tou_df = pd.read_csv('./inputs/time_of_use_25-26.csv')
    df.loc[df["DayOfWeek"] == 5, "DayType"] = "Sat"
    df.loc[df["DayOfWeek"] == 6, "DayType"] = "Sun"

    month_season_map = {
        1: "low",
        2: "low",
        3: "low",
        4: "low",
        5: "low",
        6: "high",
        7: "high",
        8: "high",
        9: "low",
        10: "low",
        11: "low",
        12: "low",
    }

    df['season'] = df['Month'].map(month_season_map)
    df['time'] = df['DateTime'].dt.strftime('%H:%M')
    df_merged = df.merge(tou_df, on=['season','DayType', 'time'], how='left')

    return df_merged

def calculate_time_of_use_ratios(df):
    data = df.copy()
    data = enrich_data(data)

    result = data.groupby(['Month', 'TOU'])['HourlyLoad_kW'].sum().reset_index()
    result = result.pivot(index = 'Month', columns = 'TOU', values = 'HourlyLoad_kW')
    result['total'] = result['OP'] + result['PK'] + result['STD']
    result['pk_pct'] = result['PK'] / result['total']
    result['op_pct'] = result['OP'] / result['total']
    result['std_pct'] = result['STD'] / result['total']

    return result

def generate_simple_load_profile(max_demand, year=2025):
    """Generate hourly load profile from a single max demand value and a load pattern."""
    pattern_dir = "./inputs/load factor patterns"
    load_pattern_df = pd.read_csv(os.path.join(pattern_dir, f"{LOAD_PATTERN}.csv"))
    load_pattern_df.columns = load_pattern_df.columns.str.strip()

    weekday_load_pattern = dict(zip(load_pattern_df["Hour"], load_pattern_df["WeekdayLoadFactor"]))
    weekend_load_pattern = dict(zip(load_pattern_df["Hour"], load_pattern_df["WeekendLoadFactor"]))

    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    date_range = pd.date_range(start=start_date, end=end_date, freq="h", inclusive="left")

    results = []
    for dt in date_range:
        hour = dt.hour
        day_of_week = dt.weekday()
        is_weekend = day_of_week >= 5

        if is_weekend:
            base_load_factor = weekend_load_pattern[hour]
            day_type = "Weekend"
        else:
            base_load_factor = weekday_load_pattern[hour]
            day_type = "Weekday"

        variability = np.random.normal(0, BANDWIDTH * base_load_factor)
        load_factor = max(0.1, min(1.0, base_load_factor + variability))
        hourly_load = max_demand * load_factor

        results.append({
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
            "MonthlyConsumption_kWh": 0,
            "MonthlyDemand_kW": max_demand,
            "HourlyLoad_kW": round(hourly_load, 2),
        })

    df = pd.DataFrame(results)

    print(f"Simple Load Profile Generated for {LOAD_PATTERN} pattern in {year}")
    print(f"Max Demand: {max_demand:.0f} kW  |  Bandwidth: {BANDWIDTH*100:.0f}%  |  seed=42")
    print(f"Total Hours: {len(df)}")
    print(f"Total Consumption: {df['HourlyLoad_kW'].sum():.2f} kWh")
    print(f"Peak Load: {df['HourlyLoad_kW'].max():.2f} kW")
    print(f"Minimum Load: {df['HourlyLoad_kW'].min():.2f} kW")
    print(f"Average Load: {df['HourlyLoad_kW'].mean():.2f} kW")

    return df


def plot_weekly_comparison(df):
    """Plot one representative week in summer (Jan) and winter (Jul) on the same axis."""
    import matplotlib.pyplot as plt

    # DayOfWeek 6 = Sunday (pandas Monday=0 convention)
    summer_start = df[(df["Month"] == 1) & (df["DayOfWeek"] == 6)]["DateTime"].iloc[0]
    winter_start = df[(df["Month"] == 7) & (df["DayOfWeek"] == 6)]["DateTime"].iloc[0]

    summer_week = df[
        (df["DateTime"] >= summer_start) &
        (df["DateTime"] < summer_start + pd.Timedelta(days=7))
    ]["HourlyLoad_kW"].values

    winter_week = df[
        (df["DateTime"] >= winter_start) &
        (df["DateTime"] < winter_start + pd.Timedelta(days=7))
    ]["HourlyLoad_kW"].values

    hours = range(len(summer_week))
    day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(hours, winter_week, color="steelblue", label="Winter (Jul)", linewidth=1.5)
    ax.plot(hours, summer_week, color="darkorange", label="Summer (Jan)", linewidth=1.5)

    for d in range(7):
        ax.axvline(x=d * 24, color="gray", linestyle="--", linewidth=0.5, alpha=0.4)

    ax.set_xticks([d * 24 + 12 for d in range(7)])
    ax.set_xticklabels(day_labels)
    ax.set_ylabel("Load (kW)")
    ax.set_title(f"Weekly Load Profile — {LOAD_PATTERN}")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()

    output_path = "./outputs/weekly_comparison.png"
    plt.savefig(output_path, dpi=150)
    print(f"Weekly comparison chart saved to {output_path}")
    plt.show()


def main():
    """Main function to generate and save the hourly load profile"""
    try:
        if MODE == "simple":
            load_profile_df = generate_simple_load_profile(MAX_DEMAND, YEAR)
        else:
            load_profile_df = generate_hourly_load_profile(
                YEAR, peak_multiplier=MD_MULTIPLIER
            )

        save_load_profile(load_profile_df)

        enrich_data(load_profile_df).to_csv('./outputs/enriched_load_profile.csv')

        tou_summary = calculate_time_of_use_ratios(load_profile_df)
        print(tou_summary.sum(numeric_only=True))
        tou_summary.to_csv('./outputs/tou_summary.csv')



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
            variability_pct = (
                (row["LoadFactor"] - row["BaseLoadFactor"]) / row["BaseLoadFactor"]
            ) * 100
            print(
                f"Hour {row['Hour']:2d} ({row['DayType']}): Base={row['BaseLoadFactor']:.3f}, Actual={row['LoadFactor']:.4f} ({variability_pct:+.1f}%)"
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
            f"{LOAD_PATTERN}.csv (with columns: Hour, WeekdayLoadFactor, WeekendLoadFactor)"
        )
        print(f"Specific error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return load_profile_df

#%%
if __name__ == "__main__":
    df = main()
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df = df.set_index('DateTime')
    df.plot(y='HourlyLoad_kW')
# %%
