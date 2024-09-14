import numpy as np
import streamlit as st

def pretty_dataframe(df):
    df = df.copy()
    df.columns = df.columns.str.replace("_", " ").str.title()
    
    return df

def pretty_map_zoom(lat, long):
    min_lat, max_lat = lat.min(), lat.max()
    min_long, max_long = long.min(), long.max()
    
    lat_diff = max_lat - min_lat
    long_diff = max_long - min_long

    # Base zoom levels for approximately 0.01 degree difference
    base_zoom_lat = 14
    base_zoom_long = 14
    
    # Adjust zoom level based on the span
    zoom_lat = base_zoom_lat - int((lat_diff // 0.05))
    zoom_long = base_zoom_long - int((long_diff // 0.05))
    
    # Return the smaller of the two zooms (more zoomed out)
    return min(zoom_lat, zoom_long)

def custom_map_tooltip(row):
    tooltip = f"""
        <h6>{row['name'].title()}</h6>
        <strong>""" + ("📍 Center" if row['type'] == "Center" else "🏫 School") + f"""</strong><br/>
        <b>Latitude:</b> {row['lat']}<br/>
        <b>Longitude:</b> {row['long']}<br/> """ + (
        f"""<b>Allocation:</b> {int(row['allocation'])}<br/>""" if row["allocation"] > 0 else ""
        )
    
    return tooltip