@echo off
echo Running Pylint on all Python files...
echo.

pylint main.py
pylint main_window.py
pylint database.py
pylint setup.py
pylint widgets/dashboard_widget.py
pylint widgets/add_entry_widget.py
pylint widgets/visualizations_widget.py
pylint widgets/chatbot_widget.py

echo.
echo Pylint analysis complete!
pause
