"""Database layer for the Test Data Management System.

This module provides the DatabaseManager class for all SQLite operations:
initialization, CSV import, CRUD, and queries. Follows Google Python style.
"""

import logging
import sqlite3
from typing import Any, Dict, Tuple

import pandas as pd


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for test data.

    Handles schema creation, CSV import, add_entry, get_all_data,
    query_data, and get_statistics.

    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str = "database.db") -> None:
        """Initializes the DatabaseManager.

        Args:
            db_path: Path to the SQLite database file. Defaults to 'database.db'.
        """
        self.db_path = db_path
        logger.info("Initializing database at %s", self.db_path)
        self.init_database()

    def init_database(self) -> None:
        """Creates the lca_test_data table if it does not exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lca_test_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lru_name TEXT NOT NULL,
                project TEXT,
                division_group TEXT,
                system TEXT,
                part_number TEXT,
                serial_no TEXT,
                received_data TEXT,
                type_of_test TEXT,
                test_rig TEXT,
                date_of_pi TEXT,
                results_remarks TEXT,
                date_of_clearance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()
        logger.info("Database initialized (table lca_test_data ensured)")

    def import_csv(self, csv_path: str) -> Tuple[bool, str]:
        """Imports data from a CSV file into the database.

        Args:
            csv_path: Path to the CSV file.

        Returns:
            A tuple (success: bool, message: str).
        """
        try:
            logger.info("Importing CSV from %s", csv_path)
            df = pd.read_csv(csv_path)
            df.columns = df.columns.str.strip()
            column_mapping = {
                "LRU Name": "lru_name",
                "Project": "project",
                "Division / Group": "division_group",
                "System": "system",
                "Part Number": "part_number",
                "Serial No": "serial_no",
                "Received Data": "received_data",
                "Type of Test": "type_of_test",
                "Test Rig": "test_rig",
                "Date of PI": "date_of_pi",
                "Results & Remarks": "results_remarks",
                "Date of Clearance": "date_of_clearance",
            }
            df = df.rename(columns=column_mapping)
            conn = sqlite3.connect(self.db_path)
            existing_count = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM lca_test_data", conn
            )["count"][0]
            if existing_count == 0:
                df.to_sql("lca_test_data", conn, if_exists="append", index=False)
                conn.commit()
                conn.close()
                logger.info("CSV import completed: %d records", len(df))
                return True, f"Successfully imported {len(df)} records"
            conn.close()
            logger.info(
                "CSV import skipped: database already contains %d records",
                existing_count,
            )
            return False, (
                f"Database already contains {existing_count} records. "
                "Use 'Add Entry' to add new records."
            )
        except Exception as e:
            logger.error(
                "Error importing CSV from %s: %s", csv_path, e, exc_info=True
            )
            return False, f"Error importing CSV: {str(e)}"

    def add_entry(self, entry_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Adds a new entry to the database.

        Args:
            entry_data: Dict of column names to values.

        Returns:
            A tuple (success: bool, message: str).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO lca_test_data
                (lru_name, project, division_group, system, part_number, serial_no,
                 received_data, type_of_test, test_rig, date_of_pi, results_remarks,
                 date_of_clearance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_data.get("lru_name", ""),
                    entry_data.get("project", ""),
                    entry_data.get("division_group", ""),
                    entry_data.get("system", ""),
                    entry_data.get("part_number", ""),
                    entry_data.get("serial_no", ""),
                    entry_data.get("received_data", ""),
                    entry_data.get("type_of_test", ""),
                    entry_data.get("test_rig", ""),
                    entry_data.get("date_of_pi", ""),
                    entry_data.get("results_remarks", ""),
                    entry_data.get("date_of_clearance", ""),
                ),
            )
            conn.commit()
            conn.close()
            logger.info(
                "Added entry for project='%s', system='%s'",
                entry_data.get("project", ""),
                entry_data.get("system", ""),
            )
            return True, "Entry added successfully"
        except Exception as e:
            logger.error("Error adding entry: %s", e, exc_info=True)
            return False, f"Error adding entry: {str(e)}"

    def get_all_data(self) -> pd.DataFrame:
        """Returns all records from the database as a DataFrame."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM lca_test_data", conn)
        conn.close()
        return df

    def query_data(self, query: str) -> pd.DataFrame:
        """Executes a custom SQL query and returns results as a DataFrame.

        Args:
            query: SQL query string.

        Returns:
            DataFrame of query results.

        Raises:
            Exception: If the query fails.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            logger.debug("Executed query: %s (rows=%d)", query, len(df))
            return df
        except Exception as e:
            logger.error("Query error for '%s': %s", query, e, exc_info=True)
            raise Exception(f"Query error: {str(e)}") from e

    def get_statistics(self) -> Dict[str, Any]:
        """Returns aggregate statistics (total_records, projects, test_rigs, etc.)."""
        df = self.get_all_data()
        if df.empty:
            return {}
        return {
            "total_records": len(df),
            "projects": (
                df["project"].value_counts().to_dict()
                if "project" in df.columns
                else {}
            ),
            "test_rigs": (
                df["test_rig"].value_counts().to_dict()
                if "test_rig" in df.columns
                else {}
            ),
            "test_types": (
                df["type_of_test"].value_counts().to_dict()
                if "type_of_test" in df.columns
                else {}
            ),
            "results": (
                df["results_remarks"].value_counts().to_dict()
                if "results_remarks" in df.columns
                else {}
            ),
            "divisions": (
                df["division_group"].value_counts().to_dict()
                if "division_group" in df.columns
                else {}
            ),
        }
