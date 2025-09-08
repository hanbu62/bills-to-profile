"""This script generates a complimentary load profile based on a selected
schedule and number of electric vehicle chargers.

Creates an hourly load profile for EV charging at a FedEx-style facility with
charging restricted to weekdays between 9pm and 6am only. No charging occurs
on weekends or during business hours (6am-9pm weekdays).

Args:
    year (int): Target year for the load profile (defaults to 2025).
        Note: Currently uses global YEAR constant instead of parameter.
    num_chargers (int): Number of EV chargers in the fleet (defaults to 20).
        Each charger is assumed to be 5 kW capacity.

Returns:
    pandas.DataFrame: Hourly load profile with the following columns:
        - datetime: Timestamp for each hour
        - month: Month number (1-12)
        - day_of_week: Day of week (0=Monday, 6=Sunday)
        - day_type: "Weekday" or "Weekend"
        - hour: Hour of day (0-23)
        - ev_power: EV charging power demand in kW (0 or num_chargers*5)

Example:
    df = create_ev_load(2025, 20)
    # Creates profile with 100 kW peak demand (20 chargers x 5 kW each)
    # Active only weekdays 9pm-6am (hours 21-23, 0-5)
"""
    
from datetime import datetime
import pandas as pd


# ======= SCRIPT CONTROLS ======
YEAR = 2025
# ==============================

def create_ev_load(year=2025, num_chargers =20):
    # Generate date range for the year
    start_date = datetime(YEAR, 1, 1)
    end_date = datetime(YEAR + 1, 1, 1)
    date_range = pd.date_range(
        start=start_date, end=end_date, freq="h", inclusive="left"
    )
    df = pd.DataFrame(date_range,columns=['datetime'])
    
    # enrich data
    df['month'] = df['datetime'].dt.month
    df['day_of_week'] = df['datetime'].dt.day_of_week
    df['day_type'] = "Weekday"
    df.loc[df['day_of_week']>=5,"day_type"] = "Weekend"
    df['hour'] = df['datetime'].dt.hour
    
    # generate load profile
    power_chargers = num_chargers*5 # 5 kW chargers
    df['ev_power'] = power_chargers
    df.loc[(df['day_type']=="Weekend") ,"ev_power"] = 0 # no charging on weekends
    df.loc[((df['hour']>=6) & (df['hour']<21)) ,"ev_power"] = 0 # no charging from 6am-9pm

    return df


if __name__ == "__main__":
    year = 2025
    num_chargers = 20
    
    df = create_ev_load(year, num_chargers)
    
    print('EV Charger load profile created successfully')
    
    weekend_sum = df.loc[df['day_type']=="Weekend","ev_power"].sum()
    workday_sum = df.loc[((df['hour']>=6) & (df['hour']<21)) ,"ev_power"].sum()
    charge_avg = df['ev_power'].max()
    
    if weekend_sum == 0 | workday_sum == 0:
        print('Timing rules observed. Function test passed!')
        
    if charge_avg == num_chargers*5:
        print('Power limit applied correctly. Function test passed!')
        

# %%
