#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — add your API keys before running research."
fi

python -c "from memory.database import CompetitiveIntelligenceDB; CompetitiveIntelligenceDB(); print('Database ready.')"

echo "Starting Streamlit app at http://localhost:8501"
exec streamlit run app.py
