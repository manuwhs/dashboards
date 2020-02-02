# Import required libraries
import pickle
import copy
import pathlib
import dash
import math
import datetime as dt
import pandas as pd
from dash.dependencies import Input, Output, State, ClientsideFunction
import sys

from layout.layout import get_layout
from utils import *
from plotting import *
import queue

from mqq_utils import load_topic_df,MQTTCONFIG
sys.path.append(pathlib.Path(__file__))

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server


# Load data
df = pd.read_csv(DATA_PATH.joinpath("wellspublic.csv"), low_memory=False)
df["Date_Well_Completed"] = pd.to_datetime(df["Date_Well_Completed"])
df = df[df["Date_Well_Completed"] > dt.datetime(1960, 1, 1)]

trim = df[["API_WellNo", "Well_Type", "Well_Name"]]
trim.index = trim["API_WellNo"]
dataset = trim.to_dict(orient="index")

points = pickle.load(open(DATA_PATH.joinpath("points.pkl"), "rb"))


# Create layout
app.layout = get_layout(app)


# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("count_graph", "figure")],
)


from mqq_utils import get_configured_mqtt_client

messages_queue = queue.Queue
client = get_configured_mqtt_client(messages_queue)

@app.callback(
    [Output("content-mqtt", "children"),
    Output("toast-chart", "figure")],
    [
        Input("show-mqtt-button", "n_clicks"),
    ],
)

def show_mqtt_data_callback(n_clicks):
    list_messages = ""
    # print (MQTTCONFIG.SUBSCRIPTIONS)
    # for topic in MQTTCONFIG.SUBSCRIPTIONS:
    #     df = load_topic_df(topic)
    #     list_messages += str(df)
    
    df = load_topic_df("house/toast")
    
    chart_toast = make_toasts_chart(df)
    return str(list_messages), chart_toast

@app.callback(
    Output("temperature-chart", "figure"),
    [
        Input("show-mqtt-button", "n_clicks"),
        Input('graph-update', 'n_intervals')]
)

def plot_tempreature(n_clicks, interval):
    list_messages = ""
    print(interval)
    # print (MQTTCONFIG.SUBSCRIPTIONS)
    # for topic in MQTTCONFIG.SUBSCRIPTIONS:
    #     df = load_topic_df(topic)
    #     list_messages += str(df)
    
    df = load_topic_df("houseMonitor/temperature")
    
    chart_temp = make_temperature_chart(df)
    return  chart_temp


@app.callback(
    Output("aggregate_data", "data"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def update_production_text(well_statuses, well_types, year_slider):

    dff = filter_dataframe(df,points, well_statuses, well_types, year_slider)
    selected = dff["API_WellNo"].values
    index, gas, oil, water = produce_aggregate(selected, year_slider)
    return [human_format(sum(gas)), human_format(sum(oil)), human_format(sum(water))]


# Radio -> multi
@app.callback(
    Output("well_statuses", "value"), [Input("well_status_selector", "value")]
)
def display_status(selector):
    if selector == "all":
        return list(WELL_STATUSES.keys())
    elif selector == "active":
        return ["AC"]
    return []


# Radio -> multi
@app.callback(Output("well_types", "value"), [Input("well_type_selector", "value")])
def display_type(selector):
    if selector == "all":
        return list(WELL_TYPES.keys())
    elif selector == "productive":
        return ["GD", "GE", "GW", "IG", "IW", "OD", "OE", "OW"]
    return []


# Slider -> count graph
@app.callback(Output("year_slider", "value"), [Input("count_graph", "selectedData")])
def update_year_slider(count_graph_selected):

    if count_graph_selected is None:
        return [1990, 2010]

    nums = [int(point["pointNumber"])
            for point in count_graph_selected["points"]]
    return [min(nums) + 1960, max(nums) + 1961]


# Selectors -> well text
@app.callback(
    Output("well_text", "children"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def update_well_text(well_statuses, well_types, year_slider):

    dff = filter_dataframe(df,points, well_statuses, well_types, year_slider)
    return dff.shape[0]


@app.callback(
    [
        Output("gasText", "children"),
        Output("oilText", "children"),
        Output("waterText", "children"),
    ],
    [Input("aggregate_data", "data")],
)
def update_text(data):
    return data[0] + " mcf", data[1] + " bbl", data[2] + " bbl"


# Selectors -> main graph
@app.callback(
    Output("main_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
    [State("lock_selector", "value"), State("main_graph", "relayoutData")],
)
def make_main_figure_callback(
    well_statuses, well_types, year_slider, selector, main_graph_layout
):
    return make_main_figure(df,points,
                            well_statuses, well_types, year_slider, selector, main_graph_layout)

# Main graph -> individual graph
@app.callback(Output("individual_graph", "figure"), [Input("main_graph", "hoverData")])
def make_individual_figure_callback(main_graph_hover):
    return make_individual_figure(dataset, points, main_graph_hover)

    # Selectors, main graph -> aggregate graph


@app.callback(
    Output("aggregate_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
        Input("main_graph", "hoverData"),
    ],
)
def make_aggregate_figure_callback(well_statuses, well_types, year_slider, main_graph_hover):
    return make_aggregate_figure(dataset, df, points, well_statuses, well_types, year_slider, main_graph_hover)


# Selectors, main graph -> pie graph
@app.callback(
    Output("pie_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def make_pie_figure_callback(well_statuses, well_types, year_slider):
    return make_pie_figure(df, points,well_statuses, well_types, year_slider)

# Selectors -> count graph


@app.callback(
    Output("count_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def make_count_figure_callback(well_statuses, well_types, year_slider):
    return make_count_figure(df,points, well_statuses, well_types, year_slider)


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
