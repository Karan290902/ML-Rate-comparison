import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Insurance Insurer Comparison Engine",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("Insurance Insurer Comparison Dashboard")

st.write("""
This dashboard helps compare insurers based on:

- Rate Per Lakh
- COA %
- Age
- Tenure
- Overall business attractiveness
""")

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Insurer Comparison Excel/CSV",
    type=["xlsx", "csv"]
)

# ---------------------------------------------------
# MAIN LOGIC
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

    # Check columns
    if all(col in df.columns for col in required_cols):

        # ---------------------------------------------------
        # DATA CLEANING
        # ---------------------------------------------------

        df['Rate_Per_Lakh'] = pd.to_numeric(
            df['Rate_Per_Lakh'],
            errors='coerce'
        )

        df['COA'] = pd.to_numeric(
            df['COA'],
            errors='coerce'
        )

        df['Age'] = pd.to_numeric(
            df['Age'],
            errors='coerce'
        )

        df['Tenure'] = pd.to_numeric(
            df['Tenure'],
            errors='coerce'
        )

        # Remove missing values
        df = df.dropna()

        # ---------------------------------------------------
        # BUSINESS SCORING LOGIC
        # ---------------------------------------------------

        # Lower Rate = Better
        df['Rate_Score'] = (
            (1 / df['Rate_Per_Lakh']) /
            (1 / df['Rate_Per_Lakh']).max()
        ) * 100

        # Higher COA = Better
        df['COA_Score'] = (
            df['COA'] /
            df['COA'].max()
        ) * 100

        # Stability score
        # Lower variance across age/tenure preferred
        df['Stability_Score'] = 100 - (
            (
                df['Rate_Per_Lakh'] -
                df['Rate_Per_Lakh'].mean()
            ).abs()
            /
            df['Rate_Per_Lakh'].max()
        ) * 100

        # Final weighted score
        df['Final_Score'] = (
            df['Rate_Score'] * 0.50 +
            df['COA_Score'] * 0.30 +
            df['Stability_Score'] * 0.20
        )

        # ---------------------------------------------------
        # SHOW SCORES
        # ---------------------------------------------------

        st.subheader("Calculated Insurer Scores")

        st.dataframe(
            df[
                [
                    'Insurer',
                    'Age',
                    'Tenure',
                    'Rate_Per_Lakh',
                    'COA',
                    'Rate_Score',
                    'COA_Score',
                    'Stability_Score',
                    'Final_Score'
                ]
            ]
        )

        # ---------------------------------------------------
        # INSURER RANKING
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

        # Best insurer
        best_insurer = ranking.iloc[0]['Insurer']

        best_score = ranking.iloc[0]['Final_Score']

        st.success(
            f"""
            Best Overall Insurer:
            {best_insurer}

            Average Business Score:
            {best_score:.2f}
            """
        )

        # ---------------------------------------------------
        # FILTERS
        # ---------------------------------------------------

        st.sidebar.header("Filters")

        selected_age = st.sidebar.selectbox(
            "Select Age",
            sorted(df['Age'].unique())
        )

        selected_tenure = st.sidebar.selectbox(
            "Select Tenure",
            sorted(df['Tenure'].unique())
        )

        # Filtered Data
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
                Best insurer for selected criteria:

                {best_filtered['Insurer']}

                Rate Per Lakh:
                {best_filtered['Rate_Per_Lakh']}

                COA:
                {best_filtered['COA']}%
                """
            )

        # ---------------------------------------------------
        # BUSINESS INSIGHTS
        # ---------------------------------------------------

        st.subheader("Business Interpretation")

        st.write("""
        ### How Final Score is Calculated

        - Lower Rate Per Lakh = Better customer pricing
        - Higher COA = Better broker economics
        - Stable pricing across age & tenure = Better scalability

        ### Best Insurer Usually Means:

        - Competitive pricing
        - Sustainable COA
        - Better age-term stability
        - Better business scalability

        ### Use Cases

        - Group Insurance
        - Affinity Business
        - Embedded Insurance
        - PA / CI / GCL / GTL Comparison
        """)

    else:

        st.error(f"""
        Missing Required Columns.

        Required Columns:
        {required_cols}
        """)

# ---------------------------------------------------
# NO FILE
# ---------------------------------------------------

else:

    st.warning("Please upload an Excel or CSV file.")
