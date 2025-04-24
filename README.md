
# Code Insight API

A powerful API that combines static code analysis with AI-powered explanations.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)

## 🔍 Overview

Code Insight API analyzes Python code to extract key information about functions, dependencies, and structure, then uses AI to provide natural language explanations. 

## ✨ Features

- **Static Code Analysis**: Extract function details, dependencies, entry points, and documentation
- **AI-Powered Explanations**: Get human-like answers to questions about your code
- **Key Function Identification**: Automatically detect the most important functions in a codebase
- **Flexible Input Options**: Analyze local files, directories, or uploaded code
- **Markdown Documentation**: Generate well-formatted documentation from analysis results

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/analyzer-agent-api.git
cd analyzer-agent-api

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY=your_api_key_here

# Start the server
python run.py
```

The API will be available at `http://localhost:10000`

## 🔌 API Endpoints

### Code Analyzer

Static code analysis endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/codebase-analyzer/file` | POST | Analyze a local Python file |
| `/codebase-analyzer/directory` | POST | Analyze a directory of Python files |
| `/codebase-analyzer/upload` | POST | Analyze an uploaded Python file |

### Code Explainer

AI-powered explanation endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/code-explainer/explain` | POST | Ask questions about pre-analyzed code |
| `/code-explainer/upload` | POST | Upload a file and ask questions about it |
| `/code-explainer/all-in-one` | POST | Analyze and explain code in a single request |
| `/code-explainer/debug-format` | POST | Debug endpoint for data format inspection |

## 📝 Usage Examples

### Analyze and Explain Code (All-in-One)

```bash
curl -X 'POST' \
  'http://localhost:10000/code-explainer/all-in-one' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@user_service.py;type=text/x-python' \
  -F 'query=What are the most important functions in this code?'
```

Response will include both static analysis and AI explanations:

```json
{
  "analysis": {
    "results": {
      "user_service.py": {
        "file": "user_service.py",
        "functions": [...]
      }
    }
  },
  "explanation": {
    "file": "user_service.py",
    "important_functions": [...],
    "markdown": "# 📄 Documentation for `user_service.py`\n\n..."
  }
}
```

## 🔧 Configuration

Required environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key (required for AI explanations)

Optional configuration in `run.py`:

```python
# Change host and port
uvicorn.run("app.main:app", host="0.0.0.0", port=10000, reload=False)
```

## 🛠️ Architecture

```
app/
├── api/                # API endpoints
│   ├── codebase_analyzer.py   # Static analysis endpoints
│   ├── analyzer_agent.py      # AI explanation endpoints
│   └── endpoints.py           # Router configuration
├── models/             # Pydantic models
│   ├── analyze_models.py      # Models for code analysis
│   └── analyzer_agent_models.py  # Models for AI agent
├── modules/
│   ├── code_analyzer/  # Static analysis module
│   └── analyzer_agent/ # AI explanation module
│       ├── agents/     # Agent implementation
│       └── core/       # Core functionality
└── main.py             # FastAPI application
```

## 💬 Example Queries

- "What are the most important functions in this code?"
- "Explain what this code does in simple terms"
- "What does the create_user function do?"
- "How are the functions related to each other?"
- "What are the entry points of this application?"

---

