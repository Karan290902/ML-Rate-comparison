import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Insurance Commercial Dashboard",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("Insurance Commercial Comparison Dashboard")

st.markdown("""
Compare insurers based on:
- Pricing competitiveness
- COA attractiveness
- Age-wise comparison
- Tenure-wise comparison
- Commercial suitability
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

    coa_inputs = {}

    st.sidebar.header("COA Inputs")

    # ---------------------------------------------------
    # PROCESS FILES
    # ---------------------------------------------------

    for uploaded_file in uploaded_files:

        insurer_name = uploaded_file.name.split(".")[0]

        coa = st.sidebar.text_input(
            f"{insurer_name} COA %",
            value=""
        )

        try:
            coa = float(coa)
        except:
            coa = 0

        coa_inputs[insurer_name] = coa

        # Read File
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Validation
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

        df_long.rename(
            columns={
                'Entry Age': 'Age'
            },
            inplace=True
        )

        # Add insurer
        df_long['Insurer'] = insurer_name

        df_long['COA'] = coa

        # Clean data
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

    final_df = pd.concat(
        all_data,
        ignore_index=True
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
        by='Rate_Per_Lakh'
    )

    # ---------------------------------------------------
    # SUMMARY CARDS
    # ---------------------------------------------------

    overall_rates = (
        final_df.groupby('Insurer')[
            'Rate_Per_Lakh'
        ]
        .mean()
        .reset_index()
    )

    cheapest_overall = overall_rates.loc[
        overall_rates['Rate_Per_Lakh'].idxmin()
    ]

    highest_coa = max(
        coa_inputs,
        key=coa_inputs.get
    )

    stability = (
        final_df.groupby('Insurer')[
            'Rate_Per_Lakh'
        ]
        .std()
    )

    most_stable = stability.idxmin()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Cheapest Overall",
        cheapest_overall['Insurer']
    )

    col2.metric(
        "Highest COA",
        highest_coa
    )

    col3.metric(
        "Most Stable Pricing",
        most_stable
    )

    col4.metric(
        "Best Scale Insurer",
        cheapest_overall['Insurer']
    )

    # ---------------------------------------------------
    # BEST PRICING OUTPUT
    # ---------------------------------------------------

    st.subheader(
        f"Best Pricing | Age {selected_age} | Tenure {selected_tenure}"
    )

    if not filtered_df.empty:

        best_price = filtered_df.iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Lowest Price Insurer",
            best_price['Insurer']
        )

        col2.metric(
            "Rate Per Lakh",
            round(best_price['Rate_Per_Lakh'], 2)
        )

        col3.metric(
            "COA %",
            best_price['COA']
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
    # CHEAPEST INSURER FREQUENCY
    # ---------------------------------------------------

    st.subheader("Cheapest Insurer Frequency")

    cheapest_cases = (
        final_df.loc[
            final_df.groupby(
                ['Age', 'Tenure']
            )['Rate_Per_Lakh'].idxmin()
        ]
    )

    frequency = (
        cheapest_cases['Insurer']
        .value_counts()
        .reset_index()
    )

    frequency.columns = [
        'Insurer',
        'Cheapest Cases'
    ]

    frequency['Cheapest %'] = (
        frequency['Cheapest Cases']
        /
        frequency['Cheapest Cases'].sum()
    ) * 100

    frequency['Cheapest %'] = (
        frequency['Cheapest %']
        .round(2)
    )

    st.dataframe(
        frequency,
        use_container_width=True
    )

    # ---------------------------------------------------
    # AGE-WISE WINNER TABLE
    # ---------------------------------------------------

    st.subheader("Age-wise Winner Table")

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

    slab = (
        final_df.groupby(
            ['Age_Slab', 'Insurer']
        )['Rate_Per_Lakh']
        .mean()
        .reset_index()
    )

    best_slab = (
        slab.loc[
            slab.groupby('Age_Slab')[
                'Rate_Per_Lakh'
            ].idxmin()
        ]
    )

    st.dataframe(
        best_slab,
        use_container_width=True
    )

    # ---------------------------------------------------
    # BEST VALUE INSURER
    # ---------------------------------------------------

    st.subheader("Best Value Insurer")

    value_df = overall_rates.copy()

    value_df['COA'] = value_df['Insurer'].map(
        coa_inputs
    )

    value_df['Value_Index'] = (
        value_df['COA'] /
        value_df['Rate_Per_Lakh']
    )

    best_value = value_df.loc[
        value_df['Value_Index'].idxmax()
    ]

    st.success(
        f"""
Best Value Insurer:
{best_value['Insurer']}

Reason:
- Strong balance between pricing and COA
- Better commercial attractiveness
"""
    )

    # ---------------------------------------------------
    # HEATMAP
    # ---------------------------------------------------

    st.subheader("Heatmap Dashboard")

    heatmap_data = final_df.pivot_table(
        index='Age',
        columns='Insurer',
        values='Rate_Per_Lakh'
    )

    fig_heatmap = px.imshow(
        heatmap_data,
        text_auto=True,
        aspect='auto',
        title="Age-wise Rate Heatmap"
    )

    st.plotly_chart(
        fig_heatmap,
        use_container_width=True
    )

    # ---------------------------------------------------
    # INSURER RECOMMENDATION ENGINE
    # ---------------------------------------------------

    st.subheader("Insurer Recommendation Engine")

    recommendations = ""

    for _, row in value_df.iterrows():

        insurer = row['Insurer']
        rate = row['Rate_Per_Lakh']
        coa = row['COA']

        pricing_view = ""

        if rate <= value_df['Rate_Per_Lakh'].quantile(0.25):
            pricing_view = "Excellent Pricing"

        elif rate <= value_df['Rate_Per_Lakh'].median():
            pricing_view = "Good Pricing"

        else:
            pricing_view = "Higher Pricing"

        coa_view = ""

        if coa >= value_df['COA'].quantile(0.75):
            coa_view = "Strong COA"

        elif coa >= value_df['COA'].median():
            coa_view = "Moderate COA"

        else:
            coa_view = "Lower COA"

        recommendation = ""

        if pricing_view == "Excellent Pricing" and coa_view == "Strong COA":
            recommendation = "Excellent Commercial Proposition"

        elif pricing_view == "Excellent Pricing":
            recommendation = "Best for Scale Business"

        elif coa_view == "Strong COA":
            recommendation = "Best for Revenue Focus"

        else:
            recommendation = "Balanced Proposition"

        recommendations += f"""
### {insurer}

Pricing:
- {pricing_view}

COA:
- {coa_view}

Recommendation:
- {recommendation}

"""

    st.markdown(recommendations)

    # ---------------------------------------------------
    # AGE VS RATE GRAPH
    # ---------------------------------------------------

    st.subheader("Age vs Rate Comparison")

    selected_chart_tenure = st.selectbox(
        "Select Tenure",
        sorted(final_df['Tenure'].unique())
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

    st.plotly_chart(
        fig_age,
        use_container_width=True
    )

    # ---------------------------------------------------
    # TENURE VS RATE GRAPH
    # ---------------------------------------------------

    st.subheader("Tenure vs Rate Comparison")

    selected_chart_age = st.selectbox(
        "Select Age",
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

    st.plotly_chart(
        fig_tenure,
        use_container_width=True
    )

    # ---------------------------------------------------
    # EXPORT REPORT
    # ---------------------------------------------------

    st.subheader("Export Report")

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine='openpyxl'
    ) as writer:

        comparison_matrix.to_excel(
            writer,
            index=False,
            sheet_name='Comparison'
        )

        frequency.to_excel(
            writer,
            index=False,
            sheet_name='Cheapest Frequency'
        )

        best_slab.to_excel(
            writer,
            index=False,
            sheet_name='Age Winners'
        )

        value_df.to_excel(
            writer,
            index=False,
            sheet_name='Value Analysis'
        )

    st.download_button(
        label="Download Excel Report",
        data=output.getvalue(),
        file_name="insurance_comparison_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------------------------------------------------
    # RAW DATA
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
