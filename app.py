import streamlit as st
import pandas as pd

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Insurance Comparison Engine",
    layout="wide"
)

st.title("Insurance Insurer Comparison Dashboard")

st.write("""
Compare insurers based on:
- Rate Per Lakh
- COA
- Entry Age
- Tenure
""")

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx", "csv"]
)

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Uploaded Rate Card")

    st.dataframe(df)

    # ---------------------------------------------------
    # INSURER DETAILS
    # ---------------------------------------------------

    st.sidebar.header("Insurer Details")

    insurer_name = st.sidebar.text_input(
        "Insurer Name",
        value="Bajaj"
    )

    coa = st.sidebar.number_input(
        "COA %",
        value=8.0
    )

    # ---------------------------------------------------
    # CONVERT MATRIX TO LONG FORMAT
    # ---------------------------------------------------

    df_long = df.melt(
        id_vars=['Entry Age'],
        var_name='Tenure',
        value_name='Rate_Per_Lakh'
    )

    df_long.rename(
        columns={
            'Entry Age': 'Age'
        },
        inplace=True
    )

    # Add insurer
    df_long['Insurer'] = insurer_name

    # Add COA
    df_long['COA'] = coa

    # ---------------------------------------------------
    # CLEAN DATA
    # ---------------------------------------------------

    df_long['Age'] = pd.to_numeric(
        df_long['Age'],
        errors='coerce'
    )

    df_long['Tenure'] = pd.to_numeric(
        df_long['Tenure'],
        errors='coerce'
    )

    df_long['Rate_Per_Lakh'] = pd.to_numeric(
        df_long['Rate_Per_Lakh'],
        errors='coerce'
    )

    df_long.dropna(inplace=True)

    # ---------------------------------------------------
    # SCORING LOGIC
    # ---------------------------------------------------

    # Lower rate better
    df_long['Rate_Score'] = (
        (
            1 / df_long['Rate_Per_Lakh']
        ) /
        (
            1 / df_long['Rate_Per_Lakh']
        ).max()
    ) * 100

    # Higher COA better
    df_long['COA_Score'] = (
        df_long['COA'] /
        df_long['COA'].max()
    ) * 100

    # Final score
    df_long['Final_Score'] = (
        df_long['Rate_Score'] * 0.7 +
        df_long['COA_Score'] * 0.3
    )

    # ---------------------------------------------------
    # SHOW RESULTS
    # ---------------------------------------------------

    st.subheader("Processed Comparison Data")

    st.dataframe(df_long)

    # ---------------------------------------------------
    # FILTERS
    # ---------------------------------------------------

    st.sidebar.header("Comparison Filters")

    selected_age = st.sidebar.selectbox(
        "Select Age",
        sorted(df_long['Age'].unique())
    )

    selected_tenure = st.sidebar.selectbox(
        "Select Tenure",
        sorted(df_long['Tenure'].unique())
    )

    filtered = df_long[
        (df_long['Age'] == selected_age) &
        (df_long['Tenure'] == selected_tenure)
    ]

    st.subheader(
        f"Comparison for Age {selected_age} | Tenure {selected_tenure}"
    )

    st.dataframe(filtered)

    # ---------------------------------------------------
    # BEST RESULT
    # ---------------------------------------------------

    if not filtered.empty:

        best = filtered.sort_values(
            by='Final_Score',
            ascending=False
        ).iloc[0]

        st.success(
            f"""
            Best Insurer:
            {best['Insurer']}

            Rate Per Lakh:
            {best['Rate_Per_Lakh']}

            COA:
            {best['COA']}%
            """
        )

    # ---------------------------------------------------
    # BUSINESS INTERPRETATION
    # ---------------------------------------------------

    st.subheader("Interpretation")

    st.write("""
    Lower rates improve:
    - customer conversion
    - scalability
    - competitiveness

    Higher COA improves:
    - broker revenue
    - acquisition economics

    Best insurer usually balances:
    - low rates
    - reasonable COA
    - stable pricing
    """)

else:

    st.warning("Please upload an Excel file.")
