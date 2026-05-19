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
    # PROCESS FILES
    # ---------------------------------------------------

    for uploaded_file in uploaded_files:

        insurer_name = uploaded_file.name.split(".")[0]

        # Read file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Validate
        if 'Entry Age' not in df.columns:

            st.error(
                f"'Entry Age' column missing in {uploaded_file.name}"
            )

            continue

        # Convert matrix to long format
        df_long = df.melt(
            id_vars=['Entry Age'],
            var_name='Tenure',
            value_name='Rate_Per_Lakh'
        )

        # Rename
        df_long.rename(
            columns={
                'Entry Age': 'Age'
            },
            inplace=True
        )

        # Add insurer
        df_long['Insurer'] = insurer_name

        # Convert numeric
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

        # Remove nulls
        df_long.dropna(inplace=True)

        # Append
        all_data.append(df_long)

    # ---------------------------------------------------
    # FINAL DATA
    # ---------------------------------------------------

    if all_data:

        final_df = pd.concat(
            all_data,
            ignore_index=True
        )

        # ---------------------------------------------------
        # FILTERS
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

        filtered_df = filtered_df.sort_values(
            by='Rate_Per_Lakh'
        )

        # ---------------------------------------------------
        # SHOW COMPARISON
        # ---------------------------------------------------

        st.subheader(
            f"Comparison for Age {selected_age} | Tenure {selected_tenure}"
        )

        st.dataframe(filtered_df)

        # ---------------------------------------------------
        # BEST INSURER
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
        # OVERALL BEST INSURER
        # ---------------------------------------------------

        overall_best = (
            final_df.groupby('Insurer')['Rate_Per_Lakh']
            .mean()
            .reset_index()
            .sort_values(
                by='Rate_Per_Lakh'
            )
        )

        best_overall = overall_best.iloc[0]

        st.subheader("Overall Best Insurer")

        st.success(
            f"""
            Insurer:
            {best_overall['Insurer']}

            Average Rate Per Lakh:
            {round(best_overall['Rate_Per_Lakh'], 2)}
            """
        )

        # ---------------------------------------------------
        # BEST INSURER BY AGE SLAB
        # ---------------------------------------------------

        st.subheader("Best Insurer by Age Slab")

        age_summary = (
            final_df.groupby(
                ['Age', 'Insurer']
            )['Rate_Per_Lakh']
            .mean()
            .reset_index()
        )

        best_age = (
            age_summary.loc[
                age_summary.groupby('Age')[
                    'Rate_Per_Lakh'
                ].idxmin()
            ]
        )

        st.dataframe(best_age)

        # ---------------------------------------------------
        # OPTIONAL DETAILED VIEW
        # ---------------------------------------------------

        show_details = st.checkbox(
            "Show Detailed Comparison Data"
        )

        if show_details:

            st.subheader("Detailed Comparison Data")

            st.dataframe(final_df)

else:

    st.warning(
        "Please upload insurer Excel files."
    )
