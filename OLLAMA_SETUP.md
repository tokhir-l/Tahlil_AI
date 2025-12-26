# Using Tahlil with Ollama (GPT OS 120B)

## Setup Overview

The Tahlil project already has built-in support for Ollama! Here's how to use it with your local Ollama GPT OS 120B model.

---

## Step 1: Ensure Ollama is Running

On the computer with Ollama GPT OS 120B installed:

```bash
# Start Ollama service (or make sure it's running)
# On Windows/Mac/Linux, Ollama should run on http://localhost:11434 by default
ollama serve
```

Or if Ollama is already installed as a service, just verify it's accessible at `http://localhost:11434`.

---

## Step 2: Configure Tahlil to Use Ollama

After setting up the project on the new computer (activate venv + install requirements), you have **two options**:

### Option A: Use Environment Variable (Recommended)

Set the Ollama model before running the app. Examples for different models:

**For GPT-OSS 20B (recommended - faster):**

**Windows (PowerShell):**
```powershell
$env:OLLAMA_MODEL = "ollama/gpt-oss-20b"
python app.py
```

**Windows (CMD):**
```cmd
set OLLAMA_MODEL=ollama/gpt-oss-20b
python app.py
```

**Mac/Linux:**
```bash
export OLLAMA_MODEL="ollama/gpt-oss-20b"
python app.py
```

**For GPT-OSS 120B (more capable, slower):**
- Windows (PowerShell): `$env:OLLAMA_MODEL = "ollama/gpt-oss-120b"`
- Windows (CMD): `set OLLAMA_MODEL=ollama/gpt-oss-120b`
- Mac/Linux: `export OLLAMA_MODEL="ollama/gpt-oss-120b"`

### Option B: Modify config.yaml

Edit `config.yaml` in the project root:

```yaml
run_id: "experiment_name"
model_name: "ollama/gpt-oss-20b"  # ← Change this (note: gpt-oss with double 's')
interactive: false
max_refinement_rounds: 2
auto_debug: false
debug_attempts: 2
preserve_artifacts: true
```

Then run:
```bash
python app.py
```

---

## Step 3: Test the Setup

Once the Flask server starts (`python app.py`), open the web UI at `http://localhost:5000`.

1. **Check the Model Selector** — it should show your model choice
2. **Upload a test file** (CSV, Excel, etc.)
3. **Submit a query** — the UI will send it to your local Ollama model
4. **Watch the terminal** — you should see logs like:
   ```
   Run started: <run_id>
   Processing with model: ollama/gpt-oss-20b
   Run completed: <run_id>
   ```

---

## Important: Model Name Format

The model name **must start with `ollama/`** to trigger the OllamaProvider:

✅ **Correct:**
- `ollama/gpt-oss-20b` (note: double 's')
- `ollama/gpt-oss-120b` (note: double 's')
- `ollama/llama2`
- `ollama/mistral`

❌ **Wrong:**
- `gpt-oss-20b` (missing `ollama/` prefix)
- `ollama/gpt-os-20b` (single 's' - incorrect)
- `GPT-OSS-20B` (case-sensitive)

---

## Troubleshooting

### "Connection refused" or "Cannot connect to Ollama"

**Fix:** Ensure Ollama is running:
```bash
ollama serve
```

Or check if it's accessible:
```bash
curl http://localhost:11434/api/tags
```

### "Model not found"

**Fix:** Ensure the model is pulled in Ollama:
```bash
ollama pull gpt-oss-20b
```

Or for the larger model:
```bash
ollama pull gpt-oss-120b
```

List available models:
```bash
ollama list
```

### "OLLAMA_HOST not correct"

If Ollama runs on a different port/host, set the environment variable:

**Windows (PowerShell):**
```powershell
$env:OLLAMA_HOST = "http://localhost:11434"
```

**Mac/Linux:**
```bash
export OLLAMA_HOST="http://localhost:11434"
```

---

## How It Works (Technical Details)

1. **Web UI** (frontend) — User uploads files and submits queries
2. **Flask Backend** (`app.py`) — Reads `model_name` from config or env
3. **Provider Router** (`provider.py`) — Detects `ollama/` prefix and routes to OllamaProvider
4. **OllamaProvider** — Connects to local Ollama at `http://localhost:11434` and sends prompts
5. **Results** — Backend processes Ollama's response and returns results to the UI

---

## Using Ollama on a Different Computer

If Ollama runs on a **different machine** (not localhost), set:

**Windows (PowerShell):**
```powershell
$env:OLLAMA_HOST = "http://192.168.1.100:11434"  # Replace with actual IP
python app.py
```

**Mac/Linux:**
```bash
export OLLAMA_HOST="http://192.168.1.100:11434"
python app.py
```

---

## Summary

| Setting | Command |
|---------|---------|
| Use Ollama GPT-OSS 20B | `set OLLAMA_MODEL=ollama/gpt-oss-20b && python app.py` |
| Use Ollama GPT-OSS 120B | `set OLLAMA_MODEL=ollama/gpt-oss-120b && python app.py` |
| Custom Ollama host | `set OLLAMA_HOST=http://custom-host:11434` |
| List available models | `ollama list` |
| Pull GPT-OSS 20B | `ollama pull gpt-oss-20b` |
| Pull GPT-OSS 120B | `ollama pull gpt-oss-120b` |
| Test connection | `curl http://localhost:11434/api/tags` |

---

## Questions?

- **Model runs but no results?** Check the Flask server terminal for error messages
- **Slow responses?** GPT OS 120B is large; ensure adequate RAM and check Ollama logs
- **Want to switch back to Gemini/OpenAI?** Simply change `OLLAMA_MODEL` or `config.yaml` to a different model prefix (`gpt-`, `gemini-`)
