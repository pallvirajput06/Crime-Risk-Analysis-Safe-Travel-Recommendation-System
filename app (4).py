"""
Sentinel — Crime Risk Analysis & Safe Travel Recommendation
Streamlit app built from the Crime_Risk_Analysis notebook logic.

Run with:
    streamlit run app.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# ----------------------------------------------------------------------
# PAGE CONFIG  (must be the first Streamlit call)
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Sentinel — Crime Risk Analysis",
    page_icon="🛡️",
    layout="wide",
)

DISTRICT_NAMES = {
    1: "Central", 2: "Wentworth", 3: "Grand Crossing", 4: "South Chicago",
    5: "Calumet", 6: "Gresham", 7: "Englewood", 8: "Chicago Lawn",
    9: "Deering", 10: "Ogden", 11: "Harrison", 12: "Near West",
    14: "Shakespeare", 15: "Austin", 16: "Jefferson Park", 17: "Albany Park",
    18: "Near North", 19: "Town Hall", 20: "Lincoln", 22: "Morgan Park",
    24: "Rogers Park", 25: "Grand Central", 31: "Unknown",
}


def time_slot(hour: int) -> str:
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"


# ----------------------------------------------------------------------
# DATA LOADING / CLEANING  (cached so it only runs once per file)
# ----------------------------------------------------------------------
@st.cache_data(show_spinner="Loading and cleaning crime data...")
def load_data(file) -> pd.DataFrame:
    df = pd.read_csv(file, low_memory=False)

    # Drop Socrata's computed-region columns if present
    drop_cols = [c for c in df.columns if c.startswith(":@computed_region")]
    df = df.drop(columns=drop_cols, errors="ignore")

    # Type conversions
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["year", "latitude", "longitude", "x_coordinate", "y_coordinate", "district"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill common missing values
    if "location_description" in df.columns:
        df["location_description"] = df["location_description"].fillna("Unknown")
    if "ward" in df.columns and df["ward"].notna().any():
        df["ward"] = df["ward"].fillna(df["ward"].mode()[0])
    if "community_area" in df.columns and df["community_area"].notna().any():
        df["community_area"] = df["community_area"].fillna(df["community_area"].mode()[0])

    df = df.dropna(subset=["date"])

    # Derived time fields
    df["hour"] = df["date"].dt.hour
    df["day_name"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.month_name()
    df["time_slot"] = df["hour"].apply(time_slot)
    df["weekend"] = df["day_name"].isin(["Saturday", "Sunday"])

    # District name mapping
    if "district" in df.columns:
        df["district_name"] = df["district"].map(DISTRICT_NAMES)
        df["district_name"] = df["district_name"].fillna("Unknown")

    return df


def crime_risk_analysis(df: pd.DataFrame, district: str, slot: str):
    data = df[(df["district_name"] == district) & (df["time_slot"] == slot)]

    if data.empty:
        st.warning("No data available for this district and time slot.")
        return

    total_crimes = len(data)
    common_crime = data["primary_type"].mode()[0]

    if total_crimes >= 18000:
        risk, color = "HIGH", "🔴"
    elif total_crimes >= 12000:
        risk, color = "MEDIUM", "🟡"
    else:
        risk, color = "LOW", "🟢"

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Crimes", f"{total_crimes:,}")
    c2.metric("Most Common Crime", common_crime)
    c3.metric("Risk Level", f"{color} {risk}")

    st.subheader("Safety Tips")
    if risk == "HIGH":
        tips = [
            "Avoid isolated streets.",
            "Travel with someone if possible.",
            "Share your live location.",
            "Prefer trusted cab or public transport.",
            "Stay alert and avoid carrying valuables.",
        ]
    elif risk == "MEDIUM":
        tips = [
            "Stay alert.",
            "Use well-lit roads.",
            "Keep your phone charged.",
            "Inform a family member about your trip.",
        ]
    else:
        tips = [
            "Area appears comparatively safer based on historical data.",
            "Stay aware of your surroundings.",
            "Follow normal safety precautions.",
        ]
    for tip in tips:
        st.markdown(f"- {tip}")


# ----------------------------------------------------------------------
# SIDEBAR — DATA INPUT
# ----------------------------------------------------------------------
st.sidebar.title("🛡️ Sentinel")
st.sidebar.caption("Crime Risk Analysis & Safe Travel Recommendation")

uploaded = st.sidebar.file_uploader(
    "Upload cleaned Chicago crime CSV",
    type=["csv"],
    help="Export the dataframe from your notebook with df.to_csv(...) and upload it here.",
)

if uploaded is None:
    st.title("🛡️ Sentinel — Crime Risk Analysis")
    st.info(
        "👈 Upload your Chicago crime CSV in the sidebar to get started.\n\n"
        "This should be the raw (or lightly processed) export from the Socrata "
        "`ijzp-q8t2` dataset used in your notebook — it needs at minimum the "
        "columns `date`, `district`, and `primary_type`."
    )
    st.stop()

df = load_data(uploaded)

required_cols = {"district_name", "time_slot", "primary_type"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"Uploaded file is missing required columns: {', '.join(missing)}")
    st.stop()

# ----------------------------------------------------------------------
# MAIN — FILTERS + RISK ANALYSIS
# ----------------------------------------------------------------------
st.title("🛡️ Sentinel — Crime Risk Analysis")
st.caption(f"Loaded {len(df):,} records")

districts = sorted(df["district_name"].dropna().unique())
slots = ["Morning", "Afternoon", "Evening", "Night"]

col1, col2 = st.columns(2)
with col1:
    district = st.selectbox("District", districts)
with col2:
    slot = st.selectbox("Time Slot", slots)

st.divider()
crime_risk_analysis(df, district, slot)

# ----------------------------------------------------------------------
# CHARTS
# ----------------------------------------------------------------------
st.divider()
st.header("Exploratory Charts")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Top Crime Types", "By Time Slot", "By District", "District × Time Heatmap", "Weekend vs Weekday"]
)

with tab1:
    fig, ax = plt.subplots(figsize=(10, 6))
    order = df["primary_type"].value_counts().head(10).index
    sns.countplot(data=df, y="primary_type", order=order, ax=ax)
    ax.set_title("Top 10 Crime Types")
    ax.set_xlabel("Crime Count")
    ax.set_ylabel("Crime Type")
    st.pyplot(fig)

with tab2:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=df, x="time_slot", order=slots, ax=ax)
    ax.set_title("Crime Count by Time Slot")
    st.pyplot(fig)

with tab3:
    fig, ax = plt.subplots(figsize=(10, 8))
    order = df["district_name"].value_counts().index
    sns.countplot(data=df, y="district_name", order=order, ax=ax)
    ax.set_title("Crime Count by District")
    st.pyplot(fig)

with tab4:
    fig, ax = plt.subplots(figsize=(10, 8))
    district_time = pd.crosstab(df["district_name"], df["time_slot"])
    sns.heatmap(district_time, annot=True, fmt="d", cmap="Reds", ax=ax)
    ax.set_title("Crime Count by District and Time Slot")
    st.pyplot(fig)

with tab5:
    fig, ax = plt.subplots(figsize=(5, 5))
    df["weekend"].value_counts().plot(kind="pie", autopct="%1.1f%%", ax=ax)
    ax.set_ylabel("")
    ax.set_title("Weekend vs Weekday Crime")
    st.pyplot(fig)
