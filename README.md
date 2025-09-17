# Autonomous PDF Parser Agent

Manually extracting data from PDF bank statements is tedious and error-prone. This project introduces an intelligent AI agent that automates the entire process. It uses the Groq API and Llama 3.1 to autonomously write, test, and debug its own Python code, transforming any bank statement PDF into clean, structured data.

This agent was developed as a submission for the "Agent-as-Coder" Challenge.

---
## 🤖 Agent Logic & Architecture

At its core, the agent is a problem-solver. It follows a strategic loop: **Generate → Test → Refine**. This cycle allows it to learn from its mistakes and progressively build a perfect parser for any document format. If the AI-driven approach doesn't succeed after a few attempts, it deploys a reliable backup plan, ensuring you always get a working result.

The diagram below visualizes the agent's step-by-step decision-making process:

![flowchart](https://github.com/user-attachments/assets/01be56aa-0fad-45c7-bb27-6277cf5c4220)



The agent's workflow can be broken down into these key phases:

1.  **Setup & Context**: The agent begins by analyzing the sample PDF and the desired CSV output format to understand the parsing goal.
2.  **AI-Powered Generation**: It queries the LLM with a detailed prompt, requesting a custom Python parser. This is the "Generate" step.
3.  **Rigorous Validation**: The freshly generated code is immediately executed and its output is compared against the ground-truth CSV. This is the "Test" step.
4.  **Iterative Refinement**: If the test fails, the agent notes the error and loops back, asking the LLM for a better solution. This "Refine" cycle repeats up to three times.
5.  **Failsafe Mechanism**: If all AI attempts are exhausted, the agent activates a pre-built, deterministic parser to guarantee a functional output.
6.  **Final Output**: Once successful, the agent delivers the final Python parser file and a verified CSV of the extracted data.

---
## ▶️ Quick Start Guide

Get the agent up and running on your machine by following these steps.

### Prerequisites

* Python 3.10+
* A free API key from [Groq](https://console.groq.com/keys)

### Step 1: Get the Code

Clone the repository to your local machine and navigate into the project directory.

```bash
git clone <your-repository-url>
cd ai-agent-challenge
```

### Step 2: Create an Isolated Environment

Using a virtual environment is highly recommended to avoid conflicts with other projects.

```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install the Tools

Install all the necessary libraries with a single command.

```bash
pip install -r requirements.txt
```

### Step 4: Provide Your API Key

The agent needs your Groq API key to function. Create a `.env` file in the main project folder.

```
GROQ_API_KEY="your-groq-api-key-here"
```

### Step 5: Bring the Agent to Life

Run the agent from your terminal. For this example, we'll use the included `icici` bank data.

```bash
python agent.py --target icici
```
Watch as the agent generates and tests code. The final parser will appear in `custom_parsers/` and the data in `output/`.

### Step 6: Confirm the Results

You can run the included test suite to formally verify that the generated parser is 100% correct.

```bash
pytest
```

---
## ✨ Core Capabilities

* **AI-Powered Code Creation**: The agent doesn't use templates; it writes bespoke Python parsers in real-time, tailored to the specific document.
* **Automated Error Correction**: If its first attempt isn't perfect, the agent analyzes the failure and tries again with a better approach.
* **Adaptable to Any Bank**: Introduce a new PDF and CSV sample, change the `--target` flag, and the agent can learn a new format instantly.
* **Guaranteed Success**: A built-in, deterministic parser acts as a failsafe, ensuring you get a working result even in challenging cases.
* **Transparent & Trustworthy**: The agent produces both the final parser code and the extracted data in CSV format, so you can easily see and verify its work.

