# ⚙️ AI-Driven AutoTestDesign Tool

**AutoTestDesign** is an intelligent, AI-powered software testing utility built to streamline the requirements analysis and test case generation process. It strictly aligns with **ISTQB Foundation Level** principles and the detailed test techniques defined in **ISO/IEC/IEEE standards**.

By leveraging the Google Gemini API, this tool automatically ingests raw software requirements, performs risk assessments, models state transitions, and generates optimized test suites. It also features interactive validation, allowing human testers to review and revise designs on the fly.

---

## ✨ Key Features (Assignment Requirements)

* **FR 1.0 (Input & Ingestion):** Supports direct user input, plain text, and file uploads (CSV) for software requirement ingestion.


* **FR 1.1 (Requirement Structuring):** Automatically parses and tokenizes raw text to identify key components such as Input Fields, Data Ranges, Conditions, and Expected Actions.


* **FR 2.0 (Risk Analysis & Prioritization):** Evaluates imported requirements to assign a Risk Score and a Test Priority (High, Medium, Low).


* **FR 3.0 (Black-Box Test Design):** Automatically applies at least three core Black-Box techniques from ISO 29119-4, including Equivalence Partitioning, Boundary Value Analysis, and Decision Tables.


* **FR 4.0 (White-Box Test Modeling):** Models system behavior using State Transition Diagrams and generates optimal test sequences for All States coverage.


* **FR 5.0 (Test Oracle Generation):** Synthesizes the Expected Result for given requirements and specific test data dynamically.


* **FR 6.0 (Output & Export):** Generates test artifacts (Test Cases, Test Suites, Risk Scores) in a structured CSV format suitable for import into Test Management Tools.


* **FR 7.0 (Test Suite Optimization):** Features optimization tools to prioritize or minimize the generated Test Suite based on risk or coverage efficiency.


* **Interactive Validation (Human-in-the-Loop):** Allows the designer to interactively review, revise, and change design items during the testing process.



---

## 🛠️ Technology Stack

* **Language:** Python 3.9+
* **Frontend UI:** Streamlit
* **AI Engine:** Google GenAI SDK (`gemini-2.5-flash`)
* **Data Processing:** Pandas
* **Graph/Modeling Logic:** NetworkX & Graphviz

---

## 🚀 Installation & Setup

### 1. Prerequisites

Ensure you have Python installed on your system. You will also need a free **Google Gemini API Key**.

### 2. Install Dependencies

Open your terminal and navigate to your project folder. Install the required Python libraries using `pip`:

```bash
pip install streamlit google-genai pandas networkx graphviz

```

### 3. Run the Application

Because this is a Streamlit application, it requires its own local server to run. Run the following command in your terminal:

```bash
streamlit run app.py

```

The application will automatically open in your default web browser at `http://localhost:8501`.

---

## 📖 Usage Guide

1. **Configure API:** Paste your Gemini API key into the secure sidebar configuration panel.
2. **Select Optimization:** Choose your preferred FR 7.0 optimization strategy from the sidebar dropdown (e.g., *Minimize Redundancy* or *Risk-Based*).
3. **Ingest Requirements:**
* **Direct Input Tab:** Paste raw software requirements into the text area.
* **File Upload Tab:** Upload a `.csv` or `.txt` file containing your requirements. If using a CSV, select the column that contains the requirement text.


4. **Generate Artifacts:** Click "Generate Initial Test Design Artifacts." The AI will break down the text, assign risk scores, and populate the testing tables.
5. **Iterate & Improve:** Review the generated suite. Type specific refinement instructions into the feedback box at the bottom of the app and click "Apply Feedback" to dynamically adjust the suite.
6. **Export:** Click the **Download Full Test Suite as CSV** button to export your final artifacts.

---

## ⚠️ Performance Note

The tool aims for rapid test case generation. However, due to the reliance on a cloud-based LLM API, network latency and token generation may occasionally impact execution times.
