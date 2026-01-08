import os
import sys
import warnings
import time
from contextlib import contextmanager
from typing import Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import streamlit as st
import unidecode
from helper import display_code_plots, display_text_with_images
from llm_agent import initialize_python_agent, initialize_sql_agent
from constants import OPENAI_API_KEY, LLM_MODEL_NAME, DATABASE
from trace_handler import QueryTrace, extract_sql_from_text, parse_agent_output, display_trace
from visitor_tracker import track_visitor, get_visitor_count
from input_validation import validate_query_input, sanitize_input
from rate_limiter import rate_limiter

# Suppress warnings
warnings.filterwarnings("ignore")

# Configure paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, "..")
sys.path.insert(0, parent_dir)

# Configure Streamlit page
st.set_page_config(page_title="Data Insights", page_icon="📊", layout="wide")

# Track visitor
if 'visitor_tracked' not in st.session_state:
    # Get unique session ID (convert to string)
    session_id = st.session_state.get('_session_id', str(id(st.session_state)))
    visitor_stats = track_visitor(session_id)
    st.session_state.visitor_tracked = True
    st.session_state.visitor_count = visitor_stats["total_visitors"]
    if visitor_stats["is_new_visitor"]:
        st.session_state.is_new_visitor = True
else:
    # Just get the count without tracking again
    visitor_stats = get_visitor_count()
    st.session_state.visitor_count = visitor_stats["total_visitors"]

# Sidebar for API key configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key input
    st.subheader("OpenAI API Key")
    api_key_input = st.text_input(
        "Enter your OpenAI API Key",
        type="password",
        help="Your API key is stored securely in session state and never logged or saved.",
        placeholder="sk-..."
    )
    
    # Validate API key format
    def is_valid_api_key(key):
        """Basic validation for OpenAI API key format."""
        if not key:
            return False, "Please enter an API key"
        if not key.startswith("sk-"):
            return False, "API key should start with 'sk-'"
        if len(key) < 20:
            return False, "API key seems too short"
        return True, "Valid API key format"
    
    # Store API key in session state
    if api_key_input:
        is_valid, message = is_valid_api_key(api_key_input)
        if is_valid:
            # Only update if key changed
            if 'openai_api_key' not in st.session_state or st.session_state.openai_api_key != api_key_input:
                st.session_state.openai_api_key = api_key_input
                st.session_state.api_key_changed = True
                st.success("✅ API key saved!")
            else:
                st.info("✅ Using saved API key")
        else:
            st.warning(f"⚠️ {message}")
            if 'openai_api_key' in st.session_state:
                del st.session_state.openai_api_key
    elif 'openai_api_key' in st.session_state:
        # User cleared the input, keep using existing key
        st.info("Using previously saved API key")
    
    # Show API key status
    if 'openai_api_key' in st.session_state:
        st.caption(f"🔑 Key: {st.session_state.openai_api_key[:7]}...{st.session_state.openai_api_key[-4:]}")
    else:
        st.caption("⚠️ No API key configured")
    
    st.divider()
    
    # Help section
    with st.expander("ℹ️ How to get an API key"):
        st.markdown("""
        1. Go to [OpenAI Platform](https://platform.openai.com/)
        2. Sign in or create an account
        3. Navigate to **API Keys** section
        4. Click **Create new secret key**
        5. Copy and paste it here
        
        **Note**: Your API key is stored only in your browser session and never sent to our servers.
        """)
    
    st.divider()
    st.caption("💡 Tip: Your API key is required to use the AI features")
    
    # Rate limit status
    st.divider()
    remaining_requests = rate_limiter.get_remaining_requests(max_requests=20, time_window=60)
    st.caption(f"📊 Rate Limit: {remaining_requests}/20 requests per minute remaining")
    
    st.divider()
    
    # Visitor count in sidebar
    visitor_count = st.session_state.get('visitor_count', 0)
    st.metric("👥 Visitors", visitor_count, help="Total number of unique visitors to this application")
    st.divider()
    
    # Domain Information Section
    st.divider()
    st.header("📊 Database Domain")
    
    with st.expander("ℹ️ About This Database", expanded=False):
        st.markdown("""
        **E-commerce Analytics Database**
        
        This database contains e-commerce transaction data including:
        - Customer information and demographics
        - Product catalog and inventory
        - Order and order item details
        - User events and interactions
        - Distribution center locations
        
        Use natural language to query this data and generate insights!
        """)
    
    # Sample Questions
    st.subheader("💡 Sample Questions")
    sample_questions = [
        "What is the total revenue?",
        "Show me top 10 products by sales",
        "How many orders were placed last month?",
        "What is the average order value?",
        "Which state has the most customers?",
        "What is the return rate?",
        "Show me revenue by product category",
        "What are the top selling brands?",
        "How many users registered this year?",
        "What is the average age of customers?"
    ]
    
    for i, question in enumerate(sample_questions, 1):
        if st.button(f"💬 {question}", key=f"sample_q_{i}", use_container_width=True):
            # Add to chat input (this will be handled by the chat input handler)
            st.session_state.sample_question = question
    
    # Entity Details
    st.subheader("📋 Database Entities")
    
    entities_info = {
        "users": {
            "description": "Customer information and demographics",
            "key_fields": ["id", "first_name", "last_name", "email", "age", "gender", "state", "city", "country", "created_at"],
            "relationships": "Links to orders via user_id"
        },
        "orders": {
            "description": "Order transactions",
            "key_fields": ["order_id", "user_id", "status", "created_at", "shipped_at", "delivered_at", "returned_at", "num_of_item"],
            "relationships": "Links to users (user_id) and order_items (order_id)"
        },
        "order_items": {
            "description": "Individual items in each order",
            "key_fields": ["id", "order_id", "user_id", "product_id", "status", "sale_price", "created_at", "shipped_at", "delivered_at", "returned_at"],
            "relationships": "Links to orders (order_id), users (user_id), products (product_id)"
        },
        "products": {
            "description": "Product catalog",
            "key_fields": ["id", "name", "category", "brand", "department", "cost", "retail_price", "sku", "distribution_center_id"],
            "relationships": "Links to inventory_items (product_id) and distribution_centers (distribution_center_id)"
        },
        "inventory_items": {
            "description": "Inventory tracking",
            "key_fields": ["id", "product_id", "cost", "product_category", "product_name", "product_brand", "product_retail_price", "created_at", "sold_at"],
            "relationships": "Links to products (product_id)"
        },
        "events": {
            "description": "User interaction events",
            "key_fields": ["id", "user_id", "event_type", "session_id", "created_at", "city", "state", "browser", "traffic_source", "uri"],
            "relationships": "Links to users (user_id)"
        },
        "distribution_centers": {
            "description": "Warehouse locations",
            "key_fields": ["id", "name", "latitude", "longitude"],
            "relationships": "Links to products (distribution_center_id)"
        }
    }
    
    selected_entity = st.selectbox(
        "Select an entity to view details:",
        options=list(entities_info.keys()),
        key="entity_selector"
    )
    
    if selected_entity:
        entity = entities_info[selected_entity]
        st.markdown(f"**{selected_entity.upper()}**")
        st.caption(entity["description"])
        st.markdown("**Key Fields:**")
        st.code(", ".join(entity["key_fields"]), language=None)
        st.markdown(f"**Relationships:** {entity['relationships']}")
    
    st.divider()

# Get API key from session state or use environment variable (if set)
# OPENAI_API_KEY from constants will be None if not set in environment
user_api_key = st.session_state.get('openai_api_key', OPENAI_API_KEY)

# Set environment variable if we have a key
if user_api_key:
    os.environ['OPENAI_API_KEY'] = user_api_key

# Initialize session state
if 'agent_memory' not in st.session_state or st.session_state.get('api_key_changed', False):
    if user_api_key:
        st.session_state['agent_memory_sql'] = initialize_sql_agent(api_key=user_api_key)
        st.session_state['agent_memory_python'] = initialize_python_agent(api_key=user_api_key)
        st.session_state.api_key_changed = False
    else:
        # Initialize with None - will use environment variable if set
        st.session_state['agent_memory_sql'] = None
        st.session_state['agent_memory_python'] = None

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'agent' not in st.session_state:
    st.session_state.sql_agent = st.session_state.get('agent_memory_sql')
    st.session_state.python_agent = st.session_state.get('agent_memory_python')

if 'query_traces' not in st.session_state:
    st.session_state.query_traces = []

if 'show_traces' not in st.session_state:
    st.session_state.show_traces = True


def run_with_timeout(func: Callable, timeout: int = 30, *args, **kwargs) -> Any:
    """
    Execute a function with a timeout using ThreadPoolExecutor.
    This is thread-safe and works in Streamlit's execution context.
    
    Args:
        func: Function to execute
        timeout: Timeout in seconds
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Result of the function call
        
    Raises:
        TimeoutError: If the function execution exceeds the timeout
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError:
            raise TimeoutError(f"Operation exceeded {timeout} second timeout")


def generate_response(code_type, input_text, trace=None):
    """
    Generate a response based on the provided input text and code type.

    Args:
        code_type (str): The type of code to be generated ("python" or "sql").
        input_text (str): The input text to be processed.
        trace (QueryTrace): Optional trace object to capture execution details.

    Returns:
        str: The generated response based on the input text and code type.
             If no response is generated, it returns "NO_RESPONSE".
    """
    # Safety check for agents
    if not st.session_state.get('sql_agent') or not st.session_state.get('python_agent'):
        if trace:
            trace.add_error("Agents not initialized")
        return "NO_RESPONSE"
    
    # Rate limiting check
    is_allowed, rate_limit_error = rate_limiter.check_rate_limit(
        max_requests=20,  # 20 requests per minute
        time_window=60
    )
    if not is_allowed:
        if trace:
            trace.add_error(f"Rate limit: {rate_limit_error}")
        return f"⚠️ {rate_limit_error}"
    
    # Input validation
    is_valid, validation_error = validate_query_input(input_text)
    if not is_valid:
        if trace:
            trace.add_error(f"Validation error: {validation_error}")
        return f"❌ Input validation failed: {validation_error}"
    
    # Sanitize input
    sanitized_input = sanitize_input(input_text)
    local_prompt = unidecode.unidecode(sanitized_input)
    start_time = time.time()
    
    if code_type == "python":
        try:
            # First get SQL data with timeout
            if trace:
                trace.add_agent_step("thought", "Getting data from SQL agent for visualization")
            
            try:
                local_response = run_with_timeout(
                    lambda: st.session_state.sql_agent.invoke({"input": local_prompt})['output'],
                    timeout=30
                )
            except TimeoutError as e:
                if trace:
                    trace.add_error(f"Query timeout: {str(e)}")
                return f"⏱️ Query execution timed out after 30 seconds. Please try a simpler query or break it into smaller parts."
            
            if trace:
                # Extract SQL queries from response
                sql_queries = extract_sql_from_text(local_response)
                for sql in sql_queries:
                    trace.add_sql_query(sql)
                trace.add_agent_step("observation", f"SQL Agent returned: {local_response[:200]}...")
            
            print("Response->", local_response)
        except Exception as e:
            if trace:
                trace.add_error(f"SQL Agent error: {str(e)}")
            return "NO_RESPONSE"
        exclusion_keywords = ["please provide", "don't know", "more context", "provide more", "vague request"]
        if any(keyword in local_response.lower() for keyword in exclusion_keywords):
            if trace:
                trace.add_error("SQL Agent returned exclusion keywords")
            return "NO_RESPONSE"
        
        if trace:
            trace.add_agent_step("thought", "Generating Python/Plotly code for visualization")

        local_prompt = {"input": "Write a code in python to plot the following data\n\n" + local_response}
        try:
            result = run_with_timeout(
                lambda: st.session_state.python_agent.invoke(local_prompt),
                timeout=30
            )
        except TimeoutError as e:
            if trace:
                trace.add_error(f"Python code generation timeout: {str(e)}")
            return f"⏱️ Code generation timed out after 30 seconds. Please try a simpler visualization request."
        
        if trace:
            if isinstance(result, dict) and 'output' in result:
                trace.add_agent_step("final_answer", f"Python code generated: {result['output'][:200]}...")
            trace.execution_time = time.time() - start_time
        
        return result
    else:
        # SQL query path
        if trace:
            trace.add_agent_step("thought", "Processing SQL query request")
        
        if not st.session_state.get('sql_agent'):
            if trace:
                trace.add_error("SQL agent not initialized")
            return "NO_RESPONSE"
        
        try:
            result = run_with_timeout(
                lambda: st.session_state.sql_agent.run(local_prompt),
                timeout=30
            )
        except TimeoutError as e:
            if trace:
                trace.add_error(f"SQL query timeout: {str(e)}")
            return f"⏱️ Query execution timed out after 30 seconds. Please try a simpler query or add more specific filters."
        
        if trace:
            # Extract SQL queries and agent steps from result
            sql_queries = extract_sql_from_text(str(result))
            for sql in sql_queries:
                trace.add_sql_query(sql)
            
            # Try to parse agent reasoning steps
            agent_steps = parse_agent_output(str(result))
            for step in agent_steps:
                trace.add_agent_step(step["type"], step["content"])
            
            trace.execution_time = time.time() - start_time
        
        return result


def reset_conversation():
    st.session_state.messages = []
    st.session_state.query_traces = []
    user_api_key = st.session_state.get('openai_api_key', OPENAI_API_KEY)
    if user_api_key:
        st.session_state.sql_agent = initialize_sql_agent(api_key=user_api_key)
        st.session_state.python_agent = initialize_python_agent(api_key=user_api_key)
    else:
        st.session_state.sql_agent = None
        st.session_state.python_agent = None


# Display title and reset button
col_title, col_visitor = st.columns([3, 1])
with col_title:
    st.title("📊 Data Insights - E-commerce Analytics")
    st.caption("Ask questions about customers, orders, products, and sales in natural language")
with col_visitor:
    # Display visitor count
    visitor_count = st.session_state.get('visitor_count', 0)
    st.metric("👥 Total Visitors", visitor_count)
    if st.session_state.get('is_new_visitor', False):
        st.success("✨ Welcome! You're a new visitor")

col1, col2, col3 = st.columns([2, 1, 1])
with col2:
    st.session_state.show_traces = st.checkbox("Show Query Traces", value=st.session_state.show_traces)
with col3:
    st.button("Reset Chat", on_click=reset_conversation)

# Quick reference card
with st.expander("📚 Quick Reference - What can I ask?", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **📈 Sales & Revenue:**
        - Total revenue
        - Revenue by period
        - Average order value
        - Sales by category/brand
        - Return percentage
        
        **📦 Orders:**
        - Order count
        - Order status breakdown
        - Shipping times
        - Delivery performance
        """)
    with col2:
        st.markdown("""
        **👥 Customers:**
        - Customer demographics
        - Customer count by location
        - New customer registrations
        - Customer segmentation
        
        **🛍️ Products:**
        - Top selling products
        - Product categories
        - Inventory levels
        - Brand performance
        """)

# Display chat messages from history
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] in ("assistant", "error"):
            display_text_with_images(message["content"])
            # Show trace if available and enabled
            if st.session_state.show_traces and idx < len(st.session_state.query_traces):
                display_trace(st.session_state.query_traces[idx])
        elif message["role"] == "plot":
            exec(message["content"])
            # Show trace if available and enabled
            if st.session_state.show_traces and idx < len(st.session_state.query_traces):
                display_trace(st.session_state.query_traces[idx])
        else:
            st.markdown(message["content"])

# Check if API key is configured before accepting input
if not user_api_key:
    st.warning("⚠️ Please configure your OpenAI API key in the sidebar to use this application.")
    st.stop()

# Check if agents are initialized
if not st.session_state.sql_agent or not st.session_state.python_agent:
    st.error("❌ Agents not initialized. Please check your API key and refresh the page.")
    st.stop()

# Handle sample question from sidebar
sample_prompt = None
if 'sample_question' in st.session_state:
    sample_prompt = st.session_state.sample_question
    del st.session_state.sample_question

# Accept user input
if sample_prompt:
    prompt = sample_prompt
elif prompt := st.chat_input("Please ask your question:"):
    pass
else:
    prompt = None

if prompt:
    # Create trace for this query
    trace = QueryTrace()
    trace.user_input = prompt
    
    # Display user message in chat
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    keywords = ["plot", "graph", "chart", "diagram"]
    if any(keyword in prompt.lower() for keyword in keywords):
        trace.query_type = "visualization"
        prev_context = ""
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "assistant":
                prev_context = msg["content"] + "\n\n" + prev_context
                break
        if prev_context:
            prompt += f"\n\nGiven previous agent responses:\n{prev_context}\n"
        response = generate_response("python", prompt, trace)
        if response == "NO_RESPONSE":
            response = "Please try again with a re-phrased query and more context"
            with st.chat_message("error"):
                display_text_with_images(response)
            st.session_state.messages.append({"role": "error", "content": response})
        else:
            code = display_code_plots(response['output'])
            try:
                if trace:
                    trace.add_agent_step("final_answer", f"Python code extracted and processed")
                code = f"import pandas as pd\n{code.replace('fig.show()', '')}"
                code += "st.plotly_chart(fig, theme='streamlit', use_container_width=True)"
                exec(code)
                
                # Store trace
                st.session_state.query_traces.append(trace)
                
                st.session_state.messages.append({"role": "plot", "content": code})
            except Exception as e:
                if trace:
                    trace.add_error(f"Code execution error: {str(e)}")
                    st.session_state.query_traces.append(trace)
                response = "Please try again with a re-phrased query and more context"
                with st.chat_message("error"):
                    display_text_with_images(response)
                st.session_state.messages.append({"role": "error", "content": response})
    else:
        if len(st.session_state.messages) > 1:
            context_length = 0
            prev_context = ""
            for msg in reversed(st.session_state.messages):
                if context_length > 1:
                    break
                if msg["role"] == "assistant":
                    prev_context = msg["content"] + "\n\n" + prev_context
                    context_length += 1
            response = generate_response("sql", f"{prompt}\n\nGiven previous agent responses:\n{prev_context}\n", trace)
        else:
            trace.query_type = "sql"
            response = generate_response("sql", prompt, trace)
        
        # Store trace
        st.session_state.query_traces.append(trace)
        
        with st.chat_message("assistant"):
            display_text_with_images(response)
            # Display trace if enabled
            if st.session_state.show_traces:
                display_trace(trace)
        st.session_state.messages.append({"role": "assistant", "content": response})
