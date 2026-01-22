import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import DatabaseManager
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="LCA Test Data Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_db():
    db = DatabaseManager()
    # Import CSV if database is empty
    if os.path.exists("LCA_Test_Data.csv"):
        db.import_csv("LCA_Test_Data.csv")
    return db

db = init_db()

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Choose a page",
    ["🏠 Dashboard", "➕ Add New Entry", "📈 Visualizations", "🤖 Chatbot Assistant"]
)

# Dashboard Page
if page == "🏠 Dashboard":
    st.markdown('<h1 class="main-header">LCA Test Data Management System</h1>', unsafe_allow_html=True)
    
    # Get all data
    df = db.get_all_data()
    
    if df.empty:
        st.warning("No data found in the database. Please import the CSV file or add entries.")
    else:
        # Statistics
        stats = db.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", stats.get('total_records', 0))
        
        with col2:
            unique_projects = len(stats.get('projects', {}))
            st.metric("Unique Projects", unique_projects)
        
        with col3:
            unique_rigs = len(stats.get('test_rigs', {}))
            st.metric("Test Rigs", unique_rigs)
        
        with col4:
            ok_count = stats.get('results', {}).get('OK', 0)
            not_ok_count = stats.get('results', {}).get('NOT OK', 0)
            st.metric("OK Results", f"{ok_count}/{ok_count + not_ok_count}")
        
        st.divider()
        
        # Data table
        st.subheader("📋 All Test Data")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            projects = ['All'] + sorted(df['project'].dropna().unique().tolist())
            selected_project = st.selectbox("Filter by Project", projects)
        
        with col2:
            test_rigs = ['All'] + sorted(df['test_rig'].dropna().unique().tolist())
            selected_rig = st.selectbox("Filter by Test Rig", test_rigs)
        
        with col3:
            results = ['All'] + sorted(df['results_remarks'].dropna().unique().tolist())
            selected_result = st.selectbox("Filter by Results", results)
        
        # Apply filters
        filtered_df = df.copy()
        if selected_project != 'All':
            filtered_df = filtered_df[filtered_df['project'] == selected_project]
        if selected_rig != 'All':
            filtered_df = filtered_df[filtered_df['test_rig'] == selected_rig]
        if selected_result != 'All':
            filtered_df = filtered_df[filtered_df['results_remarks'] == selected_result]
        
        # Display filtered data
        st.dataframe(
            filtered_df.drop(columns=['id', 'created_at', 'updated_at'], errors='ignore'),
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Showing {len(filtered_df)} of {len(df)} records")

# Add New Entry Page
elif page == "➕ Add New Entry":
    st.markdown('<h1 class="main-header">Add New Test Data Entry</h1>', unsafe_allow_html=True)
    
    with st.form("add_entry_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            lru_name = st.text_input("LRU Name *", placeholder="e.g., 5RW GEN, DCMB GPRU")
            project = st.text_input("Project *", placeholder="e.g., LCA")
            division_group = st.text_input("Division / Group *", placeholder="e.g., A/C Division")
            system = st.text_input("System *", placeholder="e.g., ELE")
            part_number = st.text_input("Part Number", placeholder="e.g., GCCAIA")
            serial_no = st.text_input("Serial No *", placeholder="e.g., 96 / 1610000412024")
        
        with col2:
            received_data = st.text_input("Received Data", placeholder="e.g., Unit received for inspection")
            type_of_test = st.text_input("Type of Test *", placeholder="e.g., PI, PI Starter")
            test_rig = st.text_input("Test Rig *", placeholder="e.g., LCA EPGS, IJT EPGS")
            date_of_pi = st.text_input("Date of PI *", placeholder="e.g., 01-01-2026")
            results_remarks = st.selectbox("Results & Remarks *", ["OK", "NOT OK", ""])
            date_of_clearance = st.text_input("Date of Clearance", placeholder="e.g., 04-01-2026")
        
        submitted = st.form_submit_button("Add Entry", use_container_width=True)
        
        if submitted:
            # Validate required fields
            required_fields = {
                'lru_name': lru_name,
                'project': project,
                'division_group': division_group,
                'system': system,
                'serial_no': serial_no,
                'type_of_test': type_of_test,
                'test_rig': test_rig,
                'date_of_pi': date_of_pi,
                'results_remarks': results_remarks
            }
            
            missing_fields = [k for k, v in required_fields.items() if not v]
            
            if missing_fields:
                st.error(f"Please fill in all required fields. Missing: {', '.join(missing_fields)}")
            else:
                entry_data = {
                    'lru_name': lru_name,
                    'project': project,
                    'division_group': division_group,
                    'system': system,
                    'part_number': part_number,
                    'serial_no': serial_no,
                    'received_data': received_data,
                    'type_of_test': type_of_test,
                    'test_rig': test_rig,
                    'date_of_pi': date_of_pi,
                    'results_remarks': results_remarks,
                    'date_of_clearance': date_of_clearance
                }
                
                success, message = db.add_entry(entry_data)
                
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)

# Visualizations Page
elif page == "📈 Visualizations":
    st.markdown('<h1 class="main-header">Data Visualizations</h1>', unsafe_allow_html=True)
    
    df = db.get_all_data()
    
    if df.empty:
        st.warning("No data available for visualization.")
    else:
        # Visualization options
        viz_type = st.selectbox(
            "Select Visualization Type",
            [
                "Results Distribution",
                "Test Rigs Analysis",
                "Projects Overview",
                "Division/Group Distribution",
                "Type of Test Analysis",
                "Timeline Analysis (Date of PI)",
                "Clearance Status"
            ]
        )
        
        if viz_type == "Results Distribution":
            results_counts = df['results_remarks'].value_counts()
            fig = px.pie(
                values=results_counts.values,
                names=results_counts.index,
                title="Test Results Distribution",
                color_discrete_map={'OK': '#2ecc71', 'NOT OK': '#e74c3c'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Test Rigs Analysis":
            rig_counts = df['test_rig'].value_counts()
            fig = px.bar(
                x=rig_counts.index,
                y=rig_counts.values,
                title="Test Rigs Usage",
                labels={'x': 'Test Rig', 'y': 'Count'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Projects Overview":
            project_counts = df['project'].value_counts()
            fig = px.bar(
                x=project_counts.index,
                y=project_counts.values,
                title="Projects Distribution",
                labels={'x': 'Project', 'y': 'Count'},
                color=project_counts.values,
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Division/Group Distribution":
            div_counts = df['division_group'].value_counts()
            fig = px.pie(
                values=div_counts.values,
                names=div_counts.index,
                title="Division/Group Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Type of Test Analysis":
            test_counts = df['type_of_test'].value_counts()
            fig = px.bar(
                x=test_counts.index,
                y=test_counts.values,
                title="Type of Test Distribution",
                labels={'x': 'Type of Test', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Timeline Analysis (Date of PI)":
            # Convert date strings to datetime for better visualization
            df_copy = df.copy()
            df_copy['date_of_pi_parsed'] = pd.to_datetime(df_copy['date_of_pi'], format='%d-%m-%Y', errors='coerce')
            df_copy = df_copy.dropna(subset=['date_of_pi_parsed'])
            df_copy = df_copy.sort_values('date_of_pi_parsed')
            
            daily_counts = df_copy.groupby(df_copy['date_of_pi_parsed'].dt.date).size()
            
            fig = px.line(
                x=daily_counts.index,
                y=daily_counts.values,
                title="Test Entries Over Time (Date of PI)",
                labels={'x': 'Date', 'y': 'Number of Tests'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Clearance Status":
            cleared = df['date_of_clearance'].notna().sum()
            not_cleared = df['date_of_clearance'].isna().sum()
            
            fig = go.Figure(data=[
                go.Bar(
                    x=['Cleared', 'Not Cleared'],
                    y=[cleared, not_cleared],
                    marker_color=['#2ecc71', '#f39c12']
                )
            ])
            fig.update_layout(
                title="Clearance Status",
                xaxis_title="Status",
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Additional statistics
        st.divider()
        st.subheader("📊 Summary Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Records", len(df))
            st.metric("Unique Projects", df['project'].nunique())
        
        with col2:
            st.metric("Unique Test Rigs", df['test_rig'].nunique())
            st.metric("Unique LRU Names", df['lru_name'].nunique())
        
        with col3:
            ok_rate = (df['results_remarks'] == 'OK').sum() / len(df) * 100
            st.metric("OK Rate", f"{ok_rate:.1f}%")
            cleared_rate = df['date_of_clearance'].notna().sum() / len(df) * 100
            st.metric("Clearance Rate", f"{cleared_rate:.1f}%")

# Chatbot Page
elif page == "🤖 Chatbot Assistant":
    st.markdown('<h1 class="main-header">AI Chatbot Assistant</h1>', unsafe_allow_html=True)
    
    st.info("💡 This chatbot uses Ollama to answer questions about your test data. Make sure Ollama is running locally.")
    
    # Example queries
    with st.expander("💡 Example Queries"):
        st.markdown("""
        Try asking:
        - "How many records are in the database?"
        - "Show me all projects"
        - "What test rigs are being used?"
        - "Count tests by project"
        - "How many tests have OK results?"
        - "List all test types"
        - "What is the distribution of results?"
        """)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your test data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from chatbot
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_chatbot_response(prompt, db)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})


def get_chatbot_response(prompt: str, db: DatabaseManager) -> str:
    """Get response from Ollama chatbot"""
    try:
        import ollama
        
        # Get database statistics and sample data for context
        df = db.get_all_data()
        stats = db.get_statistics()
        
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
                sql_query = "SELECT project, COUNT(*) as count FROM lca_test_data GROUP BY project"
            elif "test rig" in prompt_lower:
                sql_query = "SELECT test_rig, COUNT(*) as count FROM lca_test_data GROUP BY test_rig"
            elif "ok" in prompt_lower or "not ok" in prompt_lower:
                sql_query = "SELECT results_remarks, COUNT(*) as count FROM lca_test_data GROUP BY results_remarks"
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
        query_result = None
        if sql_query:
            try:
                query_result = db.query_data(sql_query)
                query_result_str = query_result.to_string() if not query_result.empty else "No results found"
            except Exception as e:
                query_result_str = f"Query error: {str(e)}"
        else:
            query_result_str = None
        
        # Prepare message for Ollama
        user_message = f"{context}\n\nUser Question: {prompt}"
        if query_result_str:
            user_message += f"\n\nQuery Result:\n{query_result_str}"
        
        # Get response from Ollama
        response = ollama.chat(
            model='llama3.2',  # You can change this to any model you have
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant for an LCA Test Data Management System. Answer questions about test data clearly and concisely.'
                },
                {
                    'role': 'user',
                    'content': user_message
                }
            ]
        )
        
        return response['message']['content']
    
    except ImportError:
        return """
        **Ollama is not installed.** 
        
        To use the chatbot, please install Ollama:
        1. Install Ollama from https://ollama.ai
        2. Install the Python client: `pip install ollama`
        3. Start Ollama service: `ollama serve`
        4. Pull a model: `ollama pull llama3.2`
        
        Then restart this application.
        """
    except Exception as e:
        # Fallback: provide basic information without Ollama
        df = db.get_all_data()
        stats = db.get_statistics()
        
        if "how many" in prompt.lower():
            return f"The database contains **{stats.get('total_records', 0)}** total records."
        elif "project" in prompt.lower():
            projects = ', '.join(list(stats.get('projects', {}).keys()))
            return f"Projects in the database: {projects}"
        elif "test rig" in prompt.lower():
            rigs = ', '.join(list(stats.get('test_rigs', {}).keys()))
            return f"Test rigs in the database: {rigs}"
        else:
            return f"I encountered an error: {str(e)}. Please make sure Ollama is running and a model is available."
