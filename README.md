# fastapi_v1

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
