import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    patients = pd.read_csv("data/patients_filtered.csv")
    encounters = pd.read_csv("data/encounters_filtered.csv")

    # claims_filtered.csv from Google Drive
    claims = pd.read_csv(
        "https://drive.google.com/uc?export=download&id=1SgsAesNi3SHouEtESiNnhY0KdFkvXsr9"
    )

    # claims_transactions_filtered.csv from Google Drive
    transactions = pd.read_csv(
        "https://drive.google.com/uc?export=download&id=1CXiodxDFeTDxGc0iyIovXY2BDekHtKtd"
    )

    payer_trans = pd.read_csv("data/payer_transitions_filtered.csv")
    return patients, encounters, claims, transactions, payer_trans

