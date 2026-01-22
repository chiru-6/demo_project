# LCA Test Data Management System

A comprehensive web-based application for managing and analyzing LCA (Light Combat Aircraft) test data with SQLite database, interactive visualizations, and AI-powered chatbot assistance.

## Features

- 📊 **Interactive Dashboard**: View and filter all test data with real-time statistics
- ➕ **Data Entry**: Add new test data entries through an intuitive form
- 📈 **Visualizations**: Multiple chart types including:
  - Results distribution (pie charts)
  - Test rigs analysis
  - Projects overview
  - Division/Group distribution
  - Type of test analysis
  - Timeline analysis
  - Clearance status
- 🤖 **AI Chatbot**: Query your data using natural language with Ollama integration
- 💾 **SQLite Database**: Lightweight, local database for data storage

## Installation

### Prerequisites

- Python 3.8 or higher
- Ollama (for chatbot functionality)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Install and Setup Ollama (for Chatbot)

1. Download and install Ollama from [https://ollama.ai](https://ollama.ai)

2. Start Ollama service:
   ```bash
   ollama serve
   ```

3. Pull a language model (in a new terminal):
   ```bash
   ollama pull llama3.2
   ```
   
   You can use other models like `llama3`, `mistral`, or `codellama` as well. Just update the model name in `app.py` if you use a different one.

## Usage

### Running the Application

1. Make sure your `LCA_Test_Data.csv` file is in the project directory

2. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

3. The application will automatically:
   - Create the SQLite database (`lca_test_data.db`)
   - Import data from `LCA_Test_Data.csv` if the database is empty
   - Open in your default web browser

### Application Pages

1. **Dashboard** 🏠
   - View all test data
   - Filter by Project, Test Rig, or Results
   - See summary statistics

2. **Add New Entry** ➕
   - Fill in the form with test data
   - Required fields are marked with *
   - Data is saved to SQLite database

3. **Visualizations** 📈
   - Select from various chart types
   - Interactive charts with Plotly
   - View summary statistics

4. **Chatbot Assistant** 🤖
   - Ask questions about your data in natural language
   - Examples:
     - "How many records are in the database?"
     - "Show me all projects"
     - "What test rigs are being used?"
     - "Count tests by project"

## Database Schema

The SQLite database contains the following columns:

- `id` (Primary Key, Auto-increment)
- `lru_name` (Text)
- `project` (Text)
- `division_group` (Text)
- `system` (Text)
- `part_number` (Text)
- `serial_no` (Text)
- `received_data` (Text)
- `type_of_test` (Text)
- `test_rig` (Text)
- `date_of_pi` (Text)
- `results_remarks` (Text)
- `date_of_clearance` (Text)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

## File Structure

```
HAL_Project/
├── app.py                 # Main Streamlit application
├── database.py            # Database management module
├── LCA_Test_Data.csv     # Source CSV file
├── lca_test_data.db      # SQLite database (created automatically)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Troubleshooting

### Chatbot not working?

1. Make sure Ollama is installed and running:
   ```bash
   ollama serve
   ```

2. Verify a model is available:
   ```bash
   ollama list
   ```

3. If using a different model, update the model name in `app.py` (line ~340):
   ```python
   model='llama3.2'  # Change to your model name
   ```

### Database issues?

- The database is created automatically on first run
- If you need to re-import the CSV, delete `lca_test_data.db` and restart the app
- The app prevents duplicate imports to avoid data duplication

## Future Enhancements

- Export data to CSV/Excel
- Advanced filtering and search
- Data editing and deletion
- User authentication
- Report generation
- Email notifications

## License

This project is for internal use at HAL (Hindustan Aeronautics Limited).

## Support

For issues or questions, please contact the development team.
