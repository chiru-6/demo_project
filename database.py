"""Database management module for LCA Test Data Management System.

This module provides the DatabaseManager class for handling all database operations
including initialization, data import, CRUD operations, and queries for the LCA
(Light Combat Aircraft) test data management system.

Typical usage example:
    db = DatabaseManager()
    db.import_csv('LCA_Test_Data.csv')
    data = db.get_all_data()
"""

import sqlite3
from typing import Any, Dict, Tuple

import pandas as pd


class DatabaseManager:
    """Manages SQLite database operations for LCA Test Data.
    
    This class handles all database operations including schema creation,
    data import from CSV, CRUD operations, and statistical queries.
    
    Attributes:
        db_path: Path to the SQLite database file.
    """
    
    def __init__(self, db_path: str = "lca_test_data.db") -> None:
        """Initializes the DatabaseManager with the specified database path.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to 'lca_test_data.db'.
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Initializes the database with the required schema.
        
        Creates the lca_test_data table if it doesn't exist with all required
        columns for storing test data records.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
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
        """)
        
        conn.commit()
        conn.close()
    
    def import_csv(self, csv_path: str) -> Tuple[bool, str]:
        """Imports data from CSV file into the database.
        
        Reads the CSV file, maps column names to database schema, and imports
        records if the database is empty. Prevents duplicate imports.
        
        Args:
            csv_path: Path to the CSV file to import.
            
        Returns:
            A tuple containing:
                - bool: True if import was successful, False otherwise.
                - str: Success or error message.
        """
        try:
            df = pd.read_csv(csv_path)
            
            # Rename columns to match database schema (handle spaces and special chars)
            df.columns = df.columns.str.strip()
            column_mapping = {
                'LRU Name': 'lru_name',
                'Project': 'project',
                'Division / Group': 'division_group',
                'System': 'system',
                'Part Number': 'part_number',
                'Serial No': 'serial_no',
                'Received Data': 'received_data',
                'Type of Test': 'type_of_test',
                'Test Rig': 'test_rig',
                'Date of PI': 'date_of_pi',
                'Results & Remarks': 'results_remarks',
                'Date of Clearance': 'date_of_clearance'
            }
            
            df = df.rename(columns=column_mapping)
            
            conn = sqlite3.connect(self.db_path)
            
            # Check if data already exists to avoid duplicates
            existing_count = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM lca_test_data", 
                conn
            )['count'][0]
            
            if existing_count == 0:
                df.to_sql('lca_test_data', conn, if_exists='append', index=False)
                conn.commit()
                conn.close()
                return True, f"Successfully imported {len(df)} records"
            
            conn.close()
            return False, (f"Database already contains {existing_count} records. "
                          f"Use 'Add Entry' to add new records.")
        
        except Exception as e:
            return False, f"Error importing CSV: {str(e)}"
    
    def add_entry(self, entry_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Adds a new entry to the database.
        
        Args:
            entry_data: Dictionary containing entry data with keys matching
                       database column names.
            
        Returns:
            A tuple containing:
                - bool: True if entry was added successfully, False otherwise.
                - str: Success or error message.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO lca_test_data 
                (lru_name, project, division_group, system, part_number, serial_no,
                 received_data, type_of_test, test_rig, date_of_pi, results_remarks, 
                 date_of_clearance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_data.get('lru_name', ''),
                entry_data.get('project', ''),
                entry_data.get('division_group', ''),
                entry_data.get('system', ''),
                entry_data.get('part_number', ''),
                entry_data.get('serial_no', ''),
                entry_data.get('received_data', ''),
                entry_data.get('type_of_test', ''),
                entry_data.get('test_rig', ''),
                entry_data.get('date_of_pi', ''),
                entry_data.get('results_remarks', ''),
                entry_data.get('date_of_clearance', '')
            ))
            
            conn.commit()
            conn.close()
            return True, "Entry added successfully"
        
        except Exception as e:
            return False, f"Error adding entry: {str(e)}"
    
    def get_all_data(self) -> pd.DataFrame:
        """Retrieves all data from the database.
        
        Returns:
            DataFrame containing all records from the database.
        """
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM lca_test_data", conn)
        conn.close()
        return df
    
    def query_data(self, query: str) -> pd.DataFrame:
        """Executes a custom SQL query.
        
        Args:
            query: SQL query string to execute.
            
        Returns:
            DataFrame containing query results.
            
        Raises:
            Exception: If query execution fails.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            raise Exception(f"Query error: {str(e)}") from e
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculates and returns statistics about the data.
        
        Returns:
            Dictionary containing various statistics including:
                - total_records: Total number of records
                - projects: Count of records per project
                - test_rigs: Count of records per test rig
                - test_types: Count of records per test type
                - results: Count of records per result type
                - divisions: Count of records per division/group
        """
        df = self.get_all_data()
        
        if df.empty:
            return {}
        
        stats = {
            'total_records': len(df),
            'projects': (df['project'].value_counts().to_dict() 
                        if 'project' in df.columns else {}),
            'test_rigs': (df['test_rig'].value_counts().to_dict() 
                         if 'test_rig' in df.columns else {}),
            'test_types': (df['type_of_test'].value_counts().to_dict() 
                          if 'type_of_test' in df.columns else {}),
            'results': (df['results_remarks'].value_counts().to_dict() 
                       if 'results_remarks' in df.columns else {}),
            'divisions': (df['division_group'].value_counts().to_dict() 
                         if 'division_group' in df.columns else {}),
        }
        
        return stats
