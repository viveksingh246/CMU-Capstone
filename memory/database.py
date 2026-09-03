"""SQLite database for long-term competitive intelligence memory."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

from config import settings
from memory.schemas import Alert, CompanyScore, ExtractedFact


class CompetitiveIntelligenceDB:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS companies (
                    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL UNIQUE,
                    industry TEXT,
                    website TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS research_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    research_topic TEXT NOT NULL,
                    industry TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    categories TEXT,
                    status TEXT NOT NULL DEFAULT 'in_progress',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS findings (
                    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    company_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    evidence TEXT,
                    source_url TEXT,
                    source_title TEXT,
                    published_date TEXT,
                    source_type TEXT,
                    confidence REAL,
                    is_company_claim INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES research_runs(run_id),
                    FOREIGN KEY (company_id) REFERENCES companies(company_id)
                );

                CREATE TABLE IF NOT EXISTS company_scores (
                    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    company_id INTEGER NOT NULL,
                    product_score REAL,
                    pricing_score REAL,
                    innovation_score REAL,
                    market_score REAL,
                    ai_score REAL,
                    partnerships_score REAL,
                    hiring_score REAL,
                    overall_score REAL,
                    rationale TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES research_runs(run_id),
                    FOREIGN KEY (company_id) REFERENCES companies(company_id)
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    run_id INTEGER,
                    alert_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    source_url TEXT,
                    priority TEXT DEFAULT 'medium',
                    detected_at TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    FOREIGN KEY (company_id) REFERENCES companies(company_id),
                    FOREIGN KEY (run_id) REFERENCES research_runs(run_id)
                );
                """
            )

    def upsert_company(self, company_name: str, industry: str = "") -> int:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT company_id FROM companies WHERE company_name = ?",
                (company_name,),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE companies SET industry = ?, updated_at = ? WHERE company_id = ?",
                    (industry, now, row["company_id"]),
                )
                return int(row["company_id"])

            cursor = conn.execute(
                """
                INSERT INTO companies (company_name, industry, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (company_name, industry, now, now),
            )
            return int(cursor.lastrowid)

    def create_research_run(
        self,
        research_topic: str,
        industry: str,
        categories: list[str],
        start_date: str,
        end_date: str,
    ) -> int:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO research_runs
                (research_topic, industry, start_date, end_date, categories, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'in_progress', ?)
                """,
                (research_topic, industry, start_date, end_date, ",".join(categories), now),
            )
            return int(cursor.lastrowid)

    def complete_research_run(self, run_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE research_runs SET status = 'completed' WHERE run_id = ?",
                (run_id,),
            )

    def save_finding(
        self,
        run_id: int,
        company_id: int,
        fact: ExtractedFact,
    ) -> int:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO findings
                (run_id, company_id, category, claim, evidence, source_url,
                 source_title, published_date, source_type, confidence,
                 is_company_claim, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    company_id,
                    fact.category,
                    fact.claim,
                    fact.evidence,
                    fact.source_url,
                    fact.source_title,
                    fact.published_date,
                    fact.source_type.value,
                    fact.confidence,
                    int(fact.is_company_claim),
                    now,
                ),
            )
            return int(cursor.lastrowid)

    def save_score(self, run_id: int, company_id: int, score: CompanyScore) -> None:
        now = datetime.utcnow().isoformat()
        rationale = str(score.rationale)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO company_scores
                (run_id, company_id, product_score, pricing_score, innovation_score,
                 market_score, ai_score, partnerships_score, hiring_score,
                 overall_score, rationale, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    company_id,
                    score.product_breadth,
                    score.pricing_attractiveness,
                    score.innovation_momentum,
                    score.feature_differentiation,
                    score.ai_maturity,
                    score.partnerships,
                    score.hiring_momentum,
                    score.overall_score,
                    rationale,
                    now,
                ),
            )

    def save_alert(self, company_id: int, alert: Alert, run_id: Optional[int] = None) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO alerts
                (company_id, run_id, alert_type, description, source_url, priority, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company_id,
                    run_id,
                    alert.alert_type,
                    alert.description,
                    alert.source_url,
                    alert.priority,
                    alert.detected_at.isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def get_previous_findings(
        self,
        company_name: str,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT f.*, c.company_name, r.created_at AS run_created_at
            FROM findings f
            JOIN companies c ON f.company_id = c.company_id
            JOIN research_runs r ON f.run_id = r.run_id
            WHERE c.company_name = ?
        """
        params: list[Any] = [company_name]
        if category:
            query += " AND f.category = ?"
            params.append(category)
        query += " ORDER BY f.created_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_latest_scores(self, company_name: str) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT cs.*, c.company_name, r.created_at AS run_created_at
                FROM company_scores cs
                JOIN companies c ON cs.company_id = c.company_id
                JOIN research_runs r ON cs.run_id = r.run_id
                WHERE c.company_name = ?
                ORDER BY cs.created_at DESC
                LIMIT 1
                """,
                (company_name,),
            ).fetchone()
            return dict(row) if row else None

    def get_completed_queries_for_run(self, run_id: int) -> list[str]:
        """Return distinct source URLs as a proxy for completed searches."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT source_url FROM findings WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [row["source_url"] for row in rows if row["source_url"]]

    def get_findings_for_run(self, run_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT f.*, c.company_name
                FROM findings f
                JOIN companies c ON f.company_id = c.company_id
                WHERE f.run_id = ?
                ORDER BY f.category, f.company_id
                """,
                (run_id,),
            ).fetchall()
            return [dict(row) for row in rows]
