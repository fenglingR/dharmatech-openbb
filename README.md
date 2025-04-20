# dharmatech-openbb

A custom OpenBB backend providing Treasury and Federal Reserve data visualizations.

![CleanShot 2025-04-20 at 16 15 36](https://github.com/user-attachments/assets/1f6335b6-5b0f-4a21-b19f-6cabd6bba870)

You can add it on OpenBB by copy-pasting this link ot the workspace: https://dharmatech-openbb.fly.dev

![CleanShot 2025-04-20 at 16 13 50](https://github.com/user-attachments/assets/75e74175-2990-4597-8820-9c6d10bb21c2)

## Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)

## Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dharmatech-openbb.git
cd dharmatech-openbb
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn main:app --port 5050
```

The application will be available at `http://localhost:5050`

## Docker Setup

1. Build the Docker image:
```bash
docker build -t dharmatech-openbb .
```

2. Run the container:
```bash
docker run -p 5050:5050 dharmatech-openbb
```

## Deployment to Fly.io

1. Install the Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Login to Fly:
```bash
fly auth login
```

3. Launch the application:
```bash
fly launch
```

4. Deploy:
```bash
fly deploy
```

## Available Endpoints

- `/widgets.json` - List of available widgets
- `/templates.json` - Widget templates
- `/transactions` - Treasury transactions data
- `/fed-net-liquidity` - Federal Reserve net liquidity metrics
- `/fed-balance-sheet` - Federal Reserve balance sheet data
- `/mts-income-taxes-monthly` - Monthly income tax receipts
- And more...

## Development

To add new widgets or modify existing ones, edit the `main.py` file and follow the existing patterns for widget registration and endpoint implementation.
