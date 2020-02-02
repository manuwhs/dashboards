import pickle
import copy
import pathlib
import dash
import math
import datetime as dt
import pandas as pd

import pydriller
pydriller.Commit
# Multi-dropdown options
from controls import COUNTIES, WELL_STATUSES, WELL_TYPES, WELL_COLORS

# Create controls
county_options = [
    {"label": str(COUNTIES[county]), "value": str(county)} for county in COUNTIES
]

well_status_options = [
    {"label": str(WELL_STATUSES[well_status]), "value": str(well_status)}
    for well_status in WELL_STATUSES
]

well_type_options = [
    {"label": str(WELL_TYPES[well_type]), "value": str(well_type)}
    for well_type in WELL_TYPES
]

# Create global chart template
mapbox_access_token = "pk.eyJ1IjoiamFja2x1byIsImEiOiJjajNlcnh3MzEwMHZtMzNueGw3NWw5ZXF5In0.fk8k06T96Ml9CLGgKmk81w"

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(lon=-78.05, lat=42.54),
        zoom=7,
    ),
)



# Helper functions
def human_format(num):
    if num == 0:
        return "0"

    magnitude = int(math.log(num, 1000))
    mantissa = str(int(num / (1000 ** magnitude)))
    return mantissa + ["", "K", "M", "G", "T", "P"][magnitude]


def filter_dataframe(df, points, well_statuses, well_types, year_slider):
    dff = df[
        df["Well_Status"].isin(well_statuses)
        & df["Well_Type"].isin(well_types)
        & (df["Date_Well_Completed"] > dt.datetime(year_slider[0], 1, 1))
        & (df["Date_Well_Completed"] < dt.datetime(year_slider[1], 1, 1))
    ]
    return dff


def produce_individual(api_well_num, points):
    try:
        points[api_well_num]
    except:
        return None, None, None, None

    index = list(
        range(min(points[api_well_num].keys()), max(points[api_well_num].keys()) + 1)
    )
    gas = []
    oil = []
    water = []

    for year in index:
        try:
            gas.append(points[api_well_num][year]["Gas Produced, MCF"])
        except:
            gas.append(0)
        try:
            oil.append(points[api_well_num][year]["Oil Produced, bbl"])
        except:
            oil.append(0)
        try:
            water.append(points[api_well_num][year]["Water Produced, bbl"])
        except:
            water.append(0)

    return index, gas, oil, water


def produce_aggregate(selected, year_slider):

    index = list(range(max(year_slider[0], 1985), 2016))
    gas = []
    oil = []
    water = []

    for year in index:
        count_gas = 0
        count_oil = 0
        count_water = 0
        for api_well_num in selected:
            try:
                count_gas += points[api_well_num][year]["Gas Produced, MCF"]
            except:
                pass
            try:
                count_oil += points[api_well_num][year]["Oil Produced, bbl"]
            except:
                pass
            try:
                count_water += points[api_well_num][year]["Water Produced, bbl"]
            except:
                pass
        gas.append(count_gas)
        oil.append(count_oil)
        water.append(count_water)

    return index, gas, oil, water