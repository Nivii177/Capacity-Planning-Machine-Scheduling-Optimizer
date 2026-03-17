# SD Capacity Scheduler — Web Application

A Python-powered web application that replicates the Excel-based capacity scheduling and LP solver workflow.

## Features

- **Excel Import**: Upload your `.xlsm` / `.xlsx` capacity schedule file
- **LP Optimization**: Uses SciPy HiGHS solver to optimally allocate machine-days across products
- **Capacity Planning**: Month-by-month demand vs. capacity analysis
- **Schedule View**: Per-product machine-day allocation breakdown
- **Surplus/Shortage Summary**: Machine type utilization with surplus/shortage counts
- **CSV Export**: Download optimized schedule as CSV

## Project Structure

```
capacity_scheduler/
├── backend/
│   ├── app.py              # Flask API + LP optimization engine
│   └── requirements.txt    # Python dependencies
└── frontend/
    └── templates/
        └── index.html      # Full single-page UI (served by Flask)
```

## Setup & Run

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or with virtual environment:
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the backend

```bash
python backend/app.py
```

The app will be available at: **http://localhost:5050**

### 3. Open in browser

Navigate to `http://localhost:5050` — the Flask server serves the full UI.

---

## Workflow (mirrors the Excel)

| Step | Action | Equivalent Excel Tab |
|------|--------|---------------------|
| 1 | Upload Excel or enter data manually | SD Data |
| 2 | Review/edit product list and priorities | CapacityPlan |
| 3 | Set machine counts and working days | CapacityPlan row 1 |
| 4 | Select a month and run optimization | CapacityPlan → Solver |
| 5 | View per-product machine-day allocations | Schedule1 / Schedule2 |
| 6 | Review machine surplus & shortage | CapacitySummary |
| 7 | Export schedule CSV | SaveSchedule |

---

## Optimization Model

The solver uses **Linear Programming (SciPy HiGHS)**:

- **Decision variables**: `x[i][j]` = machine-days allocated to product `i` on machine type `j`
- **Objective**: Minimize total demand shortfall (weighted by product priority)
- **Constraints**:
  - Machine capacity: `Σ x[i][j] ≤ num_machines[j] × num_days` for each machine type `j`
  - Demand satisfaction: `Σ (x[i][j] × capacity[i][j]) + shortfall[i] ≥ demand[i]` for each product `i`
  - Compatibility: `x[i][j] = 0` if product `i` cannot run on machine type `j`
  - Non-negativity: `x[i][j] ≥ 0`, `shortfall[i] ≥ 0`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serve the UI |
| POST | `/api/upload` | Upload and parse Excel file |
| GET/POST | `/api/products` | List or add products |
| PUT/DELETE | `/api/products/<id>` | Update or delete product |
| GET/PUT | `/api/machines` | Get or update machine config |
| GET/PUT | `/api/config` | Get or update working days |
| POST | `/api/optimize` | Run LP optimization for a month |
| GET | `/api/schedule` | Retrieve last schedule |
| GET | `/api/capacity_summary` | Retrieve last capacity summary |
