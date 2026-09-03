.PHONY: setup install test run db-init clean mcp-search mcp-memory

setup: install db-init

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@test -f .env || cp .env.example .env

db-init:
	.venv/bin/python -c "from memory.database import CompetitiveIntelligenceDB; CompetitiveIntelligenceDB(); print('Database initialized.')"

test:
	.venv/bin/pytest -q

run:
	.venv/bin/streamlit run app.py

mcp-search:
	.venv/bin/python mcp_servers/search_server.py

mcp-memory:
	.venv/bin/python mcp_servers/memory_server.py

clean:
	rm -rf .venv memory/*.db reports/*.md reports/*.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
