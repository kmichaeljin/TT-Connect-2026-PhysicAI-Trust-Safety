import streamlit as st
import string
import base64
import os
from collections import Counter

# --- NEW IMPORT FOR RAIN EFFECT ---
try:
    from streamlit_extras.let_it_rain import rain
except ImportError:
    def rain(emoji, font_size, falling_speed, animation_length):
        st.error("⚠️ Install 'streamlit-extras' to see the rain effect.")

# --- CONFIGURATION ---
st.set_page_config(page_title="F1 Score Checker", page_icon="📱", layout="centered")

# --- GLOBAL SETTINGS ---
TARGET_PROMPT = "I am a salaryman. I wake up early to catch the morning train. The office coffee is the fuel that keeps me going. Typing reports feels like a marathon of endless keystrokes. I dream of the weekend while staring at my screen."
WINNING_RESULT = "TT Connect 2026: Trust and Safety lang MALAKAS"

# --- SESSION STATE ---
if 'f1_score' not in st.session_state: st.session_state['f1_score'] = 0.0
if 'precision' not in st.session_state: st.session_state['precision'] = 0.0
if 'recall' not in st.session_state: st.session_state['recall'] = 0.0

# --- ASSETS & CSS ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

background_style = """background-color: #000000;"""
if os.path.exists("background.jpg"):
    bin_str = get_base64_of_bin_file("background.jpg")
    background_style = f"""
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    """

st.markdown(f"""
    <style>
    .stApp {{ {background_style} color: #FFFFFF; }}
    .stMarkdown p, .stMarkdown h3, .stMarkdown h2, .stMarkdown div {{ text-align: center !important; }}
    
    /* INPUT FIELDS & DROPDOWNS */
    .stTextArea textarea, .stTextInput input {{
        background-color: rgba(0, 0, 0, 0.8) !important;
        color: #FFFFFF !important;
        border: 2px solid #D71313 !important;
        border-radius: 5px;
        text-align: center;
    }}
    
    /* BUTTONS */
    .stButton > button {{
        background-color: #D71313;
        color: #FFFFFF;
        font-weight: 800;
        border: none;
        border-radius: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
        height: 60px; /* Taller for mobile tapping */
        font-size: 1.2rem;
    }}
    .stButton > button:hover {{ background-color: #ff1f1f; color: #FFFFFF; border: 1px solid white; }}
    
    /* HIDE STREAMLIT UI */
    #MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- F1 LOGIC ---
def calculate_f1(prediction, ground_truth):
    def normalize(text):
        return text.lower().translate(str.maketrans('', '', string.punctuation)).split()
    pred, truth = normalize(prediction), normalize(ground_truth)
    if not pred or not truth: return 0.0, 0.0, 0.0
    common = sum((Counter(pred) & Counter(truth)).values())
    p, r = common / len(pred), common / len(truth)
    return (0.0 if p + r == 0 else 2 * (p * r) / (p + r)), p, r

# --- MOBILE LAYOUT (SINGLE COLUMN) ---

# 1. LOGO
c1, c2, c3 = st.columns([1,2,1])
with c2:
    if os.path.exists("physicai_logo.png"): st.image("physicai_logo.png", use_container_width=True) 
    elif os.path.exists("company_logo.png"): st.image("company_logo.png", width=100)

st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <div style='font-weight: 900; letter-spacing: 3px; font-size: 1.8rem; color: #FFFFFF;'>FINAL QUEST</div>
        <div style='font-weight: 400; letter-spacing: 1px; font-size: 0.9rem; color: #D71313; margin-top: 5px;'>ENTER MASTER PROMPT</div>
    </div>
    """, unsafe_allow_html=True)

# 2. SCOREBOARD HUD
f1_val, prec_val, rec_val = st.session_state['f1_score'], st.session_state['precision'], st.session_state['recall']
st.markdown(f"""
    <div style="background-color: #262626; border: 2px solid #D71313; border-radius: 8px; padding: 15px; margin-bottom: 20px; display: flex; justify-content: space-around; align-items: center;">
        <div style="text-align: center;"><div style="color: #AAA; font-size: 0.7rem;">F1 SCORE</div><div style="color: #D71313; font-size: 2rem; font-weight: 900;">{int(f1_val * 100)}%</div></div>
        <div style="width: 1px; height: 40px; background-color: #444;"></div>
        <div style="text-align: center;"><div style="color: #AAA; font-size: 0.7rem;">PRECISION</div><div style="color: #D71313; font-size: 2rem; font-weight: 900;">{int(prec_val * 100)}%</div></div>
        <div style="width: 1px; height: 40px; background-color: #444;"></div>
        <div style="text-align: center;"><div style="color: #AAA; font-size: 0.7rem;">RECALL</div><div style="color: #D71313; font-size: 2rem; font-weight: 900;">{int(rec_val * 100)}%</div></div>
    </div>
""", unsafe_allow_html=True)

# 3. INPUT
st.markdown("<p style='color: #888; font-size: 0.8rem; margin-bottom: 5px; text-align: center;'>INPUT SEQUENCE</p>", unsafe_allow_html=True)
user_input = st.text_area("Input Phrase:", placeholder="Type code here...", label_visibility="collapsed", height=120)

st.write("") 

# 4. ACTION BUTTON
if st.button("LOCK IN", use_container_width=True): 
    if not user_input:
        st.error("⚠️ PROMPT REQUIRED")
    else:
        # Calculate F1 locally only
        f1, prec, rec = calculate_f1(user_input, TARGET_PROMPT)
        st.session_state.update({'f1_score': f1, 'precision': prec, 'recall': rec})
        st.rerun()

# 5. RESULTS
if st.session_state['f1_score'] > 0:
    f1_score = st.session_state['f1_score']
    st.write("")
    if f1_score == 1.0:
        try: rain(emoji="🟥 ⬜ 🛡️", font_size=40, falling_speed=5, animation_length="3s")
        except: st.balloons()
        st.toast("🔒 QUEST COMPLETE", icon="✅")
        st.markdown(f"""<div style="background-color: #000; border: 1px solid #00FF41; padding: 15px; text-align: center; box-shadow: 0 0 20px rgba(0,255,65,0.2);"><h3 style="color: #FFF; font-size: 0.8rem; opacity: 0.8;">QUEST STATUS:</h3><h1 style="color: #00FF41; margin: 10px 0; font-size: 1.2rem; font-weight: 900;">{WINNING_RESULT}</h1></div>""", unsafe_allow_html=True)
    elif f1_score >= 0.8: st.warning(f"⚠️ FORM CHECK // ONE REP LEFT: {int(f1_score*100)}%")
    elif f1_score >= 0.5: st.info(f"⚠️ NOT STRONG ENOUGH: {int(f1_score*100)}%")
    else: st.error("❌ FAILED LIFT // NO REP")

st.caption("PHYSICAI // CHECKER TERMINAL")