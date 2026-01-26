#%%
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import sys
from pathlib import Path

# Get the project root (parent of src/)
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / "python"))


def read_input_file(filename = "hourly_data_processed.csv",power_column=5):
    """Read the input CSV files from the input directory"""
    input_dir = "./inputs"
    file_path = os.path.join(input_dir,filename)
    
    try:
        data = pd.read_csv(file_path, header =0)
        data = data.iloc[:,[0,power_column]] 
        data.columns = ['datetime', 'power']
        return data
        
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        print("Please ensure the energy data processing script has been run first.")
        return None
    
    except Exception as e:
        print(f"Error loading data: {e}")
    return None

def enrich_data(data):
    '''
    Add necessary columns to hourly data for aggregation
    '''
    data['weekday'] = data['datetime'].dt.weekday
    data['month'] = data['datetime'].dt.month
    data['month_name'] = data['datetime'].dt.strftime("%B")
    data['hour'] = data['datetime'].dt.hour
    
    data['day_type'] = "weekday"
    data.loc[data['weekday']>=5, 'day_type'] = "weekend"
    
    return data
    
def clean_gaps(data,threshold):
    
    row_count = len(data)
    data = data.loc[data['power']>threshold]
    row_count_cleaned = len(data)
    rows_cleaned = row_count-row_count_cleaned
    rows_cleaned_pct = (1-row_count_cleaned/row_count)*100
    stats = {
        'rows_before':row_count,
        'rows_after':row_count_cleaned,
        'cleaned': rows_cleaned,
        'cleaned_pct': rows_cleaned_pct
    }    
    return data, stats

def calculate_loadfactors(data):
    '''
    Calculate load factors based on daytype and month aggregations.
    Expects hourly load data.
    Returns aggregated dataframes, raw hourly dataframe for boxplots, and maximum demand.
    '''
    
    max_demand = data["power"].max()
    print(f'Maximum demand across all data: {max_demand:.2f} kW')
    
    # Aggregated daytype load factors
    daytype_loadfactor = (
        data.groupby(['day_type','hour'])['power']
        .agg(['mean','count','std'])
        .reset_index()
    )
    daytype_loadfactor['load_factor'] = daytype_loadfactor['mean']/max_demand
    daytype_loadfactor['load_factor_pct'] = daytype_loadfactor['load_factor']*100
    
    # Aggregated monthly load factors
    month_loadfactor = (
        data.groupby(['month_name','hour'])['power']
        .agg(['mean','count','std'])
        .reset_index()
    )
    month_loadfactor['load_factor'] = month_loadfactor['mean']/max_demand
    month_loadfactor['load_factor_pct'] = month_loadfactor['load_factor']*100
    
    # Raw hourly data for boxplots (each data point normalized to max_demand)
    hourly_boxplot_data = data.copy()
    hourly_boxplot_data['load_factor'] = hourly_boxplot_data['power'] / max_demand
    hourly_boxplot_data['load_factor_pct'] = hourly_boxplot_data['load_factor'] * 100
    
    return daytype_loadfactor, month_loadfactor, hourly_boxplot_data, max_demand

def create_daytype_plot(data):
    """
    Create plot showing weekday vs weekend load factor patterns
    Expects hourly loadfactor dataframe
    Returns html plot saved to local machine
    """
    fig = go.Figure()

    # Add weekday trace
    weekday_data = data[data["day_type"] == "weekday"]
    fig.add_trace(
        go.Scatter(
            x=weekday_data["hour"],
            y=weekday_data["load_factor_pct"],
            mode="lines+markers",
            name="Weekday",
            line=dict(color="blue", width=2),
            marker=dict(size=6),
        )
    )

    # Add weekend trace
    weekend_data = data[data["day_type"] == "weekend"]
    fig.add_trace(
        go.Scatter(
            x=weekend_data["hour"],
            y=weekend_data["load_factor_pct"],
            mode="lines+markers",
            name="Weekend",
            line=dict(color="red", width=2),
            marker=dict(size=6),
        )
    )

    fig.update_layout(
        title="Hourly Load Factor: Weekday vs Weekend",
        xaxis_title="Hour of Day",
        yaxis_title="Load Factor (%)",
        xaxis=dict(tickmode="linear", tick0=0, dtick=2, range=[0, 23]),
        yaxis=dict(range=[0, 100]),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig

def create_monthly_heatmap(data):
    """
    Create heatmap showing monthly load factor patterns by hour
    Expects monthly load factor dataframe
    Returns html plot saved to local machine
    """
    # Pivot data for heatmap
    heatmap_data = data.pivot(
        index="hour", columns="month_name", values="load_factor_pct"
    )

    # Reorder columns to calendar order
    month_order = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    heatmap_data = heatmap_data.reindex(
        columns=[col for col in month_order if col in heatmap_data.columns]
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale="RdYlBu_r",
            colorbar=dict(title="Load Factor (%)"),
            hoverongaps=False,
        )
    )

    fig.update_layout(
        title="Monthly Load Factor Heatmap by Hour",
        xaxis_title="Month",
        yaxis_title="Hour of Day",
        yaxis=dict(tickmode="linear", tick0=0, dtick=2, range=[0, 23]),
    )

    return fig

def create_monthly_line_plot(data):
    """
    Create line plot showing monthly load factor patterns
    Expects monthly load factor dataframe
    Returns html plot saved to local machine
    """
    fig = go.Figure()

    # Get unique months and create a color palette
    months = data["month_name"].unique()
    colors = px.colors.qualitative.Set3[: len(months)]

    for i, month in enumerate(months):
        month_data = data[data["month_name"] == month]
        fig.add_trace(
            go.Scatter(
                x=month_data["hour"],
                y=month_data["load_factor_pct"],
                mode="lines+markers",
                name=month,
                line=dict(color=colors[i], width=2),
                marker=dict(size=4),
            )
        )

    fig.update_layout(
        title="Hourly Load Factor by Month",
        xaxis_title="Hour of Day",
        yaxis_title="Load Factor (%)",
        xaxis=dict(tickmode="linear", tick0=0, dtick=2, range=[0, 23]),
        yaxis=dict(range=[0, 100]),
        hovermode="x unified",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    )

    return fig

def create_daytype_boxplot(data):
    """
    Create box plots showing distribution of load factors by hour.
    
    Two subplots: one for weekday, one for weekend.
    Each subplot shows a box plot for each hour of the day (0-23),
    displaying the distribution of all load_factor_pct values for that hour.
    
    Expects daytype load factor dataframe with columns: day_type, hour, load_factor_pct
    Returns plotly figure
    """
    
    from plotly.subplots import make_subplots
    
    # Create subplots (vertical stack)
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Weekday", "Weekend"),
        vertical_spacing=0.12
    )
    
    # Separate weekday and weekend data
    weekday_data = data[data["day_type"] == "weekday"]
    weekend_data = data[data["day_type"] == "weekend"]
    
    # Add weekday box plots (one for each hour)
    for hour in sorted(weekday_data["hour"].unique()):
        hour_data = weekday_data[weekday_data["hour"] == hour]
        fig.add_trace(
            go.Box(
                y=hour_data["load_factor_pct"],
                name=f"Hour {int(hour)}",
                boxmean='sd',
                marker_color="blue",
                showlegend=False,
                x=[f"{int(hour):02d}:00"] * len(hour_data),
            ),
            row=1, col=1
        )
    
    # Add weekend box plots (one for each hour)
    for hour in sorted(weekend_data["hour"].unique()):
        hour_data = weekend_data[weekend_data["hour"] == hour]
        fig.add_trace(
            go.Box(
                y=hour_data["load_factor_pct"],
                name=f"Hour {int(hour)}",
                boxmean='sd',
                marker_color="red",
                showlegend=False,
                x=[f"{int(hour):02d}:00"] * len(hour_data),
            ),
            row=2, col=1
        )
    
    # Update layout
    fig.update_xaxes(title_text="Hour of Day", row=1, col=1)
    fig.update_xaxes(title_text="Hour of Day", row=2, col=1)
    fig.update_yaxes(title_text="Load Factor (%)", row=1, col=1)
    fig.update_yaxes(title_text="Load Factor (%)", row=2, col=1)
    
    fig.update_layout(
        title="Distribution of Load Factors by Hour (Weekday vs Weekend)",
        height=900,
        width=1200,
        hovermode="x unified",
    )
    
    return fig

def export_results(daytype_data, month_data):
    """Export results to CSV files"""
    # Create outputs directory if it doesn't exist
    os.makedirs("./outputs", exist_ok=True)

    # Export weekday/weekend load factors
    daytype_export = daytype_data.copy()
    daytype_export = daytype_export.round(4)
    daytype_export.to_csv(
        "./outputs/load_factor_daytype.csv", index=False
    )
    print(
        "Exported weekday/weekend load factors to: ./outputs/load_factor_daytype.csv"
    )

    # Export monthly load factors
    monthly_export = month_data.copy()
    monthly_export = monthly_export.round(4)
    monthly_export.to_csv("./outputs/load_factor_monthly.csv", index=False)
    print("Exported monthly load factors to: ./outputs/load_factor_monthly.csv")
    
def print_summary_statistics(daytype_data, monthly_data, max_demand,clean_stats):
    """
    Print summary statistics
    Expects monthly and daytype load factor dataframes, maximum demand and cleaning
    statistics dictionary
    Returns console printout
    """
    
    print("\n" + "=" * 60)
    print("LOAD FACTOR ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Maximum Demand: {max_demand:.2f} kW")

    print("\nWeekday vs Weekend Load Factors:")
    weekday_avg = daytype_data[daytype_data["day_type"] == "weekday"][
        "load_factor_pct"
    ].mean()
    weekend_avg = daytype_data[daytype_data["day_type"] == "weekend"][
        "load_factor_pct"
    ].mean()
    print(f"  Average Weekday Load Factor: {weekday_avg:.2f}%")
    print(f"  Average Weekend Load Factor: {weekend_avg:.2f}%")

    print("\nMonthly Load Factor Range:")
    monthly_avg = monthly_data.groupby("month_name")["load_factor_pct"].mean()
    print(f"  Highest: {monthly_avg.max():.2f}% ({monthly_avg.idxmax()})")
    print(f"  Lowest: {monthly_avg.min():.2f}% ({monthly_avg.idxmin()})")

    print("\nHourly Load Factor Range:")
    hourly_avg = daytype_data.groupby("hour")["load_factor_pct"].mean()
    print(f"  Peak hour: {hourly_avg.max():.2f}% (Hour {hourly_avg.idxmax()})")
    print(f"  Lowest hour: {hourly_avg.min():.2f}% (Hour {hourly_avg.idxmin()})")
    
    print("\nData Cleaning Summary:")
    print(f"  Rows before cleaning: {clean_stats['rows_before']}")
    print(f"  Rows after cleaning: {clean_stats['rows_after']}")
    print(f"  Rows removed: {clean_stats['cleaned']} ({clean_stats['cleaned_pct']:.2f}%)")

# %%
if __name__ == "__main__":
    THRESHOLD = 1
    
    power_col = 5
    data = read_input_file("hourly_data_processed.csv",power_col)
    data['datetime'] = pd.to_datetime(data['datetime'], format="%Y-%m-%d %H:%M:%S")
    data = enrich_data(data) 
    data, stats = clean_gaps(data,THRESHOLD)
    
    daytype_loadfactor, month_loadfactor, hourly_boxplot_data, max_demand = calculate_loadfactors(data)
    
    print("\nCreating visualizations...")
    fig1 = create_daytype_plot(daytype_loadfactor)
    fig1.write_html(os.path.join(project_root, "outputs", "daytype_plot.html"))
    fig2 = create_daytype_boxplot(hourly_boxplot_data)
    fig2.write_html(os.path.join(project_root, "outputs", "daytype_boxplot.html"))
    fig3 = create_monthly_heatmap(month_loadfactor)
    fig3.write_html(os.path.join(project_root, "outputs", "monthly_heatmap_plot.html"))
    fig4 = create_monthly_line_plot(month_loadfactor)
    fig4.write_html(os.path.join(project_root, "outputs", "monthly_line_plot.html"))
    
    print("\nExporting results...")
    export_results(daytype_loadfactor, month_loadfactor)
    
    print_summary_statistics(daytype_loadfactor, month_loadfactor, max_demand,stats)

    print("\nLoad Factor Analysis Complete!")
    
# %%
