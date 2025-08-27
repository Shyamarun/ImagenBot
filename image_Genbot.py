import streamlit as st
import requests
import os
import json
from langchain.memory import ConversationBufferMemory
import time

SAVE_DIR = "sessions"
OUTPUT_DIR = "outputs"
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------- Utility ----------
def get_session_file(session_name):
    return os.path.join(SAVE_DIR, f"{session_name}.json")

def load_session(session_name):
    memory = ConversationBufferMemory(return_messages=True)
    history = []
    file = get_session_file(session_name)
    if os.path.exists(file):
        with open(file, "r") as f:
            data = json.load(f)
        for item in data:
            if item["type"] == "human":
                memory.chat_memory.add_user_message(item["content"])
            else:
                memory.chat_memory.add_ai_message(item["content"])
            history.append(item)
    return memory, history

def save_session(session_name, memory, history):
    data = []
    for item in history:
        data.append(item)
    with open(get_session_file(session_name), "w") as f:
        json.dump(data, f)

def list_sessions():
    return [f.replace(".json", "") for f in os.listdir(SAVE_DIR) if f.endswith(".json")]

def delete_session(session_name):
    file_path = get_session_file(session_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    for file in os.listdir(OUTPUT_DIR):
        if file.startswith(f"{session_name}_") and file.endswith(".jpg"):
            os.remove(os.path.join(OUTPUT_DIR, file))
    if st.session_state.active_session == session_name:
        st.session_state.active_session = None
        st.session_state.memory = None
        st.session_state.history = []

# ---------- Session State ----------
if "active_session" not in st.session_state:
    st.session_state.active_session = None
if "memory" not in st.session_state:
    st.session_state.memory = None
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- CSS for Black Background Theme and Responsive Design ----------
st.markdown(
    """
    <style>
    /* Force black background on all Streamlit elements */
    :root {
        --primary-bg: #000000;
        --secondary-bg: #000000;
        --text-color: #b4a5f5; /* Fallback color for non-WebKit support */
        --chat-text-color: #ffffff; /* High-contrast color for chat bubbles */
        --accent-color: #4a90e2;
        --button-bg: #000000; /* Black background for buttons */
        --button-text: #ffffff; /* White font color for buttons */
        --button-border: linear-gradient(90deg, #8269f0, #a08df3, #b3a4f5, #b4a5f5); /* Gradient for button border */
        --input-bg: #1a1a1a;
        --border-radius: 8px;
        --font-size-base: 2rem; /* Increased to max fit */
        --font-size-title: 3.5rem; /* Increased to max fit */
        --font-size-subheader: 2.5rem; /* Increased to max fit */
        --button-font-size: 6rem; /* Increased to max fit */
    }

    /* Override Streamlit's default background */
    body, .stApp, .main, .css-1v3fvcr, .css-1avcm0n {
        background-color: var(--primary-bg) !important;
        color: var(--text-color) !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        font-size: var(--font-size-base);
    }

    /* Sidebar styling with enhanced specificity */
    .css-1d391kg, .sidebar .sidebar-content, .stSidebar, [data-testid="stSidebar"] {
        background-color: var(--secondary-bg) !important;
        color: var(--text-color) !important;
        
    }

    /* Apply gradient text effect to headings and main text */
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText {
        background: linear-gradient(90deg, #8269f0, #a08df3, #b3a4f5, #b4a5f5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        color: var(--text-color); /* Fallback for non-WebKit browsers */
    }

    /* Chat bubbles with forced visibility and large font */
    .chat-user {
        
        color: var(--chat-text-color) !important; /* Force white text */
        font-size: 50px !important; /* Match your requested size */
        padding: 1rem;
        border-radius: var(--border-radius);
        margin: 0.5rem 0;
        max-width: 80%;
        word-wrap: break-word;
        margin-left: auto;
        text-align: right;
        border: 1px solid #333333;
        display: block !important; /* Ensure visibility */
        visibility: visible !important; /* Ensure visibility */
        opacity: 1 !important; /* Ensure opacity is not zero */
    }

    .chat-ai {
        
        color: var(--chat-text-color) !important; /* Force white text */
        font-size: 50px !important; /* Match your requested size */
        padding: 1rem;
        border-radius: var(--border-radius);
        margin: 0.5rem 0;
        max-width: 80%;
        word-wrap: break-word;
        margin-right: auto;
        text-align: left;
        border: 1px solid #333333;
        display: block !important; /* Ensure visibility */
        visibility: visible !important; /* Ensure visibility */
        opacity: 1 !important; /* Ensure opacity is not zero */
    }
   

    /* Buttons with black background and gradient border */
    .stButton > button {
        background: #020024;
background: linear-gradient(90deg,rgba(2, 0, 36, 1) 0%, rgba(133, 133, 222, 1) 0%, rgba(0, 212, 255, 1) 100%);
-webkit-background-clip: text;
 !important;
        color: var(--button-text) !important; /* White font color */
       font-size: var(--button-font-size);
       
        padding: 0.75rem 1.25rem;
        border-radius: var(--border-radius);
        border: 4px solid transparent; /* Initial border */
        background-clip: padding-box; /* Ensure background doesn't overlap border */
        -webkit-background-clip: padding-box; /* WebKit support */
        /* Apply gradient to border */
        border-image-slice: 1; /* Use the entire gradient */
        width: 100%;
        transition: background-color 0.2s, border-color 0.2s;
    }

    .stButton > button:hover {
        
        border-image: var(--button-border); /* Maintain gradient border on hover */
    }
    



    /* Text input */
    .stTextInput > div > div > input {
        background-color: var(--input-bg) !important;
        color: var(--text-color) !important;
        font-size: var(--font-size-base);
        border-radius: var(--border-radius);
        padding: 0.75rem;
        border: 1px solid #333333;
    }

    /* Ensure containers and other elements are black */
    .stContainer, .stExpander, .stImage {
        background-color: var(--primary-bg) !important;
        color: var(--text-color) !important;
    }

    /* Override any white backgrounds */
    div[data-testid="stAppViewContainer"], div[data-testid="stVerticalBlock"] {
        background-color: var(--primary-bg) !important;
    }

    /* Responsive design */
    @media (max-width: 600px) {
        :root {
            --font-size-base: 1.5rem; /* Adjusted for smaller screens */
            --font-size-title: 2.5rem; /* Adjusted for smaller screens */
            --font-size-subheader: 2rem; /* Adjusted for smaller screens */
            --button-font-size: 1.5rem; /* Adjusted for smaller screens */
        }

        .chat-user, .chat-ai {
            max-width: 90%;
            padding: 0.5rem;
            color: white !important; /* Corrected typo */
        }

        .stButton > button {
            padding: 0.5rem 1rem;
        }
    }

    @media (min-width: 601px) and (max-width: 1024px) {
        :root {
            --font-size-base: 2rem; /* Adjusted for medium screens */
            --font-size-title: 3rem; /* Adjusted for medium screens */
            --font-size-subheader: 2.2rem; /* Adjusted for medium screens */
            --button-font-size: 1.8rem; /* Adjusted for medium screens */
        }
    }

    /* Ensure images are responsive */
    img {
        max-width: 100%;
        height: auto;
    }

    /* Sidebar buttons layout */
    .sidebar .stButton > button {
        margin-bottom: 0.5rem;
    }

    /* Override Streamlit's default info/error messages */
    .stAlert, .stInfo, .stError, .stSuccess, .stWarning {
        background-color: #1a1a1a !important;
        color: var(--text-color) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Sidebar ----------
st.sidebar.title("💬 Chats")



st.markdown("""
    <style>
    /* Target ALL sidebar buttons, override Streamlit's auto CSS */
    section[data-testid="stSidebar"] .st-emotion-cache-479nsk {
    
        font-size: 30px !important;
        font-weight: 20 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)




if st.sidebar.button("➕ New Chat"):
    new_name = f"chat_{len(list_sessions())+1}"
    st.session_state.active_session = new_name
    st.session_state.memory = ConversationBufferMemory(return_messages=True)
    st.session_state.history = []
    save_session(new_name, st.session_state.memory, st.session_state.history)
    st.rerun()

sessions = list_sessions()
for s in sessions:
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        if st.button(s, use_container_width=True):
            st.session_state.active_session = s
            st.session_state.memory, st.session_state.history = load_session(s)
            st.rerun()
    with col2:
        if st.button("🗑️", key=f"delete_{s}"):
            delete_session(s)
            st.rerun()

# ---------- Main Area ----------
#st.title("🖼️ ImaGenBot")
import streamlit as st

import streamlit as st

# Custom CSS
st.markdown("""
    <style>
    .big-font {
        font-weight : bolder;
        font-size:100px !important;
        background: linear-gradient(90deg,rgba(2, 0, 36, 1) 0%, rgba(133, 133, 222, 1) 0%, rgba(0, 212, 255, 1) 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        color: transparent !important;
    }
        text-align: center; /* Optional: center align */
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="big-font">ImaGenBot</p>', unsafe_allow_html=True)



if st.session_state.active_session:
    st.subheader(f"Chat: {st.session_state.active_session}")

    txt = st.text_input("Enter your prompt:")
    if st.button("Generate"):
        url = f"https://pollinations.ai/p/{txt}"
        max_retries = 3
        retry_delay = 2  # seconds
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    image_path = os.path.join(
                        OUTPUT_DIR,
                        f"{st.session_state.active_session}_{len(st.session_state.history)}.jpg"
                    )
                    with open(image_path, "wb") as f:
                        f.write(resp.content)

                    st.session_state.memory.chat_memory.add_user_message(txt)
                    st.session_state.memory.chat_memory.add_ai_message("Generated image ✅")
                    st.session_state.history.append({
                        "type": "human",
                        "content": txt
                    })
                    st.session_state.history.append({
                        "type": "ai",
                        "content": "Generated image ✅",
                        "image": image_path,
                        "prompt": txt
                    })
                    save_session(st.session_state.active_session, st.session_state.memory, st.session_state.history)
                    st.rerun()
                    break
                else:
                    error_msg = f"❌ Image generation failed. Status: {resp.status_code}, Response: {resp.text}"
                    st.error(error_msg)
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        st.session_state.memory.chat_memory.add_user_message(txt)
                        st.session_state.memory.chat_memory.add_ai_message(error_msg)
                        st.session_state.history.append({"type": "human", "content": txt})
                        st.session_state.history.append({"type": "ai", "content": error_msg})
                        save_session(st.session_state.active_session, st.session_state.memory, st.session_state.history)
                        st.rerun()
            except requests.RequestException as e:
                error_msg = f"❌ Image generation failed. Error: {str(e)}"
                st.error(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    st.session_state.memory.chat_memory.add_user_message(txt)
                    st.session_state.memory.chat_memory.add_ai_message(error_msg)
                    st.session_state.history.append({"type": "human", "content": txt})
                    st.session_state.history.append({"type": "ai", "content": error_msg})
                    save_session(st.session_state.active_session, st.session_state.memory, st.session_state.history)
                    st.rerun()

# ---------- Chat History ----------
st.subheader("History")

paired_history = []
i = 0
while i < len(st.session_state.history):
    if st.session_state.history[i]["type"] == "human":
        user_msg = st.session_state.history[i]
        ai_msg = st.session_state.history[i + 1] if i + 1 < len(st.session_state.history) else None
        paired_history.append((user_msg, ai_msg))
        i += 2
    else:
        i += 1

for idx, (user_msg, ai_msg) in enumerate(paired_history):
    with st.container():
        preview = user_msg["content"][:50] + ("..." if len(user_msg["content"]) > 50 else "")
        st.markdown(f"<div class='chat-user'>👤 {preview}</div>", unsafe_allow_html=True)
        if len(user_msg["content"]) > 50:
            with st.expander("View full prompt"):
                st.write(user_msg["content"])

        if ai_msg:
            st.markdown(f"<div class='chat-ai'>🤖 {ai_msg['content']}</div>", unsafe_allow_html=True)
            if "image" in ai_msg and os.path.exists(ai_msg["image"]):
                st.image(ai_msg["image"], caption=f"Prompt: {ai_msg['prompt']}", use_container_width=True)
                st.download_button(
                    "📥 Download",
                    open(ai_msg["image"], "rb").read(),
                    f"generated_{st.session_state.active_session}_{idx}.jpg",
                    "image/jpeg",
                    key=f"download_{st.session_state.active_session}_{idx}"
                )
else:
    st.info("👉 Start a new chat from the sidebar.")