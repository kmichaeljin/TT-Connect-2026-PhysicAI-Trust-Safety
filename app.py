import streamlit as st
import pandas as pd
import string
import base64
import os
import time
from collections import Counter

# --- GOOGLE SHEETS IMPORTS ---
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- NEW IMPORT FOR RAIN EFFECT ---
try:
    from streamlit_extras.let_it_rain import rain
except ImportError:
    def rain(emoji, font_size, falling_speed, animation_length):
        st.error("⚠️ Install 'streamlit-extras' to see the rain effect.")

# --- CONFIGURATION ---
st.set_page_config(page_title="PHYSICAI Agent", page_icon="🛡️", layout="wide")

# --- GLOBAL SETTINGS ---
TEAMS_LIST = [
    "BLUE ANALYSTS",
    "GREEN DETECTIVES",
    "YELLOW MEDIATORS",
    "GRAY SHIELDS",
    "VIOLET STRATEGISTS",
    "PINK FIREFIGHTERS"
]

ADMIN_PASSWORD = "COMMUNITY"
TARGET_PROMPT = "I am a salaryman. I wake up early to catch the morning train. The office coffee is the fuel that keeps me going. Typing reports feels like a marathon of endless keystrokes. I dream of the weekend while staring at my screen."
WINNING_RESULT = "TT Connect 2026: Trust and Safety lang MALAKAS"

SHEET_NAME = "PhysicAI_Leaderboard"
WORKSHEET_SCORES = "Sheet1"
WORKSHEET_MEDALS = "Medals"

# --- CACHED CONNECTION (FIXES LAG) ---
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

# --- CACHED DATA LOADING ---
@st.cache_data(ttl=5)
def get_cached_leaderboard():
    sheet = connect_to_sheet(WORKSHEET_SCORES)
    if sheet:
        try:
            data = sheet.get_all_records()
            if data:
                return pd.DataFrame(data)
        except:
            pass
    return pd.DataFrame(columns=["Team", "Score"])

@st.cache_data(ttl=5)
def get_cached_medals():
    sheet = connect_to_sheet(WORKSHEET_MEDALS)
    if sheet:
        try:
            data = sheet.get_all_records()
            if data:
                return pd.DataFrame(data)
        except:
            pass
    return pd.DataFrame(columns=["Quest", "Gold", "Silver", "Bronze"])

# --- WRITE FUNCTIONS ---
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
    get_cached_leaderboard.clear()

def record_medal_winners(quest_name, gold_team, silver_team, bronze_team):
    sheet = connect_to_sheet(WORKSHEET_MEDALS)
    if sheet:
        sheet.append_row([quest_name, gold_team, silver_team, bronze_team])
    get_cached_medals.clear()

def wipe_data():
    sheet1 = connect_to_sheet(WORKSHEET_SCORES)
    if sheet1:
        sheet1.clear()
        sheet1.append_row(["Team", "Score"])
    
    sheet2 = connect_to_sheet(WORKSHEET_MEDALS)
    if sheet2:
        sheet2.clear()
        sheet2.append_row(["Quest", "Gold", "Silver", "Bronze"])
    
    get_cached_leaderboard.clear()
    get_cached_medals.clear()

# --- HELPER: MEDAL TALLY ---
def get_medal_standings(medal_df):
    if medal_df.empty:
        return pd.DataFrame(columns=["Team", "🥇", "🥈", "🥉"])
    
    all_teams = set(medal_df["Gold"]).union(set(medal_df["Silver"])).union(set(medal_df["Bronze"]))
    if "" in all_teams: all_teams.remove("")
    
    standings = []
    for team in all_teams:
        golds = len(medal_df[medal_df["Gold"] == team])
        silvers = len(medal_df[medal_df["Silver"] == team])
        bronzes = len(medal_df[medal_df["Bronze"] == team])
        sort_score = (golds * 3) + (silvers * 2) + (bronzes * 1)
        # FIX: The colon was missing below
        standings.append({"Team": team, "🥇": golds, "🥈": silvers, "🥉": bronzes, "Sort": sort_score})
    
    df = pd.DataFrame(standings)
    if not df.empty:
        df = df.sort_values(by="Sort", ascending=False).drop(columns=["Sort"])
    return df

# --- SESSION STATE ---
if 'f1_score' not in st.session_state: st.session_state['f1_score'] = 0.0
if 'precision' not in st.session_state: st.session_state['precision'] = 0.0
if 'recall' not in st.session_state: st.session_state['recall'] = 0.0
if 'admin_logged_in' not in st.session_state: st.session_state['admin_logged_in'] = False

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
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
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
        height: 50px; 
    }}
    .stButton > button:hover {{ background-color: #ff1f1f; color: #FFFFFF; border: 1px solid white; }}
    
    /* HIDE STREAMLIT UI */
    #MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}
    
    /* TABLES */
    th {{ background-color: #262626 !important; color: #D71313 !important; border-bottom: 2px solid #D71313 !important; }}
    td {{ background-color: #111 !important; color: white !important; border-bottom: 1px solid #333 !important; }}
    
    /* --- ADMIN PANEL STYLING (NEW) --- */
    /* Target the Expander container */
    div[data-testid="stExpander"] {{
        background-color: #111111 !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
        margin-top: 20px;
    }}
    /* Target the Header of the Expander */
    div[data-testid="stExpander"] details summary {{
        color: #888888 !important; 
        font-weight: bold !important;
    }}
    div[data-testid="stExpander"] details[open] summary {{
        color: #D71313 !important; /* Red when open */
    }}
    /* Target the Content inside the Expander */
    div[data-testid="stExpander"] div[data-testid="stExpanderContent"] {{
        background-color: #000000 !important;
        color: white !important;
        padding: 20px !important;
        border-top: 1px solid #333 !important;
    }}
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

# --- LAYOUT ---
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("physicai_logo.png"): st.image("physicai_logo.png", use_container_width=True) 
        elif os.path.exists("company_logo.png"): st.image("company_logo.png", width=100)
    
    st.markdown("""
        <div style='text-align: center; margin-bottom: 30px;'>
            <div style='font-weight: 900; letter-spacing: 3px; font-size: 2rem; color: #FFFFFF;'>FINAL QUEST</div>
            <div style='font-weight: 400; letter-spacing: 1px; font-size: 1rem; color: #D71313; margin-top: 5px;'>ENTER YOUR MASTER PROMPT</div>
        </div>
        """, unsafe_allow_html=True)

    f1_val, prec_val, rec_val = st.session_state['f1_score'], st.session_state['precision'], st.session_state['recall']
    st.markdown(f"""
        <div style="background-color: #262626; border: 2px solid #D71313; border-radius: 8px; padding: 20px; margin-bottom: 20px; display: flex; justify-content: space-around; align-items: center;">
            <div style="text-align: center;"><div style="color: #AAA; font-size: 0.8rem;">F1 SCORE</div><div style="color: #D71313; font-size: 2.5rem; font-weight: 900;">{int(f1_val * 100)}%</div></div>
            <div style="width: 1px; height: 50px; background-color: #444;"></div>
            <div style="text-align: center;"><div style="color: #AAA; font-size: 0.8rem;">PRECISION</div><div style="color: #D71313; font-size: 2.5rem; font-weight: 900;">{int(prec_val * 100)}%</div></div>
            <div style="width: 1px; height: 50px; background-color: #444;"></div>
            <div style="text-align: center;"><div style="color: #AAA; font-size: 0.8rem;">RECALL</div><div style="color: #D71313; font-size: 2.5rem; font-weight: 900;">{int(rec_val * 100)}%</div></div>
        </div>
    """, unsafe_allow_html=True)

with right_col:
    st.write(""); st.write("")
    st.markdown("<p style='color: #888; font-size: 0.8rem; margin-bottom: 5px; text-align: center;'>IDENTIFY YOUR SQUAD</p>", unsafe_allow_html=True)
    team_name_input = st.selectbox("Team Name", TEAMS_LIST, index=None, placeholder="SELECT YOUR TEAM", label_visibility="collapsed")
    st.write("")
    st.markdown("<p style='color: #888; font-size: 0.8rem; margin-bottom: 5px; text-align: center;'>INPUT SEQUENCE</p>", unsafe_allow_html=True)
    user_input = st.text_area("Input Phrase:", placeholder="Type code here...", label_visibility="collapsed", height=150)
    st.write("")
    
    if st.button("LOCK IN", use_container_width=True): 
        if not user_input or not team_name_input:
            st.error("⚠️ PROMPT AND TEAM REQUIRED")
        else:
            f1, prec, rec = calculate_f1(user_input, TARGET_PROMPT)
            st.session_state.update({'f1_score': f1, 'precision': prec, 'recall': rec})
            update_leaderboard(team_name_input.upper(), int(f1 * 100))
            st.rerun()

    if st.session_state['f1_score'] > 0:
        f1_score = st.session_state['f1_score']
        st.write("")
        if f1_score == 1.0:
            try: rain(emoji="🟥 ⬜ 🛡️", font_size=54, falling_speed=5, animation_length="3s")
            except: st.balloons()
            st.toast("🔒 QUEST COMPLETE", icon="✅")
            st.markdown(f"""<div style="background-color: #000; border: 1px solid #00FF41; padding: 20px; text-align: center; box-shadow: 0 0 20px rgba(0,255,65,0.2);"><h3 style="color: #FFF; font-size: 0.8rem; opacity: 0.8;">QUEST STATUS:</h3><h1 style="color: #00FF41; margin: 15px 0; font-size: 1.5rem; font-weight: 900;">{WINNING_RESULT}</h1></div>""", unsafe_allow_html=True)
        elif f1_score >= 0.8: st.warning(f"⚠️ FORM CHECK // ONE REP LEFT: {int(f1_score*100)}%")
        elif f1_score >= 0.5: st.info(f"⚠️ NOT STRONG ENOUGH: {int(f1_score*100)}%")
        else: st.error("❌ FAILED LIFT // NO REP")

st.divider()
lb_col1, lb_col2 = st.columns(2, gap="large")

with lb_col1:
    st.markdown("<h3 style='text-align: center; color: #888; letter-spacing: 2px; font-size:1.2rem;'>// LIVE TEAM LEADERBOARD //</h3>", unsafe_allow_html=True)
    df_scores = get_cached_leaderboard() 
    if not df_scores.empty:
        st.dataframe(df_scores.sort_values(by="Score", ascending=False), hide_index=True, use_container_width=True, column_config={"Team": st.column_config.TextColumn("SQUAD"), "Score": st.column_config.ProgressColumn("F1 SCORE", format="%d%%", min_value=0, max_value=100)})
    else: st.caption("AWAITING DATA...")

with lb_col2:
    st.markdown("<h3 style='text-align: center; color: #888; letter-spacing: 2px; font-size:1.2rem;'>// MEDAL STANDINGS //</h3>", unsafe_allow_html=True)
    df_medals = get_medal_standings(get_cached_medals()) 
    if not df_medals.empty: st.dataframe(df_medals, hide_index=True, use_container_width=True, column_config={"Team": st.column_config.TextColumn("SQUAD")})
    else: st.caption("AWAITING QUEST RESULTS...")

st.write(""); st.write("")

# --- UPDATED ADMIN PANEL WITH CSS BOX ---
with st.expander("⚙️ ADMIN PROTOCOLS (RESTRICTED)"):
    if not st.session_state['admin_logged_in']:
        c_pass, c_btn = st.columns([3, 1])
        with c_pass:
            admin_pass_input = st.text_input("ENTER ADMIN KEY:", type="password", key="login_pass")
        with c_btn:
            st.write("") # Spacer to align button
            st.write("") 
            if st.button("🔓 LOGIN", use_container_width=True):
                if admin_pass_input == ADMIN_PASSWORD:
                    st.session_state['admin_logged_in'] = True
                    st.rerun()
                else:
                    st.error("❌ INVALID KEY")
    else:
        st.success("✅ SYSTEM ACCESS GRANTED")
        
        tab1, tab2 = st.tabs(["🏅 AWARD MEDALS", "🔴 DANGER ZONE"])
        
        with tab1:
            st.info("Award Medals (Auto-filters previously selected teams)")
            quest_select = st.selectbox("Select Quest:", ["Quest 1", "Quest 2", "Quest 3", "Quest 4", "Quest 5"])
            
            # SMART FILTERING (Requires Page Reload)
            col_g, col_s, col_b = st.columns(3)
            with col_g:
                gold = st.selectbox("🥇 GOLD", TEAMS_LIST, index=None, placeholder="Winner")
            silver_options = [t for t in TEAMS_LIST if t != gold] if gold else TEAMS_LIST
            with col_s:
                silver = st.selectbox("🥈 SILVER", silver_options, index=None, placeholder="2nd")
            bronze_options = [t for t in silver_options if t != silver] if silver else silver_options
            with col_b:
                bronze = st.selectbox("🥉 BRONZE", bronze_options, index=None, placeholder="3rd")
            
            if st.button("SUBMIT MEDAL RESULTS", use_container_width=True):
                if gold and silver and bronze:
                    with st.spinner("Writing to Database..."):
                        record_medal_winners(quest_select, gold, silver, bronze)
                    st.success(f"Saved: {quest_select}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("⚠️ Select all 3 winners first.")

        with tab2:
            st.warning("This action cannot be undone.")
            if st.button("🔴 WIPE EVERYTHING"):
                with st.spinner("Purging Systems..."):
                    wipe_data()
                st.success("CLEAN SLATE.")
                time.sleep(1)
                st.rerun()
        
        if st.button("LOG OUT"):
            st.session_state['admin_logged_in'] = False
            st.rerun()

st.caption("PHYSICAI // TRUST & SAFETY BREAKOUT SESSION")
