import streamlit as st
from google import genai
import json
import pandas as pd
import networkx as nx

class AutoTestDesignEngine:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'
        self.system_prompt = """
        You are an expert QA Engineer following ISTQB and ISO 29119-4 standards.
        Output ONLY a valid JSON object. Do not include markdown formatting like ```json.
        JSON Structure exactly like this:
        {
            "parsed_requirement": { "components": ["List of identified inputs, ranges, and conditions"] },
            "risk_analysis": { "score": 8, "priority": "High", "justification": "Brief reason" },
            "black_box_tests": [
                { "id": "TC_BB_001", "technique": "BVA", "input": "Specific test data", "expected_oracle": "Expected result", "type": "Positive" }
            ],
            "state_transitions": [
                { "source": "State_A", "target": "State_B", "trigger": "Action that causes transition" }
            ]
        }
        """

    def _call_model(self, prompt: str) -> dict:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            # Clean up potential markdown wrapping just in case
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            st.error(f"Failed to generate or parse response. Error: {e}")
            return None

    def analyze_and_generate(self, raw_requirement: str) -> dict:
        prompt = f"""
        {self.system_prompt}
        Analyze the following software requirement(s):
        "{raw_requirement}"
        """
        return self._call_model(prompt)

    def refine_artifacts(self, raw_requirement: str, current_json: dict, user_feedback: str) -> dict:
        """Takes the existing test suite and modifies it based on user feedback."""
        prompt = f"""
        {self.system_prompt}
        
        Original Requirement: "{raw_requirement}"
        
        Current Test Suite JSON:
        {json.dumps(current_json)}
        
        USER FEEDBACK / INSTRUCTIONS FOR IMPROVEMENT:
        "{user_feedback}"
        
        Apply the user's feedback to improve, expand, or fix the Current Test Suite. 
        Return the ENTIRE updated suite following the exact required JSON structure.
        """
        return self._call_model(prompt)

    def optimize_test_suite(self, test_cases: list, optimization_strategy: str) -> list:
        if not test_cases: return []
        df = pd.DataFrame(test_cases)
        
        if optimization_strategy == "Minimize Redundancy":
            optimized_df = df.drop_duplicates(subset=['technique', 'type'], keep='first')
        elif optimization_strategy == "Risk-Based (High/Medium Only)":
            optimized_df = df[df['technique'].isin(['BVA', 'Decision Table'])]
            if optimized_df.empty: optimized_df = df 
        else:
            optimized_df = df
            
        return optimized_df.to_dict('records')

    def generate_state_diagram_dot(self, transitions: list) -> str:
        if not transitions: return ""
        dot = "digraph StateMachine {\n  rankdir=LR;\n  node [shape = rectangle, style=filled, fillcolor=lightblue];\n"
        for t in transitions:
            dot += f'  "{t["source"]}" -> "{t["target"]}" [label="{t["trigger"]}"];\n'
        dot += "}"
        return dot

    def generate_white_box_test_cases(self, transitions: list) -> list:
        if not transitions: return []
        G = nx.DiGraph()
        for t in transitions: G.add_edge(t['source'], t['target'], trigger=t['trigger'])
        
        start_nodes = [n for n, d in G.in_degree() if d == 0] or list(G.nodes())[:1]
        dead_ends = [n for n, d in G.out_degree() if d == 0] or list(G.nodes())
        
        wb_tests = []
        tc_counter = 1
        
        for start in start_nodes:
            for end in dead_ends:
                if start != end:
                    for path in nx.all_simple_paths(G, source=start, target=end):
                        path_str = [f"{path[i]} --[{G[path[i]][path[i+1]]['trigger']}]--> {path[i+1]}" for i in range(len(path)-1)]
                        full_path = "  =>  ".join(path_str)
                        
                        wb_tests.append({
                            "id": f"TC_WB_{tc_counter:03d}",
                            "technique": "State Transition",
                            "input": f"Sequence: {full_path}",
                            "expected_oracle": f"Halt at: {end}",
                            "type": "White-Box"
                        })
                        tc_counter += 1
        return wb_tests

# --- Streamlit UI Setup ---
st.set_page_config(page_title="AutoTestDesign AI", layout="wide")

# Initialize Session State variables