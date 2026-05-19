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

        # COA Input
        coa = st.sidebar.text_input(
            f"{insurer_name} COA %",
            value=""
        )

        try:
            coa = float(coa)
        except:
            coa = 0

        # Read File
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

        # ---------------------------------------------------
        # CONVERT TO LONG FORMAT
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

        df_long['Insurer'] = insurer_name

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
        # FILTERED DATA
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
        # SIDE-BY-SIDE MATRIX
        # ---------------------------------------------------

        st.subheader("Side-by-Side Rate Comparison")

        comparison_matrix = final_df.pivot_table(
            index=['Age', 'Tenure'],
            columns='Insurer',
            values='Rate_Per_Lakh'
        ).reset_index()

        insurer_cols = comparison_matrix.columns[2:]

        if len(insurer_cols) >= 2:

            base = insurer_cols[0]

            for insurer in insurer_cols[1:]:

                comparison_matrix[
                    f'{insurer} Difference %'
                ] = (
                    (
                        comparison_matrix[insurer] -
                        comparison_matrix[base]
                    )
                    /
                    comparison_matrix[base]
                ) * 100

                comparison_matrix[
                    f'{insurer} Difference %'
                ] = comparison_matrix[
                    f'{insurer} Difference %'
                ].round(2)

        st.dataframe(
            comparison_matrix,
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
        # AGE SLAB ANALYSIS
        # ---------------------------------------------------

        st.subheader("Best Insurer by Age Slab")

        bins = [18, 25, 35, 45, 55, 100]

        labels = [
            '18-25',
            '26-35',
            '36-45',
            '46-55',
            '56+'
        ]

        final_df['Age_Slab'] = pd.cut(
            final_df['Age'],
            bins=bins,
            labels=labels,
            right=True
        )

        slab_analysis = (
            final_df.groupby(
                ['Age_Slab', 'Insurer']
            )['Commercial_Score']
            .mean()
            .reset_index()
        )

        best_slab = (
            slab_analysis.loc[
                slab_analysis.groupby('Age_Slab')[
                    'Commercial_Score'
                ].idxmax()
            ]
        )

        st.dataframe(
            best_slab,
            use_container_width=True
        )

        # ---------------------------------------------------
        # AGE VS RATE GRAPH
        # ---------------------------------------------------

        st.subheader("Age vs Rate Comparison")

        selected_chart_tenure = st.selectbox(
            "Select Tenure for Age Comparison",
            sorted(final_df['Tenure'].unique()),
            key='age_chart'
        )

        chart_df = final_df[
            final_df['Tenure'] == selected_chart_tenure
        ]

        fig_age = px.line(
            chart_df,
            x='Age',
            y='Rate_Per_Lakh',
            color='Insurer',
            markers=True,
            title=f'Age vs Rate | Tenure {selected_chart_tenure}'
        )

        fig_age.update_layout(
            height=500
        )

        st.plotly_chart(
            fig_age,
            use_container_width=True
        )

        # ---------------------------------------------------
        # TENURE VS RATE GRAPH
        # ---------------------------------------------------

        st.subheader("Tenure vs Rate Comparison")

        selected_chart_age = st.selectbox(
            "Select Age for Tenure Comparison",
            sorted(final_df['Age'].unique()),
            key='tenure_chart'
        )

        tenure_chart_df = final_df[
            final_df['Age'] == selected_chart_age
        ]

        fig_tenure = px.line(
            tenure_chart_df,
            x='Tenure',
            y='Rate_Per_Lakh',
            color='Insurer',
            markers=True,
            title=f'Tenure vs Rate | Age {selected_chart_age}'
        )

        fig_tenure.update_layout(
            height=500
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
