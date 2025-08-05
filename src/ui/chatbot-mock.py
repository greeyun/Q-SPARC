import json
import re

import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(layout="centered")

# --- Session State Setup ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_bot_reply" not in st.session_state:
    st.session_state.pending_bot_reply = False


st.markdown("### 🤖 Ask Q-SPARC, Know More.")

# Display Chat History
with st.container():

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div style='text-align: right; background-color: #dbe9ff; padding: 10px; border-radius: 10px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            if msg["type"] == "table":
                data_table = msg['content']
                df = pd.DataFrame(data_table["rows"], columns=data_table["head"])
                # Custom CSS for styling links
                st.markdown(
                    """
                    <style>
                    .custom-link {
                        color: blue; /* Link color */
                        text-decoration: underline; /* Add underline */
                    }
                    .custom-table {
                        width: 100%;
                        max-width: 100%;
                        overflow-x: auto;
                        display: block;
                    }
                    .custom-table th, .custom-table td {
                        white-space: nowrap;
                        text-align: center;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                # Process each element to check for URLs
                for index, row in df.iterrows():
                    for col in df.columns:
                        if re.match(r'https?://', str(row[col])):  # Check if the element is a URL
                            last_part = row[col].split("/")[-1]
                            print(last_part)  # 输出: neuron-type-keast-3
                            df.at[index, col] = f'<a class="custom-link" href="{row[col]}" target="_blank">{last_part}</a>'

                # Set index to start from 1
                df.index = df.index + 1
                # Render the table with HTML links
                st.markdown(df.to_html(classes='custom-table', escape=False, index=True), unsafe_allow_html=True)
            elif msg["type"] == "image":
                img_url = msg['content']
                st.markdown(
                    f"""
                    <div style='text-align: left;'>
                        <img src="{img_url}" style="max-width: 600px; height: auto;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"<div style='text-align: left; background-color: #f1f0f0; padding: 10px; border-radius: 10px; margin: 5px 0;'>{msg['content']}</div>", unsafe_allow_html=True)

    if st.session_state.pending_bot_reply:
        st.markdown("<div style='text-align: left; color: gray; font-style: italic; margin: 5px 0;'>🤖 Q-SPARC is thinking...</div>", unsafe_allow_html=True)

# with st.form(key="chat_form", clear_on_submit=True):
#     user_input = st.text_area("Your message", height=100, label_visibility="collapsed")
#     submitted = st.form_submit_button("Send")

user_input = st.chat_input("How can I help you today?")

if user_input:
    st.session_state.chat_history.append({"role": "user", "type": "text", "content": user_input})
    st.session_state.pending_bot_reply = True
    st.rerun()

# if submitted and user_input.strip() != "":
#     # Append user message and trigger bot reply
#     st.session_state.chat_history.append({"role": "user", "type": "text", "content": user_input})
#     st.session_state.pending_bot_reply = True
#     st.rerun()

# --- Handle Bot Reply After Rerun ---
if st.session_state.pending_bot_reply:
    last_user_input = next((msg["content"] for msg in reversed(st.session_state.chat_history) if msg["role"] == "user"), "")

    payload = {
        "input": last_user_input,
        "session_id": "user123_session456"
    }

    # try:
        # response = requests.post("http://localhost:7777/chat", json=payload)
        # print(f"response.status_code = {response.status_code}")
        # if response.status_code == 200:
        #     result = response.json()
        #     print(f"response.result = {result}")
    time.sleep(2)
    result = """{
    "flatmap_metadata":"https://models.physiomeproject.org/workspace/608/rawfile/4b92ad68f7ce52bfadf22621ea6de7686342a718/whole-rat.svg",
"generated_text": "Yes, there is a connection from the inferior mesenteric ganglion to the urinary bladder in rats. The pathways are summarized as follows based on the nerves involved: 1. Via Bladder Nerve Pathway: Inferior mesenteric ganglion Urinary bladder Target Sites: Dome of the Bladder Neck of the Urinary Bladder 2. Via Hypogastric Nerve Pathway: Inferior mesenteric ganglion Urinary bladder Target Sites: Dome of the Bladder Neck of the Urinary Bladder 3. Via Pelvic Ganglion Pathway: Inferior mesenteric ganglion Pelvic ganglion Urinary bladder Target Sites: Dome of the Bladder Neck of the Urinary Bladder These connections demonstrate the role of the inferior mesenteric ganglion in the sympathetic innervation of the urinary bladder via multiple pathways, primarily through the bladder nerve, hypogastric nerve, and pelvic ganglion.",
"table_data": {
"head": [
    "A_ID",
    "A",
    "C_ID",
    "C",
    "C_Type",
    "B_ID",
    "B",
    "Target_Organ_IRI",
    "Target_Organ"
],
"rows": [
    [
        "http://purl.obolibrary.org/obo/UBERON_0005453",
        "inferior mesenteric ganglion",
        "http://uri.interlex.org/base/ilx_0793559",
        "bladder nerve",
        "nerve",
        "http://purl.obolibrary.org/obo/UBERON_0001258",
        "neck of urinary bladder",
        "http://purl.obolibrary.org/obo/UBERON_0001556",
        "lower urinary tract"
    ],
    [
        "http://purl.obolibrary.org/obo/UBERON_0005453",
        "inferior mesenteric ganglion",
        "http://uri.interlex.org/base/ilx_0793559",
        "bladder nerve",
        "nerve",
        "http://uri.interlex.org/base/ilx_0738433",
        "Dome of the Bladder",
        "http://purl.obolibrary.org/obo/UBERON_0001556",
        "lower urinary tract"
    ],
    [
        "http://purl.obolibrary.org/obo/UBERON_0005453",
        "inferior mesenteric ganglion",
        "http://purl.obolibrary.org/obo/UBERON_0005303",
        "hypogastric nerve",
        "nerve plexus",
        "http://purl.obolibrary.org/obo/UBERON_0001258",
        "neck of urinary bladder",
        "http://purl.obolibrary.org/obo/UBERON_0001556",
        "lower urinary tract"
    ],
    [
        "http://purl.obolibrary.org/obo/UBERON_0005453",
        "inferior mesenteric ganglion",
        "http://purl.obolibrary.org/obo/UBERON_0005303",
        "hypogastric nerve",
        "nerve plexus",
        "http://uri.interlex.org/base/ilx_0738433",
        "Dome of the Bladder",
        "http://purl.obolibrary.org/obo/UBERON_0001556",
        "lower urinary tract"
    ],
    [
        "http://purl.obolibrary.org/obo/UBERON_0005453",
        "inferior mesenteric ganglion",
        "http://purl.obolibrary.org/obo/UBERON_0016508",
        "pelvic ganglion",
        "ganglion",
        "http://purl.obolibrary.org/obo/UBERON_0001258",
        "neck of urinary bladder",
        "http://purl.obolibrary.org/obo/UBERON_0001556",
        "lower urinary tract"
    ],
    [
        "http://purl.obolibrary.org/obo/UBERON_0005453",
        "inferior mesenteric ganglion",
        "http://purl.obolibrary.org/obo/UBERON_0016508",
        "pelvic ganglion",
        "ganglion",
        "http://uri.interlex.org/base/ilx_0738433",
        "Dome of the Bladder",
        "http://purl.obolibrary.org/obo/UBERON_0001556",
        "lower urinary tract"
    ]
]
}
}"""

    try:
        result = json.loads(result)
        print("Converted JSON:", result)
    except json.JSONDecodeError as e:
        print("Invalid JSON string:", e)

    generated_text = result.get("generated_text", "")
    table_data = result.get("table_data", None)
    print("parsed data JSON:", table_data)
    flatmap_metadata = result.get("flatmap_metadata", "")

    bot_message = generated_text
    st.session_state.chat_history.append({"role": "bot", "type": "text", "content": bot_message})
    st.session_state.chat_history.append({
            "role": "bot",
            "type": "table",
            "content": table_data
        })
    st.session_state.chat_history.append({
        "role": "bot",
        "type": "image",
        "content": flatmap_metadata
    })

    #     else:
    #         error_msg = f"❌ Server Error {response.status_code}: {response.text}"
    #         st.session_state.chat_history.append({"role": "bot", "type": "text", "content": error_msg})
    #
    # except Exception as e:
    #     st.session_state.chat_history.append({"role": "bot", "type": "text", "content": f"Error: {e}"})

    st.session_state.pending_bot_reply = False
    st.rerun()

