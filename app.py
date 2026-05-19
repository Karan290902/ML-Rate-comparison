import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Insurance Insurer Comparison",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("Insurance Insurer Comparison Dashboard")

st.write("""
Compare insurers based on:
- Rate Per Lakh
- COA %
- Age
- Tenure
""")

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Comparison Excel File",
    type=["xlsx", "csv"]
)

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if uploaded_file:

    # Read file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Uploaded Data")

    st.dataframe(df)

    # ---------------------------------------------------
    # REQUIRED COLUMNS
    # ---------------------------------------------------

    required_cols = [
        'Insurer',
        'Age',
        'Tenure',
        'Rate_Per_Lakh',
        'COA'
    ]

    # ---------------------------------------------------
    # CHECK COLUMNS
    # ---------------------------------------------------

    if all(col in df.columns for col in required_cols):

        # Convert numeric
        df['Age'] = pd.to_numeric(df['Age'])

        df['Tenure'] = pd.to_numeric(df['Tenure'])

        df['Rate_Per_Lakh'] = pd.to_numeric(
            df['Rate_Per_Lakh']
        )

        df['COA'] = pd.to_numeric(df['COA'])

        # ---------------------------------------------------
        # SCORING LOGIC
        # ---------------------------------------------------

        # Lower Rate = Better
        df['Rate_Score'] = (
            (
                1 / df['Rate_Per_Lakh']
            ) /
            (
                1 / df['Rate_Per_Lakh']
            ).max()
        ) * 100

        # Higher COA = Better
        df['COA_Score'] = (
            df['COA'] /
            df['COA'].max()
        ) * 100

        # Stability
        df['Stability_Score'] = 100 - (
            (
                abs(
                    df['Rate_Per_Lakh'] -
                    df['Rate_Per_Lakh'].mean()
                )
            ) /
            df['Rate_Per_Lakh'].max()
        ) * 100

        # Final Score
        df['Final_Score'] = (
            df['Rate_Score'] * 0.60 +
            df['COA_Score'] * 0.25 +
            df['Stability_Score'] * 0.15
        )

        # ---------------------------------------------------
        # SHOW SCORES
        # ---------------------------------------------------

        st.subheader("Calculated Scores")

        st.dataframe(df)

        # ---------------------------------------------------
        # OVERALL RANKING
        # ---------------------------------------------------

        ranking = (
            df.groupby('Insurer')['Final_Score']
            .mean()
            .reset_index()
            .sort_values(
                by='Final_Score',
                ascending=False
            )
        )

        st.subheader("Overall Insurer Ranking")

        st.dataframe(ranking)

        # ---------------------------------------------------
        # BEST INSURER
        # ---------------------------------------------------

        best_insurer = ranking.iloc[0]['Insurer']

        st.success(
            f"Best Overall Insurer: {best_insurer}"
        )

        # ---------------------------------------------------
        # FILTERS
        # ---------------------------------------------------

        st.sidebar.header("Comparison Filters")

        selected_age = st.sidebar.selectbox(
            "Select Age",
            sorted(df['Age'].unique())
        )

        selected_tenure = st.sidebar.selectbox(
            "Select Tenure",
            sorted(df['Tenure'].unique())
        )

        # ---------------------------------------------------
        # FILTER DATA
        # ---------------------------------------------------

        filtered_df = df[
            (df['Age'] == selected_age) &
            (df['Tenure'] == selected_tenure)
        ]

        st.subheader(
            f"Comparison for Age {selected_age} | Tenure {selected_tenure}"
        )

        st.dataframe(filtered_df)

        # ---------------------------------------------------
        # BEST FILTERED INSURER
        # ---------------------------------------------------

        if not filtered_df.empty:

            best_filtered = filtered_df.sort_values(
                by='Final_Score',
                ascending=False
            ).iloc[0]

            st.info(
                f"""
                Best Insurer:

                {best_filtered['Insurer']}

                Rate Per Lakh:
                {best_filtered['Rate_Per_Lakh']}

                COA:
                {best_filtered['COA']}%
                """
            )

        # ---------------------------------------------------
        # LOWEST RATE INSURER
        # ---------------------------------------------------

        lowest_rate = filtered_df.sort_values(
            by='Rate_Per_Lakh'
        ).iloc[0]

        st.subheader("Lowest Rate Insurer")

        st.write(
            f"""
            Insurer:
            {lowest_rate['Insurer']}

            Rate:
            {lowest_rate['Rate_Per_Lakh']}
            """
        )

        # ---------------------------------------------------
        # HIGHEST COA INSURER
        # ---------------------------------------------------

        highest_coa = filtered_df.sort_values(
            by='COA',
            ascending=False
        ).iloc[0]

        st.subheader("Highest COA Insurer")

        st.write(
            f"""
            Insurer:
            {highest_coa['Insurer']}

            COA:
            {highest_coa['COA']}%
            """
        )

        # ---------------------------------------------------
        # BUSINESS INTERPRETATION
        # ---------------------------------------------------

        st.subheader("Business Interpretation")

        st.write("""
        ### Lower Rate Per Lakh
        Better for:
        - customer conversion
        - scalability
        - affinity business

        ### Higher COA
        Better for:
        - broker revenue
        - acquisition economics

        ### Best Insurer
        Usually means:
        - competitive pricing
        - reasonable COA
        - stable pricing across age & tenure
        """)

    else:

        st.error(
            f"""
            Missing Required Columns.

            Required:
            {required_cols}
            """
        )

else:

    st.warning(
        "Please upload Excel or CSV file."
    )
