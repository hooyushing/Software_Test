import streamlit as st
from google import genai

# --- UI Configuration ---
st.set_page_config(page_title="QA Test Case Generator", page_icon="🧪", layout="centered")

st.title("🧪 EP & BVA Test Case Generator")
st.write("Upload your software requirements to automatically generate Equivalence Partitioning (EP) and Boundary Value Analysis (BVA) test cases.")

# --- Sidebar for API Key ---
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Gemini API Key", type="password", help="Get your API key from Google AI Studio.")
    st.markdown("[Get an API Key here](https://aistudio.google.com/app/apikey)")

# --- Main Input Area ---
st.subheader("1. Input Requirements")
input_method = st.radio("Choose input method:", ("Upload .txt file", "Paste text"))

requirements_text = ""

if input_method == "Upload .txt file":
    uploaded_file = st.file_uploader("Choose a requirements file", type=["txt"])
    if uploaded_file is not None:
        requirements_text = uploaded_file.getvalue().decode("utf-8")
        with st.expander("Preview Uploaded Requirements"):
            st.write(requirements_text)
else:
    requirements_text = st.text_area("Paste your requirements here:", height=150)

# --- Generation Logic ---
st.subheader("2. Generate Test Cases")
if st.button("Generate QA Report", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
    elif not requirements_text.strip():
        st.error("⚠️ Please provide some requirements to analyze.")
    else:
        try:
            # Configure the NEW client
            client = genai.Client(api_key=api_key)
            
            system_prompt = """
            You are a Senior Quality Assurance Engineer. Your task is to analyze the provided software requirements 
            and generate comprehensive test cases specifically using Equivalence Partitioning (EP) and 
            Boundary Value Analysis (BVA) techniques.
            
            Format your output strictly as a Markdown table with the following columns:
            - Test Case ID (e.g., TC-001)
            - Technique (EP or BVA)
            - Description
            - Input Data
            - Expected Result
            
            Ensure you cover both valid and invalid partitions/boundaries.
            """
            
            full_prompt = f"{system_prompt}\n\nHere are the requirements to analyze:\n\n{requirements_text}"
            
            with st.spinner("Analyzing requirements and writing test cases... ⏳"):
                # Call Gemini API using the new syntax
                response = client.models.generate_content(
                    model='gemini-3.1-pro-preview',
                    contents=full_prompt
                )
            
            # Display Results
            st.success("✅ Generation Complete!")
            st.markdown("---")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")