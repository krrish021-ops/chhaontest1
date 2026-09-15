"""
Multi-Scenario Comparison Engine (TRD §8.2 & PRD §6.5).

Evaluates 2-4 counterfactual scenarios simultaneously:
  - Computes per-scenario ΔT distributions (P10, P50, P90)
  - Calculates cost-efficiency: ₹ per °C cooling per capita
  - Produces differential matrices between Scenario A and Scenario B

SUPPORTED ACTIONS: "add_trees", "add_concrete", "restore_water" only.
"cool_roofs" is NOT supported — the underlying model has no albedo
feature to represent it. See models/transfer_function/scenario_engine.py
module docstring for the full explanation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import lightgbm as lgb
import json

from models.transfer_function.scenario_engine import simulate_intervention

DATA_DIR = Path("data/tables")
MODEL_PATH = Path("models/registry/lightgbm_suhii_night_v2.txt")


def compare_scenarios(city_id: str, cell_id: str, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compares multiple scenario interventions on a target cell.

    scenarios format (valid actions: add_trees, add_concrete, restore_water):
      [
        {"name": "Option A: Tree Canopy", "action": "add_trees", "area_pct": 25},
        {"name": "Option B: Water Body", "action": "restore_water", "area_pct": 15},
        {"name": "Option C: Densification", "action": "add_concrete", "area_pct": 10}
      ]
    """
    results = []

    for sc in scenarios:
        name = sc.get("name", "Unnamed Scenario")
        action = sc.get("action", "add_trees")
        area_pct = float(sc.get("area_pct", 20))

        # Run inference via scenario engine — city_id MUST be passed
        # through, otherwise this silently defaults to Nagpur's data
        # regardless of which city the cell actually belongs to.
        sim = simulate_intervention(
            cell_id=cell_id,
            action=action,
            area_pct_change=area_pct,
            city_id=city_id,
        )

        delta_degC = sim["delta_T_degC"]["p50"]
        delta_p10 = sim["delta_T_degC"]["p10"]
        delta_p90 = sim["delta_T_degC"]["p90"]
        cost_lakh = sim["estimated_cost_inr"] / 100000.0

        eff = round(cost_lakh / abs(delta_degC) * 0.1, 2) if abs(delta_degC) > 0 else 0.0

        results.append({
            "name": name,
            "action": action,
            "area_pct": area_pct,
            "delta_T_p50": delta_degC,
            "delta_T_p10": delta_p10,
            "delta_T_p90": delta_p90,
            "original_suhii": sim["original_suhii_night"]["p50"],
            "new_suhii": sim["new_suhii_night"]["p50"],
            "cost_inr": sim["estimated_cost_inr"],
            "cost_inr_formatted": sim["cost_formatted"],
            "cost_per_tenth_degree_lakh": eff,
            "confidence": sim.get("confidence", "high"),
            "extrapolation_warning": sim.get("extrapolation_warning", False),
            "cross_city_model": sim.get("cross_city_model", False),
        })

    results_sorted = sorted(results, key=lambda x: x["delta_T_p50"])
    best_scenario = results_sorted[0]["name"] if results_sorted else None

    return {
        "cell_id": cell_id,
        "city_id": city_id,
        "scenarios_evaluated": len(results),
        "best_cooling_scenario": best_scenario,
        "comparison_table": results,
    }
