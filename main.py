import json
from pathlib import Path
import pandas as pd
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly_config import create_base_layout, apply_config_to_figure
from registry import WIDGETS, register_widget
import treasury_gov_pandas.datasets.deposits_withdrawals_operating_cash.load
import fed_net_liquidity
import datetime

app = FastAPI()

origins = [
    "https://pro.openbb.co",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_PATH = Path(__file__).parent.resolve()

@app.get("/")
def read_root():
    return {"Info": "Full example for OpenBB Custom Backend"}


@app.get("/widgets.json")
async def get_widgets():
    return WIDGETS


@app.get("/chains")
@register_widget({
    "name": "Top Chains by TVL",
    "description": "Displays the top 30 chains by Total Value Locked using data from DeFi Llama",
    "category": "DeFi",
    "type": "chart",
    "endpoint": "chains",
    "gridData": {"w": 40, "h": 15},
    "source": "DeFi Llama",
    "data": {"chart": {"type": "bar"}},
    "params": [
        {
            "paramName": "top_n",
            "value": 30,
            "label": "Top N",
            "show": True,
            "description": "Number of top chains to display",
            "type": "number",
        }
    ],
})
def get_chains(theme: str = "dark", top_n: int = 30):
    """Get current TVL of all chains using Defi LLama, allowing the number of top chains to be specified."""
    params = {}
    response = requests.get("https://api.llama.fi/v2/chains", params=params)

    if response.status_code == 200:
        # Create a DataFrame from the JSON data
        df = pd.DataFrame(response.json())

        # Sort the DataFrame by 'tvl' in descending order and select the top N chains as specified
        top_chains_df = df.sort_values(by='tvl', ascending=False).head(top_n)

        # Create a bar chart using Plotly
        figure = go.Figure(
            data=[go.Bar(x=top_chains_df["tokenSymbol"], y=top_chains_df["tvl"])],
            layout=create_base_layout(
                x_title="Token Symbol",
                y_title="Total Value Locked (TVL)",
                theme=theme
            )
        )

        # Apply theme configuration
        figure = apply_config_to_figure(figure, theme)

        # return the plotly json
        return json.loads(figure.to_json())

    print(f"Request error {response.status_code}: {response.text}")
    return JSONResponse(
        content={"error": response.text}, status_code=response.status_code
    )


# @app.get("/tga-explorer")
# @register_widget({
#     "name": "TGA Explorer",
#     "description": "Explores Treasury General Account (TGA) deposits and withdrawals data",
#     "category": "Treasury",
#     "type": "chart",
#     "endpoint": "tga-explorer",
#     "gridData": {"w": 40, "h": 15},
#     "source": "U.S. Treasury",
#     "data": {"chart": {"type": "bar"}},
#     "params": [
#         {
#             "paramName": "metric",
#             "value": "transaction_fytd_amt",
#             "label": "Metric",
#             "show": True,
#             "description": "Select metric to display",
#             "type": "select",
#             "options": [
#                 {"label": "Today", "value": "transaction_today_amt"},
#                 {"label": "Month to Date", "value": "transaction_mtd_amt"},
#                 {"label": "Fiscal Year to Date", "value": "transaction_fytd_amt"}
#             ],
#         },
#         {
#             "paramName": "year",
#             "value": 2022,
#             "label": "Year Start",
#             "show": True,
#             "description": "Starting year for data",
#             "type": "number"
#         },
#         {
#             "paramName": "min_amount",
#             "value": 100000,
#             "label": "Minimum Amount",
#             "show": True,
#             "description": "Minimum transaction amount to display",
#             "type": "number"
#         }
#     ],
# })
# def get_tga_explorer(
#     theme: str = "dark",
#     metric: str = "transaction_fytd_amt",
#     year: int = 2022,
#     min_amount: int = 100000
# ):
#     """Get TGA explorer data and return as Plotly figure."""
#     try:
#         # Load the dataframe
#         df = treasury_gov_pandas.datasets.deposits_withdrawals_operating_cash.load.load()

#         # Convert numeric columns
#         numeric_cols = [
#             'transaction_today_amt',
#             'transaction_mtd_amt',
#             'transaction_fytd_amt'
#         ]
#         for col in numeric_cols:
#             df[col] = pd.to_numeric(df[col], errors='coerce')

#         # Filter out unwanted categories
#         exclude_categories = [
#             "null",
#             "Sub-Total Withdrawals",
#             "Sub-Total Deposits",
#             "Transfers from Depositaries",
#             "Transfers from Federal Reserve Account (Table V)",
#             "Transfers to Depositaries",
#             "Transfers to Federal Reserve Account (Table V)",
#             "ShTransfersCtohFederalmReserve Account (Table V)"
#         ]
#         for cat in exclude_categories:
#             df = df.query(f'transaction_catg != "{cat}"')

#         # Apply year filter
#         df = df.query(f'record_date >= "{year}-10-01"')

#         # Convert withdrawals to negative values
#         for col in numeric_cols:
#             df.loc[df['transaction_type'] == 'Withdrawals', col] = -df[col]

#         # Apply minimum amount filter
#         df['absolute_value'] = df[metric].abs()
#         df = df.query(f'absolute_value > {min_amount}')

#         # Create the figure
#         fig = go.Figure()
#         for category, group in df.groupby('transaction_catg'):
#             fig.add_trace(go.Bar(
#                 x=group['record_date'],
#                 y=group[metric],
#                 name=category
#             ))

#         # Set the layout
#         fig.update_layout(
#             create_base_layout(
#                 x_title="Record Date",
#                 y_title="Transaction Amount",
#                 theme=theme
#             )
#         )

#         # Apply theme configuration
#         fig = apply_config_to_figure(fig, theme)

#         return json.loads(fig.to_json())

#     except Exception as e:
#         return JSONResponse(
#             content={"error": str(e)},
#             status_code=500
#         )


@app.get("/transactions")
@register_widget({
    "name": "Transactions",
    "description": "Shows all transactions for a specific date with minimum amount filter",
    "category": "Treasury",
    "type": "chart",
    "endpoint": "transactions",
    "gridData": {"w": 40, "h": 15},
    "source": "U.S. Treasury",
    "data": {"chart": {"type": "bar"}},
    "params": [
        {
            "paramName": "metric",
            "value": "transaction_fytd_amt",
            "label": "Metric",
            "show": True,
            "description": "Select metric to display",
            "type": "text",
            "options": [
                {"label": "Today", "value": "transaction_today_amt"},
                {"label": "Month to Date", "value": "transaction_mtd_amt"},
                {"label": "Fiscal Year to Date", "value": "transaction_fytd_amt"}
            ],
        },
        {
            "paramName": "date",
            "value": "2025-01-02",
            "label": "Date",
            "show": True,
            "description": "Select date to view transactions",
            "type": "date"
        },
        {
            "paramName": "min_amount",
            "value": 100000,
            "label": "Minimum Amount",
            "show": True,
            "description": "Minimum transaction amount to display",
            "type": "number"
        }
    ],
})
def get_transactions(
    theme: str = "dark",
    metric: str = "transaction_fytd_amt",
    date: str = "2025-01-02",
    min_amount: int = 100000
):
    """Get daily transactions data and return as Plotly figure."""
    try:
        # Validate date format
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return JSONResponse(
                content={"error": "Invalid date format. Please use YYYY-MM-DD format."},
                status_code=400
            )

        # Load the dataframe
        try:
            df = treasury_gov_pandas.datasets.deposits_withdrawals_operating_cash.load.load()
        except ImportError:
            return JSONResponse(
                content={"error": "treasury_gov_pandas package not found. Please install it."},
                status_code=500
            )
        except Exception as e:
            return JSONResponse(
                content={"error": f"Error loading data: {str(e)}"},
                status_code=500
            )

        # Convert numeric columns
        numeric_cols = [
            'transaction_today_amt',
            'transaction_mtd_amt',
            'transaction_fytd_amt'
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Filter out unwanted categories
        exclude_categories = [
            "null",
            "Sub-Total Withdrawals",
            "Sub-Total Deposits",
            "Transfers from Depositaries",
            "Transfers from Federal Reserve Account (Table V)",
            "Transfers to Depositaries",
            "Transfers to Federal Reserve Account (Table V)",
            "ShTransfersCtohFederalmReserve Account (Table V)"
        ]
        for cat in exclude_categories:
            df = df.query(f'transaction_catg != "{cat}"')

        # Filter for specific date
        df = df.query(f'record_date == "{date}"')
        
        # Check if data exists for the given date
        if df.empty:
            return JSONResponse(
                content={"error": f"No data available for date {date}"},
                status_code=404
            )

        # Convert withdrawals to negative values
        df.loc[df['transaction_type'] == 'Withdrawals', metric] = -df[metric]

        # Apply minimum amount filter
        df['absolute_value'] = df[metric].abs()
        df = df.query(f'absolute_value > {min_amount}')

        # Check if any data remains after filtering
        if df.empty:
            return JSONResponse(
                content={"error": f"No transactions found above minimum amount {min_amount}"},
                status_code=404
            )

        # Sort by metric value (from negative to positive)
        df = df.sort_values(metric, ascending=True)

        # Create the figure
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['transaction_catg'],
            y=df[metric],
            text=df[metric].apply(lambda x: f"${x:,.2f}"),
            textposition='auto',
            marker_color=df[metric].apply(lambda x: 'red' if x < 0 else 'green')
        ))

        # Set the layout
        fig.update_layout(
            create_base_layout(
                x_title="Transaction Category",
                y_title="Transaction Amount",
                theme=theme
            ),
            xaxis_tickangle=-45,
            showlegend=False
        )

        # Apply theme configuration
        fig = apply_config_to_figure(fig, theme)

        return json.loads(fig.to_json())

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@app.get("/fed-net-liquidity")
@register_widget({
    "name": "Fed Net Liquidity",
    "description": "Shows Federal Reserve Net Liquidity metrics including WALCL, RRP, TGA, REM and NL",
    "category": "Treasury",
    "type": "chart",
    "endpoint": "fed-net-liquidity",
    "gridData": {"w": 40, "h": 15},
    "source": "Federal Reserve",
    "data": {"chart": {"type": "line"}},
    "params": [
        {
            "paramName": "start_date",
            "value": (datetime.datetime.now() - datetime.timedelta(days=3*365)).strftime("%Y-%m-%d"),
            "label": "Start Date",
            "show": True,
            "description": "Start date for the data",
            "type": "date"
        },
        {
            "paramName": "metric",
            "value": "NL",
            "label": "Metric",
            "show": True,
            "description": "Select metric to display",
            "type": "text",
            "options": [
                {"label": "Net Liquidity", "value": "NL"},
                {"label": "WALCL", "value": "WALCL"},
                {"label": "RRP", "value": "RRP"},
                {"label": "TGA", "value": "TGA"},
                {"label": "REM", "value": "REM"}
            ]
        }
    ],
})
def get_fed_net_liquidity(
    start_date: str = "2023-01-01",
    metric: str = "NL",
    theme: str = "dark"
):
    """Get Federal Reserve Net Liquidity data and return as Plotly figure."""
    try:
        # Load the dataframe
        df = fed_net_liquidity.load_dataframe()

        # Filter by date
        df = df[df['date'] > start_date]

        # Create subplots with 2 rows
        fig = make_subplots(
            rows=2, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )

        # Add main line chart
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df[metric],
                mode='lines',
                name=metric,
            ),
            row=1, col=1
        )

        # Add diff bar chart if available
        diff_col = f"{metric}_diff"
        if diff_col in df.columns:
            # Create separate traces for positive and negative values
            positive_mask = df[diff_col] >= 0
            negative_mask = df[diff_col] < 0
            
            # Add positive values trace
            fig.add_trace(
                go.Bar(
                    x=df.loc[positive_mask, 'date'],
                    y=df.loc[positive_mask, diff_col],
                    name=f"{metric} Increase",
                    marker_color='green'
                ),
                row=2, col=1
            )
            
            # Add negative values trace
            fig.add_trace(
                go.Bar(
                    x=df.loc[negative_mask, 'date'],
                    y=df.loc[negative_mask, diff_col],
                    name=f"{metric} Decrease",
                    marker_color='red'
                ),
                row=2, col=1
            )

        # Set the layout
        fig.update_layout(
            create_base_layout(
                x_title="Date",
                y_title="Amount (Billions)",
                theme=theme
            ),
            xaxis_tickangle=-45
        )

        # Apply theme configuration
        fig = apply_config_to_figure(fig, theme)

        return json.loads(fig.to_json())

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
