# AlgoGenie
Microsoft AutoGen — Multi-Agent DSA Solver
Complete Agent Context & Prompt Document

## PURPOSE OF THIS DOCUMENT
This document gives any AI agent complete project understanding without reading code files.
 
## SECTION 1 — PROJECT OVERVIEW  
**What is AlgoGenie?**
AlgoGenie is a multi-agent AI system built using Microsoft AutoGen framework (v0.4+). It solves Data Structures and Algorithms (DSA) problems by using two specialized AI agents that work together in a loop. It does NOT just suggest code — it actually RUNS the code inside a Docker container and verifies it works before showing it to the user.
It can also be used as a LeetCode problem solver. You give it a problem statement + function signature, and it returns a verified, working Python solution.

**What problem does it solve?**
* User gives a DSA problem in plain English (e.g. 'Write merge sort in Python')
* Agent explains the logic step by step
* Agent writes Python code for it
* Code is run in an isolated Docker container
* If there is an error, agent fixes it and tries again automatically
* Final working code is saved as solution.py
* Everything is shown in a clean Streamlit web UI

## SECTION 2 — AUTOGEN FRAMEWORK BASICS  
**Important: Which AutoGen to Use**
WARNING: Do NOT use 'from autogen import ...' — that is the OLD framework (now called AG2). The correct library is autogen-agentchat version 0.4+, maintained by Microsoft.
Correct pip install commands:
pip install autogen-agentchat
pip install autogen-core
pip install autogen-ext[docker]

**5 Core AutoGen Concepts Used in This Project**
| Concept | What It Means in This Project |
| :--- | :--- |
| Agent | An artificial worker with a specific job. Like a human specialist. |
| AssistantAgent | Smart agent connected to an LLM (GPT-4). Thinks, plans, writes code. |
| CodeExecutorAgent | Runs Python code. Has no LLM — it just executes and reports output/errors. |
| RoundRobinGroupChat | Team type where agents take turns: PSA → CEA → PSA → CEA... in order. |
| TextMentionTermination | Stops the team when a specific word (STOP) appears in any message. |

**How Agents Communicate**
Agents send messages to each other as text. AutoGen is built on async/await (asyncio). Messages flow like this:
1. User sends a task string to the Team
2. Team gives it to Problem Solver Agent (first in order)
3. Problem Solver Agent replies with explanation + Python code block
4. Code Executor Agent picks up the code block and runs it in Docker
5. If error: Code Executor sends error back → Problem Solver fixes code
6. If success: Problem Solver explains result and says STOP
7. TextMentionTermination detects STOP and ends the conversation

## SECTION 3 — PROJECT FILE STRUCTURE  
**Directory Layout**
```
algo_genie/
    config/
        settings.py        <-- creates OpenAI model client
        constants.py       <-- all config values in one place
        docker_utils.py    <-- start/stop Docker helpers
    agents/
        problem_solver.py  <-- AssistantAgent definition
        code_executor.py   <-- CodeExecutorAgent definition
    team/
        dsa_team.py        <-- combines agents into RoundRobin team
    main.py                <-- entry point for terminal run
    app.py                 <-- Streamlit web UI
    requirements.txt       <-- all pip dependencies
    .env                   <-- OPENAI_API_KEY stored here
```

**File-by-File Explanation**
| File | What it defines | Key content |
| :--- | :--- | :--- |
| constants.py | All magic values | MODEL = 'gpt-4', STOP_WORD = 'STOP', MAX_TURNS = 15, WORK_DIR = 'tmp' |
| settings.py | OpenAI client | Reads API key from .env, creates OpenAIChatCompletionClient with model from constants |
| docker_utils.py | Docker helpers | start_docker_container(docker) and stop_docker_container(docker) async functions |
| problem_solver.py | Smart agent | AssistantAgent named 'DSA_problem_solver_agent' with system prompt and GPT-4 |
| code_executor.py | Runner agent | CodeExecutorAgent with DockerCommandLineCodeExecutor, work_dir=tmp, timeout=120s |
| dsa_team.py | Team builder | RoundRobinGroupChat([problem_solver, code_executor], termination, max_turns=15) |
| main.py | Terminal entry | Gets team+docker, runs team.run_stream(task=...) in async loop, prints messages |
| app.py | Streamlit UI | st.text_input for problem, st.button to run, asyncio.run() to call team, renders messages |

## SECTION 4 — AGENT SYSTEM PROMPTS (FULL TEXT)  
**Problem Solver Agent — System Prompt**
This is the exact instruction given to the AssistantAgent. It controls ALL behaviour:

```text
You are a problem solver agent that is an expert in solving DSA problems.
You will be working with code executor agent to execute code.

You will be given a task. You should:
1. At the beginning of your response, specify your plan to solve the task.
2. Write code to solve the task. Your code shall be ONLY in Python.
3. Give the code in a single code block (use ```python ... ``` format).
4. Pass the code to code executor agent to execute it.
5. Make sure to have at least 3 test cases for the code you write.

Once the code is executed and if the same has been done successfully,
you should explain the code execution result.

You should also ask the code executor agent to save the code in a file.
Use the following format to save:

```python
code = '''
<your complete solution code here>
'''
with open('solution.py', 'w') as f:
    f.write(code)
print('Code saved successfully!')
```

In the end, once the code is executed successfully, you MUST say: STOP

Note: The word STOP is the termination trigger. The moment it appears in any message, the team stops.
```

**Code Executor Agent — System Prompt**
The CodeExecutorAgent has NO LLM and NO custom system prompt. It simply receives messages containing Python code blocks (` ```python ... ``` `) and runs them inside Docker. It returns stdout output or error messages back to the team.

## SECTION 5 — ACTUAL CODE SKELETONS  

**constants.py**
```python
MODEL = 'gpt-4'
STOP_WORD = 'STOP'
WORK_DIR = 'tmp'
TIMEOUT = 120
MAX_TURNS = 15
```

**settings.py**
```python
import os
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from config.constants import MODEL

load_dotenv()

def get_model_client():
    return OpenAIChatCompletionClient(
        model=MODEL,
        api_key=os.getenv('OPENAI_API_KEY')
    )
```

**docker_utils.py**
```python
async def start_docker_container(docker):
    print('Starting Docker container...')
    await docker.start()

async def stop_docker_container(docker):
    print('Stopping Docker container...')
    await docker.stop()
```

**problem_solver.py**
```python
from autogen_agentchat.agents import AssistantAgent
from config.settings import get_model_client

def get_problem_solver_agent():
    model_client = get_model_client()
    return AssistantAgent(
        name='DSA_problem_solver_agent',
        description='An agent that solves DSA problems',
        model_client=model_client,
        system_message=<FULL SYSTEM PROMPT FROM SECTION 4>
    )
```

**code_executor.py**
```python
from autogen_agentchat.agents import CodeExecutorAgent
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from config.constants import WORK_DIR, TIMEOUT

def get_code_executor_agent():
    docker = DockerCommandLineCodeExecutor(
        image='python:3-slim',
        work_dir=WORK_DIR,
        timeout=TIMEOUT
    )
    agent = CodeExecutorAgent(
        name='code_executor_agent',
        code_executor=docker
    )
    return agent, docker
```

**dsa_team.py**
```python
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from agents.problem_solver import get_problem_solver_agent
from agents.code_executor import get_code_executor_agent
from config.constants import STOP_WORD, MAX_TURNS

def get_dsa_team():
    problem_solver = get_problem_solver_agent()
    code_executor, docker = get_code_executor_agent()
    termination = TextMentionTermination(STOP_WORD)
    team = RoundRobinGroupChat(
        participants=[problem_solver, code_executor],
        termination_condition=termination,
        max_turns=MAX_TURNS
    )
    return team, docker
```

**main.py**
```python
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult
from team.dsa_team import get_dsa_team
from config.docker_utils import start_docker_container, stop_docker_container

async def main():
    team, docker = get_dsa_team()
    task = 'Write a Python function to add two numbers'
    try:
        await start_docker_container(docker)
        async for message in team.run_stream(task=task):
            if isinstance(message, TextMessage):
                print(f'{message.source}: {message.content}')
            elif isinstance(message, TaskResult):
                print(f'STOP reason: {message.stop_reason}')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await stop_docker_container(docker)

if __name__ == '__main__':
    asyncio.run(main())
```

## SECTION 6 — STREAMLIT UI (app.py)  
**How the Frontend Works**
The Streamlit UI (app.py) wraps the exact same backend logic but shows messages in a browser. Key things:
* st.text_input() takes the DSA problem from the user
* st.button('Run') triggers the agent team via asyncio.run()
* Messages are yielded one by one (generator pattern) using 'async for' + 'yield'
* Different message sources get different st.chat_message() styles
* 'user' messages show with a human icon
* 'DSA_problem_solver_agent' messages show with a brain/AI icon
* 'code_executor_agent' messages show with a robot/gear icon
* TaskResult (stop message) shows with a checkmark icon

**Important app.py Pattern**
The UI uses a generator function to yield messages as they come in real time:
```python
async def run(team, docker, task):
    async for message in team.run_stream(task=task):
        yield message.source, message.content  # one at a time

async def collect_messages():
    team, docker = get_dsa_team()
    try:
        await start_docker_container(docker)
        async for source, content in run(team, docker, task):
            # render in streamlit based on source name
            if source.startswith('user'):
                st.chat_message('user').markdown(content)
            elif source.startswith('DSA'):
                st.chat_message('assistant').markdown(content)
            elif source.startswith('code'):
                st.chat_message('assistant', avatar='🤖').markdown(content)
    finally:
        await stop_docker_container(docker)

# In the button click handler:
if st.button('Run'):
    asyncio.run(collect_messages())
```

## SECTION 7 — DOCKER CONTAINER DETAILS  
**Why Docker is Used**
The Code Executor Agent runs all Python code inside a Docker container — NOT directly on the host machine. This is intentional for safety and isolation.
* Safety: if the LLM generates bad code (e.g. 'delete all files'), it only affects the container
* Cleanliness: no leftover files or state on the host system
* Reproducibility: always a fresh Python environment

**Docker Configuration**
| Setting | Value / Notes |
| :--- | :--- |
| Image | python:3-slim (minimal Python 3 image) |
| Work Directory | /tmp inside container |
| Timeout | 120 seconds per code execution |
| Start | Called before team.run_stream() begins |
| Stop | Called in 'finally' block — always runs even on error |
| solution.py saved at | /tmp/solution.py inside container |

Important: Docker must be running on the host machine before starting the app. The container starts and stops with each request.

## SECTION 8 — FULL AGENT INTERACTION EXAMPLE  
**Example: User asks 'Write selection sort in Python'**
| Turn | Agent | What it does |
| :--- | :--- | :--- |
| 1 | DSA_problem_solver_agent | Explains selection sort algorithm. Writes Python code block with 3 test cases. |
| 2 | code_executor_agent | Runs the code in Docker. If no print() → reports 'script ran but produced no output'. |
| 3 | DSA_problem_solver_agent | Sees the error. Adds print() statements. Sends corrected code block. |
| 4 | code_executor_agent | Runs corrected code. Output is correct. Reports success. |
| 5 | DSA_problem_solver_agent | Explains the result. Sends code-saving block. Says STOP. |
| — | TextMentionTermination | Detects STOP. Team ends. solution.py saved in /tmp. |

**Common Error Cases Handled Automatically**
* No output: Agent adds print() statements and retries
* IndentationError: Agent fixes indentation and retries
* NameError / TypeError: Agent corrects the logic and retries
* ImportError: Agent removes or replaces unavailable imports
* Infinite loop: Docker timeout (120s) kills it, agent gets error message

## SECTION 9 — SETUP & REQUIREMENTS  
**requirements.txt**
```
autogen-agentchat
autogen-core
autogen-ext[docker]
openai
python-dotenv
asyncio
streamlit
```

**Setup Steps**
1. Install Docker Desktop and make sure it is running
2. Create virtual environment: python -m venv envgenie
3. Activate: source envgenie/bin/activate
4. Install: pip install -r requirements.txt
5. Create .env file and add: OPENAI_API_KEY=your_key_here
6. Run terminal version: python main.py
7. Run web UI: streamlit run app.py

## SECTION 10 — INSTRUCTIONS FOR ANY AGENT READING THIS  
If you are an AI agent reading this document, here is how to work with this project:
* To understand the flow: Read Sections 1, 2, and 8 first
* To modify an agent's behaviour: Edit the system prompt in Section 4, then update problem_solver.py
* To add a new agent: Create a new file in agents/, import in dsa_team.py, add to participants list
* To change the LLM model: Update MODEL value in constants.py only — it propagates everywhere
* To change stop word: Update STOP_WORD in constants.py AND the system prompt in Section 4
* To change max turns: Update MAX_TURNS in constants.py
* To support a new language (e.g. Java): Change system prompt to say 'code shall be only in Java' and update Docker image to one with Java
* To test without Streamlit: Run python main.py from the algo_genie/ directory
* If Docker not starting: Make sure Docker Desktop app is open and running on the host machine
* If 'module not found': Make sure virtual environment is activated before running

**What NOT to do:**
* Do NOT use 'from autogen import ...' — this is the wrong/old library (AG2)
* Do NOT hardcode the API key — always use .env file
* Do NOT add unicode bullets manually in docx (use LevelFormat.BULLET)
* Do NOT change agent order in participants[] — problem_solver must be first
* Do NOT run code directly on host — always use DockerCommandLineCodeExecutor
