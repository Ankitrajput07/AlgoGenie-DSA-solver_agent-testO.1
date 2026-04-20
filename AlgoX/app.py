import streamlit as st
# st.set_page_config MUST be the first Streamlit command
st.set_page_config(page_title="AlgoGenie | DSA Solver", page_icon="🧞‍♂️", layout="wide")

from team.dsa_team import get_dsa_team_and_docker
from config.docker_utils import start_docker_container, stop_docker_container
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult
import asyncio
import traceback

# === Custom CSS for Premium UI ===
st.markdown("""
<style>
    /* Gradient animated title */
    .premium-title {
        background: linear-gradient(to right, #00B4D8, #0077B6, #03045E);
        background-size: 200% auto;
        color: transparent;
        -webkit-background-clip: text;
        font-weight: 800;
        font-size: 3.5rem;
        padding-bottom: 0.5rem;
        animation: textclip 3s linear infinite;
    }
    @keyframes textclip {
        to { background-position: 200% center; }
    }
    /* Custom button styling */
    .stButton>button {
        background: linear-gradient(135deg, #0077B6 0%, #00B4D8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4);
        color: white;
    }
    /* Subtitle styling */
    .premium-sub {
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# === Sidebar: How it works ===
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10435/10435133.png", width=100) # Placeholder AI/Genie icon
    st.markdown("### 🧬 How AlgoGenie Works")
    st.info("""
    AlgoGenie uses a **Multi-Agent AI framework** (Microsoft AutoGen) to solve Data Structures and Algorithms problems.
    
    1. **🧠 Problem Solver Agent**: Analyzes your problem, explains the logic, and writes Python solutions.
    2. **🐳 Code Executor Agent**: Bootstraps an isolated Docker container to safely run the code.
    3. **🔄 Feedback Loop**: If the code encounters errors, the Executor sends logs back to the Solver to fix it automatically!
    """)
    st.divider()
    st.markdown("<small>Powered by AutoGen & Docker</small>", unsafe_allow_html=True)

# === Main Layout ===
st.markdown('<h1 class="premium-title">AlgoGenie 🧞‍♂️</h1>', unsafe_allow_html=True)
st.markdown('<p class="premium-sub">Your intelligent, multi-agent Data Structures and Algorithms solver.</p>', unsafe_allow_html=True)

# Input container
with st.container():
    st.markdown("### 📝 Enter Problem Statement")
    task = st.text_area(
        label="DSA Problem",
        value="Write a function to add two numbers",
        height=150,
        placeholder="Paste your LeetCode problem here...",
        label_visibility="collapsed"
    )

async def run(team, docker, task):
    try:
        await start_docker_container(docker)
        async for message in team.run_stream(task=task):
            if isinstance(message, TextMessage):
                print(f"{message.source} : {message.content}")
                yield message
            elif isinstance(message, TaskResult):
                print(f"Stop Reason: {message.stop_reason}")
                yield message
        print("Task Completed")
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error: {e}")
        yield {"type": "error", "message": str(e), "traceback": error_trace}
    finally:
        await stop_docker_container(docker)

col1, col2 = st.columns([1, 5])
with col1:
    run_btn = st.button("🚀 Solve Problem")

if run_btn:
    st.divider()
    
    chat_container = st.container()
    
    team, docker = get_dsa_team_and_docker()

    async def collect_messages():
        with chat_container:
            async for msg in run(team, docker, task):
                if isinstance(msg, TextMessage):
                    if "user" in msg.source.lower():
                        with st.chat_message('user', avatar='👤'):
                            st.markdown(msg.content)
                    elif 'dsa' in msg.source.lower() or 'solver' in msg.source.lower():
                        with st.chat_message('assistant', avatar='🧑‍💻'):
                            st.markdown(msg.content)
                    elif 'code' in msg.source.lower() or 'executor' in msg.source.lower():
                        with st.chat_message('assistant', avatar='🐳'):
                            st.markdown("**Executed in Docker:**")
                            st.markdown(msg.content)
                    else:
                        with st.chat_message('assistant', avatar='🤖'):
                            st.markdown(msg.content)
                elif isinstance(msg, TaskResult):
                    with st.chat_message('assistant', avatar='✅'):
                        st.success(f"Execution finished automatically. System reported: {msg.stop_reason}")
                elif isinstance(msg, dict) and msg.get("type") == "error":
                    with st.chat_message('assistant', avatar='🚨'):
                        st.error(f"**An error occurred:** {msg['message']}", icon="🚨")
                        with st.expander("View detailed error logs"):
                            st.code(msg['traceback'], language="python")
                elif isinstance(msg, str) and msg.startswith('Error:'):
                    with st.chat_message('assistant', avatar='⚠️'):
                        st.error(msg, icon="⚠️")
    
    status_container = st.empty()
    with status_container.status("Agents are analyzing and executing...", expanded=True) as status:
        st.write("Initializing Docker and AutoGen agents...")
        asyncio.run(collect_messages())
        status.update(label="Problem Solved Successfully!", state="complete", expanded=False)