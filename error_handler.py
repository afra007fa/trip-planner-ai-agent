import time
import json
import requests
import streamlit as st


# =====================================
# INPUT VALIDATION
# =====================================

def validate_inputs(
        destination,
        interests,
        days):

    errors = []

    if not destination.strip():
        errors.append(
            "Please enter a destination."
        )

    if len(interests) == 0:
        errors.append(
            "Select at least one interest."
        )

    if days <= 0:
        errors.append(
            "Invalid trip length."
        )

    return errors


# =====================================
# API RETRY
# =====================================

def request_with_retry(
        method,
        url,
        retries=3,
        timeout=20,
        **kwargs):

    delay = 1

    for i in range(retries):

        try:

            response = requests.request(
                method,
                url,
                timeout=timeout,
                **kwargs
            )

            if response.status_code == 429:

                time.sleep(delay)
                delay *= 2
                continue

            return response

        except Exception:

            if i == retries - 1:
                raise

            time.sleep(delay)
            delay *= 2


# =====================================
# SAFE JSON
# =====================================

def safe_json(response):

    try:
        return response.json()

    except json.JSONDecodeError:

        st.error(
            "Invalid JSON response."
        )

        return None


# =====================================
# GEOCODING ERROR
# =====================================

def handle_geocode_failure(city):

    st.warning(
        f"No location found: {city}"
    )


# =====================================
# EMPTY RESULTS
# =====================================

def handle_empty_pois():

    st.info(
        "No matching POIs found."
    )


# =====================================
# TIMEOUT
# =====================================

def handle_timeout():

    st.error(
        "Request timed out."
    )


# =====================================
# UNKNOWN ERROR
# =====================================

def handle_unknown(error):

    st.error(
        f"Unexpected error: {error}"
    )