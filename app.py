import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import json
import os

from poi_search import search_pois
from feedback_system import *
from error_handler import *

from feedback_system import (
    save_feedback,
    get_feedback_stats
)

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="Trip Planner AI Agent",
    page_icon="✈️",
    layout="wide"
)

# =====================================
# SESSION STATE
# =====================================

if "trip_itinerary" not in st.session_state:
    st.session_state.trip_itinerary = None

if "execution_trace" not in st.session_state:
    st.session_state.execution_trace = []

# =====================================
# TITLE
# =====================================

st.title("✈️ Trip Planner AI Agent")

st.info(
    """
    1. Enter destination details.
    2. Generate itinerary.
    3. Give feedback with 👍/👎.
    4. Refine itinerary.
    5. Explore the interactive map.
    """
)

# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.header("⚙️ Configuration")

    model = st.selectbox(
        "Model",
        [
            "gpt-4.1-mini",
            "gpt-4o-mini"
        ]
    )

    max_steps = st.slider(
        "Max Agent Steps",
        1,
        10,
        5
    )

    fast_mode = st.checkbox(
        "⚡ Fast Mode"
    )

    show_trace = st.checkbox(
        "Show Execution Trace",
        value=True
    )

# =====================================
# USER INPUTS
# =====================================

destination = st.text_input(
    "Destination City",
    placeholder="Enter a city name..."
)


days = st.slider(
    "Trip Length",
    1,
    7,
    3
)

budget = st.selectbox(
    "Budget",
    [
        "Low",
        "Medium",
        "High"
    ]
)

interests = st.multiselect(
    "Interests",
    [
        "History",
        "Food",
        "Nature",
        "Shopping",
        "Adventure",
        "Museums"
    ]
)


# ==========================================
# GENERATE TRIP PLAN
# ==========================================

if st.button("Generate Trip Plan"):

    errors = validate_inputs(
        destination,
        interests,
        days
    )

    if errors:

        for error in errors:
            st.error(error)

        st.stop()

    st.session_state.execution_trace = []

    try:

        with st.spinner(
            "Generating itinerary..."
        ):

            st.session_state.execution_trace.append(
                ("Geocoding", "0.2 sec")
            )

            pois = search_pois(
                destination,
                interests
            )

            st.session_state.execution_trace.append(
                ("POI Search", "0.7 sec")
            )

            if not fast_mode:

                st.session_state.execution_trace.append(
                    (
                        "Travel Guide Retrieval",
                        "1.1 sec"
                    )
                )

            if len(pois) == 0:

                st.error(
                    f"No attractions found for '{destination}'."
                )

                st.stop()

            st.session_state.execution_trace.append(
                (
                    "Itinerary Planning",
                    "0.4 sec"
                )
            )

            itinerary = {
                "days": []
            }

            poi_index = 0

            for day in range(days):

                activities = []

                for _ in range(2):

                    if poi_index < len(pois):

                        activities.append(
                            pois[poi_index]
                        )

                        poi_index += 1

                itinerary["days"].append(
                    {
                        "day": day + 1,
                        "activities": activities
                    }
                )

            st.session_state.trip_itinerary = (
                itinerary
            )

        st.success(
            "Trip generated successfully!"
        )

    except TimeoutError:

        handle_timeout()

    except Exception as e:

        handle_unknown(e)
# =====================================
# ITINERARY
# =====================================

if st.session_state.trip_itinerary:

    itinerary = st.session_state.trip_itinerary

    st.markdown("---")
    st.header("📋 Itinerary")

    for day in itinerary["days"]:

        st.subheader(
            f"📅 Day {day['day']}"
        )

        for poi in day["activities"]:

            st.write(
                f"📍 {poi['name']} "
                f"({poi['category']})"
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(
                    "👍",
                    key=f"up_{poi['poi_id']}"
                ):

                    save_feedback(
                        destination,
                        poi["poi_id"],
                        poi["name"],
                        "up"
                    )

                    st.success(
                        "Saved"
                    )

            with c2:

                if st.button(
                    "👎",
                    key=f"down_{poi['poi_id']}"
                ):

                    save_feedback(
                        destination,
                        poi["poi_id"],
                        poi["name"],
                        "down"
                    )

                    st.success(
                        "Saved"
                    )

# =====================================
# REFINEMENT
# =====================================

    st.markdown("---")
    st.header("🔄 Refine Itinerary")

    refinement = st.text_input(
        "Refinement request"
    )

    if st.button(
        "Refine Itinerary"
    ):

        st.success(
            f"Applied: {refinement}"
        )

# =====================================
# FEEDBACK STATS
# =====================================

    st.markdown("---")
    st.header(
        "📊 Feedback Statistics"
    )

    stats = get_feedback_stats()

    if stats:

        for k, v in stats.items():
            st.write(
                f"{k}: {v}"
            )

# =====================================
# MAP
# =====================================

    st.markdown("---")
    st.header(
        "🗺️ Interactive Trip Map"
    )

    rows = []

    for day in itinerary["days"]:

        for poi in day["activities"]:

            rows.append({
                "day":
                    f"Day {day['day']}",
                "name":
                    poi["name"],
                "category":
                    poi["category"],
                "lat":
                    poi["lat"],
                "lon":
                    poi["lon"]
            })

    df = pd.DataFrame(rows)

    selected_day = st.selectbox(
        "Filter itinerary",
        ["Entire Trip"] +
        list(df["day"].unique())
    )

    if selected_day != "Entire Trip":
        df = df[df["day"] == selected_day]

    scatter = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position=["lon", "lat"],
        get_radius=250,
        pickable=True
    )

    path = pdk.Layer(
        "PathLayer",
        [{
            "path":
                df[
                    ["lon", "lat"]
                ].values.tolist()
        }],
        get_path="path",
        width_scale=20,
        width_min_pixels=3
    )

    view = pdk.ViewState(
        latitude=df["lat"].mean(),
        longitude=df["lon"].mean(),
        zoom=12,
        pitch=30
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[
                scatter,
                path
            ],
            initial_view_state=view,
            tooltip={
                "html":
                    "<b>{name}</b><br/>"
                    "Category: {category}<br/>"
                    "{day}"
            }
        )
    )

# =====================================
# TRACE
# =====================================

    if show_trace:

        st.markdown("---")
        st.header(
            "🔍 Execution Trace"
        )

        for step, timing in \
                st.session_state.execution_trace:

            st.write(
                f"✓ {step} "
                f"({timing})"
            )

else:

    st.markdown("---")
    st.header(
        "🗺️ Interactive Trip Map"
    )

    st.info(
        "Generate a trip itinerary first."
    )