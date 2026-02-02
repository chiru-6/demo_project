"""Chatbot widget module for AI-powered data querying.

This module provides the ChatbotWidget class which implements an AI chatbot
interface using Ollama for natural language queries about test data.
"""

from typing import List, Dict

import pandas as pd
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget)


class ChatbotWidget(QWidget):
    """Widget for AI chatbot interface.
    
    This widget provides a chat interface for querying test data using
    natural language. It uses Ollama for AI responses and can execute
    SQL queries based on user questions.
    
    Attributes:
        db: DatabaseManager instance for database operations.
        chat_history: List of chat messages (role and content).
        chat_display: QTextEdit for displaying chat messages.
        input_field: QLineEdit for user input.
        send_btn: QPushButton for sending messages.
    """
    
    def __init__(self, db) -> None:
        """Initializes the chatbot widget.
        
        Args:
            db: DatabaseManager instance for database operations.
        """
        super().__init__()
        self.db = db
        self.chat_history: List[Dict[str, str]] = []
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initializes the user interface.
        
        Creates and configures all UI elements including title, info labels,
        chat display area, and input controls.
        """
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🤖 AI Chatbot Assistant")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Info label
        info_label = QLabel(
            "💡 Ask questions about your test data in natural language. "
            "Make sure Ollama is running locally."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "background-color: #e3f2fd; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info_label)
        
        # Example queries
        examples_label = QLabel(
            "Example queries: 'How many records?', 'Show all projects', "
            "'What test rigs are used?'"
        )
        examples_label.setWordWrap(True)
        examples_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(examples_label)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 10))
        self.chat_display.setStyleSheet("background-color: #f5f5f5; padding: 10px;")
        layout.addWidget(self.chat_display)
        
        # Add welcome message
        self.add_message(
            "assistant", 
            "Hello! I'm your AI assistant. I can help you query and "
            "analyze your test data. Ask me anything!"
        )
        
        # Input area
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
        """Adds a message to the chat display.
        
        Args:
            role: Message role ('user' or 'assistant').
            content: Message content text.
        """
        if role == "user":
            self.chat_display.append(f"<b>You:</b> {content}<br>")
        else:
            self.chat_display.append(f"<b>Assistant:</b> {content}<br><br>")
        
        self.chat_history.append({"role": role, "content": content})
        # Scroll to bottom
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
    
    def send_message(self) -> None:
        """Sends message to chatbot.
        
        Gets the user's message, sends it to the chatbot, and displays
        the response. Disables the send button while processing.
        """
        prompt = self.input_field.text().strip()
        if not prompt:
            return
        
        # Add user message
        self.add_message("user", prompt)
        self.input_field.clear()
        
        # Get response
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
        """Gets response from Ollama chatbot.
        
        Processes the user's prompt, generates SQL queries if applicable,
        executes them, and sends the results to Ollama for a natural
        language response.
        
        Args:
            prompt: User's question or prompt.
            
        Returns:
            Chatbot's response as a string.
        """
        try:
            import ollama  # pylint: disable=import-outside-toplevel
            
            # Get database statistics and sample data for context
            df = self.db.get_all_data()
            stats = self.db.get_statistics()
            
            # Create context about the database
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
            
            # Try to generate SQL query from natural language
            sql_query = None
            prompt_lower = prompt.lower()
            
            # Simple query patterns
            if "how many" in prompt_lower or "count" in prompt_lower:
                if "project" in prompt_lower:
                    sql_query = ("SELECT project, COUNT(*) as count "
                               "FROM lca_test_data GROUP BY project")
                elif "test rig" in prompt_lower:
                    sql_query = ("SELECT test_rig, COUNT(*) as count "
                               "FROM lca_test_data GROUP BY test_rig")
                elif "ok" in prompt_lower or "not ok" in prompt_lower:
                    sql_query = ("SELECT results_remarks, COUNT(*) as count "
                               "FROM lca_test_data GROUP BY results_remarks")
                else:
                    sql_query = "SELECT COUNT(*) as total FROM lca_test_data"
            
            elif "list" in prompt_lower or "show" in prompt_lower or "get" in prompt_lower:
                if "all" in prompt_lower:
                    sql_query = "SELECT * FROM lca_test_data LIMIT 20"
                elif "project" in prompt_lower:
                    sql_query = "SELECT DISTINCT project FROM lca_test_data"
                elif "test rig" in prompt_lower:
                    sql_query = "SELECT DISTINCT test_rig FROM lca_test_data"
            
            # Execute query if available
            query_result_str = None
            if sql_query:
                try:
                    query_result = self.db.query_data(sql_query)
                    query_result_str = (query_result.to_string() 
                                       if not query_result.empty 
                                       else "No results found")
                except Exception as error:
                    query_result_str = f"Query error: {str(error)}"
            
            # Prepare message for Ollama
            user_message = f"{context}\n\nUser Question: {prompt}"
            if query_result_str:
                user_message += f"\n\nQuery Result:\n{query_result_str}"
            
            # Get response from Ollama
            response = ollama.chat(
                model='llama3.2',
                messages=[
                    {
                        'role': 'system',
                        'content': ('You are a helpful assistant for an LCA Test Data '
                                  'Management System. Answer questions about test data '
                                  'clearly and concisely.')
                    },
                    {
                        'role': 'user',
                        'content': user_message
                    }
                ]
            )
            
            return response['message']['content']
        
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
            # Fallback: provide basic information without Ollama
            stats = self.db.get_statistics()
            
            if "how many" in prompt.lower():
                total = stats.get('total_records', 0)
                return f"The database contains **{total}** total records."
            if "project" in prompt.lower():
                projects = ', '.join(list(stats.get('projects', {}).keys()))
                return f"Projects in the database: {projects}"
            if "test rig" in prompt.lower():
                rigs = ', '.join(list(stats.get('test_rigs', {}).keys()))
                return f"Test rigs in the database: {rigs}"
            
            return (f"I encountered an error: {str(error)}. "
                   f"Please make sure Ollama is running and a model is available.")
