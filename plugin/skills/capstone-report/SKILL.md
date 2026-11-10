---
name: capstone-report
description: Write or update SE331 capstone deliverables for the Real Estate Price Prediction System — progress reports, final report, SRS sections, UML/diagrams, presentation slides, viva prep — using the project's real results.
---

# Capstone report helper

Team: Afroza Yesmin (232-35-636), Taspia Ahmed (232-35-710), Sanzida Islam (232-35-701).
Course SE331 Software Engineering Design Capstone, Section E1, Batch 41. Teacher: MD. Rashedul Alam.

## Always pull real numbers

- Model comparison: `models/metadata.json` → `results` (test R², CV R², MAE, MAE %).
- Cleaning stats: `metadata.json` → `cleaning` (raw rows, rows after cleaning, locations kept).
- Charts: `reports/figures/*.png`.
- Never invent metrics. If the model was trained on the synthetic dataset, say so.

## Map work to the proposal

| Proposal item | Where it is implemented |
|---|---|
| FR-1 inputs, FR-2 searchable locations | `app/templates/index.html`, `app/static/app.js` |
| FR-3 validation, FR-5 out-of-range message | `validate()` in `app/server.py` + client checks |
| FR-4 BDT price < 2 s, 500 ms target | `/api/predict`; `test_predict_ok_and_fast` |
| FR-6 median imputation, FR-7 one-hot | `src/train.py` `build_preprocessor()` |
| FR-8 continuous prediction | model pipeline (log-target regressor) |
| FR-9 R² ≥ 0.80, FR-10 MAE < 10% | gates in `src/train.py`; `test_model_meets_accuracy_gates` |
| IQR filtering, "Other" grouping | `src/preprocess.py` |
| Logs in SQL DB | `app/db.py` |
| Ethics disclaimer | API `disclaimer` field + UI footer |

## Diagrams

Use Mermaid for: use-case diagram (Buyer, Seller, Agent, Admin/Developer), sequence diagram
(User → UI → Flask API → Model → DB), class diagram (Preprocessor, Trainer, PredictionAPI, PredictionLog),
and an activity diagram of the 5-step workflow in proposal §1.6.
