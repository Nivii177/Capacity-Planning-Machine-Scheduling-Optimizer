from ortools.linear_solver import pywraplp

def optimize_capacity(demands, rates, counts, hours_per_day, running_days, eligible):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if not solver:
        raise RuntimeError("Solver not available")

    types = list(counts.keys())
    products = list(demands.keys())

    x = {}
    for p in products:
        for t in types:
            if t in eligible[p]:
                x[p, t] = solver.NumVar(0.0, solver.infinity(), f"x_{p}_{t}")
            else:
                x[p, t] = solver.NumVar(0.0, 0.0, f"x_{p}_{t}")

    for p in products:
        solver.Add(sum(x[p, t] for t in types) == demands[p])

    for t in types:
        cap_hours = counts[t] * hours_per_day * running_days
        solver.Add(sum(x[p, t] / rates[p][t] for p in products) <= cap_hours)

    solver.Minimize(sum(x[p, t] / rates[p][t] for p in products for t in types))

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        return {"feasible": False}

    allocation = {p: {t: x[p, t].solution_value() for t in types} for p in products}
    used_hours = {t: sum(allocation[p][t] / rates[p][t] for p in products) for t in types}

    return {"feasible": True, "allocation": allocation, "used_hours": used_hours}
