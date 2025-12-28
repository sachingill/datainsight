# Text2SQL Application Flow

## Overview
The application converts natural language questions into SQL queries, executes them, and can generate visualizations using Python/Plotly.

---

## 🔄 Complete Application Flow

### 1. **Initialization Phase** (App Startup)

```
┌─────────────────────────────────────┐
│  Streamlit App Starts                │
│  - Loads constants.py                │
│  - Sets OPENAI_API_KEY environment   │
│  - Configures page title             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Initialize Agents                   │
│  ├─ SQL Agent (for SQL queries)     │
│  │  └─ Connects to ecommerce.db     │
│  │  └─ Sets up conversation memory  │
│  │                                    │
│  └─ Python Agent (for visualizations)│
│     └─ Uses Python REPL tool        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Session State Initialized           │
│  - agent_memory_sql                  │
│  - agent_memory_python               │
│  - messages (empty array)            │
└─────────────────────────────────────┘
```

---

### 2. **User Input Processing**

```
User types question in chat input
         │
         ▼
┌─────────────────────────────────────┐
│  Check for Visualization Keywords   │
│  Keywords: "plot", "graph", "chart", │
│            "diagram"                │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        │             │
    YES │             │ NO
        │             │
        ▼             ▼
```

---

### 3. **SQL Query Path** (No visualization keywords)

```
┌─────────────────────────────────────┐
│  SQL Query Path                      │
│                                      │
│  1. Check conversation history       │
│     - If messages exist, get last   │
│       2 assistant responses           │
│     - Add as context to prompt       │
│                                      │
│  2. Normalize input                  │
│     - Remove accents (unidecode)     │
│                                      │
│  3. Call SQL Agent                  │
│     └─ generate_response("sql")     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  SQL Agent Processing                │
│                                      │
│  Agent uses ReAct pattern:          │
│  1. Thought: Analyze question        │
│  2. Action: Choose SQL tool          │
│  3. Action Input: Generate SQL       │
│  4. Observation: Execute query       │
│  5. Repeat until answer found        │
│  6. Final Answer: Format response    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  SQL Agent Components                │
│                                      │
│  ├─ LLM (ChatOpenAI)                 │
│  │  └─ Model: gpt-4.1-2025-04-14    │
│  │  └─ Temperature: 0              │
│  │                                    │
│  ├─ SQLDatabaseToolkit              │
│  │  ├─ List tables                  │
│  │  ├─ Describe table schema        │
│  │  ├─ Query checker               │
│  │  └─ Query executor              │
│  │                                    │
│  ├─ Conversation Memory             │
│  │  └─ SQLChatMessageHistory        │
│  │     └─ Stored in session_history.db│
│  │                                    │
│  └─ Custom Instructions              │
│     ├─ Use LOWER() for case-insensitive│
│     ├─ Use LIKE for fuzzy matching   │
│     ├─ No hallucination              │
│     └─ User-friendly formatting     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Display Results                     │
│  - Format text with markdown        │
│  - Handle images if present         │
│  - Add to message history           │
└─────────────────────────────────────┘
```

---

### 4. **Visualization Path** (Contains visualization keywords)

```
┌─────────────────────────────────────┐
│  Visualization Path                  │
│                                      │
│  1. Get previous SQL response       │
│     - Look for last assistant msg   │
│     - Extract data/query results    │
│                                      │
│  2. Add context to prompt           │
│     "Given previous agent responses: │
│      [SQL results]"                 │
│                                      │
│  3. Call SQL Agent First             │
│     └─ Get data for visualization   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Check SQL Response                  │
│  - Exclude if contains:             │
│    "please provide", "don't know",  │
│    "more context", "vague request"  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Call Python Agent                   │
│  Prompt: "Write a code in python to │
│          plot the following data"   │
│          + SQL results              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Python Agent Processing             │
│                                      │
│  ├─ LLM (ChatOpenAI)                 │
│  │  └─ Generates Python code        │
│  │                                    │
│  ├─ PythonREPLTool                   │
│  │  └─ Validates code execution      │
│  │  └─ Returns success/error         │
│  │                                    │
│  └─ Instructions:                    │
│     ├─ Use Plotly only (no matplotlib)│
│     ├─ Return code in ```python```  │
│     └─ Debug on errors              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Extract & Process Python Code       │
│                                      │
│  1. Extract code from markdown      │
│     └─ display_code_plots()         │
│                                      │
│  2. Modify code:                     │
│     ├─ Add: import pandas as pd      │
│     ├─ Remove: fig.show()            │
│     └─ Add: st.plotly_chart(fig)    │
│                                      │
│  3. Execute code in Streamlit        │
│     └─ exec(code)                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Display Visualization               │
│  - Render Plotly chart in Streamlit  │
│  - Store code in message history    │
│  - Role: "plot"                     │
└─────────────────────────────────────┘
```

---

## 🔧 Key Components

### SQL Agent Architecture

```
┌─────────────────────────────────────┐
│  SQL Agent                           │
├─────────────────────────────────────┤
│                                      │
│  ┌──────────────┐                   │
│  │   LLM        │                   │
│  │  (ChatOpenAI)│                   │
│  └──────┬───────┘                   │
│         │                           │
│         ▼                           │
│  ┌──────────────┐                   │
│  │   Toolkit    │                   │
│  │  (SQL Tools) │                   │
│  └──────┬───────┘                   │
│         │                           │
│         ▼                           │
│  ┌──────────────┐                   │
│  │   Database   │                   │
│  │ (ecommerce)  │                   │
│  └──────────────┘                   │
│                                      │
│  ┌──────────────┐                   │
│  │   Memory     │                   │
│  │ (Conversation)│                  │
│  └──────────────┘                   │
└─────────────────────────────────────┘
```

### Python Agent Architecture

```
┌─────────────────────────────────────┐
│  Python Agent                        │
├─────────────────────────────────────┤
│                                      │
│  ┌──────────────┐                   │
│  │   LLM        │                   │
│  │  (ChatOpenAI)│                   │
│  └──────┬───────┘                   │
│         │                           │
│         ▼                           │
│  ┌──────────────┐                   │
│  │ Python REPL  │                   │
│  │    Tool      │                   │
│  └──────────────┘                   │
│                                      │
│  Generates Plotly visualization code │
└─────────────────────────────────────┘
```

---

## 📊 Data Flow Example

### Example: "Show me total revenue by category"

```
1. User Input
   └─ "Show me total revenue by category"
   
2. SQL Agent Processing
   ├─ Thought: Need to join orders, order_items, products
   ├─ Action: sql_db_query
   ├─ SQL Generated:
   │  SELECT p.category, SUM(oi.sale_price) as revenue
   │  FROM products p
   │  JOIN order_items oi ON p.id = oi.product_id
   │  GROUP BY p.category
   ├─ Observation: Query results
   └─ Final Answer: Formatted table with results
   
3. Display
   └─ Shows formatted results in chat
```

### Example: "Plot a chart of sales over time"

```
1. User Input
   └─ "Plot a chart of sales over time"
   
2. Detection
   └─ Contains "plot" → Visualization path
   
3. SQL Agent (First Pass)
   ├─ Gets previous context or generates query
   ├─ SQL: SELECT DATE(created_at), SUM(sale_price)
   │        FROM order_items GROUP BY DATE(created_at)
   └─ Returns: Data results
   
4. Python Agent (Second Pass)
   ├─ Input: SQL results + "plot the following data"
   ├─ Generates Plotly code:
   │  import plotly.graph_objects as go
   │  fig = go.Figure(data=go.Scatter(...))
   └─ Validates code execution
   
5. Code Processing
   ├─ Extract from markdown
   ├─ Add pandas import
   ├─ Replace fig.show() with st.plotly_chart()
   └─ Execute in Streamlit
   
6. Display
   └─ Interactive Plotly chart rendered
```

---

## 🧠 Memory & Context Management

### Conversation Memory
- **SQL Agent**: Uses `SQLChatMessageHistory` stored in `session_history.db`
- **Streamlit**: Maintains `st.session_state.messages` array
- **Context Window**: Last 1-2 assistant responses used for context

### Message Roles
- `"user"`: User questions
- `"assistant"`: SQL query results
- `"plot"`: Visualization code (executed)
- `"error"`: Error messages

---

## ⚙️ Configuration

### Key Settings
- **Model**: `gpt-4.1-2025-04-14`
- **Temperature**: 0 (deterministic)
- **Max Tokens**: 4000
- **Database**: SQLite (`ecommerce`)
- **Memory**: SQLChatMessageHistory

### Custom Instructions (SQL Agent)
- Use `LOWER()` for case-insensitive string comparisons
- Use `LIKE` for fuzzy matching
- No hallucination - only use actual data
- Return "No results found" if query is empty
- User-friendly, well-formatted output

---

## 🔄 Error Handling

### SQL Agent Errors
- Handled by `handle_parsing_errors=True`
- Returns error message to user

### Python Agent Errors
- Code validation catches errors
- Returns "NO_RESPONSE" if validation fails
- Shows error message: "Please try again with a re-phrased query"

### Visualization Errors
- Try/except around code execution
- Falls back to error message
- Preserves conversation flow

---

## 🎯 Decision Points

```
User Question
    │
    ├─ Contains "plot/graph/chart/diagram"?
    │   │
    │   ├─ YES → Visualization Path
    │   │   ├─ Get previous SQL context
    │   │   ├─ Run SQL agent for data
    │   │   ├─ Run Python agent for code
    │   │   └─ Execute & display chart
    │   │
    │   └─ NO → SQL Query Path
    │       ├─ Check conversation history
    │       ├─ Run SQL agent
    │       └─ Display formatted results
    │
    └─ Reset Chat?
        └─ YES → Clear all state & reinitialize agents
```

---

## 📝 Summary

The application uses a **two-agent architecture**:
1. **SQL Agent**: Converts natural language → SQL → Results
2. **Python Agent**: Converts data → Plotly visualization code

The flow intelligently routes between SQL queries and visualizations based on user intent, maintains conversation context, and provides a seamless chat interface for data exploration.

