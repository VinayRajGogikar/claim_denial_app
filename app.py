import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    patients = pd.read_csv("data/patients_filtered.csv")
    encounters = pd.read_csv("data/encounters_filtered.csv")
    claims = pd.read_csv(
        "https://drive.google.com/uc?export=download&id=1SgsAesNi3SHouEtESiNnhY0KdFkvXsr9"
    )
