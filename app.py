import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------
st.set_page_config(
    page_title="Real-Time Insurance Claim Denial Prediction",
    layout="wide"
)

# -----------------------------------------------------------
# DATA LOADING
# -----------------------------------------------------------
@st.cache_data
def load_data():
    # Local CSVs from GitHub repo
    patients = pd.read_csv("data/patients_filtered.csv")
    encounters = pd.read_csv("data/encounters_filtered.csv")
    payer_trans = pd.read_csv("data/payer_transitions_filtered.csv")

    # Big files from Google Drive
    claims = pd.read_csv(
        "https://drive.google.com/uc?export=download&id=1SgsAesNi3SHouEtESiNnhY0KdFkvXsr9"
    )
    transactions = pd.read_csv(
        "https://drive.google.com/uc?export=download&id=1CXiodxDFeTDxGc0iyIovXY2BDekHtKtd"
    )

    # ---------- Fix/standardize columns ----------

    # Encounter class: make sure column is ENCOUNTERCLASS
    if "ENCOUNTERCLASS" not in encounters.columns and "CLASS" in encounters.columns:
        encounters = encounters.rename(columns={"CLASS": "ENCOUNTERCLASS"})

    # Claims STATUS column
    if "STATUS" not in claims.columns:
        if "STATUSP" in claims.columns:
            claims["STATUS"] = claims["STATUSP"]
        elif "STATUS1" in claims.columns:
            claims["STATUS"] = claims["STATUS1"]
        else:
            claims["STATUS"] = "UNKNOWN"

    # Simple DENIED flag based on patient outstanding balance
    if "OUTSTANDINGP" in claims.columns:
        claims["DENIED"] = claims["OUTSTANDINGP"] > 0
    else:
        claims["DENIED"] = False

    # Attach payer from payer_transitions (latest payer per patient)
    if (
        "PATIENTID" in claims.columns
        and "PATIENT" in payer_trans.columns
        and "PAYER" in payer_trans.columns
    ):
        pt_sorted = payer_trans.copy()
        if "START_DATE" in pt_sorted.columns:
            pt_sorted["START_DATE"] = pd.to_datetime(
                pt_sorted["START_DATE"], errors="coerce"
            )
            pt_sorted = pt_sorted.sort_values("START_DATE")
        latest_payer = pt_sorted.drop_duplicates("PATIENT", keep="last")[
            ["PATIENT", "PAYER"]
        ]
        claims = claims.merge(
            latest_payer, left_on="PATIENTID", right_on="PATIENT", how="left"
        )
    if "PAYER" not in claims.columns:
        claims["PAYER"] = "Unknown"

    # Parse FROMDATE in transactions for date filtering
    if "FROMDATE" in transactions.columns:
        transactions["FROMDATE"] = pd.to_datetime(
            transactions["FROMDATE"], errors="coerce"
        )

    return patients, encounters, claims, transactions, payer_trans


patients, encounters, claims, transactions, payer_trans = load_data()

# -----------------------------------------------------------
# HELPERS
# -----------------------------------------------------------
def kpi_card(label: str, value, color: str) -> None:
    """Simple KPI card."""
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


def compute_payer_denial_rate(claims_df: pd.DataFrame, payer_id: str) -> float:
    """Percent of claims for this payer that are marked as DENIED."""
    subset = claims_df[claims_df["PAYER"] == payer_id]
    if len(subset) == 0:
        return 0.0
    return float(subset["DENIED"].mean() * 100.0)


# -----------------------------------------------------------
# KPIs
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# OVERVIEW TAB
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# PATIENTS TAB
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# ENCOUNTERS TAB
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# CLAIMS TAB  (includes Total Financial Exposure chart)
# -----------------------------------------------------------
with tabs[3]:
    st.subheader("Review claims status, financial exposure, and payer details.")

    # ---------- Top: Financial exposure ----------
    st.markdown("### Total Financial Exposure")

    # Use only valid dates
    tx_valid = transactions.dropna(subset=["FROMDATE"]).copy()

    if tx_valid.empty:
        st.info("No valid transaction dates available.")
    else:
        min_tx = tx_valid["FROMDATE"].min()
        max_tx = tx_valid["FROMDATE"].max()

        ten_years_ago = max_tx - pd.DateOffset(years=10)
        default_start = max(min_tx, ten_years_ago)

        min_date = min_tx.date()
        max_date = max_tx.date()
        default_start_date = default_start.date()

        date_range = st.date_input(
            "Filter by Service Date (Last 10 Years)",
            value=(default_start_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        if isinstance(date_range, tuple):
            start_date, end_date = date_range
        else:
            start_date, end_date = date_range, max_date

        mask = (tx_valid["FROMDATE"].dt.date >= start_date) & (
            tx_valid["FROMDATE"].dt.date <= end_date
        )
        tx_filtered = tx_valid[mask].copy()

        exposure_by_date = (
            tx_filtered.assign(ServiceDate=tx_filtered["FROMDATE"].dt.date)
            .groupby("ServiceDate", as_index=False)["AMOUNT"]
            .sum()
        )

        if not exposure_by_date.empty:
            fig_exposure = px.line(
                exposure_by_date,
                x="ServiceDate",
                y="AMOUNT",
                title="Total Financial Exposure over Time",
                labels={
                    "ServiceDate": "Service Date",
                    "AMOUNT": "Exposure (Sum of AMOUNT)",
                },
            )
            st.plotly_chart(fig_exposure, use_container_width=True)
        else:
            st.info("No transactions found in this date range.")

        total_exposure = tx_filtered["AMOUNT"].sum()
        st.markdown(
            f"**Total Exposure in selected period:** ${total_exposure:,.2f}"
        )
        st.caption(
            "Exposure = Sum of AMOUNT from claims_transactions_filtered for filtered claim lines."
        )

    st.markdown("---")

    # ---------- Bottom: claims status & payer ----------
    st.markdown("### Claims by Status and Payer")

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

# -----------------------------------------------------------
# DENIAL REASONS TAB (illustrative counts)
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# PAYERS TAB
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# PREDICT DENIAL TAB
# -----------------------------------------------------------
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
            f"Threshold used: {threshold:.1f}%. Historical denial rate for this payer "
            f"is {payer_rate:.2f}%, based on claims with any outstanding patient balance."
        )

        st.info(
            "Most frequent denial reasons include incorrect submission, "
            "incorrect billing, and coverage issues. Double-check documentation "
            "and eligibility before submission."
        )
