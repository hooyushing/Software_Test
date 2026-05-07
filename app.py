import streamlit as st
from google import genai
import json
import pandas as pd
import networkx as nx

class AutoTestDesignEngine:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'
        # UPDATED: The prompt now demands an array of 'analyzed_requirements'
        self.system_prompt = """
        You are an expert QA Engineer following ISTQB and ISO 29119-4 standards.
        Output ONLY a valid JSON object. Do not include markdown formatting like ```json.
        JSON Structure exactly like this:
        {
            "analyzed_requirements": [
                {
                    "requirement_snippet": "A short 5-10 word snippet of the requirement",
                    "parsed_components": ["List of identified inputs, ranges, and conditions"],
                    "risk_analysis": { "score": 8, "priority": "High", "justification": "Brief reason" },
                    "black_box_tests": [
                        { "id": "TC_BB_001", "technique": "BVA", "input": "Specific test data", "expected_oracle": "Expected result", "type": "Positive" }
                    ],
                    "state_transitions": [
                        { "source": "State_A", "target": "State_B", "trigger": "Action that causes transition" }
                    ]
                }
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
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            st.error(f"Failed to generate or parse response. Error: {e}")
            return None

    def analyze_and_generate(self, raw_requirement: str) -> dict:
        prompt = f"""
        {self.system_prompt}
        Analyze the following software requirement(s) individually:
        "{raw_requirement}"
        """
        return self._call_model(prompt)

    def refine_artifacts(self, raw_requirement: str, current_json: dict, user_feedback: str) -> dict:
        prompt = f"""
        {self.system_prompt}
        Original Requirement: "{raw_requirement}"
        Current Test Suite JSON: {json.dumps(current_json)}
        USER FEEDBACK: "{user_feedback}"
        Apply the user's feedback. Return the ENTIRE updated suite following the exact required JSON structure.
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

if 'results' not in st.session_state:
    st.session_state.results = None
if 'current_requirement' not in st.session_state:
    st.session_state.current_requirement = ""

st.title("⚙️ AI-Driven AutoTestDesign Tool")
st.markdown("*(Aligns with ISTQB Foundation Level & ISO 29119-4 Standards)*")

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Google Gemini API Key", type="password")
    st.markdown("[Get an API key here](https://aistudio.google.com/app/apikey)")
    st.divider()
    optimization_choice = st.selectbox(
        "FR 7.0: Test Suite Optimization",
        ("None", "Minimize Redundancy", "Risk-Based (High/Medium Only)")
    )
    if st.button("Reset Session", type="secondary"):
        st.session_state.results = None
        st.session_state.current_requirement = ""
        st.rerun()

st.subheader("FR 1.0: Ingest Software Requirements")
tab1, tab2 = st.tabs(["📝 Direct Input", "📁 File Upload (CSV/TXT)"])

final_requirement_text = ""

with tab1:
    req_input = st.text_area(
        "Paste your software requirement here:", 
        "Example:\n1. The system must accept codes that are exactly 8 chars long.\n2. Passwords must contain a special character.",
        height=100
    )
    if req_input: final_requirement_text = req_input

with tab2:
    uploaded_file = st.file_uploader("Upload a requirement file", type=['csv', 'txt'])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            target_col = st.selectbox("Select column containing requirements:", df.columns)
            # UPDATED: Number each row so the AI knows they are distinct requirements
            req_list = df[target_col].dropna().astype(str).tolist()
            final_requirement_text = "\n".join([f"Req {i+1}: {text}" for i, text in enumerate(req_list)])
        elif uploaded_file.name.endswith('.txt'):
            final_requirement_text = uploaded_file.read().decode("utf-8")

st.divider()

if st.button("Generate Initial Test Design Artifacts", type="primary"):
    if not api_key:
        st.warning("Please enter your Gemini API Key in the sidebar.")
    elif not final_requirement_text.strip():
        st.warning("Please provide a requirement.")
    else:
        with st.spinner("Analyzing requirements and generating initial artifacts..."):
            engine = AutoTestDesignEngine(api_key=api_key)
            st.session_state.current_requirement = final_requirement_text
            st.session_state.results = engine.analyze_and_generate(final_requirement_text)

if st.session_state.results:
    results = st.session_state.results
    engine = AutoTestDesignEngine(api_key=api_key)
    
    # Extract the array of requirements
    reqs_array = results.get("analyzed_requirements", [])
    
    # --- UPDATED FR 1.1 & 2.0 UI: Render a Table instead of a single metric ---
    st.success("### FR 1.1 & 2.0: Risk Analysis & Component Parsing (Per Requirement)")
    
    risk_table_data = []
    all_bb_tests = []
    all_transitions = []
    
    for req in reqs_array:
        # Build Risk Table Row
        risk_table_data.append({
            "Requirement Snippet": req.get("requirement_snippet", ""),
            "Risk Score": req.get("risk_analysis", {}).get("score", "N/A"),
            "Priority": req.get("risk_analysis", {}).get("priority", "N/A"),
            "Justification": req.get("risk_analysis", {}).get("justification", ""),
            "Parsed Components": ", ".join(req.get("parsed_components", []))
        })
        
        # Aggregate Tests for the lower sections, adding the snippet so we know which req it belongs to
        for t in req.get("black_box_tests", []):
            t["Source Req"] = req.get("requirement_snippet", "")
            all_bb_tests.append(t)
            
        all_transitions.extend(req.get("state_transitions", []))

    # Display the new Risk Analysis Table
    if risk_table_data:
        df_risk = pd.DataFrame(risk_table_data)
        st.dataframe(df_risk, use_container_width=True)
    else:
        st.warning("No requirements were successfully parsed.")

    st.divider()

    st.subheader("FR 3.0 & 5.0: Black-Box Test Cases")
    optimized_bb_tests = engine.optimize_test_suite(all_bb_tests, optimization_choice)
    df_bb_tests = pd.DataFrame(optimized_bb_tests)
    # Reorder columns to put Source Req first
    if not df_bb_tests.empty and "Source Req" in df_bb_tests.columns:
        cols = ["Source Req"] + [col for col in df_bb_tests.columns if col != "Source Req"]
        df_bb_tests = df_bb_tests[cols]
    st.dataframe(df_bb_tests, use_container_width=True)

    st.divider()

    st.subheader("FR 4.0: White-Box Test Modeling & Cases")
    col_diagram, col_table = st.columns([1, 2])
    
    with col_diagram:
        st.write("**Visual State Transition Diagram**")
        dot_source = engine.generate_state_diagram_dot(all_transitions)
        if dot_source: st.graphviz_chart(dot_source)
        else: st.write("No distinct states identified.")

    with col_table:
        st.write("**Generated White-Box Test Cases (All-Paths Coverage)**")
        wb_tests = engine.generate_white_box_test_cases(all_transitions)
        df_wb_tests = pd.DataFrame(wb_tests)
        if not df_wb_tests.empty: st.dataframe(df_wb_tests, use_container_width=True)
        else: st.write("No distinct paths identified.")

    st.divider()

    st.subheader("🗣️ Iterate & Improve")
    st.markdown("Not satisfied with the suite? Tell the AI what to change, add, or remove.")
    
    user_feedback = st.text_input("e.g., 'Make the risk scores higher', 'Add negative test cases'")
    
    if st.button("Apply Feedback", type="secondary"):
        with st.spinner("Refining test suite based on your feedback..."):
            updated_results = engine.refine_artifacts(
                st.session_state.current_requirement, 
                st.session_state.results, 
                user_feedback
            )
            if updated_results:
                st.session_state.results = updated_results
                st.rerun()

    st.divider()

    st.subheader("FR 6.0: Consolidated Artifact Export")
    if not df_wb_tests.empty:
        final_df = pd.concat([df_bb_tests, df_wb_tests], ignore_index=True)
    else:
        final_df = df_bb_tests
        
    csv = final_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Full Test Suite as CSV",
        data=csv,
        file_name='master_test_suite.csv',
        mime='text/csv',
    )