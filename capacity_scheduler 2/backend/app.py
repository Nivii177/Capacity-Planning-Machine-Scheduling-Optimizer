from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
from scipy.optimize import linprog
import json
import os

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
CORS(app)

# ─────────────────────────────────────────────
# In-memory state
# ─────────────────────────────────────────────
state = {
    "products": [],        # list of product dicts
    "machines": [],        # list of machine type dicts
    "num_days": 20,
    "schedule": {},        # optimized machine-day allocations
    "capacity_summary": {} # surplus/shortage per machine type
}

MACHINE_TYPES = [
    "MCT1 : SS (G21 TY M)",
    "MCT2 : SS (G21 TY L)",
    "MCT3 : SS (G21 TY L2-JUMBO)",
    "MCT4 : SS (G21 M)",
    "MCT5 : SS (G21 L)",
    "MCT 6 : SS (G21 L2 JUMBO)",
    "MCT7 : SS (G21 TY L3)",
    "MCT8 : SS (G21 TY L4)",
    "MCT9: BMAC (G21 S/124)",
    "MCT10: BMAC (G21 M/134)",
    "MCT11 : RAV (G21 L/133)",
    "MCT12 : RAV (G21 L2 JUMBO)"
]

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify(state)

@app.route("/api/upload", methods=["POST"])
def upload_excel():
    """Parse uploaded .xlsm and populate state."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    try:
        xl = pd.ExcelFile(f)
        sheet_names = xl.sheet_names

        products = []
        machines_map = {}  # machine_type -> num_machines

        if "SD Data" in sheet_names:
            df = xl.parse("SD Data", header=None)
            # Row 1 (index 1) is header, row 0 has some label info
            # Actual data starts row index 2
            header_row = df.iloc[1].tolist()
            mct_start = 9   # column index where MCT1 starts
            demand_start = 22  # column index where Jan demand starts

            for i in range(2, len(df)):
                row = df.iloc[i].tolist()
                if pd.isna(row[0]) and pd.isna(row[2]):
                    continue
                try:
                    fp = row[1] if not pd.isna(row[1]) else ""
                    style = row[2] if not pd.isna(row[2]) else ""
                    cylinder = row[3] if not pd.isna(row[3]) else ""
                    machine_type = row[4] if not pd.isna(row[4]) else ""
                    needle_qty = row[5] if not pd.isna(row[5]) else 0
                    area = row[6] if not pd.isna(row[6]) else ""
                    capacity = float(row[7]) if not pd.isna(row[7]) else 0

                    # Compatible machine types
                    compatible = []
                    for mi, mct in enumerate(MACHINE_TYPES):
                        col_idx = mct_start + mi
                        if col_idx < len(row):
                            val = row[col_idx]
                            if val != "" and not pd.isna(val) and val is not None:
                                try:
                                    cap_val = float(val)
                                    if cap_val > 0:
                                        compatible.append({"machine_type": mct, "capacity_per_day": cap_val})
                                except:
                                    pass

                    # Monthly demands
                    demands = {}
                    for mi, month in enumerate(MONTHS):
                        col_idx = demand_start + mi
                        if col_idx < len(row):
                            val = row[col_idx]
                            try:
                                demands[month] = float(val) if not pd.isna(val) else 0
                            except:
                                demands[month] = 0
                        else:
                            demands[month] = 0

                    if style and capacity > 0:
                        products.append({
                            "id": int(row[0]) if not pd.isna(row[0]) else i - 1,
                            "fp": str(fp),
                            "style": str(style),
                            "cylinder_type": str(cylinder),
                            "machine_type": str(machine_type),
                            "needle_qty": int(needle_qty) if needle_qty else 0,
                            "area": str(area),
                            "capacity_per_day": capacity,
                            "compatible_machines": compatible,
                            "demands": demands,
                            "priority": 1000,
                        })
                except Exception as e:
                    continue

        # Parse machine counts from CapacityPlan row 1
        if "CapacityPlan" in sheet_names:
            df_cp = xl.parse("CapacityPlan", header=None)
            row0 = df_cp.iloc[0].tolist()
            # Machine counts are at specific positions after "No. of Machines Available"
            # From examination: columns 9-20 correspond to MCT1-MCT12 machine counts
            # Row 0: index 28..33 had values 1,1,4,6,1,1 for some machines
            machine_count_cols = list(range(28, 34)) + [9,10,11,12,13,14]
            machines_map = {}
            for mi, mct in enumerate(MACHINE_TYPES):
                # default to 1
                machines_map[mct] = 1

            # Try to read from row 0, columns that have numbers for machine counts
            # Based on the data: (12, 20, 3, 0, 0, 0, 1, 1, 4, 6, 1, 1) at cols 28-33 area
            cp_row0 = df_cp.iloc[0].tolist()
            # Find the "No. of Machines Available" label
            for ci, val in enumerate(cp_row0):
                if val == "No. of Machines Available" or val == "No. of Machines Available ":
                    # Machine counts follow right after
                    for mi, mct in enumerate(MACHINE_TYPES):
                        idx = ci + 1 + mi
                        if idx < len(cp_row0):
                            v = cp_row0[idx]
                            try:
                                machines_map[mct] = int(float(v)) if v and not pd.isna(v) else 1
                            except:
                                machines_map[mct] = 1
                    break

            # If not found, try to get num_days from CapacityPlan row 0
            num_days_val = None
            for ci, val in enumerate(cp_row0):
                if val == "Number of Days available " or val == "Number of Days available":
                    for oi in range(1, 15):
                        idx = ci + oi
                        if idx < len(cp_row0):
                            v = cp_row0[idx]
                            try:
                                if v and not pd.isna(v):
                                    num_days_val = int(float(v))
                                    break
                            except:
                                pass
                    break
            if num_days_val:
                state["num_days"] = num_days_val

        machines_list = [{"machine_type": mct, "num_machines": machines_map.get(mct, 1)} for mct in MACHINE_TYPES]

        state["products"] = products
        state["machines"] = machines_list
        state["schedule"] = {}
        state["capacity_summary"] = {}

        return jsonify({
            "success": True,
            "num_products": len(products),
            "num_machines": len(machines_list),
            "message": f"Loaded {len(products)} products and {len(machines_list)} machine types."
        })
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(state["products"])

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    data["id"] = len(state["products"]) + 1
    if "demands" not in data:
        data["demands"] = {m: 0 for m in MONTHS}
    state["products"].append(data)
    return jsonify({"success": True, "product": data})

@app.route("/api/products/<int:pid>", methods=["PUT"])
def update_product(pid):
    data = request.json
    for i, p in enumerate(state["products"]):
        if p["id"] == pid:
            state["products"][i].update(data)
            return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/products/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    state["products"] = [p for p in state["products"] if p["id"] != pid]
    return jsonify({"success": True})

@app.route("/api/machines", methods=["GET"])
def get_machines():
    return jsonify(state["machines"])

@app.route("/api/machines", methods=["PUT"])
def update_machines():
    data = request.json
    state["machines"] = data
    return jsonify({"success": True})

@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify({"num_days": state["num_days"], "machine_types": MACHINE_TYPES, "months": MONTHS})

@app.route("/api/config", methods=["PUT"])
def update_config():
    data = request.json
    if "num_days" in data:
        state["num_days"] = int(data["num_days"])
    return jsonify({"success": True})


@app.route("/api/optimize", methods=["POST"])
def optimize():
    """
    Core optimization: allocate machine-days to products to meet demand.
    
    Decision variables: x[i][j] = machine-days allocated to product i on machine type j
    
    Objective: Minimize total shortfall (unmet demand)
    
    Constraints:
    - For each machine type j: sum_i(x[i][j]) <= num_machines[j] * num_days
    - For each product i: sum_j(x[i][j] * capacity[i][j]) >= demand[i]  (soft, penalized)
    - x[i][j] = 0 if product i is not compatible with machine type j
    - x[i][j] >= 0
    """
    data = request.json or {}
    selected_month = data.get("month", "Jul")
    num_days = state["num_days"]
    products = state["products"]
    machines = state["machines"]

    if not products:
        return jsonify({"error": "No products loaded"}), 400

    # Build machine available days map
    mach_avail = {}
    for m in machines:
        mach_avail[m["machine_type"]] = m["num_machines"] * num_days

    n_prod = len(products)
    n_mach = len(MACHINE_TYPES)

    # x variables: x[i*n_mach + j] = machine-days for product i on machine type j
    # slack variables: s[i] = shortfall for product i
    n_vars = n_prod * n_mach + n_prod  # x's + slacks

    # Objective: minimize sum of slacks (shortfalls), weighted by priority
    c = [0.0] * (n_prod * n_mach)
    for i, prod in enumerate(products):
        priority = prod.get("priority", 1000)
        weight = 1.0 / max(priority, 1)
        c.append(-weight * 1000)  # negative because linprog minimizes; but we penalize shortfall
    # Actually: minimize shortfall => minimize sum(s_i)
    c = [0.0] * (n_prod * n_mach) + [1.0] * n_prod

    # Inequality constraints: A_ub @ x <= b_ub
    A_ub = []
    b_ub = []

    # Machine capacity constraints: for each machine type j,
    # sum_i(x[i*n_mach+j]) <= avail[j]
    for j, mct in enumerate(MACHINE_TYPES):
        row = [0.0] * n_vars
        for i in range(n_prod):
            row[i * n_mach + j] = 1.0
        A_ub.append(row)
        b_ub.append(mach_avail.get(mct, n_days_default(num_days)))

    # Demand satisfaction: for each product i,
    # -sum_j(x[i*n_mach+j] * cap[i][j]) + s[i] >= -demand[i]
    # => sum_j(-cap * x) + (-s) <= -demand  ... rewrite:
    # sum_j(cap[i][j] * x[i][j]) + s[i] >= demand[i]
    # => -sum_j(cap[i][j]*x) - s[i] <= -demand[i]
    for i, prod in enumerate(products):
        demand = prod.get("demands", {}).get(selected_month, 0)
        if demand <= 0:
            continue
        row = [0.0] * n_vars
        cap_map = {cm["machine_type"]: cm["capacity_per_day"] for cm in prod.get("compatible_machines", [])}
        for j, mct in enumerate(MACHINE_TYPES):
            cap = cap_map.get(mct, 0)
            row[i * n_mach + j] = -cap
        # slack variable for product i
        row[n_prod * n_mach + i] = -1.0
        A_ub.append(row)
        b_ub.append(-demand)

    # Bounds: x >= 0, s >= 0
    bounds = [(0, None)] * (n_prod * n_mach) + [(0, None)] * n_prod

    # Zero out incompatible machine-product pairs via bounds
    for i, prod in enumerate(products):
        cap_map = {cm["machine_type"]: cm["capacity_per_day"] for cm in prod.get("compatible_machines", [])}
        for j, mct in enumerate(MACHINE_TYPES):
            if cap_map.get(mct, 0) == 0:
                bounds[i * n_mach + j] = (0, 0)

    try:
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
        if result.status not in (0, 1):
            return jsonify({"error": f"Solver failed: {result.message}"}), 500

        x = result.x

        # Build schedule output
        schedule = []
        capacity_by_mct = {mct: 0.0 for mct in MACHINE_TYPES}
        total_produced = {}
        total_demand = {}

        for i, prod in enumerate(products):
            demand = prod.get("demands", {}).get(selected_month, 0)
            cap_map = {cm["machine_type"]: cm["capacity_per_day"] for cm in prod.get("compatible_machines", [])}
            allocs = {}
            produced = 0.0
            for j, mct in enumerate(MACHINE_TYPES):
                val = x[i * n_mach + j]
                if val > 0.001:
                    allocs[mct] = round(val, 2)
                    capacity_by_mct[mct] += val
                    produced += val * cap_map.get(mct, 0)

            shortfall = x[n_prod * n_mach + i]
            schedule.append({
                "product_id": prod["id"],
                "style": prod["style"],
                "demand": demand,
                "produced": round(produced, 0),
                "shortfall": round(shortfall, 0),
                "fulfillment_pct": round(min(produced / demand * 100, 100), 1) if demand > 0 else 100,
                "allocations": allocs
            })
            total_produced[prod["style"]] = produced
            total_demand[prod["style"]] = demand

        # Capacity summary per machine type
        cap_summary = []
        for mct in MACHINE_TYPES:
            avail = mach_avail.get(mct, 0)
            used = capacity_by_mct[mct]
            surplus = avail - used
            num_mach = next((m["num_machines"] for m in machines if m["machine_type"] == mct), 1)
            cap_summary.append({
                "machine_type": mct,
                "num_machines": num_mach,
                "total_machine_days": avail,
                "used_machine_days": round(used, 2),
                "surplus_machine_days": round(surplus, 2),
                "utilization_pct": round(used / avail * 100, 1) if avail > 0 else 0
            })

        state["schedule"] = {"month": selected_month, "items": schedule}
        state["capacity_summary"] = cap_summary

        total_demand_sum = sum(s["demand"] for s in schedule)
        total_produced_sum = sum(s["produced"] for s in schedule)
        total_shortfall = sum(s["shortfall"] for s in schedule)
        surplus_mdays = sum(s["surplus_machine_days"] for s in cap_summary if s["surplus_machine_days"] > 0)
        shortage_mdays = sum(abs(s["surplus_machine_days"]) for s in cap_summary if s["surplus_machine_days"] < 0)

        return jsonify({
            "success": True,
            "month": selected_month,
            "schedule": schedule,
            "capacity_summary": cap_summary,
            "summary": {
                "total_demand": total_demand_sum,
                "total_produced": total_produced_sum,
                "total_shortfall": total_shortfall,
                "overall_fulfillment_pct": round(total_produced_sum / total_demand_sum * 100, 1) if total_demand_sum > 0 else 100,
                "surplus_machine_days": round(surplus_mdays, 1),
                "shortage_machine_days": round(shortage_mdays, 1),
            }
        })
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


def n_days_default(num_days):
    return num_days


@app.route("/api/schedule", methods=["GET"])
def get_schedule():
    return jsonify(state.get("schedule", {}))

@app.route("/api/capacity_summary", methods=["GET"])
def get_capacity_summary():
    return jsonify(state.get("capacity_summary", []))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
