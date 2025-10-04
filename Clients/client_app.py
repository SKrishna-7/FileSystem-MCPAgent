import asyncio
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient
import os
from langchain_ollama import ChatOllama

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

CONFIG_FILE = "../Servers/FileIntract.json"

# MODEL_NAME = "openai/gpt-oss-20b"
MODEL_NAME = "openai/gpt-oss-120b"
# MODEL_NAME = "mistral:latest"



st.set_page_config(page_title="MCPAgent Chat", layout="wide")
st.title("Local File MCPAgent")
st.markdown("Interact with the MCP( ModelContextProtocol ) Agent to explore the Windows local drive. Type your queries below.")

BASE_DRIVE="D:\\"
with st.sidebar:
    st.markdown("Manage your conversation settings.")
    clear_button = st.button("Clear History", key="clear_history")
    st.markdown("---")
    st.subheader("Select Folder")
    try:
        folders = [f for f in os.listdir(BASE_DRIVE) if os.path.isdir(os.path.join(BASE_DRIVE, f))]
        folders.insert(0, "D:\\ (Root)")
        selected_folder = st.selectbox("Choose a folder to interact with:", folders, key="folder_selector")
        if selected_folder == "D:\\ (Root)":
            base_path = "D:\\"
        else:
            base_path = os.path.join("D:\\", selected_folder)
    except Exception as e:
        st.error(f"Error loading folders: {e}")
        base_path = "D:\\"

    st.markdown("---")
    st.markdown(f"**Current Path**: {base_path}")
    st.markdown("---")

    st.markdown(
        """
        <div style='text-align: center;'>
            <p>Built by Suresh krishnan 🧑‍💻</p>
        </div>
        """,
        unsafe_allow_html=True
    )
if "messages" not in st.session_state:
    st.session_state.messages = []
if "client" not in st.session_state:
    st.session_state.client = None
if "agent" not in st.session_state:
    st.session_state.agent = None

def initialize_agent():
    if st.session_state.client is None:
        st.session_state.client = MCPClient.from_config_file(CONFIG_FILE)
        llm = ChatGroq(model=MODEL_NAME)
        # llm=ChatOllama(model='mistral:latest')

        st.session_state.agent = MCPAgent(
            llm=llm,
            client=st.session_state.client,
            max_steps=15,
            memory_enabled=True,
            verbose=True,
            system_prompt="""
            You are a Windows File System Agent restricted to the D:\\ drive.
            Response should be complete.
            """
        )
def render_response(res):
    if res.strip().startswith("{") and res.strip().endswith("}"):
        st.markdown(f"```json\n{res}\n```")
    elif "def " in res or "class " in res:
        st.markdown(f"```python\n{res}\n```")
    else:
        st.write(res)

def display_chat():
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=message.get("avatar")):
                if message["role"] == "assistant":
                    st.markdown(f"```{message['content']}```")
                else:
                    st.markdown(message["content"])

async def get_agent_response(user_input):
    try:
        user_input_with_path = f"Base path: {base_path}. {user_input}"
        response = await st.session_state.agent.run(user_input_with_path)
        return render_response(response)
    except Exception as e:
        return f"Error: {e}"

async def main():
    initialize_agent()

    display_chat()

    user_input = st.chat_input("Type your message here...", key="user_input")

    if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            
        })
        with st.chat_message("user",):
            st.markdown(user_input)

        if user_input.lower() in ["exit", "quit"]:
            st.markdown("Ending Conversation...")
            if st.session_state.client and st.session_state.client.sessions:
                await st.session_state.client.close_all_sessions()
            st.session_state.client = None
            st.session_state.agent = None
            st.session_state.messages = []
            st.info("Session ended. Refresh to start a new session.")
            st.stop()

        if user_input.lower() == "clear":
            st.session_state.agent.clear_conversation_history()
            st.session_state.messages = []
            st.success("Conversation history cleared.")
            st.rerun()

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Processing..."):
                response = await get_agent_response(user_input)
                st.markdown(f"```{response}```")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "avatar": "🤖"
                })

    if clear_button:
        st.session_state.agent.clear_conversation_history()
        st.session_state.messages = []
        st.success("Conversation history cleared.")
        st.rerun()

    st.markdown("---")
   

if __name__ == "__main__":
    asyncio.run(main())