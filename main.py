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

@app.get("/fed-net-liquidity-all")
@register_widget({
    "name": "Fed Net Liquidity All",
    "description": "Shows all Federal Reserve Net Liquidity metrics including WALCL, RRP, TGA, REM and NL",
    "category": "Treasury",
    "type": "chart",
    "endpoint": "fed-net-liquidity-all",
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
        }
    ],
})
def get_fed_net_liquidity(
    start_date: str = "2023-01-01",
    theme: str = "dark"
):
    """Get Federal Reserve Net Liquidity data and return as Plotly figure."""
    try:
        # Load the dataframe
        df = fed_net_liquidity.load_dataframe()

        # Filter by date
        df = df[df['date'] > start_date]

        # Create figure
        fig = go.Figure()

        # Add all metrics as separate traces
        metrics = ["NL", "WALCL", "RRP", "TGA", "REM"]
        colors = ["#00ff00", "#00a7ff", "#00a7ff", "#ff69b4", "#ff0000"]
        for metric, color in zip(metrics, colors):
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df[metric],
                    mode='lines',
                    name=metric,
                    line=dict(color=color)
                )
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

@app.get("/fed-net-liquidity-data")
@register_widget({
    "name": "Fed Net Liquidity Data",
    "description": "Shows Federal Reserve Net Liquidity metrics as a dataframe",
    "category": "Treasury",
    "type": "table",
    "endpoint": "fed-net-liquidity-data",
    "gridData": {"w": 40, "h": 15},
    "source": "Federal Reserve",
    "data": {
        "table" : {
            "showAll": True,
            "columnsDefs": [
                {
                    "field": "WALCL Change",
                    "headerName": "WALCL Change",
                    "cellDataType": "number",
                    "renderFn": "greenRed"
                },
                {
                    "field": "RRP Change",
                    "headerName": "RRP Change",
                    "cellDataType": "number",
                    "renderFn": "greenRed"
                },
                {
                    "field": "TGA Change",
                    "headerName": "TGA Change",
                    "cellDataType": "number",
                    "renderFn": "greenRed"
                },
                {
                    "field": "REM Change",
                    "headerName": "REM Change",
                    "cellDataType": "number",
                    "renderFn": "greenRed"
                },
                {
                    "field": "NL Change",
                    "headerName": "NL Change",
                    "cellDataType": "number",
                    "renderFn": "greenRed"
                }
            ]
        }
    },
    "params": [
        {
            "paramName": "start_date",
            "value": (datetime.datetime.now() - datetime.timedelta(days=3*365)).strftime("%Y-%m-%d"),
            "label": "Start Date",
            "show": True,
            "description": "Start date for the data",
            "type": "date"
        }
    ],
})
def get_fed_net_liquidity_data(
    start_date: str = "2023-01-01"
):
    """Get Federal Reserve Net Liquidity data and return as a dataframe."""
    try:
        # Load the dataframe
        df = fed_net_liquidity.load_dataframe()

        # Filter by date
        df = df[df['date'] > start_date]

        # Select and rename columns
        df = df[['date', 'WALCL', 'WALCL_diff', 'RRP', 'RRP_diff', 'TGA', 'TGA_diff', 'REM', 'REM_diff', 'NL', 'NL_diff']]
        df = df.rename(columns={
            'WALCL_diff': 'WALCL Change',
            'RRP_diff': 'RRP Change',
            'TGA_diff': 'TGA Change',
            'REM_diff': 'REM Change',
            'NL_diff': 'NL Change'
        })

        # Format numbers in billions
        def format_billions(x):
            return round(x / 1_000_000_000, 2)

        # Apply formatting to all numeric columns
        numeric_cols = ['WALCL', 'RRP', 'TGA', 'REM', 'NL', 'WALCL Change', 'RRP Change', 'TGA Change', 'REM Change', 'NL Change']
        for col in numeric_cols:
            df[col] = df[col].apply(format_billions)

        # Convert to dictionary for JSON response
        return df.to_dict(orient="records")
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

