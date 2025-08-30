import streamlit as st
import requests
import os
import json
from langchain.memory import ConversationBufferMemory
import time

SAVE_DIR = "sessions"import streamlit as st
import requests
import os
import json
from langchain.memory import ConversationBufferMemory
import time
import base64

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
    sessions = []
    for file in os.listdir(SAVE_DIR):
        if file.endswith(".json"):
            session_name = file.replace(".json", "")
            recent_prompt = "No prompt"
            try:
                with open(get_session_file(session_name), "r") as f:
                    data = json.load(f)
                # Find the most recent human prompt and extract raw prompt text
                for item in reversed(data):
                    if item["type"] == "human":
                        content = item["content"]
                        # Remove "Prompt:" prefix and ", Model: {model}" suffix
                        if content.startswith("Prompt: "):
                            content = content[len("Prompt: "):]
                        if ", Model: " in content:
                            content = content[:content.index(", Model: ")]
                        recent_prompt = content
                        break
            except Exception:
                pass  # Use default "No prompt" if file reading fails
            sessions.append((session_name, recent_prompt))
    return sessions


def truncate_prompt(prompt, max_length=20):
    if len(prompt) > max_length:
        return prompt[:max_length - 3] + "..."
    return prompt


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


def generate_scrolling_images():
    prompts = [
        "a futuristic cityscape",
        "a serene mountain landscape",
        "a fantasy castle at sunset",
        "a cyberpunk street scene",
        "a whimsical forest with magical creatures",
        "a steampunk airship flying over a desert",
        "an underwater coral reef with vibrant fish",
        "a medieval village in a snowy valley",
        "a space station orbiting a distant planet",
        "a cozy cabin by a lake at dawn"
    ]
    image_paths = []
    for idx, prompt in enumerate(prompts):
        image_path = os.path.join(OUTPUT_DIR, f"scroll_image_{idx}.jpg")
        if not os.path.exists(image_path):
            url = f"https://pollinations.ai/p/{prompt}"
            max_retries = 3
            retry_delay = 5
            success = False
            for attempt in range(max_retries):
                try:
                    resp = requests.get(url, timeout=15)
                    if resp.status_code == 200:
                        with open(image_path, "wb") as f:
                            f.write(resp.content)
                        st.write(f"Successfully saved scrolling image {idx} for prompt: {prompt}")
                        success = True
                        break
                    else:
                        st.warning(
                            f"Failed to fetch scrolling image {idx} for prompt '{prompt}' on attempt {attempt + 1}. Status: {resp.status_code}")
                except requests.RequestException as e:
                    st.warning(
                        f"Failed to fetch scrolling image {idx} for prompt '{prompt}' on attempt {attempt + 1}. Error: {str(e)}")
                time.sleep(retry_delay)
            if not success:
                st.error(f"Failed to save scrolling image {idx} for prompt '{prompt}' after {max_retries} attempts.")
        if os.path.exists(image_path):
            image_paths.append((image_path, prompt))
        else:
            image_paths.append((None, prompt))
    return image_paths


def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        st.warning(f"Failed to encode image {image_path}: {str(e)}")
        return None


# ---------- Session State ----------
if "active_session" not in st.session_state:
    st.session_state.active_session = None
if "memory" not in st.session_state:
    st.session_state.memory = None
if "history" not in st.session_state:
    st.session_state.history = []
if "scrolling_images" not in st.session_state:
    with st.spinner("Loading showcase images..."):
        st.session_state.scrolling_images = generate_scrolling_images()

# ---------- Available Models ----------
MODELS = [
    "flux",
    "pimp",
    "dolly-mini",
    "magister",
    "stable-diffusion"
]

# ---------- CSS for Enhanced Theme with Animations ----------
st.markdown(
    """
    <style>
    :root {
        --primary-bg: #000000;
        --secondary-bg: #1a1a1a;
        --text-color: #ffffff;
        --accent-color: #4a90e2;
        --gradient: linear-gradient(90deg, #ff6f61, #ffb88c, #6b7280, #60a5fa);
        --border-radius: 12px;
        --font-size-base: 1rem;
        --font-size-title: 2.8rem;
        --font-size-subheader: 1.6rem;
        --font-size-chat: 1.1rem;
        --button-font-size: 0.9rem;
    }
    body, .stApp, .main {
        background: linear-gradient(135deg, #000000 0%, #1e1e2f 100%) !important;
        color: var(--text-color) !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: var(--font-size-base);
        animation: fadeIn 1s ease-in-out;
    }
    @keyframes fadeIn {
        0% { opacity: 0; }
        100% { opacity: 1; }
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a1a 0%, #2a2a3a 100%) !important;
        animation: slideIn 0.5s ease-in-out;
    }
    @keyframes slideIn {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(0); }
    }
    h1, h2, h3 {
        background: var(--gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 5s ease-in-out infinite;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .chat-user {
        background: linear-gradient(45deg, #ff6f61, #ffb88c) !important;
        color: var(--text-color) !important;
        font-size: var(--font-size-chat);
        padding: 1.2rem;
        border-radius: var(--border-radius);
        margin: 0.5rem 0;
        max-width: 80%;
        word-wrap: break-word;
        margin-left: auto;
        text-align: right;
        border: 2px solid #444444;
        animation: popIn 0.3s ease-in-out;
    }
    .chat-ai {
        background: linear-gradient(45deg, #60a5fa, #6b7280) !important;
        color: var(--text-color) !important;
        font-size: var(--font-size-chat);
        padding: 1.2rem;
        border-radius: var(--border-radius);
        margin: 0.5rem 0;
        max-width: 80%;
        word-wrap: break-word;
        margin-right: auto;
        text-align: left;
        border: 2px solid #444444;
        animation: popIn 0.3s ease-in-out;
    }
    @keyframes popIn {
        0% { transform: scale(0.9); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }
    .chat-user, .chat-ai {
        background-color: transparent !important;
    }
    [data-testid="stExpander"], [data-testid="stVerticalBlock"] {
        background: black !important;
    }
    button, .stButton > button, button[kind="primary"], button[kind="secondary"] {
        background: linear-gradient(135deg, #000000 0%, #1e1e2f 100%) !important;
        color: white !important;
        font-size: var(--button-font-size);
        padding: 0.6rem 1rem;
        border-radius: var(--border-radius);
        border: none;
        width: 100%;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .delete-button > button {
        background: linear-gradient(90deg, #ff4d4d, #e63946) !important;
        color: #ffffff !important;
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
        border-radius: var(--border-radius);
        min-width: 30px;
        border: none;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .delete-button > button:hover {
        background: linear-gradient(90deg, #ff4d4d, #e63946) !important;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }
    button[download], button[download]:hover {
        background: var(--gradient) !important;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: var(--secondary-bg) !important;
        color: var(--text-color) !important;
        border-radius: var(--border-radius);
        padding: 0.8rem;
        border: 2px solid #444444;
        transition: border-color 0.2s;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-color);
    }
    .stSelectbox > div > div > select {
        background-color: var(--secondary-bg) !important;
        color: var(--text-color) !important;
        border-radius: var(--border-radius);
        padding: 0.8rem;
        border: 2px solid #444444;
        transition: border-color 0.2s;
    }
    .stSelectbox > div > div > select:focus {
        border-color: var(--accent-color);
    }
    label[data-testid="stWidgetLabel"] > div {
        background: var(--gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-style: italic;
    }
    .stTextArea textarea::placeholder {
        background: var(--gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-style: italic;
        opacity: 1;
    }
    @media (max-width: 600px) {
        :root {
            --font-size-base: 0.95rem;
            --font-size-title: 2.2rem;
            --font-size-subheader: 1.4rem;
            --font-size-chat: 1rem;
            --button-font-size: 0.8rem;
        }
        .chat-user, .chat-ai {
            max-width: 95%;
        }
    }
    @media (min-width: 601px) and (max-width: 1024px) {
        :root {
            --font-size-base: 1rem;
            --font-size-title: 2.5rem;
            --font-size-subheader: 1.5rem;
            --font-size-chat: 1.1rem;
            --button-font-size: 0.85rem;
        }
    }
    img {
        max-width: 100%;
        height: auto;
        border-radius: var(--border-radius);
        animation: fadeInImage 0.5s ease-in-out;
    }
    @keyframes fadeInImage {
        0% { opacity: 0; transform: scale(0.95); }
        100% { opacity: 1; transform: scale(1); }
    }
    .session-button > button {
        font-size: 0.85rem !important;
        color: #ffffff !important;
        background: var(--gradient) !important;
        margin-bottom: 0.3rem;
        padding: 0.4rem 0.6rem; /* Adjusted for compactness */
        transition: transform 0.2s, box-shadow 0.2s;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
        border-radius: 8px;
        border: none;
        text-align: left; /* Left-aligned text for chat-like appearance */
    }
    .session-button > button:hover {
        background: var(--gradient) !important;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }
    .session-row {
        background-color: white;
        display: flex;
        align-items: center;
        margin-bottom: 0.3rem;
        padding-bottom: 0.3rem;
    }
    .scrolling-container {
        overflow: hidden;
        width: 100%;
        margin-top: 20px;
        padding: 10px 0;
    }
    .scrolling-images {
        display: inline-flex;
        white-space: nowrap;
        animation: scroll 30s linear infinite;
    }
    .scrolling-images .image-item {
        flex: 0 0 auto;
        width: 250px;
        margin-right: 15px;
        text-align: center;
    }
    .scrolling-images img {
        width: 250px;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .scrolling-images img.error {
        background-color: #333;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-color);
        font-size: 0.8rem;
        text-align: center;
    }
    .scrolling-images p {
        margin: 5px 0 0;
        font-size: 0.9rem;
        color: var(--text-color);
        white-space: normal;
        word-wrap: break-word;
        max-width: 250px;
    }
    @keyframes scroll {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }
    .scrolling-images:hover {
        animation-play-state: paused;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Main Area: Initial Search Bar ----------
st.markdown(
    '<p style="font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #ff6f61, #ffb88c, #6b7280, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">ImaGenBot</p>',
    unsafe_allow_html=True)

# Show initial prompt form only if no active session
if not st.session_state.active_session:
    with st.form(key="initial_prompt_form"):
        initial_prompt = st.text_area("Enter your image prompt to start:", height=120,
                                      placeholder="Describe the image you want to generate (e.g., 'A futuristic city at sunset')")
        selected_model = st.selectbox("Choose a model:", MODELS, index=0)
        submit_initial = st.form_submit_button(label="Generate Image")

    # Handle initial prompt submission
    if submit_initial and initial_prompt:
        with st.spinner("Generating image... This may take a moment."):
            # Create new session
            new_name = f"chat_{len([s for s, _ in list_sessions()]) + 1}"
            st.session_state.active_session = new_name
            st.session_state.memory = ConversationBufferMemory(return_messages=True)
            st.session_state.history = []

            # Generate image
            url = f"https://pollinations.ai/p/{initial_prompt}?model={selected_model}"
            max_retries = 3
            retry_delay = 5
            success = False
            for attempt in range(max_retries):
                try:
                    resp = requests.get(url, timeout=15)
                    if resp.status_code == 200:
                        image_path = os.path.join(
                            OUTPUT_DIR,
                            f"{st.session_state.active_session}_0.jpg"
                        )
                        with open(image_path, "wb") as f:
                            f.write(resp.content)

                        st.session_state.memory.chat_memory.add_user_message(
                            f"Prompt: {initial_prompt}, Model: {selected_model}")
                        st.session_state.memory.chat_memory.add_ai_message("Generated image ✅")
                        st.session_state.history.append({
                            "type": "human",
                            "content": f"Prompt: {initial_prompt}, Model: {selected_model}"
                        })
                        st.session_state.history.append({
                            "type": "ai",
                            "content": "Generated image ✅",
                            "image": image_path,
                            "prompt": initial_prompt,
                            "model": selected_model
                        })
                        save_session(st.session_state.active_session, st.session_state.memory, st.session_state.history)
                        success = True
                        break
                    else:
                        if attempt == max_retries - 1:
                            error_msg = f"❌ Image generation failed after {max_retries} attempts. Status: {resp.status_code}. Response: {resp.text}. Try a different prompt or model."
                            st.error(error_msg)
                            st.session_state.memory.chat_memory.add_user_message(
                                f"Prompt: {initial_prompt}, Model: {selected_model}")
                            st.session_state.memory.chat_memory.add_ai_message(error_msg)
                            st.session_state.history.append(
                                {"type": "human", "content": f"Prompt: {initial_prompt}, Model: {selected_model}"})
                            st.session_state.history.append({"type": "ai", "content": error_msg})
                            save_session(st.session_state.active_session, st.session_state.memory,
                                         st.session_state.history)
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        error_msg = f"❌ Image generation failed after {max_retries} attempts. Error: {str(e)}. Try a different prompt or model."
                        st.error(error_msg)
                        st.session_state.memory.chat_memory.add_user_message(
                            f"Prompt: {initial_prompt}, Model: {selected_model}")
                        st.session_state.memory.chat_memory.add_ai_message(error_msg)
                        st.session_state.history.append(
                            {"type": "human", "content": f"Prompt: {initial_prompt}, Model: {selected_model}"})
                        st.session_state.history.append({"type": "ai", "content": error_msg})
                        save_session(st.session_state.active_session, st.session_state.memory, st.session_state.history)
                time.sleep(retry_delay)
            st.rerun()

    # Scrolling images section
    st.markdown('<h3>Explore ImaGenBot AI Creations</h3>', unsafe_allow_html=True)
    image_html = ""
    for image_path, prompt in st.session_state.scrolling_images:
        if image_path and os.path.exists(image_path):
            base64_image = image_to_base64(image_path)
            if base64_image:
                image_html += f'<div class="image-item"><img src="data:image/jpeg;base64,{base64_image}" alt="{prompt}"><p>{prompt}</p></div>'
            else:
                image_html += f'<div class="image-item"><img class="error" src="" alt="{prompt}" style="width: 250px; height: 150px;">Failed to load image<p>{prompt}</p></div>'
        else:
            image_html += f'<div class="image-item"><img class="error" src="" alt="{prompt}" style="width: 250px; height: 150px;">Failed to load image<p>{prompt}</p></div>'

    image_html = image_html + image_html  # Duplicate for seamless scrolling
    st.markdown(
        f'<div class="scrolling-container"><div class="scrolling-images">{image_html}</div></div>',
        unsafe_allow_html=True
    )

# ---------- Sidebar ----------
st.sidebar.title("💬 Previous Chats")

# New Chat Button
if st.sidebar.button("New Chat", key="new_chat", help="Start a new chat session", type="primary"):
    st.session_state.active_session = None
    st.session_state.memory = None
    st.session_state.history = []
    st.rerun()

# Existing Sessions
sessions = list_sessions()
for session_name, recent_prompt in sessions:
    with st.sidebar.container():
        st.markdown('<div class="session-row">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            truncated_prompt = truncate_prompt(recent_prompt)
            if st.button(truncated_prompt, key=f"select_{session_name}", help=f"Select session: {recent_prompt}",
                         type="primary"):
                st.session_state.active_session = session_name
                st.session_state.memory, st.session_state.history = load_session(session_name)
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_{session_name}", help="Delete this chat session", type="secondary"):
                delete_session(session_name)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------- Active Session Area ----------
if st.session_state.active_session:
    st.subheader(f"Chat: {st.session_state.active_session}")

    with st.form(key="prompt_form"):
        txt = st.text_area("Enter another image prompt:", height=120,
                           placeholder="Describe another image to generate...")
        selected_model = st.selectbox("Choose a model:", MODELS, index=0)
        submit_button = st.form_submit_button(label="Generate Image")

    if submit_button and txt:
        with st.spinner("Generating image... This may take a moment."):
            url = f"https://pollinations.ai/p/{txt}?model={selected_model}"
            max_retries = 3
            retry_delay = 5
            success = False
            for attempt in range(max_retries):
                try:
                    resp = requests.get(url, timeout=15)
                    if resp.status_code == 200:
                        image_path = os.path.join(
                            OUTPUT_DIR,
                            f"{st.session_state.active_session}_{len(st.session_state.history) // 2}.jpg"
                        )
                        with open(image_path, "wb") as f:
                            f.write(resp.content)

                        st.session_state.memory.chat_memory.add_user_message(f"Prompt: {txt}, Model: {selected_model}")
                        st.session_state.memory.chat_memory.add_ai_message("Generated image ✅")
                        st.session_state.history.append({
                            "type": "human",
                            "content": f"Prompt: {txt}, Model: {selected_model}"
                        })
                        st.session_state.history.append({
                            "type": "ai",
                            "content": "Generated image ✅",
                            "image": image_path,
                            "prompt": txt,
                            "model": selected_model
                        })
                        save_session(st.session_state.active_session, st.session_state.memory, st.session_state.history)
                        success = True
                        break
                    else:
                        if attempt == max_retries - 1:
                            error_msg = f"❌ Image generation failed after {max_retries} attempts. Status: {resp.status_code}. Response: {resp.text}. Try a different prompt or model."
                            st.error(error_msg)
                            st.session_state.memory.chat_memory.add_user_message(
                                f"Prompt: {txt}, Model: {selected_model}")
                            st.session_state.memory.chat_memory.add_ai_message(error_msg)
                            st.session_state.history.append(
                                {"type": "human", "content": f"Prompt: {txt}, Model: {selected_model}"})
                            st.session_state.history.append({"type": "ai", "content": error_msg})
                            save_session(st.session_state.active_session, st.session_state.memory,
                                         st.session_state.history)
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        error_msg = f"❌ Image generation failed after {max_retries} attempts. Error: {str(e)}. Try a different prompt or model."
                        st.error(error_msg)
                        st.session_state.memory.chat_memory.add_user_message(f"Prompt: {txt}, Model: {selected_model}")
                        st.session_state.memory.chat_memory.add_ai_message(error_msg)
                        st.session_state.history.append(
                            {"type": "human", "content": f"Prompt: {txt}, Model: {selected_model}"})
                        st.session_state.history.append({"type": "ai", "content": error_msg})
                        save_session(st.session_state.active_session, st.session_state.memory, st.session_state.history)
                time.sleep(retry_delay)
            if success:
                st.rerun()

# ---------- Chat History ----------
if st.session_state.history:
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

    for idx, (user_msg, ai_msg) in enumerate(reversed(paired_history)):
        with st.expander(f"Prompt: {user_msg['content'][:50]}...", expanded=idx == 0):
            st.markdown(f"<div class='chat-user'>👤 {user_msg['content']}</div>", unsafe_allow_html=True)
            if ai_msg:
                st.markdown(f"<div class='chat-ai'>🤖 {ai_msg['content']}</div>", unsafe_allow_html=True)
                if "image" in ai_msg and os.path.exists(ai_msg["image"]):
                    st.image(ai_msg["image"], caption=f"Generated from: {ai_msg['prompt']} (Model: {ai_msg['model']})",
                             use_column_width=True)
                    st.download_button(
                        "📥 Download Image",
                        data=open(ai_msg["image"], "rb").read(),
                        file_name=f"generated_image_{idx}.jpg",
                        mime="image/jpeg",
                        key=f"download_{idx}"
                    )
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
