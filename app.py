import streamlit as st
import base64
import io
import httpx # Required for the MistralClient's internal HTTP operations
from mistralai.client import MistralClient # Use the client from mistralai.client
import ssl # Import the ssl module for context patching

# --- Mistral AI API Key (Hardcoded for testing simplicity) ---
# WARNING: This exposes your API key in public code. Use ONLY for temporary, free/test API keys.
api_key = "VYFuAzmpanni9GvQjQBoVuwRylMd7IOa" # Your API key, hardcoded here.

if api_key == "YOUR_ACTUAL_MISTRAL_AI_API_KEY_GOES_HERE" or not api_key:
    st.error("Error: Mistral AI API Key is not set. Please replace 'YOUR_ACTUAL_MISTRAL_AI_API_KEY_GOES_HERE' in app.py with your key.")
    st.stop()

# --- AGGRESSIVE, INSECURE SSL BYPASS (LAST RESORT) ---
# WARNING: This completely disables SSL certificate verification for ALL httpx connections
# by patching the default SSL context. This is EXTREMELY INSECURE for production.
# Use ONLY for temporary testing in controlled environments where you accept the risks.
try:
    _create_unverified_https_context = ssl._create_unverified_context
    ssl._create_default_https_context = _create_unverified_https_context
except AttributeError:
    pass # Fallback for older Python versions if _create_unverified_context is not available

# --- Initialize MistralClient (simplest possible initialization) ---
# Removed httpx_client=... argument, relying solely on global SSL patch.
client = MistralClient(api_key=api_key)


# --- Define the Part Number Generation Logic (as text for the LLM) ---
PN_LOGIC_PROMPT = """
You are an expert system for generating 15-digit part numbers for Cabin Attendant Seats (CAS).
Your task is to:
1.  **Analyze the provided PDF document.** This PDF is a 'CAS Definition Document' and contains information about various Cabin Attendant Seat (CAS) models, including their type (Wall-mounted 'WM' or Floor-mounted 'FM') and specific features listed in tables (Headrest Features, Other Features).
2.  **For each distinct CAS location (e.g., CAS 11, CAS 13, CAS 33, CAS 37, etc.) identified in the PDF, extract the following key information:**
    * Its type (WM or FM).
    * The presence or absence of these specific features:
        * "PBE" (Protective Breathing Equipment stowage)
        * "Handset" (e.g., "Handset with Phone cord")
        * "Worklight" (e.g., "Single Worklight Switch", "Double Worklight Switch")
        * "Am-Safe triple action"
        * "Am-safe single action"
        * "Schroth"
        * "Coat Hook" (or "Coat holder")

3.  **Generate a 15-digit part number for EACH identified CAS location using the following PRECISE and DETERMINISTIC rules.** Follow these rules exactly for each digit:

    * **First Three Digits:** Always '235'.
    * **Fourth Digit:**
        * If the CAS TDU location is Floor mounted (FM), set to '0'.
        * Otherwise (Wall-mounted WM), set to '1'.
    * **Fifth Digit:**
        * If the CAS TDU location is Floor mounted (FM), set to 'F'.
        * Otherwise (Wall-mounted WM), set to 'W'.
    * **Sixth Digit:** Always 'S'.
    * **Seventh Digit:**
        * If "Schroth" is found in the CAS features, set to '1'.
        * Else if "Am-Safe triple action" is found, set to '4'.
        * Else if "Am-safe single action" is found, set to '5'.
        * If none of these keywords are explicitly found for the CAS, use 'X'.
    * **Eighth Digit:**
        * If "PBE" is present for the CAS, set to 'U'.
        * Else if "PBE" is NOT present BUT "Handset" AND "Worklight" are BOTH present, set to 'A'.
        * If neither of these conditions is met, use 'X'.
    * **Ninth Digit:**
        * If "Coat Hook" or "Coat holder" is found in the CAS features, set to 'E'.
        * Otherwise, set to 'A'.
    * **Tenth Digit:** Always 'G'.
    * **Eleventh Digit:** Always '4'.
    * **Twelfth Digit:** Always '4'.
    * **Thirteenth and Fourteenth Digits:** Always 'ED'.
    * **Fifteenth Digit:** Always '2'.

4.  **Output Format:**
    Provide the generated part numbers as a JSON object. The keys of the JSON object should be the CAS IDs (e.g., "CAS 11", "CAS 37"), and the values should be their respective 15-digit part numbers. Ensure the JSON is valid and only contains the part numbers. If you cannot determine a specific digit, use 'X' for that digit in the part number.

    Example desirable JSON output structure:
    ```json
    {
      "CAS 11": "2351WS4UAG44ED2",
      "CAS 13": "2351WS4UAG44ED2",
      "CAS 15": "2351WS4UAG44ED2",
      // ... and so on for all identified CAS locations
    }
    ```
"""

# --- Streamlit Application UI ---
st.set_page_config(page_title="LLM-Powered CAS Part Number Generator", layout="centered")
st.title("🤖 LLM-Powered CAS Part Number Generator")
st.markdown("Upload a CAS Definition Document (PDF). The LLM will parse it and generate part numbers based on the embedded logic.")

uploaded_file = st.file_uploader("Upload CAS Definition Document (PDF)", type="pdf")

if uploaded_file is not None:
    # Read the PDF content
    pdf_bytes = uploaded_file.read()

    # Encode PDF to Base64
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

    with st.spinner("Sending PDF to LLM and generating part numbers... (This may take a moment)"):
        try:
            # Construct the messages for the Mistral API call using dictionaries
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PN_LOGIC_PROMPT},
                        {"type": "image_url", "image_url": f"data:application/pdf;base64,{base64_pdf}"}
                    ]
                }
            ]

            # Make the API call
            chat_response = client.chat(
                model="mistral-large-latest", # Or "mistral-medium-latest" or another suitable multimodal model
                messages=messages,
                temperature=0.1, # Keep temperature low for deterministic tasks
                response_format={"type": "json_object"} # Ask for JSON output if model supports it
            )

            # Get the response content (should be JSON)
            response_content = chat_response.choices[0].message.content

            # Attempt to parse the JSON response
            import json
            try:
                generated_pns = json.loads(response_content)
                st.success("Part numbers generated successfully by LLM!")
                st.subheader("Generated Part Numbers:")

                # Format for display
                output_str = ""
                for cas_id, pn in generated_pns.items():
                    output_str += f"{cas_id}: `{pn}`\n"
                st.code(output_str)

            except json.JSONDecodeError:
                st.error("LLM did not return a valid JSON object. Raw response:")
                st.code(response_content)
                st.warning("This can happen if the LLM struggles to strictly adhere to the requested JSON format, especially with complex parsing.")

        except Exception as e:
            st.error(f"An error occurred during LLM processing: {e}")
            st.info("Ensure your Mistral API key is correct and the PDF content is clear for the LLM to understand.")

st.markdown("---")
st.info("This application leverages the Mistral AI API to interpret the PDF and generate part numbers based on the detailed rules provided in the prompt. "
        "Accuracy depends heavily on the LLM's capability and the clarity of the prompt.")
