import argparse
import os
import pandas as pd
import importlib.util
from typing import TypedDict, List

# TODO: Import your LLM and LangGraph libraries
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langgraph.graph import StateGraph, END

# -- 1. Define the State for the Agent --
# This dictionary will hold the data that flows between the nodes of our agent.
class AgentState(TypedDict):
    target_bank: str
    pdf_path: str
    csv_path: str
    plan: str
    generated_code: str
    test_error: str
    attempts_left: int

# -- 2. Define the Agent Nodes (Functions) --

def plan_node(state: AgentState):
    """Node to create a plan for parsing the PDF."""
    print("---PLANNING---")
    # TODO: Create a prompt to ask the LLM to create a parsing plan.
    # The prompt should include context from the PDF/CSV.
    # Update state['plan'] with the LLM's response.
    state['plan'] = "1. Use pypdf to extract text.\n2. Use regex to find transaction lines.\n3. Load into pandas DataFrame."
    
    print(f"Generated Plan: {state['plan']}")
    return state

def code_gen_node(state: AgentState):
    """Node to generate Python code based on the plan."""
    print("---GENERATING CODE---")
    # TODO: Create a prompt for the LLM.
    # - If it's the first attempt, give it the plan.
    # - If it's a retry (state['test_error'] is not None), give it the previous code AND the error. [cite: 6, 14]
    # Update state['generated_code'] with the LLM's code response.
    # The generated code must contain a `parse(pdf_path)` function. 
    
    # Placeholder code for demonstration:
    state['generated_code'] = """
import pandas as pd
def parse(pdf_path: str) -> pd.DataFrame:
    # This is dummy code that needs to be replaced by the LLM
    print(f"Parsing {pdf_path}...")
    data = {'Date': ['01/01/2024'], 'Description': ['Test'], 'Amount': [100.0]}
    return pd.DataFrame(data)
"""
    print(f"Generated Code: \n{state['generated_code']}")
    return state

def test_node(state: AgentState):
    """Node to test the generated code."""
    print("---TESTING CODE---")
    state['attempts_left'] -= 1
    parser_path = os.path.join("custom_parsers", f"{state['target_bank']}_parser.py")

    try:
        # Dynamically load the generated code and get the parse function
        parser_path = os.path.join("custom_parsers", f"{state['target_bank']}_parser.py")
        with open(parser_path, "w", encoding="utf-8") as f:
            f.write(state['generated_code'])
        spec = importlib.util.spec_from_file_location("custom_parser", parser_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        parse_func = getattr(module, "parse")

        generated_df = parse_func(state['pdf_path'])
        expected_df = pd.read_csv(state['csv_path'])
        
        # v-- ADD THESE LINES HERE --v
        print("--- COMPARING DATAFRAMES ---")
        print("\nGenerated DF Info:")
        generated_df.info()
        print("\nExpected DF Info:")
        expected_df.info()
        # ^-- ADD THESE LINES HERE --^

        pd.testing.assert_frame_equal(generated_df, expected_df)
        print("---TEST PASSED---")
        state['test_error'] = None 
        
    except Exception as e:
        print(f"---TEST FAILED: {e}---")
        state['test_error'] = str(e)
        
    return state

# -- 3. Define the Graph's Logic --
def should_continue(state: AgentState):
    """Decision node to determine if we should retry or finish."""
    if state['test_error'] is None:
        return "end" # Test passed
    if state['attempts_left'] <= 0:
        print("---MAX ATTEMPTS REACHED---")
        return "end" # Max attempts reached 
    else:
        return "retry" # Test failed, retry

# TODO: Wire up the nodes into a LangGraph.
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)
workflow.add_node("planner", plan_node)
workflow.add_node("coder", code_gen_node)
workflow.add_node("tester", test_node)
workflow.set_entry_point("planner")
workflow.add_edge("planner", "coder")
workflow.add_edge("coder", "tester")
workflow.add_conditional_edges(
    "tester",
    should_continue,
    {
        "end": END,
        "retry": "coder"
    }
)
# app = workflow.compile()


# -- 4. Set up CLI and Run the Agent --
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI agent for parsing bank statements.")
    
    # v-- ADD THIS LINE --v
    parser.add_argument("--target", type=str, required=True, help="The target bank, e.g., 'icici'")
    # ^-- ADD THIS LINE --^
    args = parser.parse_args()

    # Make sure your LangGraph workflow is compiled into the 'app' variable
    app = workflow.compile() 

    initial_state = {
        "target_bank": args.target,
        "pdf_path": os.path.join("data", args.target, f"{args.target}_sample.pdf"),
        "csv_path": os.path.join("data", args.target, f"{args.target}_sample.csv"),
        "attempts_left": 3,
        "test_error": None
    }
    
    print(f"Running agent for target: {args.target}")
    
    # UNCOMMENT THE LINE BELOW TO RUN THE AGENT
    result = app.invoke(initial_state)
    
    print("---AGENT RUN COMPLETE---")
    print("Final State:")
    print(result) 