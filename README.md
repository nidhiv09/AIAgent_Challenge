# ai-agent-challenge
Coding agent challenge which write custom parsers for Bank statement PDF.

Follow these 5 steps to set up the environment and run the agent:

# 1. Clone the Repository
git clone https://github.com/your-username/ai-agent-challenge.git
cd ai-agent-challenge

# 2. Install Dependencies (in a Virtual Environment)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt

# 3. Set Up API Key
# This command creates the .env file with your key.
# Replace 'your_api_key_here' with your actual Groq API key.
echo "GROQ_API_KEY='your_api_key_here'" > .env

# 4. Run the Agent to Generate the Parser
python agent.py --target icici

# 5. Verify the Output with Pytest
pytest