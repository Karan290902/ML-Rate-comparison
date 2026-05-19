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
- Columns = Tenure
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

        # Convert to long format
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

        # Numeric conversion
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

        # Drop nulls
        df_long.dropna(inplace=True)

        # Append
        all_data.append(df_long)

    # ---------------------------------------------------
    # MERGE ALL DATA
    # ---------------------------------------------------

    if all_data:

        final_df = pd.concat(
            all_data,
            ignore_index=True
        )

        # ---------------------------------------------------
        # SIDEBAR FILTERS
        # ---------------------------------------------------

        st.sidebar.header("Filters")

        selected_age = st.sidebar.selectbox(
            "Select Age",
            sorted(final_df['Age'].unique())
        )

        selected_tenure = st.sidebar.selectbox(
            "Select Tenure",
            sorted(final_df['Tenure'].unique())
        )

        # ---------------------------------------------------
        # FILTERED DATA
        # ---------------------------------------------------

        filtered_df = final_df[
            (final_df['Age'] == selected_age) &
            (final_df['Tenure'] == selected_tenure)
        ]

        filtered_df = filtered_df.sort_values(
            by='Rate_Per_Lakh'
        )

        # ---------------------------------------------------
        # BEST INSURER
        # ---------------------------------------------------

        st.subheader(
            f"Best Insurer for Age {selected_age} | Tenure {selected_tenure}"
        )

        if not filtered_df.empty:

            best = filtered_df.iloc[0]

            st.success(
                f"""
                Best Insurer:
                {best['Insurer']}

                Rate Per Lakh:
                {best['Rate_Per_Lakh']}
                """
            )

        # ---------------------------------------------------
        # SIDE-BY-SIDE COMPARISON
        # ---------------------------------------------------

        st.subheader("Detailed Side-by-Side Comparison")

        comparison_table = final_df.pivot_table(
            index=['Age', 'Tenure'],
            columns='Insurer',
            values='Rate_Per_Lakh'
        ).reset_index()

        st.dataframe(
            comparison_table,
            use_container_width=True
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

        st.dataframe(
            best_age,
            use_container_width=True
        )

        # ---------------------------------------------------
        # OPTIONAL DETAILED DATA
        # ---------------------------------------------------

        show_raw = st.checkbox(
            "Show Raw Processed Data"
        )

        if show_raw:

            st.subheader("Raw Processed Data")

            st.dataframe(
                final_df,
                use_container_width=True
            )

else:

    st.warning(
        "Please upload insurer Excel files."
    )
