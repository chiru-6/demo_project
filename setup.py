"""Setup script for LCA Test Data Management System.

This script helps initialize the database and verify the setup.
It checks for the CSV file, initializes the database, imports data,
and displays statistics.

Usage:
    python setup.py
"""

import os
import sys

from database import DatabaseManager


def main() -> None:
    """Initializes the database and imports CSV data.
    
    Performs the following steps:
        1. Checks for CSV file existence
        2. Initializes the database
        3. Imports CSV data if available
        4. Displays database statistics
    """
    print("=" * 60)
    print("LCA Test Data Management System - Setup")
    print("=" * 60)
    
    # Check if CSV file exists
    csv_file = "LCA_Test_Data.csv"
    if not os.path.exists(csv_file):
        print(f"⚠️  Warning: {csv_file} not found in current directory")
        print("   Please ensure the CSV file is in the project root.")
    else:
        print(f"✓ Found {csv_file}")
    
    # Initialize database
    print("\n📊 Initializing database...")
    try:
        db = DatabaseManager()
        print("✓ Database initialized successfully")
        
        # Try to import CSV
        if os.path.exists(csv_file):
            print(f"\n📥 Importing data from {csv_file}...")
            success, message = db.import_csv(csv_file)
            if success:
                print(f"✓ {message}")
            else:
                print(f"ℹ️  {message}")
        
        # Display statistics
        stats = db.get_statistics()
        if stats:
            print("\n📈 Database Statistics:")
            print(f"   Total Records: {stats.get('total_records', 0)}")
            print(f"   Projects: {len(stats.get('projects', {}))}")
            print(f"   Test Rigs: {len(stats.get('test_rigs', {}))}")
        
    except Exception as error:
        print(f"❌ Error: {str(error)}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Setup complete! You can now run the application:")
    print("   python main.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
