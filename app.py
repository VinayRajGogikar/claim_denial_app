import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Real-Time Insurance Claim Denial Prediction",
    layout="wide"
)

# ------------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    # Local CSVs from your GitHub repo (in /data folder)
    patients = pd.read_csv("data/patients_filtered.csv")
    encounters = pd.read_csv("data/encounters_filtered.csv")
    payer_trans = pd.read_csv("data/payer_transitions_filtered.csv")

    # Claims + transactions from Google Drive
    claims = pd.read_csv(
        "https://drive.google.com/uc?export=download&id=1SgsAesNi3SHouEtESiNnhY0KdFkvXsr9"
    )
    transactions = pd.read_csv(
        "https://drive.google.com/uc?export=download&id=1CXiodxDFeTDxGc0iyIovXY2BDekHtKtd"
    )

    # Create a single STATUS column (use patient status)
    claims["STATUS"] = claims["STATUSP"]

    # Attach a payer to each claim:
    # take the latest payer row per patient from payer_transitions
    latest_payer = (
        payer_trans.sort_values("START_DATE")
        .drop_duplicates("PATIENT", keep="last")[["PATIENT", "PAYER"]]
    )
    claims = claims.merge(
        latest_payer, left_on="PATIENTID", right_on="PATIENT", how="left"
    )

    # Simple proxy for "denied": any positive outstanding patient balance
    claims["DENIED"] = claims["OUTSTANDINGP"] > 0

    return patients, encounters, claims, transactions, payer_trans


patients, encounters, claims, transactions, payer_trans = load_data()

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def kpi_card(label, value, color):
    st.markdown(
        f"""
        <div style="background:white; border-radius:10px; padding:20px;
             border:2px solid {color}; text-align:center; width:100%;">
            <h3 style="color:black;">{label}</h3>
            <h1 style="color:{color};">{value}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compute_payer_denial_rate(claims_df, payer_id: str) -> float:
    """Percent of claims for this payer that we treat as denied."""
    subset = claims_df[claims_df["PAYER"] == payer_id]
    if len(subset) == 0:
        return 0.0
    return float(subset["DENIED"].mean() * 100.0)


# ------------------------------------------------------------------
# KPIs
# ------------------------------------------------------------------
total_patients = len(patients)
total_encounters = len(encounters)
total_claims = len(claims)
total_payers = claims["PAYER"].nunique()

tabs = st.tabs(
    [
        "Overview",
        "Patients",
        "Encounters",
        "Claims",
        "Denial Reasons",
        "Payers",
        "Predict Denial",
    ]
)

# ------------------------------------------------------------------
# OVERVIEW TAB
# ------------------------------------------------------------------
with tabs[0]:
    st.subheader(
        "Overview: Use the tabs above to explore claims, denial reasons, patients, and payers."
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Patients", total_patients, "#2e8ef7")
    with col2:
        kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3:
        kpi_card("Claims", total_claims, "#f7d42e")
    with col4:
        kpi_card("Payers", total_payers, "#f72e2e")

# ------------------------------------------------------------------
# PATIENTS TAB
# ------------------------------------------------------------------
with tabs[1]:
    st.subheader("View and analyze the distribution of patients by gender and birthdate.")

    gender = st.selectbox(
        "Filter by Gender",
        ["All"] + sorted(patients["GENDER"].dropna().unique().tolist()),
    )

    df_pat = patients.copy()
    if gender != "All":
        df_pat = df_pat[df_pat["GENDER"] == gender]

    fig = px.histogram(
        df_pat,
        x="BIRTHDATE",
        color="GENDER",
        barmode="stack",
        title="Patients by Birthdate",
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Patients", total_patients, "#2e8ef7")
    with col2:
        kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3:
        kpi_card("Claims", total_claims, "#f7d42e")
    with col4:
        kpi_card("Payers", total_payers, "#f72e2e")

# ------------------------------------------------------------------
# ENCOUNTERS TAB
# ------------------------------------------------------------------
with tabs[2]:
    st.subheader("View encounter breakdown and class filters.")

    enc_classes = encounters["ENCOUNTERCLASS"].dropna().unique()
    selected_class = st.selectbox(
        "Filter by Encounter Class", ["All"] + sorted(enc_classes.tolist())
    )

    df_enc = encounters.copy()
    if selected_class != "All":
        df_enc = df_enc[df_enc["ENCOUNTERCLASS"] == selected_class]

    fig = px.histogram(
        df_enc,
        x="ENCOUNTERCLASS",
        title="Encounters by Class",
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Patients", total_patients, "#2e8ef7")
    with col2:
        kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3:
        kpi_card("Claims", total_claims, "#f7d42e")
    with col4:
        kpi_card("Payers", total_payers, "#f72e2e")

# ------------------------------------------------------------------
# CLAIMS TAB
# ------------------------------------------------------------------
with tabs[3]:
    st.subheader("Review claims status and payer details.")

    status_list = claims["STATUS"].dropna().unique()
    payer_list = claims["PAYER"].dropna().unique()

    status_sel = st.selectbox(
        "Filter by Claim Status", ["All"] + sorted(status_list.tolist())
    )
    payer_sel = st.selectbox(
        "Filter by Payer", ["All"] + sorted(payer_list.tolist())
    )

    df_clm = claims.copy()
    if status_sel != "All":
        df_clm = df_clm[df_clm["STATUS"] == status_sel]
    if payer_sel != "All":
        df_clm = df_clm[df_clm["PAYER"] == payer_sel]

    fig = px.histogram(
        df_clm,
        x="STATUS",
        title="Claims by Status",
        color="STATUS",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.write("Filtered Claims Table")
    st.dataframe(df_clm.head(200))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Patients", total_patients, "#2e8ef7")
    with col2:
        kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3:
        kpi_card("Claims", total_claims, "#f7d42e")
    with col4:
        kpi_card("Payers", total_payers, "#f72e2e")

# ------------------------------------------------------------------
# DENIAL REASONS TAB (ILLUSTRATIVE)
# ------------------------------------------------------------------
with tabs[4]:
    st.subheader("Explore top denial reasons (illustrative example).")

    denial_reasons = [
        "Incorrect billing / service excluded",
        "Duplicate claims / administrative",
        "Incorrect submission / missing info",
        "Medical claim issues",
        "Ineligibility / coverage expired",
        "Partial denials",
        "Authorization missing",
        "Out of network provider",
        "Other",
    ]
    counts = [7428, 6105, 6064, 5236, 4116, 3354, 1602, 1319, 670]

    denial_df = pd.DataFrame({"Denial Reason": denial_reasons, "Count": counts})

    fig = px.bar(
        denial_df,
        x="Denial Reason",
        y="Count",
        color="Denial Reason",
        title="Most Frequent Denial Reasons",
    )
    fig.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Patients", total_patients, "#2e8ef7")
    with col2:
        kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3:
        kpi_card("Claims", total_claims, "#f7d42e")
    with col4:
        kpi_card("Payers", total_payers, "#f72e2e")

# ------------------------------------------------------------------
# PAYERS TAB
# ------------------------------------------------------------------
with tabs[5]:
    st.subheader("See distribution of payers involved in claims.")

    fig = px.histogram(
        claims,
        x="PAYER",
        title="Payer Distribution",
    )
    fig.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Patients", total_patients, "#2e8ef7")
    with col2:
        kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3:
        kpi_card("Claims", total_claims, "#f7d42e")
    with col4:
        kpi_card("Payers", total_payers, "#f72e2e")

# ------------------------------------------------------------------
# PREDICT DENIAL TAB
# ------------------------------------------------------------------
with tabs[6]:
    st.subheader("Predict Claim Denial")

    col1, col2 = st.columns(2)

    payer_options = sorted(claims["PAYER"].dropna().unique().tolist())
    denial_reason_options = [
        "Incorrect billing / service excluded",
        "Duplicate claims / administrative",
        "Incorrect submission / missing info",
        "Medical claim issues",
        "Ineligibility / coverage expired",
        "Partial denials",
        "Authorization missing",
        "Out of network provider",
        "Other",
    ]

    with col1:
        payer = st.selectbox("Select Payer", payer_options)
        encounter_class = st.selectbox(
            "Select Encounter Class",
            sorted(encounters["ENCOUNTERCLASS"].dropna().unique().tolist()),
        )
        cost = st.number_input("Procedure Cost", min_value=0, value=100)

    with col2:
        age = st.number_input("Patient Age", min_value=0, value=30)
        reason = st.selectbox("Health Issue / Reason", denial_reason_options)

    if st.button("Predict Denial"):
        payer_rate = compute_payer_denial_rate(claims, payer)

        # Basic threshold with small adjustments based on cost and age
        threshold = 5.0
        if cost > 2000:
            threshold -= 1.0
        if age > 65:
            threshold -= 1.0

        prediction = "DENIED" if payer_rate > threshold else "NOT DENIED"

        st.markdown(
            f"""### Prediction: **{prediction}** — Denial Rate: {payer_rate:.1f}%"""
        )

        st.caption(
            f"Threshold used: {threshold:.1f}%. Historical denial rate for this payer is "
            f"{payer_rate:.2f}%, based on claims with any outstanding patient balance."
        )

        st.info(
            "Most frequent denial reasons include incorrect submission, "
            "incorrect billing, and coverage issues. Double-check documentation "
            "and eligibility before submission."
        )
