import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Real-Time Insurance Claim Denial Prediction",
    layout="wide"
)

# ----------------------------
# LOAD DATA
# ----------------------------
@st.cache_data
def load_data():
    # Small files from GitHub repo
    patients = pd.read_csv("data/patients_filtered.csv")
    encounters = pd.read_csv("data/encounters_filtered.csv")
    payer_trans = pd.read_csv("data/payer_transitions_filtered.csv")

    # CLAIMS file (46 MB) from Google Drive
    claims = pd.read_csv(
        "https://drive.google.com/uc?export=download&id=1SgsAesNi3SHouEtESiNnhY0KdFkvXsr9"
    )

    # TRANSACTIONS file (500 MB) from Google Drive
    transactions = pd.read_csv(
        "https://drive.google.com/uc?export=download&id=1CXiodxDFeTDxGc0iyIovXY2BDekHtKtd"
    )

    return patients, encounters, claims, transactions, payer_trans


patients, encounters, claims, transactions, payer_trans = load_data()

# ----------------------------
# KPI NUMBERS
# ----------------------------
total_patients = len(patients)
total_encounters = len(encounters)
total_claims = len(claims)
total_payers = claims["PAYERID"].nunique()


# ----------------------------
# KPI CARD FUNCTION
# ----------------------------
def kpi_card(label, value, color):
    st.markdown(
        f"""
        <div style="background:white; border-radius:10px; padding:20px; 
             border:2px solid {color}; text-align:center; width:100%;">
            <h3 style="color:black;">{label}</h3>
            <h1 style="color:{color};">{value}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------------------
# TABS
# ----------------------------
tabs = st.tabs(["Overview", "Patients", "Encounters", "Claims",
                "Denial Reasons", "Payers", "Predict Denial"])


# ============================================================
# 1. OVERVIEW TAB
# ============================================================
with tabs[0]:
    st.subheader("Overview: Use the tabs above to explore claims, denial reasons, patients, and payers.")

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card("Patients", total_patients, "#2e8ef7")
    with col2: kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3: kpi_card("Claims", total_claims, "#f7d42e")
    with col4: kpi_card("Payers", total_payers, "#f72e2e")


# ============================================================
# 2. PATIENTS TAB
# ============================================================
with tabs[1]:
    st.subheader("View and analyze the distribution of patients by gender and birthdate.")
    gender = st.selectbox("Filter by Gender", ["All"] + sorted(patients["GENDER"].dropna().unique().tolist()))

    df = patients.copy()
    if gender != "All":
        df = df[df["GENDER"] == gender]

    fig = px.histogram(df, x="BIRTHDATE", color="GENDER", barmode="stack",
                       title="Patients by Birthdate")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card("Patients", total_patients, "#2e8ef7")
    with col2: kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3: kpi_card("Claims", total_claims, "#f7d42e")
    with col4: kpi_card("Payers", total_payers, "#f72e2e")


# ============================================================
# 3. ENCOUNTERS TAB
# ============================================================
with tabs[2]:
    st.subheader("View encounter breakdown and class filters.")

    classes = encounters["CLASS"].dropna().unique()
    selected_class = st.selectbox("Filter by Encounter Class", ["All"] + sorted(classes))

    df = encounters.copy()
    if selected_class != "All":
        df = df[df["CLASS"] == selected_class]

    fig = px.histogram(df, x="CLASS", title="Encounters by Class")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card("Patients", total_patients, "#2e8ef7")
    with col2: kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3: kpi_card("Claims", total_claims, "#f7d42e")
    with col4: kpi_card("Payers", total_payers, "#f72e2e")


# ============================================================
# 4. CLAIMS TAB
# ============================================================
with tabs[3]:
    st.subheader("Review claims status and payer details.")

    status_list = claims["STATUS"].dropna().unique()
    payers_list = claims["PAYERID"].dropna().unique()

    status_sel = st.selectbox("Filter by Claim Status", ["All"] + sorted(status_list))
    payer_sel = st.selectbox("Filter by Payer", ["All"] + sorted(payers_list))

    df = claims.copy()
    if status_sel != "All":
        df = df[df["STATUS"] == status_sel]
    if payer_sel != "All":
        df = df[df["PAYERID"] == payer_sel]

    fig = px.histogram(df, x="STATUS", title="Claims by Status", color="STATUS")
    st.plotly_chart(fig, use_container_width=True)

    st.write("Filtered Claims Table")
    st.dataframe(df.head(200))

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card("Patients", total_patients, "#2e8ef7")
    with col2: kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3: kpi_card("Claims", total_claims, "#f7d42e")
    with col4: kpi_card("Payers", total_payers, "#f72e2e")


# ============================================================
# 5. DENIAL REASONS TAB
# ============================================================
with tabs[4]:
    st.subheader("Explore top denial reasons.")

    fig = px.histogram(claims, x="DENIAL_REASON", title="Most Frequent Denial Reasons",
                       color="DENIAL_REASON")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card("Patients", total_patients, "#2e8ef7")
    with col2: kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3: kpi_card("Claims", total_claims, "#f7d42e")
    with col4: kpi_card("Payers", total_payers, "#f72e2e")


# ============================================================
# 6. PAYERS TAB
# ============================================================
with tabs[5]:
    st.subheader("See distribution of payers involved in claims and transitions.")

    fig = px.histogram(claims, x="PAYERID", title="Payer Distribution")
    fig.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card("Patients", total_patients, "#2e8ef7")
    with col2: kpi_card("Encounters", total_encounters, "#3d2ef7")
    with col3: kpi_card("Claims", total_claims, "#f7d42e")
    with col4: kpi_card("Payers", total_payers, "#f72e2e")


# ============================================================
# 7. PREDICT DENIAL TAB
# ============================================================
with tabs[6]:
    st.subheader("Predict Claim Denial")

    col1, col2 = st.columns(2)

    with col1:
        payer = st.selectbox("Select Payer", sorted(claims["PAYERID"].dropna().unique()))
        encounter_class = st.selectbox("Select Encounter Class", sorted(encounters["CLASS"].dropna().unique()))
        cost = st.number_input("Procedure Cost", min_value=0, value=100)

    with col2:
        age = st.number_input("Patient Age", min_value=0, value=30)
        reason = st.selectbox("Health Issue / Reason",
                              sorted(claims["DENIAL_REASON"].dropna().unique()))

    if st.button("Predict Denial"):

        payer_rate = len(claims[(claims["PAYERID"] == payer) & (claims["STATUS"] == "DENIED")]) / \
                     len(claims[claims["PAYERID"] == payer]) * 100

        threshold = 7.5 + 10

        prediction = "DENIED" if payer_rate > threshold else "NOT DENIED"

        st.markdown(f"""
        ### Prediction: **{prediction}**  
        **Denial Rate: {payer_rate:.1f}%**
        """)

        st.info("Most frequent denial reasons: Incorrect submission/missing info, Incorrect billing, Coverage expired.")
        st.warning("Try submitting to a payer with lower denial rate.")
