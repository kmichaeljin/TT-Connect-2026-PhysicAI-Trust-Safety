import streamlit as st
import string
import base64
import os
from collections import Counter
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- NEW IMPORT FOR RAIN EFFECT ---
try:
    from streamlit_extras.let_it_rain import rain
except ImportError:
    def rain(emoji, font_size, falling_speed, animation_length):
        pass

# --- CONFIGURATION ---
st.set_page_config(page_title="Input Terminal", page_icon="💻", layout="centered")

# --- GLOBAL SETTINGS ---
TEAMS_LIST = [
    "BLUE ANALYSTS",
    "GRAY SHIELDS",
    "GREEN DETECTIVES",
    "VIOLET STRATEGISTS"
]

TARGET_PROMPT = "True strength is never built in isolation, but forged through the relentless effort of a united squad. When we pool our diverse talents, we inherently accomplish more than the mere sum of our separate actions. The heaviest burden feels surprisingly manageable when distributed evenly across dedicated shoulders. We must continuously align our strategies and protect each other's blind spots during the chaos. Only by moving as one cohesive unit can we shatter our perceived limits and secure the ultimate victory."
WINNING_RESULT = "TT Connect 2026: Accomplish more"

SHEET_NAME = "PhysicAI_Leaderboard"
WORKSHEET_SCORES = "Sheet1"

# --- GOOGLE SHEETS DATABASE LOGIC ---
@st.cache_resource
def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def connect_to_sheet(worksheet_name):
    try:
        client = get_gspread_client()
        return client.open(SHEET_NAME).worksheet(worksheet_name)
    except Exception as e:
        return None

def update_leaderboard(team_name, new_score):
    sheet = connect_to_sheet(WORKSHEET_SCORES)
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty and team_name in df["Team"].values:
            row_idx = df.index[df["Team"] == team_name].tolist()[0] + 2
            current_best = df.loc[df["Team"] == team_name, "Score"].max()
            if new_score > current_best:
                sheet.update_cell(row_idx, 2, new_score)
        else:
            sheet.append_row([team_name, new_score])

# --- SESSION STATE ---
if 'f1_score' not in st.session_state: st.session_state['f1_score'] = 0.0
if 'precision' not in st.session_state: st.session_state['precision'] = 0.0
if 'recall' not in st.session_state: st.session_state['recall'] = 0.0
if 'submission_status' not in st.session_state: st.session_state['submission_status'] = None

# --- F1 LOGIC ---
def calculate_f1(prediction, ground_truth):
    def normalize(text):
        return text.lower().translate(str.maketrans('', '', string.punctuation)).split()
    pred, truth = normalize(prediction), normalize(ground_truth)
    if not pred or not truth: return 0.0, 0.0, 0.0
    common = sum((Counter(pred) & Counter(truth)).values())
    p, r = common / len(pred), common / len(truth)
    return (0.0 if p + r == 0 else 2 * (p * r) / (p + r)), p, r

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
    
    div[data-testid="block-container"] {{
        background-color: rgba(0, 0, 0, 0.90) !important; 
        border: 1px solid #333 !important;
        border-radius: 15px;
        padding: 3rem !important;
        margin-top: 2rem;
    }}
    
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
        background-color: rgba(0, 0, 0, 0.8) !important;
        color: #FFFFFF !important;
        border: 2px solid #D71313 !important;
        border-radius: 5px;
        text-align: center;
    }}
    
    .btn-test > button {{
        background-color: #222;
        color: #FFF;
        font-weight: 800;
        border: 1px solid #00FF41;
        border-radius: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
        height: 50px; 
        width: 100%;
        transition: all 0.3s;
    }}
    .btn-test > button:hover {{ background-color: #00FF41; color: #000; }}
    
    .btn-lock > button {{
        background-color: #D71313;
        color: #FFFFFF;
        font-weight: 800;
        border: none;
        border-radius: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
        height: 50px; 
        width: 100%;
        transition: all 0.3s;
    }}
    .btn-lock > button:hover {{ background-color: #ff1f1f; color: #FFFFFF; border: 1px solid white; }}
    
    #MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- HEADER WITH LOGO ---
c1, c2, c3 = st.columns([1,2,1])
with c2:
    if os.path.exists("physicai_logo.png"): st.image("physicai_logo.png", use_container_width=True) 

st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <div style='font-weight: 900; letter-spacing: 3px; font-size: 2.5rem; color: #FFFFFF;'>FINAL QUEST</div>
        <div style='font-weight: 400; letter-spacing: 2px; font-size: 1rem; color: #D71313; margin-top: 5px;'>SANDBOX & SUBMISSION TERMINAL</div>
    </div>
    """, unsafe_allow_html=True)

# --- F1 DISPLAY HUD ---
f1_val, prec_val, rec_val = st.session_state['f1_score'], st.session_state['precision'], st.session_state['recall']
st.markdown(f"""
    <div style="background-color: #111; border: 2px solid #D71313; border-radius: 8px; padding: 20px; margin-bottom: 20px; display: flex; justify-content: space-around; align-items: center;">
        <div style="text-align: center;"><div style="color: #AAA; font-size: 0.8rem;">F1 SCORE</div><div style="color: #D71313; font-size: 2.5rem; font-weight: 900;">{int(f1_val * 100)}%</div></div>
        <div style="width: 1px; height: 50px; background-color: #444;"></div>
        <div style="text-align: center;"><div style="color: #AAA; font-size: 0.8rem;">PRECISION</div><div style="color: #D71313; font-size: 2.5rem; font-weight: 900;">{int(prec_val * 100)}%</div></div>
        <div style="width: 1px; height: 50px; background-color: #444;"></div>
        <div style="text-align: center;"><div style="color: #AAA; font-size: 0.8rem;">RECALL</div><div style="color: #D71313; font-size: 2.5rem; font-weight: 900;">{int(rec_val * 100)}%</div></div>
    </div>
""", unsafe_allow_html=True)

st.write("")

# --- INPUT SECTION ---
team_name_input = st.selectbox("Team Name", TEAMS_LIST, index=None, placeholder="SELECT YOUR SQUAD", label_visibility="collapsed")
st.write("")
user_input = st.text_area("Input Phrase:", placeholder="Type deciphered code here...", label_visibility="collapsed", height=150)
st.write("")

# --- TWO BUTTON LAYOUT ---
btn_col1, btn_col2 = st.columns(2, gap="large")

with btn_col1:
    st.markdown("<div class='btn-test'>", unsafe_allow_html=True)
    if st.button("🧪 TEST PROMPT (SANDBOX)"):
        if not user_input or not team_name_input:
            st.error("⚠️ PROMPT AND TEAM REQUIRED")
        else:
            f1, prec, rec = calculate_f1(user_input, TARGET_PROMPT)
            st.session_state.update({
                'f1_score': f1, 
                'precision': prec, 
                'recall': rec,
                'submission_status': "tested"
            })
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with btn_col2:
    st.markdown("<div class='btn-lock'>", unsafe_allow_html=True)
    if st.button("🔒 LOCK IN FINAL ANSWER"):
        if not user_input or not team_name_input:
            st.error("⚠️ PROMPT AND TEAM REQUIRED")
        else:
            with st.spinner("Analyzing accuracy and transmitting to Main Dashboard..."):
                f1, prec, rec = calculate_f1(user_input, TARGET_PROMPT)
                st.session_state.update({
                    'f1_score': f1, 
                    'precision': prec, 
                    'recall': rec,
                    'submission_status': "locked"
                })
                # THIS IS THE ONLY BUTTON THAT WRITES TO THE DATABASE
                update_leaderboard(team_name_input.upper(), int(f1 * 100))
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- RESULT LOGIC ---
if st.session_state['f1_score'] > 0:
    f1_score = st.session_state['f1_score']
    status = st.session_state['submission_status']
    
    st.write("")
    
    # Check if they just tested or actually locked it in
    if status == "tested":
        st.info("ℹ️ SANDBOX MODE: Score calculated but NOT saved to the leaderboard.")
    elif status == "locked":
        st.toast("🔒 DATA SENT TO MAIN DASHBOARD", icon="✅")
        st.success("✅ OFFICIAL SUBMISSION: Score locked into the Main Dashboard!")

    # Standard Tier warnings
    if f1_score == 1.0:
        if status == "locked":
            try: rain(emoji="🟥 ⬜ 🛡️", font_size=54, falling_speed=5, animation_length="3s")
            except: st.balloons()
        st.markdown(f"""<div style="background-color: #000; border: 1px solid #00FF41; padding: 20px; text-align: center; box-shadow: 0 0 20px rgba(0,255,65,0.2);"><h3 style="color: #FFF; font-size: 0.8rem; opacity: 0.8;">QUEST STATUS:</h3><h1 style="color: #00FF41; margin: 15px 0; font-size: 1.5rem; font-weight: 900;">{WINNING_RESULT}</h1></div>""", unsafe_allow_html=True)
    elif f1_score >= 0.8: st.warning(f"⚠️ FORM CHECK // ONE REP LEFT: {int(f1_score*100)}%")
    elif f1_score >= 0.5: st.info(f"⚠️ NOT STRONG ENOUGH: {int(f1_score*100)}%")
    else: st.error("❌ FAILED LIFT // NO REP")
