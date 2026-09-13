# Historical Counterfactual Validation Report
**Dataset:** Nagpur Satellite Record (May 2020 → May 2024)  
**Evaluator:** Chhaon M5 Scenario Transfer Function  
**Model:** `lightgbm_suhii_night_v2` (19 features)  
**Cells Analyzed:** 178

---

## 1. Objective
Validate that counterfactual predictions derived from simulated feature transitions match the real-world thermal response observed over a multi-year satellite record.

---

## 2. Key Metrics
| Metric | Observed | Target | Status |
|---|---|---|---|
| **Pearson Correlation ($r$)** | **0.7128** | $\ge 0.60$ | ✅ PASSED |
| **Spearman Rank ($ho$)** | **0.7647** | $\ge 0.50$ | ✅ PASS |
| **Thermal Delta MAE** | **0.608 °C** | $\le 0.80$ °C | ✅ PASS |
| **Directional Agreement** | **78.7%** | $\ge 70\%$ | ✅ PASS |

---

## 3. Scientific Defensibility
When the model predicts a temperature shift resulting from land-use and environmental feature changes, the predicted $\Delta T$ correlates ($r = 0.71$) with actual historical thermal shifts across Nagpur's grid cells.
