import urllib.parse
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_community.utilities import SQLDatabase
from langchain_experimental.tools import PythonREPLTool
#from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI

from constants import LLM_MODEL_NAME, DATABASE

CUSTOM_SUFFIX = """Begin!

Relevant pieces of previous conversation:
{chat_history}
(Note: Only reference this information if it is relevant to the current query.)

Question: {input}

CRITICAL INSTRUCTIONS:
1. You MUST answer the EXACT question asked. Do not provide related information or different metrics unless specifically asked.
2. If asked about "revenue", calculate: SUM(order_items.sale_price) or SUM(orders.total) - use the order_items table with sale_price column.
3. If asked about "total revenue", provide a single number representing the sum of all sales.
4. If asked about "top products", then provide top products. If asked about "revenue", provide revenue - answer what was asked.
5. It is imperative that I do not fabricate information not present in any table or engage in hallucination; maintaining trustworthiness is crucial.
6. In SQL queries involving string or TEXT comparisons like first_name, I must use the `LOWER()` function for case-insensitive comparisons and the `LIKE` operator for fuzzy matching. 
7. Queries for return percentage is defined as total number of returns divided by total number of orders. You can join orders table with users table to know more about each user.
8. Make sure that query is related to the SQL database and tables you are working with.
9. If the result is empty, the Answer should be "No results found". DO NOT hallucinate an answer if there is no result.

My final response should STRICTLY be based on the output SQL query result and MUST directly answer the question asked. The output should be user friendly, well-formatted and easy to read. 

{agent_scratchpad}
"""

FORMAT_INSTRUCTIONS = """Use the following format:

Input: the input question you must answer
Thought: <Reasoning for what the next step should be>
Action: the action to take, should be one of [{tool_names}] if using a tool, otherwise answer on your own.
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Final Thought: <Final reasoning to collate the answer for Input>
Final Answer: <the final answer to the original input question>"""

langchain_chat_kwargs = {
    "temperature": 0,
    "max_tokens": 4000,
    "verbose": True,
}
chat_openai_model_kwargs = {
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": -1,
}

db = SQLDatabase.from_uri(f"sqlite:///{DATABASE}")

class ValidatingPythonREPLTool(PythonREPLTool):
    """Runs Python code to validate it, but hides execution output."""

    def _run(self, code: str, **kwargs):
        try:
            super()._run(code, **kwargs)  # actually executes
            return "✅ Code executed without errors."
        except Exception as e:
            return f"❌ Validation failed: {e}"


def get_chat_openai(model_name, api_key=None):
    """
    Returns an instance of the ChatOpenAI class initialized with the specified model name.

    Args:
        model_name (str): The name of the model to use.
        api_key (str, optional): OpenAI API key. If not provided, uses environment variable.

    Returns:
        ChatOpenAI: An instance of the ChatOpenAI class.

    """
    import os
    
    # Use provided API key or fall back to environment variable
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
    
    llm = ChatOpenAI(
        model_name=model_name,
        model_kwargs=chat_openai_model_kwargs,
        **langchain_chat_kwargs
    )
    return llm


def get_sql_toolkit(tool_llm_name: str, api_key=None):
    """
    Instantiates a SQLDatabaseToolkit object with the specified language model.

    This function creates a SQLDatabaseToolkit object configured with a language model
    obtained by the provided model name. The SQLDatabaseToolkit facilitates SQL query
    generation and interaction with a database.

    Args:
        tool_llm_name (str): The name or identifier of the language model to be used.
        api_key (str, optional): OpenAI API key. If not provided, uses environment variable.

    Returns:
        SQLDatabaseToolkit: An instance of SQLDatabaseToolkit initialized with the provided language model.
    """
    llm_tool = get_chat_openai(model_name=tool_llm_name, api_key=api_key)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm_tool)
    return toolkit


def get_agent_llm(agent_llm_name: str, api_key=None):
    """
    Retrieve a language model agent for conversational tasks.

    Args:
        agent_llm_name (str): The name or identifier of the language model for the agent.
        api_key (str, optional): OpenAI API key. If not provided, uses environment variable.

    Returns:
        ChatOpenAI: A language model agent configured for conversational tasks.
    """
    llm_agent = get_chat_openai(model_name=agent_llm_name, api_key=api_key)
    return llm_agent


def initialize_python_agent(agent_llm_name: str = LLM_MODEL_NAME, api_key=None):
    """
    Create an agent for Python-related tasks.

    Args:
        agent_llm_name (str): The name or identifier of the language model for the agent.
        api_key (str, optional): OpenAI API key. If not provided, uses environment variable.

    Returns:
        AgentExecutor: An agent executor configured for Python-related tasks.

    """
    import os
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
    
    instructions = """You are an agent designed to write a python code to answer questions.
            You have access to a python REPL, which you can use to execute python code and 
            validate your code to check for any errors.
            If you get an error, debug your code and try again.
            You might know the answer without running any code, but you should still run the code to get the answer.
            If it does not seem like you can write code to answer the question, just return "I don't know" as the answer.
            Always output the python code only.
            Generate the code <code> for plotting the previous data in plotly, in the format requested. 
            The solution should be given using plotly and only plotly. Do not use matplotlib.
            Return the code <code> in the following
            format ```python <code>```
            """
    tools = [ValidatingPythonREPLTool()]
    base_prompt = hub.pull("langchain-ai/openai-functions-template")
    prompt = base_prompt.partial(instructions=instructions)
    import os
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
    agent_llm = ChatOpenAI(model=agent_llm_name, temperature=0)
    agent = create_openai_functions_agent(agent_llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=False)
    return agent_executor


def initialize_sql_agent(tool_llm_name: str = LLM_MODEL_NAME, agent_llm_name: str = LLM_MODEL_NAME, api_key=None):
    """
    Create an agent for SQL-related tasks.

    Args:
        tool_llm_name (str): The name or identifier of the language model for SQL toolkit.
        agent_llm_name (str): The name or identifier of the language model for the agent.
        api_key (str, optional): OpenAI API key. If not provided, uses environment variable.

    Returns:
        Agent: An agent configured for SQL-related tasks.

    """
    import os
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
    
    # agent_tools = sql_agent_tools()
    llm_agent = get_agent_llm(agent_llm_name, api_key=api_key)
    toolkit = get_sql_toolkit(tool_llm_name, api_key=api_key)
    message_history = SQLChatMessageHistory(
        session_id="my-session",
        connection_string=f"sqlite:///session_history.db",
        table_name="message_store",
        session_id_field_name="session_id"
    )
    memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', chat_memory=message_history, return_messages=False)

    agent = create_sql_agent(
        llm=llm_agent,
        toolkit=toolkit,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        input_variables=["input", "agent_scratchpad", "chat_history"],
        suffix=CUSTOM_SUFFIX,
        format_instructions = FORMAT_INSTRUCTIONS,
        memory=memory,
        agent_executor_kwargs={"memory": memory, "handle_parsing_errors": True, },
        verbose=True
    )
    
    return agent
