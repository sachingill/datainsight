"""
Trace handler to capture and display query execution traces.
"""
import re
import streamlit as st
from datetime import datetime

class QueryTrace:
    """Stores trace information for a query."""
    def __init__(self):
        self.timestamp = datetime.now()
        self.user_input = ""
        self.query_type = ""
        self.sql_queries = []
        self.agent_steps = []
        self.results = []
        self.errors = []
        self.execution_time = None
        
    def add_sql_query(self, query):
        """Add a SQL query to the trace."""
        self.sql_queries.append({
            "query": query,
            "timestamp": datetime.now()
        })
    
    def add_agent_step(self, step_type, content):
        """Add an agent reasoning step."""
        self.agent_steps.append({
            "type": step_type,  # "thought", "action", "observation", "final_answer"
            "content": content,
            "timestamp": datetime.now()
        })
    
    def add_result(self, result):
        """Add query result."""
        self.results.append(result)
    
    def add_error(self, error):
        """Add error information."""
        self.errors.append(error)
    
    def to_dict(self):
        """Convert trace to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_input": self.user_input,
            "query_type": self.query_type,
            "sql_queries": self.sql_queries,
            "agent_steps": self.agent_steps,
            "results": self.results,
            "errors": self.errors,
            "execution_time": self.execution_time
        }


def extract_sql_from_text(text):
    """Extract SQL queries from text using regex."""
    # Pattern to match SQL queries (SELECT, INSERT, UPDATE, DELETE, etc.)
    sql_pattern = r'(?i)(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH)\s+[^;]+(?:;|$)'
    matches = re.findall(sql_pattern, text, re.DOTALL | re.IGNORECASE)
    return matches


def parse_agent_output(output_text):
    """Parse agent output to extract reasoning steps."""
    steps = []
    
    # Look for Thought/Action/Observation pattern
    thought_pattern = r'Thought:\s*(.*?)(?=Action:|Final Answer:|$)'
    action_pattern = r'Action:\s*(.*?)(?=Action Input:|$)'
    action_input_pattern = r'Action Input:\s*(.*?)(?=Observation:|$)'
    observation_pattern = r'Observation:\s*(.*?)(?=Thought:|Action:|Final Answer:|$)'
    final_answer_pattern = r'Final Answer:\s*(.*?)$'
    
    thoughts = re.findall(thought_pattern, output_text, re.DOTALL | re.IGNORECASE)
    actions = re.findall(action_pattern, output_text, re.DOTALL | re.IGNORECASE)
    action_inputs = re.findall(action_input_pattern, output_text, re.DOTALL | re.IGNORECASE)
    observations = re.findall(observation_pattern, output_text, re.DOTALL | re.IGNORECASE)
    final_answers = re.findall(final_answer_pattern, output_text, re.DOTALL | re.IGNORECASE)
    
    for thought in thoughts:
        steps.append({"type": "thought", "content": thought.strip()})
    
    for i, action in enumerate(actions):
        steps.append({"type": "action", "content": action.strip()})
        if i < len(action_inputs):
            steps.append({"type": "action_input", "content": action_inputs[i].strip()})
    
    for observation in observations:
        steps.append({"type": "observation", "content": observation.strip()})
    
    for answer in final_answers:
        steps.append({"type": "final_answer", "content": answer.strip()})
    
    return steps


def display_trace(trace):
    """Display trace information in Streamlit."""
    with st.expander("🔍 Query Trace", expanded=False):
        st.markdown(f"**Timestamp:** `{trace.timestamp.strftime('%Y-%m-%d %H:%M:%S')}`")
        st.markdown(f"**Query Type:** `{trace.query_type}`")
        st.markdown(f"**User Input:** `{trace.user_input}`")
        
        if trace.execution_time:
            st.markdown(f"**Execution Time:** `{trace.execution_time:.2f}s`")
        
        # Display SQL Queries
        if trace.sql_queries:
            st.markdown("### 📝 SQL Queries Generated")
            for i, sql_info in enumerate(trace.sql_queries, 1):
                st.markdown(f"**Query {i}:**")
                st.code(sql_info["query"], language="sql")
                st.caption(f"Generated at: {sql_info['timestamp'].strftime('%H:%M:%S')}")
        
        # Display Agent Steps
        if trace.agent_steps:
            st.markdown("### 🤖 Agent Reasoning Steps")
            for i, step in enumerate(trace.agent_steps, 1):
                step_type = step["type"].upper()
                step_icon = {
                    "thought": "💭",
                    "action": "⚙️",
                    "action_input": "📥",
                    "observation": "👁️",
                    "final_answer": "✅"
                }.get(step["type"], "📌")
                
                st.markdown(f"**{step_icon} Step {i}: {step_type}**")
                st.code(step["content"], language="text")
        
        # Display Results
        if trace.results:
            st.markdown("### 📊 Query Results")
            for i, result in enumerate(trace.results, 1):
                st.json(result) if isinstance(result, dict) else st.text(str(result))
        
        # Display Errors
        if trace.errors:
            st.markdown("### ⚠️ Errors")
            for error in trace.errors:
                st.error(str(error))

