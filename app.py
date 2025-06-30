import streamlit as st
import io
import ssl
import json
from mistralai.client import MistralClient
from PyPDF2 import PdfReader

# --- Mistral AI API Key (Hardcoded for testing only) ---
api_key = "H8guEVvToOt8VEIRCZSgHgtAMGmVg0Dy"

# --- AGGRESSIVE, INSECURE SSL BYPASS ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
    ssl._create_default_https_context = _create_unverified_https_context
except AttributeError:
    pass  # Older Python versions

# --- Initialize MistralClient ---
client = MistralClient(api_key=api_key)

# --- Prompt Definition ---
PN_LOGIC_PROMPT = """
You are an expert system for generating 15-digit part numbers for Cabin Attendant Seats (CAS).
Your task is to:
1. Analyze the text of the CAS Definition Document provided below. It contains information about various CAS models, types (WM/FM), and features.
2. For each CAS (e.g., CAS 11, CAS 13, CAS 37), extract:
   - Type (WM or FM)
   - Features like "PBE", "Handset", "Worklight", "Am-Safe", "Schroth", "Coat Hook"
3. Generate 15-digit part numbers based on strict logic.
4. Return output as a JSON like:
{
  "CAS 11": "2351WS4UAG44ED2",
  ...
}
"""

# --- Streamlit UI ---
st.set_page_config(page_title="CAS Part Number Generator", layout="centered")
st.title("🤖 CAS Part Number Generator")
st.markdown("Upload a CAS PDF document. The app will extract text and generate part numbers using LLM logic.")

uploaded_file = st.file_uploader("Upload CAS PDF Document", type="pdf")

if uploaded_file:
    pdf_reader = PdfReader(io.BytesIO(uploaded_file.read()))
    text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])

    if not text.strip():
        st.error("Could not extract any text from the PDF.")
        st.stop()

    full_prompt = PN_LOGIC_PROMPT + "\n\n" + "CAS Document Text:\n" + text

    with st.spinner("Sending text to LLM and generating part numbers..."):
        try:
            messages = [{"role": "user", "content": full_prompt}]

            response = client.chat(
                model="mistral-large-latest",
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            result = response.choices[0].message.content

            try:
                part_numbers = json.loads(result)
                st.success("✅ Part numbers generated!")
                for cas_id, pn in part_numbers.items():
                    st.markdown(f"**{cas_id}**: `{pn}`")
            except json.JSONDecodeError:
                st.error("❌ LLM did not return valid JSON. Raw output:")
                st.code(result)

        except Exception as e:
            st.error(f"❌ Error during LLM processing: {e}")
            st.info("Make sure your API key is valid and the PDF text is clean.")

st.markdown("---")
st.info("This test app uses Mistral AI and Streamlit. Do not use this setup in production due to hardcoded keys and insecure SSL bypass.")
