# Tahlil: AI-Powered Data Analysis Platform

Tahlil is a chat-based AI platform that helps non-technical users uncover insights from their data through natural language conversations. Simply upload your data (or connect Google Sheets), ask questions, and get humanized answers with visualizations.

## 🎯 What is Tahlil?

**For Non-Technical Users:**
- Upload your data files or paste a Google Sheets link
- Ask questions in plain English
- Get easy-to-understand insights with visualizations
- No coding or technical knowledge required

**For Technical Users:**
- View the generated Python code behind every analysis
- Copy and customize the code for your own use
- Full transparency into the AI's reasoning process

## ✨ Key Features

### 💬 Chat-Based Interface
- Conversational AI that understands your questions
- Real-time progress tracking
- Step-by-step visibility into the analysis process

### 📊 Data Input
- **File Upload**: CSV, Excel (.xlsx, .xls), JSON, Parquet
- **Google Sheets**: Import directly via link

### 🤖 Multi-Agent AI System
8 specialized agents work together:
1. **Analyzer** - Understands your data structure
2. **Planner** - Creates analysis strategy
3. **Coder** - Writes Python code
4. **Executor** - Runs the analysis
5. **Debugger** - Fixes any errors
6. **Verifier** - Validates results
7. **Router** - Decides next steps
8. **Finalizer** - Formats output for humans

### 📈 Output
- **Humanized Text** - Plain language explanations
- **Visualizations** - Charts and graphs (Superset integration coming)
- **Code Visibility** - See all generated code

### 🔐 Security
- Local file storage
- API keys via environment variables
- Full audit trail of all analyses

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Set Your API Key

```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your-api-key"

# Linux/Mac
export GEMINI_API_KEY="your-api-key"
```

Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 3. Start the Server

```bash
python app.py
```

### 4. Open the Web Interface

Navigate to: **http://localhost:5000**

## 📁 Project Structure

```
Tahlil/
├── app.py                    # Flask backend API
├── tahlil.py                 # Core multi-agent pipeline
├── provider.py               # AI model providers
├── storage.py                # File storage management
├── file_validator.py         # File validation
├── prompt.yaml               # Agent prompts
├── config.yaml               # Configuration
│
├── tools/
│   └── spreadsheet_connector.py  # Google Sheets import
│
├── frontend/
│   ├── App.tsx               # Main React app
│   ├── components/           # UI components
│   └── services/api.ts       # API client
│
├── data/                     # Uploaded files
└── runs/                     # Analysis results
```

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
model_name: "gemini-2.0-flash"    # AI model to use
max_refinement_rounds: 3          # Max analysis iterations
auto_debug: false                 # Auto-fix code errors
preserve_artifacts: true          # Save all analysis steps
```

## 🤖 Supported AI Models

### Google Gemini (Default)
```bash
export GEMINI_API_KEY="your-key"
```
Models: `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`

### OpenAI
```bash
export OPENAI_API_KEY="your-key"
```
Models: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`

### Ollama (Local)
```bash
export OLLAMA_HOST="http://localhost:11434"
```
Models: `ollama/llama3`, `ollama/mistral`

## 📊 Usage Examples

### Example 1: Sales Analysis
```
📎 Upload: sales_data.csv
💬 Question: "What are the top 5 products by revenue?"
⏱️ Time: ~2-3 minutes
```

### Example 2: Trend Analysis
```
🔗 Google Sheets: https://docs.google.com/spreadsheets/d/...
💬 Question: "Show me the monthly growth trends"
⏱️ Time: ~3-4 minutes
```

### Example 3: Customer Insights
```
📎 Upload: customers.xlsx
💬 Question: "Group customers by purchase behavior"
⏱️ Time: ~4-5 minutes
```

## 🛠️ Command Line Usage

```bash
# Start new analysis
uv run python tahlil.py --data-files data.csv --query "Analyze trends"

# Resume interrupted analysis
uv run python tahlil.py --resume <run_id>

# Interactive mode (step-by-step)
uv run python tahlil.py --interactive --data-files data.csv --query "..."
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## 📄 License

MIT License
