from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import os
import plotly.graph_objs as go
import plotly.io as pio
import plotly.express as px
from datetime import datetime
from scipy.stats import kruskal

app = Flask(__name__)

# Season assignment based on month
def get_season(date):
    if date.month in [12, 1, 2]:
        return "Winter"
    elif date.month in [3, 4, 5]:
        return "Spring"
    elif date.month in [6, 7, 8]:
        return "Summer"
    elif date.month in [9, 10, 11]:
        return "Fall"

# Calculate the Nash-Sutcliffe Efficiency (NSE)
def calculate_nse(obs, sim):
    numerator = np.sum((obs - sim) ** 2)
    denominator = np.sum((obs - np.mean(obs)) ** 2)
    return 1 - (numerator / denominator) if denominator != 0 else float('nan')

# Main eval function 
def evaluate_nwm_with_boxplot():
    events_folder = "static/events/"
    # Get all events, sort them numericall
    event_files = sorted(
        [f for f in os.listdir(events_folder) if f.startswith("event") and f.endswith(".csv")],
        key=lambda x: int(x.replace("event", "").replace(".csv", ""))
    )

    # Storage
    all_data = []
    graphs = {}
    pbias_by_season = {"Winter": [], "Spring": [], "Summer": [], "Fall": []}
    pbias_list = []
    season_list = []

    # Loop through each CSv
    for file in event_files:
        file_path = os.path.join(events_folder, file)
        df = pd.read_csv(file_path, parse_dates=["time"])
        df.columns = df.columns.str.strip()

        # Get missing data ratio for filtering
        missing_ratio = df["usgs_observed"].isna().mean()
        valid_df = df.dropna(subset=["nwm_predicted", "usgs_observed"])

        # Compute performance metrics
        correlation = valid_df["nwm_predicted"].corr(valid_df["usgs_observed"])
        pbias = ((valid_df["nwm_predicted"] - valid_df["usgs_observed"]).sum() / valid_df["usgs_observed"].sum()) * 100
        nse = calculate_nse(valid_df["usgs_observed"].values, valid_df["nwm_predicted"].values)

        # Get metadata
        event_id = file.replace("event", "").replace(".csv", "")
        start_time = df["time"].min()
        end_time = df["time"].max()
        season = get_season(start_time)

        # Event info for table display
        all_data.append({
            "event_id": event_id,
            "start": start_time.to_pydatetime(),
            "end": end_time.to_pydatetime(),
            "correlation": round(correlation, 3),
            "bias": round(pbias, 3),
            "nse": round(nse, 3),
            "season": season
        })

        # Line plot for event
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["time"], y=df["nwm_predicted"], mode='lines', name='NWM Predicted', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=df["time"], y=df["usgs_observed"], mode='lines', name='USGS Observed', line=dict(color='red')))
        fig.update_layout(title=f"Event {event_id} - NWM vs USGS", xaxis_title="Date/Time", yaxis_title="Streamflow (m³/s)")
        graphs[event_id] = pio.to_json(fig)

        # Look at ratio from before (Include in calculation if in threshhold)
        if missing_ratio < 0.5:
            pbias_by_season[season].append(pbias)
            pbias_list.append(pbias)
            season_list.append(season)

    # Kruskal-Wallis Test
    try:
        groups = [pbias_by_season[s] for s in pbias_by_season if len(pbias_by_season[s]) > 0]
        if len(groups) >= 2:
            kruskal_result = kruskal(*groups)
            kruskal_stats = {
                "h_stat": round(kruskal_result.statistic, 3),
                "p_value": round(kruskal_result.pvalue, 4)
            }
        else:
            kruskal_stats = {"h_stat": "N/A", "p_value": "Not enough groups"}
    except Exception as e:
        kruskal_stats = {"h_stat": "N/A", "p_value": str(e)}

    # Get boxplot for Kruskal-Wallis Test
    box_df = pd.DataFrame({"PBIAS": pbias_list, "Season": season_list})
    boxplot_fig = px.box(box_df, x="Season", y="PBIAS", title="Seasonal Distribution of PBIAS")
    boxplot_json = pio.to_json(boxplot_fig)

    return all_data, graphs, kruskal_stats, boxplot_json

@app.route('/')
def site_info():
    return render_template('site_info.html')

@app.route('/nwm_assessment')
def nwm_assessment():
    # Get outputs from above
    all_data, graphs, kruskal_stats, boxplot_json = evaluate_nwm_with_boxplot()

    # Prepare sorting and pagination for table
    sort_by = request.args.get("sort_by", "event_id")
    sort_order = request.args.get("sort_order", "asc")
    current_page = int(request.args.get("page", 1))
    per_page = 10

    # Sort requested column
    reverse = sort_order == "desc"
    if sort_by in ["event_id", "correlation", "bias", "nse"]:
        all_data.sort(key=lambda x: float(x[sort_by]), reverse=reverse)
    elif sort_by in ["start", "end"]:
        all_data.sort(key=lambda x: x[sort_by], reverse=reverse)

    # Pagination
    total_events = len(all_data)
    total_pages = (total_events + per_page - 1) // per_page
    start_idx = (current_page - 1) * per_page
    end_idx = start_idx + per_page
    paged_data = all_data[start_idx:end_idx]

    return render_template(
        'nwm_assessment.html',
        all_data=paged_data,
        graphs=graphs,
        anova=kruskal_stats,
        boxplot_json=boxplot_json,
        sort_by=sort_by,
        sort_order=sort_order,
        current_page=current_page,
        total_pages=total_pages
    )

@app.route('/flow_prediction')
def flow_prediction():
    df = pd.read_csv("data/nwm_MediumRange.csv", parse_dates=["time"])
    df.columns = df.columns.str.strip()
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])

    # Plotly time series graph
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df["streamflow"], mode="lines+markers", name="Streamflow"))
    fig.update_layout(xaxis_title="Time", yaxis_title="Streamflow (m³/s)")
    graph_json = pio.to_json(fig)

    return render_template('flow_prediction.html', graph_json=graph_json)

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/external_resources')
def external_resources():
    return render_template('external_resources.html')

if __name__ == "__main__":
    app.run(debug=True)
