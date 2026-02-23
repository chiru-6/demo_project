"""Chatbot view: AI assistant for querying test data via Ollama."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ChatbotWidget(QWidget):
    """Widget for AI chatbot interface using Ollama."""

    def __init__(self, db) -> None:
        super().__init__()
        self.db = db
        self.chat_history: List[Dict[str, str]] = []
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        info_label = QLabel(
            "💡 Ask questions about your test data in natural language. "
            "Make sure Ollama is running locally."
        )
        info_label.setObjectName("infoLabel")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("#infoLabel { padding: 8px; border-radius: 5px; font-size: 12px; }")
        layout.addWidget(info_label)
        examples_label = QLabel(
            "Example queries: 'How many records?', 'Show all projects', "
            "'What test rigs are used?'"
        )
        examples_label.setObjectName("examplesLabel")
        examples_label.setWordWrap(True)
        examples_label.setStyleSheet("#examplesLabel { padding: 4px; font-size: 11px; }")
        layout.addWidget(examples_label)
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 10))
        self.chat_display.setStyleSheet("#chatDisplay { padding: 10px; }")
        layout.addWidget(self.chat_display)
        self.add_message(
            "assistant",
            "Hello! I'm your AI assistant. I can help you query and "
            "analyze your test data. Ask me anything!",
        )
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask me about your test data...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 8px 20px;"
        )
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

    def add_message(self, role: str, content: str) -> None:
        if role == "user":
            self.chat_display.append(f"<b>You:</b> {content}<br>")
        else:
            self.chat_display.append(f"<b>Assistant:</b> {content}<br><br>")
        self.chat_history.append({"role": role, "content": content})
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def send_message(self) -> None:
        prompt = self.input_field.text().strip()
        if not prompt:
            return
        self.add_message("user", prompt)
        self.input_field.clear()
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Thinking...")
        try:
            response = self.get_chatbot_response(prompt)
            self.add_message("assistant", response)
        except Exception as error:
            self.add_message("assistant", f"Error: {str(error)}")
        finally:
            self.send_btn.setEnabled(True)
            self.send_btn.setText("Send")

    def get_chatbot_response(self, prompt: str) -> str:
        try:
            import ollama  # pylint: disable=import-outside-toplevel

            df = self.db.get_all_data()
            stats = self.db.get_statistics()
            context = f"""
            You are an assistant for an LCA Test Data Management System.

            Database Statistics:
            - Total Records: {stats.get('total_records', 0)}
            - Projects: {', '.join(list(stats.get('projects', {}).keys())[:5])}
            - Test Rigs: {', '.join(list(stats.get('test_rigs', {}).keys())[:5])}
            - Test Types: {', '.join(list(stats.get('test_types', {}).keys())[:5])}

            Available columns in the database:
            - LRU Name, Project, Division/Group, System, Part Number, Serial No
            - Received Data, Type of Test, Test Rig, Date of PI, Results & Remarks, Date of Clearance

            When asked about data, you can query the database using SQL. Be helpful and provide accurate information.
            """
            sql_query = None
            prompt_lower = prompt.lower()

            # Deterministic answers for time-based count questions.
            # This avoids the model hallucinating when the query result is just a count.
            def _get_record_dates(frame: pd.DataFrame) -> pd.Series:
                if "date_of_pi" in frame.columns:
                    # Common in your dataset (often dd-mm-yyyy)
                    return pd.to_datetime(
                        frame["date_of_pi"], errors="coerce", dayfirst=True
                    )
                if "created_at" in frame.columns:
                    return pd.to_datetime(frame["created_at"], errors="coerce")
                return pd.to_datetime(pd.Series([pd.NaT] * len(frame)))

            def _filter_this_month(frame: pd.DataFrame) -> pd.DataFrame:
                if frame.empty:
                    return frame
                now = pd.Timestamp.now()
                start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                next_month = (start + pd.offsets.MonthBegin(1)).normalize()
                dates = _get_record_dates(frame)
                return frame[(dates >= start) & (dates < next_month)]

            def _count_by_status(frame: pd.DataFrame, status_phrase: str) -> int:
                if frame.empty or "results_remarks" not in frame.columns:
                    return 0
                s = frame["results_remarks"].astype(str).str.lower()
                return int(s.str.contains(status_phrase.lower(), na=False).sum())

            if ("how many" in prompt_lower or "count" in prompt_lower) and "this month" in prompt_lower:
                month_df = _filter_this_month(df)
                # Status first (avoid matching 'ok' inside 'not ok')
                if "not ok" in prompt_lower:
                    n = _count_by_status(month_df, "not ok")
                    return f"There are {n} NOT OK tests this month."
                if "under review" in prompt_lower:
                    n = _count_by_status(month_df, "under review")
                    return f"There are {n} Under Review tests this month."
                if "pending" in prompt_lower:
                    n = _count_by_status(month_df, "pending")
                    return f"There are {n} Pending tests this month."
                if " ok" in prompt_lower or prompt_lower.startswith("ok "):
                    # Match OK but not NOT OK (already handled above)
                    n = _count_by_status(month_df, "ok")
                    return f"There are {n} OK tests this month."
                # Generic count for this month
                return f"There are {len(month_df)} tests recorded this month."

            if "how many" in prompt_lower or "count" in prompt_lower:
                system_codes = {
                    "hyd": "HYD",
                    "ele": "ELE",
                    "pneu": "PNEU",
                    "gen": "GEN",
                    "avionics": "AVIONICS",
                }
                if "system" in prompt_lower:
                    for key, code in system_codes.items():
                        if key in prompt_lower:
                            sql_query = (
                                "SELECT COUNT(*) as count FROM lca_test_data "
                                f"WHERE UPPER(system) = '{code}'"
                            )
                            break
                if sql_query is None:
                    if (
                        "result" in prompt_lower
                        or "results" in prompt_lower
                        or "remarks" in prompt_lower
                    ):
                        status_phrases = [
                            ("under review", "Under Review"),
                            ("not ok", "NOT OK"),
                            ("pending", "Pending"),
                            ("ok", "OK"),
                        ]
                        for phrase, value in status_phrases:
                            if phrase in prompt_lower:
                                sql_query = (
                                    "SELECT COUNT(*) as count FROM lca_test_data "
                                    f"WHERE LOWER(results_remarks) = '{value.lower()}'"
                                )
                                break
                        if sql_query is None:
                            sql_query = (
                                "SELECT results_remarks, COUNT(*) as count "
                                "FROM lca_test_data GROUP BY results_remarks"
                            )
                    elif "project" in prompt_lower:
                        sql_query = (
                            "SELECT project, COUNT(*) as count "
                            "FROM lca_test_data GROUP BY project"
                        )
                    elif "test rig" in prompt_lower:
                        sql_query = (
                            "SELECT test_rig, COUNT(*) as count "
                            "FROM lca_test_data GROUP BY test_rig"
                        )
                    else:
                        sql_query = "SELECT COUNT(*) as total FROM lca_test_data"
            elif "list" in prompt_lower or "show" in prompt_lower or "get" in prompt_lower:
                if "all" in prompt_lower:
                    sql_query = "SELECT * FROM lca_test_data LIMIT 20"
                elif "project" in prompt_lower:
                    sql_query = "SELECT DISTINCT project FROM lca_test_data"
                elif "test rig" in prompt_lower:
                    sql_query = "SELECT DISTINCT test_rig FROM lca_test_data"
            query_result_str = None
            direct_answer = None
            if sql_query:
                try:
                    query_result = self.db.query_data(sql_query)
                    if not query_result.empty:
                        query_result_str = query_result.to_string()
                        # Hard-coded direct answers for common queries (fallback if Ollama fails)
                        if "COUNT(*)" in sql_query.upper() or "count" in sql_query.lower():
                            if "results_remarks" in sql_query.upper():
                                if "GROUP BY" in sql_query.upper():
                                    # Grouped results
                                    direct_answer = "Test results breakdown:\n"
                                    for _, row in query_result.iterrows():
                                        status = row.get("results_remarks", "Unknown")
                                        count = row.get("count", 0)
                                        direct_answer += f"- {status}: {count}\n"
                                else:
                                    # Single count
                                    count_val = query_result.iloc[0].get("count", 0)
                                    if "NOT OK" in sql_query.upper() or "not ok" in prompt_lower:
                                        direct_answer = f"There are {count_val} NOT OK tests."
                                    elif "OK" in sql_query.upper() and "NOT" not in sql_query.upper():
                                        direct_answer = f"There are {count_val} OK tests."
                                    else:
                                        direct_answer = f"Count: {count_val}"
                            elif "project" in sql_query.lower():
                                if "GROUP BY" in sql_query.upper():
                                    direct_answer = "Projects:\n"
                                    for _, row in query_result.iterrows():
                                        proj = row.get("project", "Unknown")
                                        count = row.get("count", 0)
                                        direct_answer += f"- {proj}: {count} tests\n"
                                else:
                                    count_val = query_result.iloc[0].get("count", 0)
                                    direct_answer = f"Total: {count_val} tests"
                            elif "test_rig" in sql_query.lower():
                                if "GROUP BY" in sql_query.upper():
                                    direct_answer = "Test rigs:\n"
                                    for _, row in query_result.iterrows():
                                        rig = row.get("test_rig", "Unknown")
                                        count = row.get("count", 0)
                                        direct_answer += f"- {rig}: {count} tests\n"
                                else:
                                    count_val = query_result.iloc[0].get("count", 0)
                                    direct_answer = f"Total: {count_val} tests"
                            else:
                                count_val = query_result.iloc[0].get("total", query_result.iloc[0].get("count", 0))
                                direct_answer = f"Total records: {count_val}"
                        elif "DISTINCT" in sql_query.upper():
                            col_name = list(query_result.columns)[0]
                            items = query_result[col_name].dropna().tolist()
                            direct_answer = f"{col_name.replace('_', ' ').title()}:\n" + "\n".join(f"- {item}" for item in items[:20])
                    else:
                        query_result_str = "No results found"
                except Exception as error:
                    query_result_str = f"Query error: {str(error)}"
            
            # Try Ollama first, fallback to direct answer if it fails
            user_message = f"{context}\n\nUser Question: {prompt}"
            if query_result_str:
                user_message += f"\n\nQuery Result:\n{query_result_str}"
            
            try:
                response = ollama.chat(
                    model="llama3.2",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a helpful assistant for an LCA Test Data "
                                "Management System.\n\n"
                                "- Answer in a simple, easy-to-read way.\n"
                                "- Prefer short sentences and bullet lists.\n"
                                "- Do NOT show SQL code, tables, or markdown fences "
                                "unless the user explicitly asks for SQL.\n"
                                "- For questions like \"list all ...\", just return a clean "
                                "bullet list of the items, nothing else.\n"
                                "- Avoid long explanations of what you are doing; go "
                                "straight to the answer.\n"
                            ),
                        },
                        {"role": "user", "content": user_message},
                    ],
                )
                return response["message"]["content"]
            except Exception as ollama_error:
                # Fallback to direct answer if Ollama fails
                if direct_answer:
                    return direct_answer
                raise ollama_error
        except ImportError:
            return (
                "Ollama is not installed.\n\n"
                "To use the chatbot, please install Ollama:\n"
                "1. Install Ollama from https://ollama.ai\n"
                "2. Install the Python client: pip install ollama\n"
                "3. Start Ollama service: ollama serve\n"
                "4. Pull a model: ollama pull llama3.2\n\n"
                "Then restart this application."
            )
        except Exception as error:
            stats = self.db.get_statistics()
            if "how many" in prompt.lower():
                total = stats.get("total_records", 0)
                return f"The database contains **{total}** total records."
            if "project" in prompt.lower():
                projects = ", ".join(list(stats.get("projects", {}).keys()))
                return f"Projects in the database: {projects}"
            if "test rig" in prompt.lower():
                rigs = ", ".join(list(stats.get("test_rigs", {}).keys()))
                return f"Test rigs in the database: {rigs}"
            return (
                f"I encountered an error: {str(error)}. "
                "Please make sure Ollama is running and a model is available."
            )
