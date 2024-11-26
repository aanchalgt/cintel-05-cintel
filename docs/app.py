# --------------------------------------------
# Imports at the top - PyShiny EXPRESS VERSION
# --------------------------------------------

# From shiny, import just reactive and render
from shiny import reactive, render

# From shiny.express, import just ui and inputs if needed
from shiny.express import ui

import random
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly
from scipy import stats

# --------------------------------------------
# Import icons as you like
# --------------------------------------------

# https://fontawesome.com/v4/cheatsheet/
from faicons import icon_svg

# --------------------------------------------
# Shiny EXPRESS VERSION
# --------------------------------------------

# --------------------------------------------
# First, set a constant UPDATE INTERVAL for all live data
# Constants are usually defined in uppercase letters
# Use a type hint to make it clear that it's an integer (: int)
# --------------------------------------------

UPDATE_INTERVAL_SECS: int = 3

# --------------------------------------------
# Initialize a REACTIVE VALUE with a common data structure
# The reactive value is used to store state (information)
# Used by all the display components that show this live data.
# This reactive value is a wrapper around a DEQUE of readings
# --------------------------------------------

DEQUE_SIZE: int = 5
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

# --------------------------------------------
# Initialize a REACTIVE CALC that all display components can call
# to get the latest data and display it.
# The calculation is invalidated every UPDATE_INTERVAL_SECS
# to trigger updates.
# It returns a tuple with everything needed to display the data.
# Very easy to expand or modify.
# --------------------------------------------

@reactive.calc()
def reactive_calc_combined():
    # Invalidate this calculation every UPDATE_INTERVAL_SECS to trigger updates
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)

    # Data generation logic
    temp_antarctic = round(random.uniform(-18, -16), 1)  # Antarctic temperature
    temp_arctic = round(random.uniform(-20, -15), 1)  # Arctic temperature
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Store both temperatures in the deque
    new_dictionary_entry = {"temp_antarctic": temp_antarctic, "temp_arctic": temp_arctic, "timestamp": timestamp}

    # get the deque and append the new entry
    reactive_value_wrapper.get().append(new_dictionary_entry)

    # Get a snapshot of the current deque for any further processing
    deque_snapshot = reactive_value_wrapper.get()

    # For Display: Convert deque to DataFrame for display
    df = pd.DataFrame(deque_snapshot)

    # For Display: Get the latest dictionary entry
    latest_dictionary_entry = new_dictionary_entry

    # Return a tuple with everything we need
    # Every time we call this function, we'll get all these values
    return deque_snapshot, df, latest_dictionary_entry

# Define the Shiny UI Page layout
ui.page_opts(title="PyShiny Express: Live Data Example", fillable=True)

# Sidebar for links and information
with ui.sidebar(open="open"):
    ui.h2("Antarctic Explorer", class_="text-center")
    ui.p(
        "A demonstration of real-time temperature readings in Antarctica and Arctic.",
        class_="text-center",
    )
    ui.hr()
    ui.h6("Links:")
    ui.a(
        "GitHub Source",
        href="https://github.com/denisecase/cintel-05-cintel",
        target="_blank",
    )
    ui.a(
        "GitHub App",
        href="https://denisecase.github.io/cintel-05-cintel/",
        target="_blank",
    )
    ui.a("PyShiny", href="https://shiny.posit.co/py/", target="_blank")
    ui.a(
        "PyShiny Express",
        href="hhttps://shiny.posit.co/blog/posts/shiny-express/",
        target="_blank",
    )

# In Shiny Express, everything not in the sidebar is in the main panel
with ui.layout_columns():
    # Antarctic temperature card
    with ui.value_box(
        showcase=icon_svg("sun"),
        theme="bg-gradient-blue-purple",
    ):
        "Current Temperature (Antarctic)"
        @render.text
        def display_temp_antarctic():
            """Get the latest Antarctic temperature"""
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
            return f"{latest_dictionary_entry['temp_antarctic']} C"
        "warmer than usual"

    # Arctic temperature card
    with ui.value_box(
        showcase=icon_svg("snowflake"),
        theme="bg-gradient-blue-purple",
    ):
        "Current Temperature (Arctic)"
        @render.text
        def display_temp_arctic():
            """Get the latest Arctic temperature"""
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
            return f"{latest_dictionary_entry['temp_arctic']} C"
        "colder than usual"

    # Compare Arctic and Antarctic temperatures
    with ui.card(full_screen=True):
        ui.card_header("Which is Colder? Arctic vs Antarctic")
        
        @render.text
        def compare_temperatures():
            """Compare Arctic and Antarctic temperatures"""
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
            temp_arctic = latest_dictionary_entry["temp_arctic"]
            temp_antarctic = latest_dictionary_entry["temp_antarctic"]
            if temp_arctic < temp_antarctic:
                return f"Arctic is colder: {temp_arctic}°C vs {temp_antarctic}°C"
            else:
                return f"Antarctic is colder: {temp_antarctic}°C vs {temp_arctic}°C"

    # Most recent readings
    with ui.card(full_screen=True):
        ui.card_header("Most Recent Readings")

        @render.data_frame
        def display_df():
            """Get the latest readings and return a dataframe with current readings"""
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
            pd.set_option('display.width', None)        # Use maximum width
            return render.DataGrid(df, width="100%")

    # Chart with current trend
    with ui.card():
        ui.card_header("Chart with Current Trend")

        @render_plotly
        def display_plot():
            # Fetch from the reactive calc function
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()

            # Ensure the DataFrame is not empty before plotting
            if not df.empty:
                # Convert the 'timestamp' column to datetime for better plotting
                df["timestamp"] = pd.to_datetime(df["timestamp"])

                # Create scatter plot for readings
                fig = px.scatter(df,
                                 x="timestamp",
                                 y="temp_antarctic",
                                 title="Temperature Readings with Regression Line (Antarctic)",
                                 labels={"temp_antarctic": "Temperature (°C)", "timestamp": "Time"},
                                 color_discrete_sequence=["blue"])

                # Linear regression for Antarctic temperature
                x_vals = range(len(df))
                y_vals = df["temp_antarctic"]

                slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)
                df['best_fit_line'] = [slope * x + intercept for x in x_vals]

                # Add the regression line to the figure
                fig.add_scatter(x=df["timestamp"], y=df['best_fit_line'], mode='lines', name='Regression Line')

                # Update layout as needed to customize further
                fig.update_layout(xaxis_title="Time", yaxis_title="Temperature (°C)")

            return fig
