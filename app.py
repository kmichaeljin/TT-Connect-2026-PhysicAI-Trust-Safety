import streamlit as st
import string
import base64
import os
import time
from collections import Counter

# --- NEW IMPORT FOR RAIN EFFECT ---
try:
    from streamlit_extras.let_it_rain import rain
except ImportError:
    def rain(emoji, font_size, falling_speed, animation_length):
        st.error("⚠️ Install 'streamlit-extras' to see the rain effect.")

# --- CONFIGURATION ---
st.set_page_config(page_title="PHYSICAI Agent", page_icon="🛡️", layout="centered")

# --- INITIALIZE SESSION STATE ---
if 'f1_score' not in st.session_state:
    st.session_state['f1_score'] = 0.0
if 'precision' not in st.session_state:
    st.session_state['precision'] = 0.0
if 'recall' not in st.session_state:
    st.session_state['recall'] = 0.0

# GAME VARIABLES
TARGET_PROMPT = "The strength of the team is each individual member"
WINNING_RESULT = "🚀 WINNING CODE: 'BLUE-OCEAN-2024'"

# --- HELPER: BACKGROUND IMAGE LOADER ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- CSS STYLING ---
background_style = """
    background-color: #000000;
"""

if os.path.exists("background.jpg"):
    bin_str = get_base64_of_bin_file("background.jpg")
    background_style = f"""
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    """
elif os.path.exists("background.png"):
    bin_str = get_base64_of_bin_file("background.png")
    background_style = f"""
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    """

st.markdown(f"""
    <style>
    /* 1. APPLY BACKGROUND */
    .stApp {{
        {background_style}
        color: #FFFFFF;
    }}
    
    /* 2. TEXT CENTERING */
    .stMarkdown p, .stMarkdown h3, .stMarkdown h2, .stMarkdown div {{
        text-align: center !important;
    }}
    
    /* 3. INPUT BOX STYLING */
    .stTextArea textarea {{
        background-color: rgba(0, 0, 0, 0.8) !important;
        color: #FFFFFF !important;
        border: 2px solid #D71313 !important;
        border-radius: 5px;
        text-align: center;
    }}
    
    /* 4. BUTTON STYLING */
    .stButton > button {{
        background-color: #D71313;
        color: #FFFFFF;
        font-weight: 800;
        border: none;
        border-radius: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .stButton > button:hover {{
        background-color: #ff1f1f;
        color: #FFFFFF;
        border: 1px solid white;
    }}
    
    /* 5. HIDE HEADER/FOOTER */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- F1 SCORE LOGIC ---
def calculate_f1(prediction, ground_truth):
    def normalize(text):
        return text.lower().translate(str.maketrans('', '', string.punctuation)).split()
    
    pred_tokens = normalize(prediction)
    truth_tokens = normalize(ground_truth)
    
    if not pred_tokens or not truth_tokens:
        return 0.0, 0.0, 0.0

    pred_counts = Counter(pred_tokens)
    truth_counts = Counter(truth_tokens)
    
    common_tokens = pred_counts & truth_counts
    num_common = sum(common_tokens.values())
    
    precision = num_common / len(pred_tokens)
    recall = num_common / len(truth_tokens)
    
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)
        
    return f1, precision, recall

# --- UI LAYOUT ---

# 1. LOGOS
col_left, col_mid, col_right = st.columns([1, 2, 1])

with col_mid:
    sub_l, sub_m, sub_r = st.columns([1, 1, 1]) 
    with sub_m:
        if os.path.exists("company_logo.png"):
            st.image("company_logo.png", width=100) 
            
    if os.path.exists("physicai_logo.png"):
        st.image("physicai_logo.png", width=400) 

st.write("") 

# 2. STATUS TEXT
st.markdown("""
    <style>
    .cinematic-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 3px;
        font-size: 1.5rem;
        color: #FFFFFF;
        margin-bottom: 0px;
    }
    .cinematic-sub {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.9rem;
        color: #D71313;
        margin-top: 5px;
    }
    </style>
    <div style='text-align: center; margin-bottom: 20px;'>
        <div class='cinematic-header'>FINAL QUEST</div>
        <div class='cinematic-sub'>ENTER YOUR MASTER PROMPT</div>
    </div>
    """, unsafe_allow_html=True)

# --- NEW: CUSTOM HTML SCOREBOARD (Percentages) ---
f1_val = st.session_state['f1_score']
prec_val = st.session_state['precision']
rec_val = st.session_state['recall']

# We convert to integer percentage for display (e.g. 0.85 -> 85%)
st.markdown(f"""
    <div style="
        background-color: #262626; 
        border: 2px solid #D71313; 
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        width: 100%;
    ">
        <div style="text-align: center;">
            <div style="color: #AAAAAA; font-size: 0.8rem; letter-spacing: 1px;">F1 SCORE</div>
            <div style="color: #D71313; font-size: 1.8rem; font-weight: 900;">{int(f1_val * 100)}%</div>
        </div>
        <div style="width: 1px; height: 40px; background-color: #444;"></div>
        <div style="text-align: center;">
            <div style="color: #AAAAAA; font-size: 0.8rem; letter-spacing: 1px;">PRECISION</div>
            <div style="color: #D71313; font-size: 1.8rem; font-weight: 900;">{int(prec_val * 100)}%</div>
        </div>
        <div style="width: 1px; height: 40px; background-color: #444;"></div>
        <div style="text-align: center;">
            <div style="color: #AAAAAA; font-size: 0.8rem; letter-spacing: 1px;">RECALL</div>
            <div style="color: #D71313; font-size: 1.8rem; font-weight: 900;">{int(rec_val * 100)}%</div>
        </div>
    </div>
""", unsafe_allow_html=True)


# 3. INPUT & BUTTON
input_col_L, input_col_M, input_col_R = st.columns([1, 3, 1])

with input_col_M:
    user_input = st.text_area("Input Phrase:", placeholder="Type code here...", label_visibility="collapsed", height=100)
    
    st.write("") 
    
    if st.button("LOCK IN", use_container_width=True): 
        if not user_input:
            st.error("⚠️ PROMPT REQUIRED")
        else:
            # 1. CALCULATE SCORES
            f1, prec, rec = calculate_f1(user_input, TARGET_PROMPT)
            
            # 2. UPDATE SESSION STATE
            st.session_state['f1_score'] = f1
            st.session_state['precision'] = prec
            st.session_state['recall'] = rec
            
            # 3. FORCE REFRESH to update the HTML box above
            st.rerun()

# --- RESULTS LOGIC ---
if st.session_state['f1_score'] > 0:
    f1_score = st.session_state['f1_score']
    
    st.write("")
    
    if f1_score == 1.0:
        try:
            rain(
                emoji="🟥 ⬜ 🛡️", 
                font_size=54,    
                falling_speed=5, 
                animation_length="3s",
            )
        except:
            st.balloons()

        st.toast("🔒 SYSTEM UNLOCKED", icon="✅")
        st.markdown(f"""
            <div style="
                background-color: #000000; 
                border: 1px solid #00FF41; 
                padding: 20px; 
                margin-top: 10px;
                text-align: center;
                box-shadow: 0 0 20px rgba(0, 255, 65, 0.2);">
                <h3 style="color: #FFFFFF; margin: 0; font-family: 'Helvetica Neue', sans-serif; font-size: 0.8rem; letter-spacing: 2px; opacity: 0.8;">ACCESS CODE GRANTED:</h3>
                <h1 style="color: #00FF41; margin: 15px 0; font-family: 'Helvetica Neue', sans-serif; font-size: 2.2rem; font-weight: 900; letter-spacing: 4px;">BLUE-OCEAN-2024</h1>
            </div>
        """, unsafe_allow_html=True)
        
    elif f1_score >= 0.8:
        st.warning(f"⚠️ MATCH: {int(f1_score*100)}% // CHECK SYNTAX")
    elif f1_score >= 0.5:
        st.info(f"⚠️ MATCH: {int(f1_score*100)}% // PARTIAL DATA DETECTED")
    else:
        st.error("❌ ACCESS DENIED")

st.divider()
st.caption("PHYSICAI // TRUST & SAFETY BREAKOUT SESSION")