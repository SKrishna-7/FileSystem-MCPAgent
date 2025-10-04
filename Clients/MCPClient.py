import asyncio
import os
import re
import time
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langgraph.checkpoint.memory import MemorySaver

memory=MemorySaver()
load_dotenv()
# MODEL_NAME = "llama-3.1-8b-instant"
MODEL_NAME = "openai/gpt-oss-20b"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found in environment variables. Please set it in the .env file.")

LOG_FILE = "file_agent.log"

def log_query(query: str, response: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] QUERY: {query}\nRESPONSE: {response}\n{'-'*50}\n")

SYSTEM_INSTRUCTIONS = """
You are a Windows File System Agent restricted to the D:\ drive.
Your job is to understand natural language and use ONLY the provided MCP tools.

When the user asks anything involving files or directories (e.g., list, read, write, move, rename, search),
you MUST call the appropriate tool instead of replying with text.

"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_INSTRUCTIONS),
    MessagesPlaceholder(variable_name="messages"),
])

async def main():
    try:
        print("Connecting...")
        client = MultiServerMCPClient({
            "file_tools": {
                "command": "python",
                "args": ["../Servers/MCPToolsServer.py"],
                "transport": "stdio"
            }
        })
        print("loading tools..")
        tools = await client.get_tools()
        print("tools loaded..")


        print("loading model..")
        model = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
        print("loaded..")

        print("loding agent...")
        agent = create_react_agent(model, tools, prompt=prompt,checkpointer=memory)
        print("agent loaded...")

        config={"configurable":{"thread_id":"1"}}

        print("----- File System Agent Ready (Restricted to D:\\) -----")
        print("Enter queries like 'list files in D:\\TestFolder' or 'read file D:\\test.txt'.")
        print("Type 'exit', 'quit', or 'stop' to exit.")

        while True:
            query = input("File Agent: ")
           

            try:
                response = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": query}]},
                    config=config
                )
                try:
                    final_message = response["messages"][-1].content
                    print("File Assistant:", final_message)
                    log_query(query, final_message)
                except (KeyError, IndexError):
                    print("File Assistant: Unexpected response format.")
                    log_query(query, f"Unexpected response format: {response}")
            except Exception as e:
                print(f"File Assistant: Error processing query: {str(e)}")
                log_query(query, f"Error: {str(e)}")

    except Exception as e:
        print(f"Error initializing agent: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
