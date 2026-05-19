import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Insurance Intelligence Dashboard",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("Insurance Insurer Intelligence Dashboard")

st.markdown("""
Compare insurers based on:
- Rate Per Lakh
- COA %
- Age-wise pricing
- Tenure-wise pricing
- Commercial attractiveness
""")

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload Insurer Rate Cards",
    type=["xlsx", "csv"],
    accept_multiple_files=True
)

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if uploaded_files:

    all_data = []

    st.sidebar.header("COA Inputs")

    # ---------------------------------------------------
    # PROCESS FILES
    # ---------------------------------------------------

    for uploaded_file in uploaded_files:

        insurer_name = uploaded_file.name.split(".")[0]

        # Optional COA
        coa = st.sidebar.text_input(
            f"{insurer_name} COA %",
            value=""
        )

        try:
            coa = float(coa)
        except:
            coa = 0

        # Read file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Validate
        if 'Entry Age' not in df.columns:

            st.error(
                f"'Entry Age' missing in {uploaded_file.name}"
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

        # Add COA
        df_long['COA'] = coa

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

        # Drop missing
        df_long.dropna(inplace=True)

        all_data.append(df_long)

    # ---------------------------------------------------
    # FINAL DATA
    # ---------------------------------------------------

    if len(all_data) > 0:

        final_df = pd.concat(
            all_data,
            ignore_index=True
        )

        # ---------------------------------------------------
        # SCORING
        # ---------------------------------------------------

        final_df['Rate_Score'] = (
            (
                1 / final_df['Rate_Per_Lakh']
            ) /
            (
                1 / final_df['Rate_Per_Lakh']
            ).max()
        ) * 100

        max_coa = max(
            final_df['COA'].max(),
            1
        )

        final_df['COA_Score'] = (
            final_df['COA'] / max_coa
        ) * 100

        final_df['Commercial_Score'] = (
            final_df['Rate_Score'] * 0.7 +
            final_df['COA_Score'] * 0.3
        )

        # ---------------------------------------------------
        # FILTERS
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
        # FILTER DATA
        # ---------------------------------------------------

        filtered_df = final_df[
            (final_df['Age'] == selected_age) &
            (final_df['Tenure'] == selected_tenure)
        ]

        filtered_df = filtered_df.sort_values(
            by='Commercial_Score',
            ascending=False
        )

        # ---------------------------------------------------
        # BEST INSURER
        # ---------------------------------------------------

        st.subheader(
            f"Best Insurer | Age {selected_age} | Tenure {selected_tenure}"
        )

        if not filtered_df.empty:

            best = filtered_df.iloc[0]

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Best Insurer",
                best['Insurer']
            )

            col2.metric(
                "Rate Per Lakh",
                round(best['Rate_Per_Lakh'], 2)
            )

            col3.metric(
                "Commercial Score",
                round(best['Commercial_Score'], 2)
            )

        # ---------------------------------------------------
        # SIDE-BY-SIDE COMPARISON
        # ---------------------------------------------------

        st.subheader("Detailed Comparison")

        comparison = filtered_df[
            [
                'Insurer',
                'Rate_Per_Lakh',
                'COA',
                'Commercial_Score'
            ]
        ]

        st.dataframe(
            comparison,
            use_container_width=True
        )

        # ---------------------------------------------------
        # OVERALL BEST INSURER
        # ---------------------------------------------------

        st.subheader("Overall Best Insurer")

        overall = (
            final_df.groupby('Insurer')[
                ['Rate_Per_Lakh', 'Commercial_Score']
            ]
            .mean()
            .reset_index()
        )

        overall = overall.sort_values(
            by='Commercial_Score',
            ascending=False
        )

        overall_best = overall.iloc[0]

        st.success(
            f"""
            {overall_best['Insurer']}

            Avg Rate:
            {round(overall_best['Rate_Per_Lakh'], 2)}

            Avg Commercial Score:
            {round(overall_best['Commercial_Score'], 2)}
            """
        )

        # ---------------------------------------------------
        # SIDE BY SIDE MATRIX
        # ---------------------------------------------------

        st.subheader("Side-by-Side Rate Matrix")

        matrix = final_df.pivot_table(
            index=['Age', 'Tenure'],
            columns='Insurer',
            values='Rate_Per_Lakh'
        ).reset_index()

        st.dataframe(
            matrix,
            use_container_width=True
        )

        # ---------------------------------------------------
        # AGE TREND
        # ---------------------------------------------------

        st.subheader("Age vs Rate Trend")

        fig_age = px.line(
            final_df,
            x='Age',
            y='Rate_Per_Lakh',
            color='Insurer',
            markers=True
        )

        st.plotly_chart(
            fig_age,
            use_container_width=True
        )

        # ---------------------------------------------------
        # TENURE TREND
        # ---------------------------------------------------

        st.subheader("Tenure vs Rate Trend")

        fig_tenure = px.line(
            final_df,
            x='Tenure',
            y='Rate_Per_Lakh',
            color='Insurer',
            markers=True
        )

        st.plotly_chart(
            fig_tenure,
            use_container_width=True
        )

        # ---------------------------------------------------
        # BUSINESS INSIGHTS
        # ---------------------------------------------------

        st.subheader("Business Insights")

        lowest_rate = (
            final_df.groupby('Insurer')[
                'Rate_Per_Lakh'
            ]
            .mean()
            .idxmin()
        )

        highest_coa = (
            final_df.groupby('Insurer')[
                'COA'
            ]
            .mean()
            .idxmax()
        )

        st.info(
            f"""
            Lowest Pricing Overall:
            {lowest_rate}

            Highest COA Opportunity:
            {highest_coa}

            Best Commercial Insurer:
            {overall_best['Insurer']}
            """
        )

        # ---------------------------------------------------
        # OPTIONAL RAW DATA
        # ---------------------------------------------------

        if st.checkbox("Show Raw Data"):

            st.dataframe(
                final_df,
                use_container_width=True
            )

else:

    st.warning(
        "Please upload insurer files."
    )
