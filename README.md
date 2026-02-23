#Test Data Management System - PySide6 Desktop Application

A comprehensive desktop application for managing and analyzing aircraft test data with SQLite database, interactive visualizations, and AI-powered chatbot assistance.

## Features

- 📊 **Interactive Dashboard**: View and filter all test data with real-time statistics
- ➕ **Data Entry**: Add new test data entries through an intuitive form
- 📈 **Visualizations**: Multiple chart types including:
  - Results distribution (pie charts)
  - Test rigs analysis
  - Projects overview
  - Division/Group distribution
  - Type of test analysis
  - Clearance status
- 🤖 **AI Chatbot**: Query your data using natural language with Ollama integration
- 💾 **SQLite Database**: Lightweight, local database for data storage
- 🖥️ **Desktop Application**: Native PySide6 desktop application with modern UI

## Installation

### Prerequisites

- Python 3.8 or higher
- Ollama (for chatbot functionality) - Optional but recommended

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note for Windows users**: If you encounter issues installing PySide6, try:
```bash
pip install --upgrade pip
pip install PySide6
```

**Note for Linux users**: You may need to install system dependencies:
```bash
sudo apt-get install python3-pyside6
```

**Note for macOS users**: 
```bash
brew install pyside6
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
   
   You can use other models like `llama3`, `mistral`, or `codellama` as well. Just update the model name in `views/chatbot_view.py` (line ~120) if you use a different one.

## Running the Application

### Method 1: Direct Python Execution

1. Make sure your `dataset.csv` file is in the project directory

2. Run the main application:
   ```bash
   python main.py
   ```

3. The application will automatically:
   - Create the SQLite database (`dataset.db`)
   - Import data from `dataset.csv` if the database is empty
   - Open the desktop application window

### Method 2: Using Setup Script (Optional)

1. Run the setup script to initialize the database:
   ```bash
   python setup.py
   ```

2. Then run the main application:
   ```bash
   python main.py
   ```

   You can also run the app entry point directly: `python app.py`

## Project architecture

The codebase is organized as follows:

- **`app.py`** — Application entry point. Sets up logging, Qt app, database, optional CSV import, creates the main window, and runs the event loop. Run with `python app.py` or `python main.py` (main.py delegates to app).
- **`views/`** — UI layer. `main_window.py` (sidebar, tabs, Dark/Light theme) and one view per screen: `dashboard_view.py`, `dataset_view.py`, `add_entry_view.py`, `visualizations_view.py`, `chatbot_view.py`, `home_view.py`. Theme (Light/Dark) is toggled from the sidebar.
- **`controllers/`** — Startup and window creation. `controller.py` provides `get_db()`, `import_csv_if_needed()`, and `create_main_window(db)`; used by `app.py` so DB and CSV logic stay out of the entry point.
- **`models/`** — Data and logic. `db.py` holds `DatabaseManager` (SQLite, CSV import, CRUD, statistics). `logic.py` for reusable business logic; `appdata.py` for app-level constants (e.g. default CSV paths).
- **Logging** — Configured in `app.py` (logs to `logs/app.log` and console).
- **Legacy** — `main.py` calls `app.main()`. `database.py` re-exports `DatabaseManager` from `models.db` for backward compatibility.

## Application Features

### 1. Dashboard 📊
   - View all test data in a sortable table
   - Filter by Project, Test Rig, or Results
   - See summary statistics (total records, projects, test rigs, OK results)
   - Refresh data button to reload from database

### 2. Add New Entry ➕
   - Fill in the form with test data
   - Required fields are marked with *
   - Form validation before submission
   - Clear form button to reset all fields
   - Data is saved to SQLite database

### 3. Visualizations 📈
   - Select from various chart types:
     - Results Distribution (pie chart)
     - Test Rigs Analysis (bar chart)
     - Projects Overview (bar chart)
     - Division/Group Distribution (pie chart)
     - Type of Test Analysis (bar chart)
     - Clearance Status (bar chart)
   - Interactive charts with matplotlib
   - Refresh button to update with latest data

### 4. Chatbot Assistant 🤖
   - Ask questions about your data in natural language
   - Examples:
     - "How many records are in the database?"
     - "Show me all projects"
     - "What test rigs are being used?"
     - "Count tests by project"
   - Uses Ollama for AI responses
   - Chat history displayed in scrollable area

## Using Qt Designer

Qt Designer is a visual tool for designing PySide6 user interfaces. Here's how to use it:

### Installing Qt Designer

**Windows:**
- Qt Designer comes with PySide6. If not installed, download Qt from https://www.qt.io/download
- Or use: `pip install pyside6-tools` (includes designer.exe)

**Linux:**
```bash
sudo apt-get install qttools5-dev-tools
# Or
sudo apt-get install qt5-designer
```

**macOS:**
```bash
brew install qt
```

### Running Qt Designer

**Windows:**
```bash
designer
# Or if installed via pyside6-tools:
pyside6-designer
```

**Linux:**
```bash
designer
# Or
qt5-designer
```

**macOS:**
```bash
designer
```

### Creating/Editing UI Files

1. **Open Qt Designer:**
   ```bash
   designer
   ```

2. **Create a new form:**
   - File → New → Main Window (or Widget, Dialog, etc.)
   - Design your UI by dragging widgets from the widget box
   - Set properties in the Property Editor
   - Save as `.ui` file (e.g., `main_window.ui`)

3. **Convert .ui to Python:**
   ```bash
   pyside6-uic main_window.ui -o main_window_ui.py
   ```
   
   Or use Python to convert:
   ```python
   from PySide6.QtUiTools import loadUi
   # Load UI file at runtime
   loadUi('main_window.ui', self)
   ```

4. **Using the generated UI in your code:**
   ```python
   from PySide6.QtUiTools import QUiLoader
   
   class MainWindow(QMainWindow):
       def __init__(self):
           super().__init__()
           loader = QUiLoader()
           self.ui = loader.load('main_window.ui', self)
   ```

### Example: Creating a Custom Widget UI

1. Open Qt Designer
2. Create a new Widget
3. Add your widgets (buttons, labels, etc.)
4. Save as `widgets/custom_widget.ui`
5. Convert to Python:
   ```bash
   pyside6-uic widgets/custom_widget.ui -o widgets/custom_widget_ui.py
   ```
6. Import and use in your code

### Tips for Qt Designer

- Use layouts (Vertical, Horizontal, Grid) for responsive design
- Set object names for widgets (used in code)
- Use QGroupBox for grouping related widgets
- Preview your design with Ctrl+R (or Cmd+R on Mac)
- Use the Signal/Slot Editor to connect signals visually

## Project Structure

```
HAL_Project/
├── main.py                 # Main application entry point
├── main_window.py          # Main window class with tabs
├── database.py             # Database management module
├── setup.py               # Setup script for database initialization
├── widgets/               # Widget modules
│   ├── __init__.py
│   ├── dashboard_widget.py      # Dashboard view
│   ├── add_entry_widget.py      # Add entry form
│   ├── visualizations_widget.py # Visualizations
│   └── chatbot_widget.py        # Chatbot interface
├── database.csv      # Source CSV file
├── database.db            # SQLite database (created automatically)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Data and file storage

- **Database:** The SQLite database file is created in the **project root** (same folder as `main.py` / `app.py`). Default name: `database.db` (or as set when creating the app).
- **LRU test data CSV files (optional):** When you upload a CSV in **Add Entry** for “Test Data” (optional), the file is **copied** into the project folder so it stays with the project:
  - **Folder:** `<project_folder>/lru_test_data/<LRU_name>/`
  - **Example:** If the project is `D:\HAL_Project` and the LRU name is `EPGS Controller`, the CSV is stored at:
    - `D:\HAL_Project\lru_test_data\EPGS Controller\<your_file>.csv`
  - The LRU name is sanitized for the folder (invalid path characters like `\ / : * ? " < > |` are replaced with `_`).
  - One subfolder per LRU; you can place multiple CSV files in the same LRU folder; the app uses the **most recently imported** CSV for that LRU when showing the **Test Data** tab in the LRU Details panel.
- **Attachments (PDFs, images):** Stored by path in the database; the actual files stay where you selected them (or you can move them into a project folder and re-add if you want everything in one place).

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

## Troubleshooting

### PySide6 Installation Issues

**Windows:**
```bash
pip install --upgrade pip setuptools wheel
pip install PySide6
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install python3-pyside6
```

**macOS:**
```bash
brew install pyside6
pip install PySide6
```

### Application Won't Start

1. Check Python version: `python --version` (should be 3.8+)
2. Verify all dependencies: `pip list | grep -i pyside6`
3. Check for error messages in terminal
4. Ensure CSV file exists in project directory

### Chatbot not working?

1. Make sure Ollama is installed and running:
   ```bash
   ollama serve
   ```

2. Verify a model is available:
   ```bash
   ollama list
   ```

3. If using a different model, update the model name in `views/chatbot_view.py` (line ~120):
   ```python
   model='llama3.2'  # Change to your model name
   ```

### Database issues?

- The database is created automatically on first run
- If you need to re-import the CSV, delete `database.db` and restart the app
- The app prevents duplicate imports to avoid data duplication

### Qt Designer Not Found?

**Windows:**
- Install: `pip install pyside6-tools`
- Run: `pyside6-designer`

**Linux:**
```bash
sudo apt-get install qttools5-dev-tools
```

**macOS:**
```bash
brew install qt
```

## Customization

### Changing the Theme/Style

Edit `main_window.py` or individual widget files to add stylesheets:

```python
self.setStyleSheet("""
    QMainWindow {
        background-color: #f0f0f0;
    }
    QPushButton {
        background-color: #4CAF50;
        color: white;
        padding: 10px;
    }
""")
```

### Adding New Visualizations

1. Add new option to `visualizations_widget.py` in `init_ui()`:
   ```python
   self.viz_combo.addItem("New Visualization")
   ```

2. Add corresponding plot method:
   ```python
   def plot_new_visualization(self, ax):
       # Your plotting code here
       pass
   ```

3. Add case in `update_visualization()`:
   ```python
   elif viz_type == "New Visualization":
       self.plot_new_visualization(ax)
   ```

## Building Executable (Optional)

To create a standalone executable:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build executable:
   ```bash
   pyinstaller --onefile --windowed --name "database" main.py
   ```

3. Executable will be in `dist/` folder

## Code Quality and Standards

This project follows **Google Python Style Guide** with **Pylint** enforcement.

### Code Standards
- ✅ 100% docstring coverage
- ✅ Type hints for all functions
- ✅ Pylint configuration included
- ✅ Consistent code formatting
- ✅ Comprehensive documentation

### Running Code Quality Checks

**Install Pylint:**
```bash
pip install pylint
```

**Run Pylint on all files:**

Windows:
```bash
run_pylint.bat
```

Linux/Mac:
```bash
chmod +x run_pylint.sh
./run_pylint.sh
```

**Run on specific file:**
```bash
pylint database.py
```

### Documentation
- `STYLE_GUIDE.md` - Detailed Python style guide
- `CODE_STANDARDS.md` - Code quality implementation details
- `CHANGELOG.md` - Project change history
- `.pylintrc` - Pylint configuration

## Future Enhancements

- Export data to CSV/Excel
- Advanced filtering and search
- Data editing and deletion
- User authentication
- Report generation
- Email notifications
- Dark mode theme
- Customizable charts

## License

This project is for internal use 

## Support

For issues or questions, please contact the development team.
