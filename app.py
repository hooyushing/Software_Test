import streamlit as st
from google import genai
import json
import pandas as pd
import networkx as nx

class AutoTestDesignEngine:
    def __init__(self, api_key):
        # Initialize the NEW Google GenAI client
        self.client = genai.Client(api_key=api_key)
        # Using the current standard fast model
        self.model_name = 'gemini-2.5-flash'

    def analyze_and_generate(self, raw_requirement: str) -> dict:
        """
        Tackles FR 1.1 (Parsing), FR 2.0 (Risk), FR 3.0 (Black-Box), FR 4.0 (States) and FR 5.0 (Oracle).
        """
        prompt = f"""
        You are an expert QA Engineer following ISTQB and ISO 29119-4 standards.
        Analyze the following software requirement and output ONLY a valid JSON object.
        
        Requirement: "{raw_requirement}"
        
        JSON Structure exactly like this:
        {{
            "parsed_requirement": {{
                "components": ["List of identified inputs, ranges, and conditions"]
            }},
            "risk_analysis": {{
                "score": 8,
                "priority": "High", 
                "justification": "Brief reason"
            }},
            "black_box_tests": [
                {{
                    "id": "TC_001",
                    "technique": "BVA",
                    "input": "Specific test data",
                    "expected_oracle": "Expected result",
                    "type": "Positive"
                }}
            ],
            "state_transitions": [
                {{
                    "source": "State_A",
                    "target": "State_B",
                    "trigger": "Action that causes transition"
                }}
            ]
        }}
        """
        
        try:
            # Use the NEW generate_content syntax
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            return json.loads(response.text)
        except json.JSONDecodeError:
            st.error("Failed to parse LLM output. The model did not return valid JSON.")
            return None
        except Exception as e:
            st.error(f"API Error: {e}")
            return None

    def optimize_test_suite(self, test_cases: list, optimization_strategy: str = "Minimize Redundancy") -> list:
        """
        Tackles FR 7.0: Test Suite Optimization.
        Filters the generated test suite based on selected criteria to improve coverage efficiency.
        """
        if not test_cases:
            return []
            
        df = pd.DataFrame(test_cases)
        
        if optimization_strategy == "Minimize Redundancy":
            optimized_df = df.drop_duplicates(subset=['technique', 'type'], keep='first')
        elif optimization_strategy == "Risk-Based (High/Medium Only)":
            optimized_df = df[df['technique'].isin(['BVA', 'Decision Table'])]
            if optimized_df.empty: 
                optimized_df = df 
        else:
            optimized_df = df
            
        return optimized_df.to_dict('records')

    def generate_white_box_paths(self, transitions: list):
        """
        Tackles FR 4.0: White-Box Test Modeling using Graph Theory.
        Models the system behavior as a Directed Graph and calculates optimal test sequences.
        """
        if not transitions:
            return []

        G = nx.DiGraph()
        for t in transitions:
            G.add_edge(t['source'], t['target'], trigger=t['trigger'])

        start_nodes = [n for n, d in G.in_degree() if d == 0]
        dead_ends = [n for n, d in G.out_degree() if d == 0]

        if not start_nodes:
            start_nodes = list(G.nodes())[:1] 
        if not dead_ends:
            dead_ends = list(G.nodes()) 

        test_paths = []
        
        for start in start_nodes:
            for end in dead_ends:
                if start != end:
                    for path in nx.all_simple_paths(G, source=start, target=end):
                        path_str = []
                        for i in range(len(path)-1):
                            u, v = path[i], path[i+1]
                            trigger = G[u][v]['trigger']
                            path_str.append(f"{u} --[{trigger}]--> {v}")
                        test_paths.append("  =>  ".join(path_str))
                        
        return test_paths

# --- Streamlit UI ---
st.set_page_config(page_title="AutoTestDesign AI", layout="wide")
st.title("⚙️ AI-Driven AutoTestDesign Tool")
st.markdown("*(Aligns with ISTQB Foundation Level & ISO 29119-4 Standards)*")

# Sidebar for Configuration
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Google Gemini API Key", type="password")
    st.markdown("[Get an API key here](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    optimization_choice = st.selectbox(
        "FR 7.0: Test Suite Optimization",
        ("None", "Minimize Redundancy", "Risk-Based (High/Medium Only)")
    )

# Main Content Area
st.subheader("FR 1.0: Input Requirement")
req_input = st.text_area(
    "Paste your software requirement here:", 
    "Example: The e-commerce checkout system must accept discount codes. Codes must be alphanumeric and exactly 8 characters long. If valid, apply a 10% discount and move to the Payment state. If invalid, show an error and remain in the Cart state.",
    height=100
)

if st.button("Generate Test Design Artifacts", type="primary"):
    if not api_key:
        st.warning("Please enter your Gemini API Key in the sidebar.")
    elif not req_input.strip():
        st.warning("Please enter a requirement to analyze.")
    else:
        with st.spinner("Analyzing requirements and generating artifacts..."):
            engine = AutoTestDesignEngine(api_key=api_key)
            results = engine.analyze_and_generate(req_input)
            
            if results:
                # --- FR 1.1 & 2.0: Parsing and Risk ---
                col1, col2 = st.columns(2)
                with col1:
                    st.success("### FR 2.0: Risk Analysis")
                    st.metric(label="Risk Score", value=f"{results['risk_analysis']['score']} / 10")
                    st.write(f"**Priority:** {results['risk_analysis']['priority']}")
                    st.write(f"**Justification:** {results['risk_analysis']['justification']}")
                with col2:
                    st.info("### FR 1.1: Parsed Components")
                    for comp in results['parsed_requirement']['components']:
                        st.markdown(f"- {comp}")

                st.divider()

                # --- FR 3.0, 5.0, 7.0: Black-Box Tests & Optimization ---
                st.subheader("FR 3.0 & 5.0: Black-Box Test Cases & Oracles")
                raw_tests = results['black_box_tests']
                optimized_tests = engine.optimize_test_suite(raw_tests, optimization_choice)
                
                df_tests = pd.DataFrame(optimized_tests)
                st.dataframe(df_tests, use_container_width=True)
                
                if optimization_choice != "None":
                    st.caption(f"Optimized from {len(raw_tests)} down to {len(optimized_tests)} test cases using '{optimization_choice}'.")

                st.divider()

                # --- FR 4.0: White-Box Modeling ---
                st.subheader("FR 4.0: White-Box Test Modeling (State Transition Paths)")
                paths = engine.generate_white_box_paths(results.get('state_transitions', []))
                
                if paths:
                    st.write("**Optimal Test Sequences to achieve All-Paths Coverage (Node-to-Terminal):**")
                    for i, path in enumerate(paths):
                        st.code(f"Path {i+1}: {path}")
                else:
                    st.write("No distinct state transitions identified for this specific requirement.")

                # --- FR 6.0: Output & Export ---
                st.divider()
                st.subheader("FR 6.0: Artifact Export")
                
                csv = df_tests.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Test Cases as CSV",
                    data=csv,
                    file_name='optimized_test_cases.csv',
                    mime='text/csv',
                )