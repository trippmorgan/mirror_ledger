# dashboard.py
# A Streamlit front-end for The Mirror Ledger project.
# This UI communicates with the FastAPI backend via HTTP requests.

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# --- Configuration ---
# The base URL for your FastAPI backend.
# You can override this with an environment variable if needed.
import os
API_BASE_URL = os.getenv("MIRROR_LEDGER_API_URL", "http://127.0.0.1:8000")
ADAPTATION_THRESHOLD = 3 # As defined in your server's policy

st.set_page_config(
    page_title="Mirror Ledger Dashboard",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- API Helper Functions ---

def get_api_status():
    """Checks if the backend API is reachable."""
    try:
        response = requests.get(f"{API_BASE_URL}/validate", timeout=2)
        return "ok" in response.json().get("status", "")
    except requests.RequestException:
        return False

def get_chain():
    """Fetches the entire blockchain from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/chain")
        response.raise_for_status()
        return response.json().get("chain", [])
    except (requests.RequestException, json.JSONDecodeError) as e:
        st.error(f"Error fetching chain: {e}")
        return []

def post_intake_draft(trace_id: str, transcript: str, vitals: dict):
    """Posts a new clinical intake event to the API."""
    payload = {
        "trace_id": trace_id,
        "content": {
            "transcript": transcript,
            "vitals": vitals
        }
    }
    try:
        response = requests.post(f"{API_BASE_URL}/events/intake_drafted", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error creating event: {e.text}")
        return None

def post_feedback(block_index: int, feedback_delta: dict):
    """Posts feedback (approval or correction) to a specific block."""
    payload = {
        "block_index": block_index,
        "feedback_delta": feedback_delta
    }
    try:
        response = requests.post(f"{API_BASE_URL}/feedback", json=payload)
        response.raise_for_status()
        st.toast(f"✅ Feedback submitted for Block #{block_index}")
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error submitting feedback: {e.text}")
        return None

# --- Page Rendering ---

def render_playground():
    """Renders the main page for generating and reviewing AI outputs."""
    st.title("🔬 Clinical Playground")
    st.markdown("Generate a new AI-drafted note, review the reflection, and provide immediate feedback.")

    # Initialize session state for trace_id
    if "trace_id" not in st.session_state:
        st.session_state.trace_id = f"trace-{int(datetime.now().timestamp())}"

    with st.form(key="intake_form"):
        st.text_input("Workflow Trace ID", key="trace_id")
        transcript = st.text_area("Patient Transcript", height=150, placeholder="e.g., 'Patient complains of a pounding headache...'")
        vitals_str = st.text_input("Vitals", placeholder='e.g., {"bp": "130/85", "temp": "99.1F"}')
        submit_button = st.form_submit_button(label="🚀 Draft Intake & Reflect")

    if submit_button:
        if not transcript:
            st.warning("Please enter a transcript.")
        else:
            try:
                vitals = json.loads(vitals_str) if vitals_str else {}
            except json.JSONDecodeError:
                st.error("Invalid format for Vitals. Please use JSON.")
                return

            with st.spinner("AI is drafting and reflecting..."):
                new_block = post_intake_draft(st.session_state.trace_id, transcript, vitals)
                st.session_state.last_created_block = new_block

    # Display the result of the last creation
    if "last_created_block" in st.session_state and st.session_state.last_created_block:
        block = st.session_state.last_created_block
        block_index = block['index']
        content = block.get('data', {}).get('content', {})
        violations = block.get('feedback', {}).get('violations', [])

        st.markdown("---")
        st.subheader(f"AI Output (Block #{block_index})")

        if violations:
            st.warning(f"⚠️ **Reflection Flagged:** This output was generated with warnings. Violations: `{violations}`")
        else:
            st.success("✅ **Reflection Approved:** No violations detected.")

        with st.container(border=True):
            st.markdown("**Generated HPI Summary:**")
            st.write(content.get('hpi_summary', 'No summary generated.'))

        st.markdown("---")
        st.subheader("Human-in-the-Loop Feedback")
        
        # Feedback Widget
        if st.button("👍 Approve Note", key=f"approve_{block_index}"):
            feedback = {"status": "approved", "annotator": "did:clinic:dr_kay"}
            post_feedback(block_index, feedback)

        with st.form(key=f"correction_form_{block_index}"):
            correction_text = st.text_area("✏️ Submit Correction", key=f"correction_text_{block_index}")
            submit_correction = st.form_submit_button("Submit Correction")
            if submit_correction and correction_text:
                feedback = {"correction": correction_text}
                post_feedback(block_index, feedback)


def render_ledger_explorer():
    """Renders the page for viewing and searching the entire blockchain."""
    st.title("🔗 Ledger Explorer")
    st.markdown("View, search, and interact with the entire, immutable history of the system.")
    
    chain = st.session_state.get('chain_cache', [])

    # Filter controls
    search_trace_id = st.text_input("Filter by Trace ID")
    
    filtered_chain = [
        b for b in chain 
        if not search_trace_id or b.get('data', {}).get('trace_id') == search_trace_id
    ]

    if not filtered_chain:
        st.info("No blocks found or chain is empty.")
        return

    st.markdown(f"Displaying **{len(filtered_chain)}** of **{len(chain)}** total blocks.")

    # Display blocks in reverse chronological order
    for block in reversed(filtered_chain):
        block_index = block['index']
        event_type = block.get('data', {}).get('type', 'N/A')
        trace_id = block.get('data', {}).get('trace_id', 'N/A')

        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Block Index", f"#{block_index}")
            col2.metric("Event Type", event_type)
            col3.metric("Trace ID", trace_id)

            with st.expander("View Details & Provide Feedback"):
                st.json(block)
                st.markdown("---")
                st.write("**Provide Retrospective Feedback**")
                if st.button("👍 Approve", key=f"approve_retro_{block_index}"):
                    post_feedback(block_index, {"status": "approved", "annotator": "did:clinic:dr_kay_retro"})
                
                correction = st.text_area("✏️ Submit Correction", key=f"correction_retro_{block_index}")
                if st.button("Submit Correction", key=f"submit_retro_{block_index}"):
                    if correction:
                        post_feedback(block_index, {"correction": correction})


def render_adaptation_dashboard():
    """Renders the page for visualizing the model adaptation loop."""
    st.title("📈 Adaptation Dashboard")
    st.markdown("See how your feedback directly contributes to improving the AI model over time.")

    chain = st.session_state.get('chain_cache', [])
    if not chain:
        st.info("No data available.")
        return

    # Find the index of the last adaptation event
    last_adapt_index = -1
    for block in reversed(chain):
        if block.get('data', {}).get('type') == 'AdapterPromoted':
            last_adapt_index = block['index']
            break

    # Count corrections since the last adaptation
    corrections_since_last_adapt = 0
    for block in chain[last_adapt_index + 1:]:
        if "correction" in block.get("feedback", {}):
            corrections_since_last_adapt += 1
    
    st.subheader("Next Adaptation Progress")
    progress = min(corrections_since_last_adapt / ADAPTATION_THRESHOLD, 1.0)
    st.progress(progress)
    st.metric(
        label="Feedback for Next Adaptation Cycle",
        value=f"{corrections_since_last_adapt} / {ADAPTATION_THRESHOLD}",
        delta="Triggered!" if progress >= 1.0 else f"{ADAPTATION_THRESHOLD - corrections_since_last_adapt} more needed"
    )

    st.markdown("---")
    st.subheader("Adaptation History")
    
    adapt_events = [b for b in chain if b.get('data', {}).get('type') == 'AdapterPromoted']

    if not adapt_events:
        st.info("No adaptation events have occurred yet.")
    else:
        # Create a DataFrame for cleaner presentation
        history_data = {
            "Block #": [b['index'] for b in adapt_events],
            "Timestamp": [b['timestamp'] for b in adapt_events],
            "New Adapter": [b['data'].get('to', 'N/A') for b in adapt_events],
            "Triggering Policy": [b['data'].get('policy', 'N/A') for b in adapt_events]
        }
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


# --- Main App Logic ---

def main():
    """Main function to run the Streamlit app."""
    st.sidebar.title("✝️ The Mirror Ledger")

    # Check API status
    api_is_online = get_api_status()
    if api_is_online:
        st.sidebar.success("✅ Backend API is Online")
        # Cache the chain in session state to reduce API calls
        if 'chain_cache' not in st.session_state or st.sidebar.button('🔄 Refresh Data'):
            st.session_state.chain_cache = get_chain()
    else:
        st.sidebar.error("❌ Backend API is Offline")
        st.error("Could not connect to the Mirror Ledger API. Please ensure the FastAPI server is running.")
        st.stop()
    
    pages = {
        "🔬 Clinical Playground": render_playground,
        "🔗 Ledger Explorer": render_ledger_explorer,
        "📈 Adaptation Dashboard": render_adaptation_dashboard,
    }

    selection = st.sidebar.radio("Go to", pages.keys())
    page = pages[selection]
    page()

if __name__ == "__main__":
    main()