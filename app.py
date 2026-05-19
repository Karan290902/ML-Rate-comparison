import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Insurance Insurer Intelligence Dashboard",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("Insurance Insurer Intelligence Dashboard")

st.markdown("""
### Compare Insurers Based On:
- Rate Per Lakh
- COA %
- Age-wise competitiveness
- Tenure-wise competitiveness
- Scalability
- Commercial attractiveness
""")

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload Multiple Insurer Rate Cards",
    type=["xlsx", "csv"],
    accept_multiple_files=True
)

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if uploaded_files:

    all_data = []

    coa_dict = {}

    st.sidebar.header("COA Inputs")

    # ---------------------------------------------------
    # PROCESS FILES
    # ---------------------------------------------------

    for uploaded_file in uploaded_files:

        insurer_name = uploaded_file.name.split(".")[0]

        # Optional COA Input
        coa = st.sidebar.number_input(
            f"{insurer_name} COA %",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0
        )

        coa_dict[insurer_name] = coa

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

        df_long.rename(
            columns={
                'Entry Age': 'Age'
            },
            inplace=True
        )

        df_long['Insurer'] = insurer_name

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

        df_long.dropna(inplace=True)

        all_data.append(df_long)

    # ---------------------------------------------------
    # MERGE ALL DATA
    # ---------------------------------------------------

    final_df = pd.concat(
        all_data,
        ignore_index=True
    )

    # ---------------------------------------------------
    # SCORING LOGIC
    # ---------------------------------------------------

    # Lower Rate Better
    final_df['Rate_Score'] = (
        (
            1 / final_df['Rate_Per_Lakh']
        ) /
        (
            1 / final_df['Rate_Per_Lakh']
        ).max()
    ) * 100

    # COA Score
    max_coa = max(final_df['COA'].max(), 1)

    final_df['COA_Score'] = (
        final_df['COA'] / max_coa
    ) * 100

    # Commercial Score
    final_df['Commercial_Score'] = (
        final_df['Rate_Score'] * 0.7 +
        final_df['COA_Score'] * 0.3
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
    # TOP METRICS
    # ---------------------------------------------------

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
    # SIDE BY SIDE COMPARISON
    # ---------------------------------------------------

    st.subheader(
        f"Detailed Comparison | Age {selected_age} | Tenure {selected_tenure}"
    )

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

    st.subheader("Overall Best Insurer")

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
    # RATE DIFFERENCE ANALYSIS
    # ---------------------------------------------------

    st.subheader("Rate Difference Analysis")

    pivot_rates = final_df.pivot_table(
        index=['Age', 'Tenure'],
        columns='Insurer',
        values='Rate_Per_Lakh'
    ).reset_index()

    st.dataframe(
        pivot_rates,
        use_container_width=True
    )

    # ---------------------------------------------------
    # AGE VS RATE CHART
    # ---------------------------------------------------

    st.subheader("Age vs Rate Trend")

    age_chart = px.line(
        final_df,
        x='Age',
        y='Rate_Per_Lakh',
        color='Insurer',
        markers=True
    )

    st.plotly_chart(
        age_chart,
        use_container_width=True
    )

    # ---------------------------------------------------
    # TENURE VS RATE CHART
    # ---------------------------------------------------

    st.subheader("Tenure vs Rate Trend")

    tenure_chart = px.line(
        final_df,
        x='Tenure',
        y='Rate_Per_Lakh',
        color='Insurer',
        markers=True
    )

    st.plotly_chart(
        tenure_chart,
        use_container_width=True
    )

    # ---------------------------------------------------
    # HEATMAP
    # ---------------------------------------------------

    st.subheader("Commercial Score Heatmap")

    heatmap_data = final_df.pivot_table(
        index='Age',
        columns='Insurer',
        values='Commercial_Score'
    )

    heatmap = px.imshow(
        heatmap_data,
        aspect='auto',
        text_auto=True
    )

    st.plotly_chart(
        heatmap,
        use_container_width=True
    )

    # ---------------------------------------------------
    # BUSINESS INSIGHTS
    # ---------------------------------------------------

    st.subheader("Business Insights")

    lowest_rate_insurer = (
        final_df.groupby('Insurer')['Rate_Per_Lakh']
        .mean()
        .idxmin()
    )

    highest_coa_insurer = (
        final_df.groupby('Insurer')['COA']
        .mean()
        .idxmax()
    )

    st.info(
        f"""
        Lowest Pricing Overall:
        {lowest_rate_insurer}

        Highest COA Opportunity:
        {highest_coa_insurer}

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
        "Please upload insurer Excel files."
    )
