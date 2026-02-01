# Quick Start Guide

## Installation (One-Time Setup)

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Ollama (Optional, for chatbot):**
   - Download from https://ollama.ai
   - Start: `ollama serve`
   - Pull model: `ollama pull llama3.2`

## Running the Application

Simply run:
```bash
python main.py
```

That's it! The application will:
- Create the database automatically
- Import CSV data if database is empty
- Open the desktop window

## Using Qt Designer

### Windows:
```bash
# If pyqt5-tools is installed:
python -m PyQt5.uic.pyuic designer

# Or download Qt from qt.io and use designer.exe
```

### Linux:
```bash
sudo apt-get install qttools5-dev-tools
designer
```

### macOS:
```bash
brew install qt
designer
```

### Converting .ui to Python:
```bash
pyuic5 your_file.ui -o your_file_ui.py
```

## Application Tabs

1. **Dashboard** - View and filter all data
2. **Add Entry** - Add new test records
3. **Visualizations** - View charts and graphs
4. **Chatbot** - Ask questions about your data

## Troubleshooting

**Can't install PyQt5?**
- Windows: `pip install --upgrade pip` then `pip install PyQt5`
- Linux: `sudo apt-get install python3-pyqt5`
- macOS: `brew install pyqt5`

**Application won't start?**
- Check Python version: `python --version` (needs 3.8+)
- Verify CSV file exists: `LCA_Test_Data.csv`
- Check for errors in terminal

**Chatbot not working?**
- Make sure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- Update model name in `widgets/chatbot_widget.py` if needed
