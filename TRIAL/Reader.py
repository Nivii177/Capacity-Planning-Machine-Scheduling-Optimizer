import pandas as pd
import numpy as np

CSV_PATH = "./SampleData.csv"  # change to your local path
MONTH = "Jul"                # Jan, Feb, ... Dec
AVAILABLE_DAYS = 20          # A

# Put your real machine counts here (must match CSV machine column headers exactly)
MACHINE_COUNTS = {
    # "MCT1 : SS (G21 TY M)": 10,
    # ...
}

def month_demand_col(month: str) -> str:
    return f"{month} Demand (pairs)"

def detect_machine_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if str(c).strip().startswith("MCT")]

def main():
    df = pd.read_csv(CSV_PATH)
    demand_col = month_demand_col(MONTH)
    machine_cols = detect_machine_columns(df)

    if demand_col not in df.columns:
        raise ValueError(f"Missing demand column: {demand_col}")

    # Keep rows that actually have a style code
    df = df[df["STYLE-SIZE"].notna()].copy()

    # Build sets
    styles = [str(s).strip() for s in df["STYLE-SIZE"].tolist()]

    # Build rates r_{s,m} from the CSV:
    # r[(style, machine)] = pairs_per_day
    rates = {}
    for _, row in df.iterrows():
        s = str(row["STYLE-SIZE"]).strip()
        for m in machine_cols:
            v = row[m]
            if pd.notna(v):
                v = pd.to_numeric(v, errors="coerce")
                if pd.notna(v) and float(v) > 0:
                    rates[(s, m)] = float(v)

    # Demands D_s
    demand_series = pd.to_numeric(df[demand_col], errors="coerce").fillna(0.0)
    demands = {str(df.iloc[i]["STYLE-SIZE"]).strip(): float(demand_series.iloc[i]) for i in range(len(df))}

    # Machine-day capacities M_m
    # You can print them even if MACHINE_COUNTS is incomplete
    machine_days = {}
    for m in machine_cols:
        c = MACHINE_COUNTS.get(m, None)
        if c is None:
            machine_days[m] = None
        else:
            machine_days[m] = float(c) * float(AVAILABLE_DAYS)

    # ============ PRINT CONSTRAINTS ============
    print("\n=============================")
    print(f"Constraint system for period/month: {MONTH}")
    print("=============================\n")

    # Decision variables that exist (only for compatible pairs)
    x_vars = sorted(rates.keys())  # list of (s,m) where x[s,m] exists

    print("Decision variables (machine-days):")
    for (s, m) in x_vars[:30]:
        print(f"  x[{s}, {m}] >= 0")
    if len(x_vars) > 30:
        print(f"  ... ({len(x_vars)} total x variables)")
    print()

    # 1) Machine capacity constraints
    print("1) Machine capacity constraints:")
    for m in machine_cols:
        # styles that can run on m
        compatible_styles = [s for s in styles if (s, m) in rates]
        if not compatible_styles:
            continue

        lhs = " + ".join([f"x[{s},{m}]" for s in compatible_styles])

        if machine_days[m] is None:
            rhs = f"(machine_count[{m}] * {AVAILABLE_DAYS})"
        else:
            rhs = f"{machine_days[m]:.3f}"

        print(f"  {lhs} <= {rhs}")
    print()

    # 2) Production definition constraints (y_s)
    print("2) Production definition constraints:")
    for s in styles:
        terms = []
        for m in machine_cols:
            if (s, m) in rates:
                r = rates[(s, m)]
                terms.append(f"{r}*x[{s},{m}]")
        if not terms:
            print(f"  y[{s}] = 0")
        else:
            rhs = " + ".join(terms)
            print(f"  y[{s}] = {rhs}")
    print()

    # 3) Demand fulfillment constraints with shortage
    print("3) Demand fulfillment constraints (with shortage):")
    for s in styles:
        D = demands.get(s, 0.0)
        print(f"  y[{s}] + u[{s}] = {D}")
        print(f"  u[{s}] >= 0")
    print()

    # 4) Compatibility constraints (if you were to create all x vars)
    print("4) Compatibility constraints (only needed if you define x for all pairs):")
    printed = 0
    for s in styles:
        for m in machine_cols:
            if (s, m) not in rates:
                print(f"  x[{s},{m}] = 0")
                printed += 1
                if printed >= 20:
                    print(f"  ... ({printed} shown, many more)")
                    break
        if printed >= 20:
            break

    print("\nDone.\n")

if __name__ == "__main__":
    main()