import streamlit as st
import pandas as pd

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
Upload multiple insurer rate-card Excel files.

Expected Excel Format:

| Entry Age | 1 | 2 | 3 | 4 | 5 | ... |

Where:
- Entry Age = Age
- Columns 1,2,3... = Tenure
- Values = Rate Per Lakh
""")

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload Multiple Insurer Excel Files",
    type=["xlsx", "csv"],
    accept_multiple_files=True
)

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if uploaded_files:

    all_data = []

    # ---------------------------------------------------
    # PROCESS EACH FILE
    # ---------------------------------------------------

    for uploaded_file in uploaded_files:

        insurer_name = uploaded_file.name.split(".")[0]

        # Read file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # ---------------------------------------------------
        # VALIDATION
        # ---------------------------------------------------

        if 'Entry Age' not in df.columns:

            st.error(
                f"'Entry Age' column missing in {uploaded_file.name}"
            )

            continue

        # ---------------------------------------------------
        # CONVERT MATRIX TO LONG FORMAT
        # ---------------------------------------------------

        df_long = df.melt(
            id_vars=['Entry Age'],
            var_name='Tenure',
            value_name='Rate_Per_Lakh'
        )

        # Rename column
        df_long.rename(
            columns={
                'Entry Age': 'Age'
            },
            inplace=True
        )

        # Add insurer name
        df_long['Insurer'] = insurer_name

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
        # APPEND
        # ---------------------------------------------------

        all_data.append(df_long)

    # ---------------------------------------------------
    # MERGE ALL INSURERS
    # ---------------------------------------------------

    if all_data:

        final_df = pd.concat(
            all_data,
            ignore_index=True
        )

        # ---------------------------------------------------
        # SCORING
        # ---------------------------------------------------

        # Lower Rate = Better
        final_df['Rate_Score'] = (
            (
                1 / final_df['Rate_Per_Lakh']
            ) /
            (
                1 / final_df['Rate_Per_Lakh']
            ).max()
        ) * 100

        # Final score
        final_df['Final_Score'] = (
            final_df['Rate_Score']
        )

        # ---------------------------------------------------
        # SHOW DATA
        # ---------------------------------------------------

        st.subheader("Combined Comparison Data")

        st.dataframe(final_df)

        # ---------------------------------------------------
        # OVERALL INSURER RANKING
        # ---------------------------------------------------

        ranking = (
            final_df.groupby('Insurer')['Final_Score']
            .mean()
            .reset_index()
            .sort_values(
                by='Final_Score',
                ascending=False
            )
        )

        st.subheader("Overall Insurer Ranking")

        st.dataframe(ranking)

        best_overall = ranking.iloc[0]['Insurer']

        st.success(
            f"Best Overall Insurer: {best_overall}"
        )

        # ---------------------------------------------------
        # SIDEBAR FILTERS
        # ---------------------------------------------------

        st.sidebar.header("Comparison Filters")

        selected_age = st.sidebar.selectbox(
            "Select Age",
            sorted(final_df['Age'].unique())
        )

        selected_tenure = st.sidebar.selectbox(
            "Select Tenure",
            sorted(final_df['Tenure'].unique())
        )

        # ---------------------------------------------------
        # FILTER DATA
        # ---------------------------------------------------

        filtered_df = final_df[
            (final_df['Age'] == selected_age) &
            (final_df['Tenure'] == selected_tenure)
        ]

        st.subheader(
            f"Comparison for Age {selected_age} | Tenure {selected_tenure}"
        )

        filtered_df = filtered_df.sort_values(
            by='Rate_Per_Lakh'
        )

        st.dataframe(filtered_df)

        # ---------------------------------------------------
        # BEST INSURER FOR FILTER
        # ---------------------------------------------------

        if not filtered_df.empty:

            best = filtered_df.iloc[0]

            st.success(
                f"""
                Best Insurer for Age {selected_age}
                and Tenure {selected_tenure}

                Insurer:
                {best['Insurer']}

                Rate Per Lakh:
                {best['Rate_Per_Lakh']}
                """
            )

        # ---------------------------------------------------
        # LOWEST RATE TABLE
        # ---------------------------------------------------

        st.subheader("Lowest Rate Summary")

        lowest_summary = (
            final_df.loc[
                final_df.groupby(
                    ['Age', 'Tenure']
                )['Rate_Per_Lakh'].idxmin()
            ]
        )

        st.dataframe(
            lowest_summary[
                [
                    'Age',
                    'Tenure',
                    'Insurer',
                    'Rate_Per_Lakh'
                ]
            ]
        )

        # ---------------------------------------------------
        # BUSINESS INTERPRETATION
        # ---------------------------------------------------

        st.subheader("Business Interpretation")

        st.write("""
        ### Lower Rate Per Lakh Means:
        - Better customer pricing
        - Better conversion
        - Better scalability
        - Stronger affinity business proposition

        ### Best Insurer Usually:
        - Has lower pricing across most ages
        - Has smoother pricing across tenures
        - Does not sharply increase rates at higher ages
        """)

else:

    st.warning(
        "Please upload insurer Excel files."
    )
