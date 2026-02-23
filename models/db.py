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
        """Creates the lca_test_data and attachments tables if they don't exist."""
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
                lru_category TEXT,
                platform_aircraft_type TEXT,
                manufacturer TEXT,
                test_standard TEXT,
                test_lab TEXT,
                temperature_range TEXT,
                humidity_level TEXT,
                vibration_level TEXT,
                altitude_condition TEXT,
                voltage_input TEXT,
                power_consumption_range TEXT,
                failure_type TEXT,
                severity_level TEXT,
                corrective_action_status TEXT,
                mtbf_category TEXT,
                reliability_rating TEXT,
                test_engineer TEXT,
                approval_status TEXT,
                revision_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lru_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lru_name) REFERENCES lca_test_data(lru_name)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lru_test_data_csv (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lru_name TEXT NOT NULL,
                csv_file_path TEXT NOT NULL,
                csv_data TEXT,
                imported_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lru_name) REFERENCES lca_test_data(lru_name)
            )
            """
        )
        # Migrate existing lca_test_data: add any columns that exist in schema but not in DB
        cursor.execute("PRAGMA table_info(lca_test_data)")
        existing = {row[1] for row in cursor.fetchall()}
        optional_columns = [
            ("lru_category", "TEXT"),
            ("platform_aircraft_type", "TEXT"),
            ("manufacturer", "TEXT"),
            ("test_standard", "TEXT"),
            ("test_lab", "TEXT"),
            ("temperature_range", "TEXT"),
            ("humidity_level", "TEXT"),
            ("vibration_level", "TEXT"),
            ("altitude_condition", "TEXT"),
            ("voltage_input", "TEXT"),
            ("power_consumption_range", "TEXT"),
            ("failure_type", "TEXT"),
            ("severity_level", "TEXT"),
            ("corrective_action_status", "TEXT"),
            ("mtbf_category", "TEXT"),
            ("reliability_rating", "TEXT"),
            ("test_engineer", "TEXT"),
            ("approval_status", "TEXT"),
            ("revision_number", "TEXT"),
        ]
        for col_name, col_type in optional_columns:
            if col_name not in existing:
                cursor.execute(
                    f"ALTER TABLE lca_test_data ADD COLUMN {col_name} {col_type}"
                )
                logger.info("Added column %s to lca_test_data", col_name)
        conn.commit()
        conn.close()
        logger.info("Database initialized (tables lca_test_data and attachments ensured)")

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
            self.init_database()  # Ensure all columns exist (e.g. lru_category) before INSERT
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO lca_test_data
                (lru_name, project, division_group, system, part_number, serial_no,
                 received_data, type_of_test, test_rig, date_of_pi, results_remarks,
                 date_of_clearance, lru_category, platform_aircraft_type, manufacturer,
                 test_standard, test_lab, temperature_range, humidity_level, vibration_level,
                 altitude_condition, voltage_input, power_consumption_range, failure_type,
                 severity_level, corrective_action_status, mtbf_category, reliability_rating,
                 test_engineer, approval_status, revision_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    entry_data.get("lru_category", ""),
                    entry_data.get("platform_aircraft_type", ""),
                    entry_data.get("manufacturer", ""),
                    entry_data.get("test_standard", ""),
                    entry_data.get("test_lab", ""),
                    entry_data.get("temperature_range", ""),
                    entry_data.get("humidity_level", ""),
                    entry_data.get("vibration_level", ""),
                    entry_data.get("altitude_condition", ""),
                    entry_data.get("voltage_input", ""),
                    entry_data.get("power_consumption_range", ""),
                    entry_data.get("failure_type", ""),
                    entry_data.get("severity_level", ""),
                    entry_data.get("corrective_action_status", ""),
                    entry_data.get("mtbf_category", ""),
                    entry_data.get("reliability_rating", ""),
                    entry_data.get("test_engineer", ""),
                    entry_data.get("approval_status", ""),
                    entry_data.get("revision_number", ""),
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

    def get_lru_data(self, lru_name: str) -> pd.DataFrame:
        """Returns all test records for a specific LRU name."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            "SELECT * FROM lca_test_data WHERE lru_name = ?", conn, params=(lru_name,)
        )
        conn.close()
        return df

    def get_lru_attachments(self, lru_name: str) -> pd.DataFrame:
        """Returns all attachments for a specific LRU."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            "SELECT * FROM attachments WHERE lru_name = ? ORDER BY uploaded_date DESC",
            conn,
            params=(lru_name,),
        )
        conn.close()
        return df

    def add_attachment(
        self, lru_name: str, file_name: str, file_path: str, file_type: str
    ) -> Tuple[bool, str]:
        """Adds an attachment record for an LRU."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO attachments (lru_name, file_name, file_path, file_type)
                VALUES (?, ?, ?, ?)
                """,
                (lru_name, file_name, file_path, file_type),
            )
            conn.commit()
            conn.close()
            logger.info("Added attachment '%s' for LRU '%s'", file_name, lru_name)
            return True, "Attachment added successfully"
        except Exception as e:
            logger.error("Error adding attachment: %s", e, exc_info=True)
            return False, f"Error adding attachment: {str(e)}"

    def get_distinct_lru_names(self) -> list:
        """Returns list of distinct LRU names from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT lru_name FROM lca_test_data ORDER BY lru_name")
        names = [row[0] for row in cursor.fetchall()]
        conn.close()
        return names

    def import_test_data_csv(self, lru_name: str, csv_path: str) -> Tuple[bool, str]:
        """Import test data from CSV file for a specific LRU."""
        try:
            import json
            df = pd.read_csv(csv_path)
            # Convert DataFrame to JSON string for storage
            csv_data_json = df.to_json(orient='records')
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO lru_test_data_csv (lru_name, csv_file_path, csv_data)
                VALUES (?, ?, ?)
                """,
                (lru_name, csv_path, csv_data_json),
            )
            conn.commit()
            conn.close()
            logger.info("Imported test data CSV for LRU '%s'", lru_name)
            return True, f"Successfully imported {len(df)} test data records"
        except Exception as e:
            logger.error("Error importing test data CSV: %s", e, exc_info=True)
            return False, f"Error importing CSV: {str(e)}"

    def get_lru_test_data_csv(self, lru_name: str) -> pd.DataFrame:
        """Returns test data CSV records for a specific LRU."""
        try:
            import json
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT csv_data FROM lru_test_data_csv WHERE lru_name = ? ORDER BY imported_date DESC LIMIT 1",
                (lru_name,),
            )
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                data_json = json.loads(row[0])
                return pd.DataFrame(data_json)
            return pd.DataFrame()
        except Exception as e:
            logger.error("Error getting test data CSV: %s", e, exc_info=True)
            return pd.DataFrame()
