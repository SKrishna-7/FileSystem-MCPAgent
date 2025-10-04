import asyncio

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from mcp_use import MCPAgent, MCPClient
import os
from langchain_ollama import ChatOllama




CONFIG_FILE = r"D:\SureshKrishna\ModelContextProtocol\InteractWithLocalFiles\Servers\FileIntract.json"

async def run_memory_chat():
    load_dotenv()
    os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")


    print("Initializing chat...")
    MODEL_NAME = "deepseek-r1-distill-llama-70b"

    client = MCPClient.from_config_file(CONFIG_FILE)
    llm = ChatGroq(model=MODEL_NAME)
    # llm=ChatOllama(model='mistral:latest')


    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=15,
        memory_enabled=True, 
        verbose=True,
        system_prompt="""
        You are a Windows File System Agent restricted to the D:\ drive.
        response should be Complete 
"""
        
    )

    print("\n===== Interactive MCP Chat =====")
    print("==================================\n")

    try:
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                    print("Ending conversation...")
    

            # Check for clear history command
            if user_input.lower() == "clear":
                agent.clear_conversation_history()
            
                


            print("\nAssistant: ", end="", flush=True)



            # Run the agent with the user input (memory handling is automatic)
            response = await agent.run(user_input)
            print("=================================="*20,"\n")
            print(response)
                

    except Exception as e:
            print(f"\nError: {e}")
                

    finally:
        # Clean up
        if client and client.sessions:
            await client.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(run_memory_chat())