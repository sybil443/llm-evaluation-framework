# FastAPI Starter + Evaluation Utilities

## Overview
This repository is a small training project for two goals:

1. practicing **ML service fundamentals** with FastAPI
2. building **evaluation utilities** for model assessment

The current repo contains:
- a FastAPI app with starter endpoints (`/hello`, `/health`, `/echo`)
- Pydantic request/response models and structured logging on `/echo`
- a bootstrap confidence-interval utility with reproducibility tests
- an A/B mean-comparison helper built on top of bootstrap CIs
- design notes and diagrams to support interview explanations

This project is intentionally small and incremental. The goal is to build a clean foundation that can later grow into:
- a more realistic ML inference service
- a reusable evaluation harness for model assessment

---

## Why I built this
I built this repository as part of a training plan for:
- **ML engineer roles**, where I need practice with service structure, API design, validation, and logging
- **evaluation-focused ML/data science roles**, where I need practice with statistical tooling, uncertainty-aware reporting, and model evaluation workflows

The idea is to practice both tracks in one lightweight codebase before splitting them into larger standalone projects.

---

## API endpoints

| Method | Path     | Purpose                                      |
|--------|----------|----------------------------------------------|
| GET    | `/hello` | Simple greeting; verify the service runs     |
| GET    | `/health`| Lightweight health check                     |
| POST   | `/echo`  | Echo a validated message; practice logging   |

`POST /echo` expects JSON `{"message": "..."}` and returns the same shape. Empty or whitespace-only messages return `400`.

See `app/endpoint_map.md` and `app/api_design_notes.md` for more detail.

---

## Repository structure

```text
fastapi_v1/
├── README.md
├── requirements.txt
├── api_contract_note.md
├── request_flow_diagram.md
├── app/
│   ├── main.py              # FastAPI routes
│   ├── schemas.py           # Pydantic models
│   ├── app_config.json
│   ├── endpoint_map.md
│   └── api_design_notes.md
└── evaluation/
    ├── bootstrap_ci.py      # Percentile bootstrap CI for the mean
    ├── ab_compare.py          # A vs B mean comparison with CIs
    ├── test_bootstrap_ci.py
    ├── test_reproducibility.py
    ├── test_ab_compare.py
    ├── bootstrap_config.json
    ├── notes.md
    ├── reproducibility_checklist.md
    ├── reproducibility_note.md
    ├── slice_eval_design.md
    ├── slice_eval_flow_diagram.md
    ├── run_logging_design.md
    ├── run_logging_schema.md
    ├── run_log_example.json
    ├── failure_analysis_workflow.md
    ├── failure_analysis_template.md
    └── report_template.md
```

---

## Run locally (virtual environment first)

1. **Go to the project directory**

   ```bash
   cd /path/to/fastapi_v1
   ```

2. **Create a virtual environment** (creates a `.venv` folder; `.gitignore` already ignores it)

   ```bash
   python3 -m venv .venv
   ```

3. **Activate it**

   - **macOS / Linux (bash or zsh):**

     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Start the API** (reload on code changes)

   ```bash
   uvicorn app.main:app --reload
   ```

6. **Try it** — open [http://127.0.0.1:8000/hello](http://127.0.0.1:8000/hello), [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health), or the interactive docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

   Example echo request:

   ```bash
   curl -X POST http://127.0.0.1:8000/echo \
     -H "Content-Type: application/json" \
     -d '{"message": "hello"}'
   ```

7. **Leave the virtual environment** when you are done

   ```bash
   deactivate
   ```

Next time you work on the project, skip steps 2–4: activate `.venv`, then run `uvicorn` again.

---

## Run evaluation tests

From the project root (with the virtual environment active):

```bash
pip install pytest
pytest evaluation/
```

Tests cover bootstrap CI behavior, seed reproducibility, and the A/B comparison helper.
