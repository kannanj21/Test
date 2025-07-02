import streamlit as st
import io
import ssl
import json
from mistralai.client import MistralClient
from PyPDF2 import PdfReader


api_key = "H8guEVvToOt8VEIRCZSgHgtAMGmVg0Dy"


try:
    _create_unverified_https_context = ssl._create_unverified_context
    ssl._create_default_https_context = _create_unverified_https_context
except AttributeError:
    pass  # Older Python versions


client = MistralClient(api_key=api_key)



# --- Prompt Definition ---
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

st.markdown("<h1 style='text-align: center; font-size: 50px;'>Version AI</h1>", unsafe_allow_html=True)


st.set_page_config(page_title="CAS Part Number Generator", layout="centered")
st.title("💺 CAS Part Number Generator")

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

st.markdown("## 🧭 Assist Space Tool")


cas_location_input = st.text_input("CAS Location")
x_value = st.number_input("X Coordinate (mm)", format="%.2f")
y_value = st.number_input("Y Coordinate (mm)", format="%.2f")


if st.button("Validate Space"):
    if not cas_location_input:
        st.warning("Please enter a CAS location to validate space.")
    else:
        # Placeholder logic
        st.success(f"✅ Space validated for {cas_location_input} at coordinates ({x_value}, {y_value}). No clashes detected.")


st.markdown("## 📦 KIT Loader")


kit_description = st.text_input("Kit Description")
loose_item_name = st.text_input("Name of the Loose Item")
equipment_unit = st.text_input("Equipment Unit to Link")

# Submit button (you can rename this if you like)
if st.button("Generate KIT Entry"):
    if not kit_description or not loose_item_name or not equipment_unit:
        st.warning("Please fill out all fields to generate the KIT entry.")
    else:
        # Placeholder for actual logic
        st.success(f"✅ KIT entry created:\n\n📄 **Description:** {kit_description}\n📦 **Item:** {loose_item_name}\n🔗 **Linked to:** {equipment_unit}")
        



st.markdown("## 🔍 Design Solutions Finder")
    

supplier_name = st.text_input("Enter Supplier Name:")
    

door_location = st.text_input("Enter Door Location:")
    

tdu = st.text_input("Enter TDU:")
    

x_distance = st.number_input("Enter X Distance:", min_value=0.0, format="%.2f")
    

cas_type = st.selectbox("Select Type of CAS", ["Wall-mounted", "Floor-mounted"])


if supplier_name or door_location or tdu or x_distance or cas_type:
    st.write("### DS Finder Details")
    st.write(f"**Supplier Name:** {supplier_name}")
    st.write(f"**Door Location:** {door_location}")
    st.write(f"**TDU:** {tdu}")
    st.write(f"**X Distance:** {x_distance}")
    st.write(f"**Type of CAS:** {cas_type}")


st.markdown("## MOD Closure")


cts_file = st.file_uploader("📄 Upload CTS", type=["pdf", "docx", "xlsx"], key="cts")


trs_file = st.file_uploader("📄 Upload TRS", type=["pdf", "docx", "xlsx"], key="trs")


if cts_file:
    st.success(f"✅ CTS File uploaded: {cts_file.name}")

if trs_file:
    st.success(f"✅ TRS File uploaded: {trs_file.name}")

st.markdown("## ❓ Need new models?")

if 'part_numbers' in locals() and isinstance(part_numbers, dict):
    st.markdown("Select **Yes** or **No** for each part number below:")

    # Dictionary to hold user responses
    model_requests = {}

    for cas_id, pn in part_numbers.items():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{cas_id}**: `{pn}`")
        with col2:
            choice = st.radio(
                label=f"Need new model for {cas_id}?",
                options=["No", "Yes"],
                key=f"model_request_{cas_id}"
            )
            model_requests[cas_id] = choice

    # Optional: Show summary
    st.markdown("### 📝 Summary of Requests")
    for cas_id, decision in model_requests.items():
        st.write(f"**{cas_id}**: `{part_numbers[cas_id]}` → **{decision}**")

else:
    st.info("👆 Upload a PDF and generate part numbers first to use this section.")




st.markdown("---")
st.info("This test app uses Mistral AI and Streamlit. Do not use this setup in production due to hardcoded keys and insecure SSL bypass.")
