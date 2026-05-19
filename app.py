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

st.title("Insurance Commercial Dashboard")

# ---------------------------------------------------
# MODE SELECTION
# ---------------------------------------------------

mode = st.sidebar.radio(
    "Select Mode",
    [
        "Insurer Comparison",
        "Bulk Premium Calculator"
    ]
)

# ===================================================
# MODE 1 : INSURER COMPARISON
# ===================================================

if mode == "Insurer Comparison":

    st.header("Insurer Comparison Dashboard")

    uploaded_files = st.file_uploader(
        "Upload Insurer Rate Cards",
        type=["xlsx", "csv"],
        accept_multiple_files=True
    )

    if uploaded_files:

        all_data = []
        coa_inputs = {}

        st.sidebar.header("COA Inputs")

        # ---------------------------------------------------
        # PROCESS INSURER FILES
        # ---------------------------------------------------

        for uploaded_file in uploaded_files:

            insurer_name = uploaded_file.name.split(".")[0]

            coa = st.sidebar.number_input(
                f"{insurer_name} COA %",
                min_value=0.0,
                value=0.0,
                step=1.0
            )

            coa_inputs[insurer_name] = coa

            # Read file
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Convert columns to numeric if possible
            df.columns = [
                pd.to_numeric(col, errors='ignore')
                for col in df.columns
            ]

            # Convert wide to long
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

            # Add insurer info
            df_long['Insurer'] = insurer_name
            df_long['COA'] = coa

            # Clean
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
        # FINAL DATAFRAME
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

        overall_rates['COA'] = overall_rates[
            'Insurer'
        ].map(coa_inputs)

        cheapest_overall = overall_rates.loc[
            overall_rates['Rate_Per_Lakh'].idxmin()
        ]

        highest_coa = overall_rates.loc[
            overall_rates['COA'].idxmax()
        ]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Cheapest Overall",
            cheapest_overall['Insurer']
        )

        col2.metric(
            "Highest COA",
            highest_coa['Insurer']
        )

        col3.metric(
            "Lowest Avg Rate",
            round(
                cheapest_overall['Rate_Per_Lakh'],
                2
            )
        )

        # ---------------------------------------------------
        # BEST PRICING
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
        # PREMIUM CALCULATOR
        # ---------------------------------------------------

        st.subheader("Premium Calculator")

        loan_amount = st.number_input(
            "Enter Loan Amount",
            min_value=10000,
            value=500000,
            step=10000
        )

        include_gst = st.checkbox(
            "Include GST @18%",
            value=True
        )

        premium_df = filtered_df.copy()

        premium_df['Premium'] = (
            loan_amount / 100000
        ) * premium_df['Rate_Per_Lakh']

        if include_gst:

            premium_df['GST'] = (
                premium_df['Premium'] * 0.18
            )

            premium_df['Final Premium'] = (
                premium_df['Premium'] +
                premium_df['GST']
            )

        else:

            premium_df['GST'] = 0

            premium_df['Final Premium'] = (
                premium_df['Premium']
            )

        premium_df = premium_df[
            [
                'Insurer',
                'Rate_Per_Lakh',
                'Premium',
                'GST',
                'Final Premium',
                'COA'
            ]
        ]

        premium_df = premium_df.round(2)

        st.dataframe(
            premium_df,
            use_container_width=True
        )

        # ---------------------------------------------------
        # CHEAPEST FREQUENCY
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
        # AGE VS RATE GRAPH
        # ---------------------------------------------------

        st.subheader("Age vs Rate Comparison")

        chart_tenure = st.selectbox(
            "Select Tenure for Chart",
            sorted(final_df['Tenure'].unique())
        )

        chart_df = final_df[
            final_df['Tenure'] == chart_tenure
        ]

        fig_age = px.line(
            chart_df,
            x='Age',
            y='Rate_Per_Lakh',
            color='Insurer',
            markers=True
        )

        st.plotly_chart(
            fig_age,
            use_container_width=True
        )

# ===================================================
# MODE 2 : BULK PREMIUM CALCULATOR
# ===================================================

elif mode == "Bulk Premium Calculator":

    st.header("Bulk Premium Calculator")

    # ---------------------------------------------------
    # LOT FILE
    # ---------------------------------------------------

    lot_file = st.file_uploader(
        "Upload Lot File",
        type=["xlsx", "csv"]
    )

    # ---------------------------------------------------
    # INSURER RATE FILES
    # ---------------------------------------------------

    insurer_files = st.file_uploader(
        "Upload Insurer Rate Cards",
        type=["xlsx", "csv"],
        accept_multiple_files=True
    )

    if lot_file and insurer_files:

        # ---------------------------------------------------
        # READ LOT FILE
        # ---------------------------------------------------

        if lot_file.name.endswith(".csv"):
            lot_df = pd.read_csv(lot_file)
        else:
            lot_df = pd.read_excel(lot_file)

        required_cols = [
            'Name',
            'Age',
            'Loan Amount',
            'Tenure'
        ]

        missing = [
            col for col in required_cols
            if col not in lot_df.columns
        ]

        if missing:

            st.error(
                f"Missing columns: {missing}"
            )

        else:

            result_df = lot_df.copy()

            summary_data = []

            # ---------------------------------------------------
            # PROCESS EACH INSURER
            # ---------------------------------------------------

            for insurer_file in insurer_files:

                insurer_name = insurer_file.name.split(".")[0]

                # Read insurer file
                if insurer_file.name.endswith(".csv"):
                    rate_df = pd.read_csv(insurer_file)
                else:
                    rate_df = pd.read_excel(insurer_file)

                # Convert columns properly
                rate_df.columns = [
                    pd.to_numeric(col, errors='ignore')
                    for col in rate_df.columns
                ]

                rate_df['Entry Age'] = pd.to_numeric(
                    rate_df['Entry Age'],
                    errors='coerce'
                )

                premiums = []
                statuses = []

                # ---------------------------------------------------
                # MATCH AGE + TENURE + CALCULATE PREMIUM
                # ---------------------------------------------------

                for _, row in lot_df.iterrows():

                    age = row['Age']
                    tenure = row['Tenure']
                    loan_amount = row['Loan Amount']

                    premium = None
                    status = "Success"

                    try:

                        # Check age exists
                        if age not in rate_df['Entry Age'].values:

                            premium = None
                            status = "Age Missing"

                        # Check tenure exists
                        elif tenure not in rate_df.columns:

                            premium = None
                            status = "Tenure Missing"

                        else:

                            rate = rate_df.loc[
                                rate_df['Entry Age'] == age,
                                tenure
                            ].values[0]

                            premium = (
                                loan_amount / 100000
                            ) * rate

                    except:

                        premium = None
                        status = "Calculation Error"

                    premiums.append(premium)
                    statuses.append(status)

                # Add premium column
                result_df[
                    f'{insurer_name} Premium'
                ] = premiums

                result_df[
                    f'{insurer_name} Status'
                ] = statuses

                # Portfolio summary
                total_premium = pd.Series(
                    premiums
                ).sum()

                summary_data.append({
                    'Insurer': insurer_name,
                    'Total Premium': round(
                        total_premium,
                        2
                    )
                })

            # ---------------------------------------------------
            # CHEAPEST INSURER
            # ---------------------------------------------------

            premium_cols = [
                col for col in result_df.columns
                if 'Premium' in col
            ]

            def get_cheapest_insurer(row):

                valid_values = row.dropna()

                if len(valid_values) == 0:
                    return "No Matching Rate"

                return (
                    valid_values.idxmin()
                    .replace(' Premium', '')
                )

            result_df['Cheapest Insurer'] = (
                result_df[premium_cols]
                .apply(
                    get_cheapest_insurer,
                    axis=1
                )
            )

            # ---------------------------------------------------
            # OUTPUT
            # ---------------------------------------------------

            st.subheader("Premium Output")

            st.dataframe(
                result_df,
                use_container_width=True
            )

            # ---------------------------------------------------
            # PORTFOLIO SUMMARY
            # ---------------------------------------------------

            st.subheader("Portfolio Summary")

            summary_df = pd.DataFrame(
                summary_data
            )

            st.dataframe(
                summary_df,
                use_container_width=True
            )

            # ---------------------------------------------------
            # EXPORT REPORT
            # ---------------------------------------------------

            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine='openpyxl'
            ) as writer:

                result_df.to_excel(
                    writer,
                    index=False,
                    sheet_name='Premium Output'
                )

                summary_df.to_excel(
                    writer,
                    index=False,
                    sheet_name='Portfolio Summary'
                )

            st.download_button(
                label="Download Premium Report",
                data=output.getvalue(),
                file_name="premium_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
