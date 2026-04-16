# FastAPI Starter + Evaluation Utilities

## Overview
This repository is a small training project for two goals:

1. practicing **ML service fundamentals** with FastAPI
2. building **evaluation utilities** for model assessment

The current repo contains:
- a minimal FastAPI app with starter endpoints
- a bootstrap confidence interval utility with tests
- notes and simple diagrams to support interview explanations

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

## Repository structure

```text
fastapi_v1/
├── README.md
├── requirements.txt
├── notes.md
├── request_flow_diagram.md
├── app/
│   └── main.py
└── evaluation/
    ├── bootstrap_ci.py
    ├── test_bootstrap_ci.py
    └── notes.md
```

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

7. **Leave the virtual environment** when you are done

   ```bash
   deactivate
   ```

Next time you work on the project, skip steps 2–4: activate `.venv`, then run `uvicorn` again.
