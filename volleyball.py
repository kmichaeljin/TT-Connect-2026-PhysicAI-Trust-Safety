import streamlit as st
import base64
import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import ssl
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# --- NEW IMPORT FOR RAIN EFFECT ---
try:
    from streamlit_extras.let_it_rain import rain
except ImportError:
    def rain(emoji, font_size, falling_speed, animation_length):
        pass

# --- CONFIGURATION ---
st.set_page_config(page_title="Tournament Bracket", page_icon="🏆", layout="wide")

TOURNAMENT_NAME = "QUEST 1: BEACH VOLLEYBALL"

# --- GLOBAL SETTINGS ---
TEAMS_LIST = [
    "BLUE ANALYSTS",
    "GRAY SHIELDS",
    "GREEN DETECTIVES",
    "VIOLET STRATEGISTS"
]

SHEET_NAME = "PhysicAI_Leaderboard"
WORKSHEET_MEDALS = "Medals"

# --- SLACK CONFIGURATION & CLUE VAULT ---
SLACK_CHANNEL_IDS = {
    "BLUE ANALYSTS": "C0B37MCBMC5",
    "GRAY SHIELDS": "C0B34PKDQNP",
    "GREEN DETECTIVES": "C0B37PS0HBP",
    "VIOLET STRATEGISTS": "C0B45EACJCQ"
}

# Safely generate Slack's Markdown triple-backticks so it doesn't break our code editor!
CB = "`" * 3 

# 🚨 LIVE VOLLEYBALL CLUES 🚨
CLUE_VAULT = {
    "🥇 GOLD": f"{CB}effort a isolation, of built through squad. relentless united but is True never forged strength in{CB}",
    "🥈 SILVER": f"{CB}eTru thgstrne is erenv tiblu in ooilsaint, utb rgeodf guohhrt eht tnleselser fetofr fo a tiendu asuod.{CB}",
    "🥉 BRONZE": f"{CB}T _ _ e | s _ _ _ _ _ _ h | _s | n _ _ _ r | b _ _ _ t | _ n | i _ _ _ _ _ _ n, | b _ t | f _ _ _ _ d | t _ _ _ _ _ h | t _ e | r _ _ _ _ _ _ _ _ s | e _ _ _ _ t | _ f | a | u _ _ _ _ d | s _ _ _ d.\n\nThe | acts as a space, when decoding, make sure to remove the |{CB}",
    "🪵 WOOD": f"{CB}• Length: 17 words\n• Punctuation: Comma after the 7th word. Period at the end.\n• Meaning: Real strength does not come from being alone; it is created through relentless teamwork.\n• Wording clues: Includes the exact phrases “never built in isolation” and “forged through.”\n• Ending clue: The final two words are “united squad.”{CB}"
}

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
        # 🚨 THIS WILL NOW PRINT THE EXACT ERROR IN RED 🚨
        st.error(f"🚨 GOOGLE SHEETS ERROR: {e}") 
        return None

def save_tournament_results(quest_name, gold, silver, bronze, wood):
    sheet = connect_to_sheet(WORKSHEET_MEDALS)
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Smart Overwrite
        if not df.empty and quest_name in df["Quest"].values:
            row_idx = df.index[df["Quest"] == quest_name].tolist()[0] + 2
            sheet.update_cell(row_idx, 2, gold)
            sheet.update_cell(row_idx, 3, silver)
            sheet.update_cell(row_idx, 4, bronze)
            sheet.update_cell(row_idx, 5, wood) 
        else:
            sheet.append_row([quest_name, gold, silver, bronze, wood]) 
        return True
    return False

# --- SLACK CLUE DELIVERY LOGIC ---
def deliver_clues_to_slack(gold_team, silver_team, bronze_team, wood_team):
    if "slack_bot_token" not in st.secrets:
        return False, "Slack Bot Token not found in Streamlit secrets!"
    
    # Create an unverified SSL context for local Mac testing bypass
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
        
    client = WebClient(token=st.secrets["slack_bot_token"], ssl=ssl_context)
    
    # Map the TIER to the WINNING TEAM
    placements = {
        "🥇 GOLD": gold_team,
        "🥈 SILVER": silver_team,
        "🥉 BRONZE": bronze_team,
        "🪵 WOOD": wood_team
    }
    
    errors = []
    for tier, team in placements.items():
        if not team: continue # Skips if no team is selected
        
        channel_id = SLACK_CHANNEL_IDS.get(team)
        clue_text = CLUE_VAULT.get(tier)
        
        if channel_id and channel_id.startswith("C"):  
            try:
                # YOUR NEW STANDARDIZED MESSAGE FORMAT
                message = (
                    f"Congratulations on finishing Quest 1: Volleyball! Your team placed: {tier}\n\n"
                    f"Here's your clue, goodluck on decoding! :\n"
                    f"{clue_text}"
                )
                client.chat_postMessage(channel=channel_id, text=message)
            except SlackApiError as e:
                errors.append(f"Failed to send to {team}: {e.response['error']}")
                
    if errors:
        return False, " | ".join(errors)
    return True, "Success"

# --- FINALE BROADCAST LOGIC ---
def check_and_broadcast_finale():
    sheet = connect_to_sheet(WORKSHEET_MEDALS)
    if not sheet: return False
    
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Check if 5 distinct quests are in the database
    if not df.empty and "Quest" in df.columns and len(df["Quest"].unique()) >= 5:
        
        # Check cell G1 to ensure we only broadcast this ONCE
        flag_cell = sheet.acell('G1').value
        if flag_cell != "BLASTED":
            
            if "slack_bot_token" not in st.secrets: return False
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            client = WebClient(token=st.secrets["slack_bot_token"], ssl=ssl_context)
            
            message = (
                "🚨 *ALL 5 QUESTS COMPLETED, AND ALL 5 CLUES COLLECTED.* 👏 *LET'S GO!!!* 💪\n\n"
                "With that, every team can now return to the main function room - and your team can now assemble your final output. "
                "To test and submit your answer, you can use the checker we've provided earlier. Here's the link: https://physicai-checker.streamlit.app\n\n"
                "Just a friendly reminder that once you've hit the *LOCK IN FINAL ANSWER* button, then that would count as your final submission and F1 score. Wishing everyone good luck! 🏆"
            )
            
            # Fire the message to all teams simultaneously
            for team, channel_id in SLACK_CHANNEL_IDS.items():
                if channel_id.startswith("C"):
                    try: client.chat_postMessage(channel=channel_id, text=message)
                    except: pass 
                        
            # Mark the database so it never double-fires
            sheet.update_acell('G1', 'BLASTED')
            return True
            
    return False

# --- RESET FUNCTION ---
def reset_bracket():
    keys_to_clear = ['s1', 's2', 's3', 's4', 'm1_win', 'm2_win', 'bronze_win', 'gold_win']
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None

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
    
    div[data-testid="stSelectbox"] label {{ display: none; }}
    div[data-baseweb="select"] {{
        background-color: rgba(0, 0, 0, 1) !important;
        border: 1px solid #444 !important;
        border-left: 6px solid #D71313 !important; 
        border-radius: 4px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.8);
    }}
    div[data-baseweb="select"]:hover {{ border-color: #D71313 !important; }}
    
    .gold-tier div[data-baseweb="select"] {{ border-left: 6px solid #FFD700 !important; }}
    .bronze-tier div[data-baseweb="select"] {{ border-left: 6px solid #CD7F32 !important; }}
    .champ-tier div[data-baseweb="select"] {{ 
        border-left: 6px solid #00FF41 !important; 
        border: 2px solid #00FF41 !important; 
        background-color: rgba(0, 255, 65, 0.05) !important;
    }}
    
    .bracket-header {{ text-align: center; font-weight: 900; font-size: 1.3rem; letter-spacing: 2px; color: #FFF; margin-bottom: 15px; text-transform: uppercase; }}
    .match-title {{ font-size: 0.75rem; font-weight: 800; color: #888; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px; }}
    
    .stButton > button {{
        background-color: #222;
        color: #FFF;
        border: 1px solid #444;
        transition: all 0.3s;
    }}
    .stButton > button:hover {{ background-color: #D71313; border: 1px solid #FFF; }}
    
    .spacer-10 {{ height: 10px; }}
    .spacer-20 {{ height: 20px; }}
    .spacer-30 {{ height: 30px; }}
    .spacer-40 {{ height: 40px; }}
    .spacer-60 {{ height: 60px; }}
    .spacer-90 {{ height: 90px; }}
    .spacer-110 {{ height: 110px; }}
    
    .line-wrapper {{ width: 100%; height: 200px; position: relative; margin-top: 100px; }}
    .line-top {{ border-top: 3px solid #555; border-right: 3px solid #555; height: 50%; width: 100%; border-top-right-radius: 6px; }}
    .line-bottom {{ border-bottom: 3px solid #555; border-right: 3px solid #555; height: 50%; width: 100%; border-bottom-right-radius: 6px; }}
    .line-straight {{ width: 100%; height: 3px; background-color: #FFD700; margin-top: 195px; }}
    
    .podium-box {{ padding: 20px; border-radius: 10px; font-weight: 900; font-size: 1.2rem; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.8); text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }}
    .gold-box {{ background: linear-gradient(135deg, #FFD700 0%, #B8860B 100%); color: white; border: 2px solid #FFF; }}
    .silver-box {{ background: linear-gradient(135deg, #C0C0C0 0%, #808080 100%); color: white; border: 2px solid #FFF; }}
    .bronze-box {{ background: linear-gradient(135deg, #CD7F32 0%, #8B4513 100%); color: white; border: 2px solid #FFF; }}
    .wood-box {{ background: linear-gradient(135deg, #8B5A2B 0%, #5C4033 100%); color: white; border: 2px solid #000; }}
    
    #MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- HEADER WITH LOGO ---
c1, c2, c3 = st.columns([1,2,1])
with c2:
    if os.path.exists("physicai_logo.png"): st.image("physicai_logo.png", use_container_width=True) 
    elif os.path.exists("company_logo.png"): st.image("company_logo.png", width=100)

st.markdown(f"""
    <div style='text-align: center; margin-bottom: 10px;'>
        <div style='font-weight: 900; letter-spacing: 3px; font-size: 2.5rem; color: #FFFFFF;'>{TOURNAMENT_NAME}</div>
        <div style='font-weight: 400; letter-spacing: 2px; font-size: 1rem; color: #D71313; margin-top: 5px;'>LIVE TOURNAMENT BRACKET</div>
    </div>
    """, unsafe_allow_html=True)

# --- RESET BUTTON ---
r1, r2, r3 = st.columns([2, 1, 2])
with r2:
    st.button("🔄 RESET BRACKET", on_click=reset_bracket, use_container_width=True)

st.divider()

# --- 5-COLUMN BRACKET LAYOUT ---
col_s, col_l1, col_f, col_l2, col_c = st.columns([3, 0.5, 3, 0.5, 3])

with col_s:
    st.markdown("<div class='bracket-header'>SEMIFINALS</div>", unsafe_allow_html=True)
    st.markdown("<div class='spacer-10'></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='match-title'>MATCH 1 (Seed 1 vs 3)</div>", unsafe_allow_html=True)
    s1 = st.selectbox("S1", TEAMS_LIST, index=None, placeholder="Assign Seed 1...", key="s1")
    opts3 = [t for t in TEAMS_LIST if t != s1] if s1 else TEAMS_LIST
    s3 = st.selectbox("S3", opts3, index=None, placeholder="Assign Seed 3...", key="s3")
    
    st.markdown("<div class='spacer-60'></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='match-title'>MATCH 2 (Seed 2 vs 4)</div>", unsafe_allow_html=True)
    opts2 = [t for t in TEAMS_LIST if t not in [s1, s3]] if s1 else TEAMS_LIST
    s2 = st.selectbox("S2", opts2, index=None, placeholder="Assign Seed 2...", key="s2")
    opts4 = [t for t in TEAMS_LIST if t not in [s1, s3, s2]] if s1 else TEAMS_LIST
    s4 = st.selectbox("S4", opts4, index=None, placeholder="Assign Seed 4...", key="s4")

with col_l1:
    st.markdown("<div class='bracket-header' style='visibility: hidden;'>-</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="line-wrapper">
        <div class="line-top"></div>
        <div class="line-bottom"></div>
    </div>
    """, unsafe_allow_html=True)

with col_f:
    st.markdown("<div class='bracket-header' style='color: #FFD700;'>FINALS</div>", unsafe_allow_html=True)
    st.markdown("<div class='spacer-110'></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='match-title' style='color: #FFD700;'>🥇 GOLD MEDAL MATCH</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-tier'>", unsafe_allow_html=True)
    m1_options = [s1, s3] if (s1 and s3) else []
    m1_win = st.selectbox("M1 Win", m1_options, index=None, placeholder="Advance Match 1 Winner...", key="m1_win")
    
    m2_options = [s2, s4] if (s2 and s4) else []
    m2_win = st.selectbox("M2 Win", m2_options, index=None, placeholder="Advance Match 2 Winner...", key="m2_win")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='spacer-60'></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='match-title' style='color: #CD7F32;'>🥉 BRONZE MEDAL MATCH</div>", unsafe_allow_html=True)
    st.markdown("<div class='bronze-tier'>", unsafe_allow_html=True)
    m1_lose = s3 if m1_win == s1 else (s1 if m1_win == s3 else None)
    m2_lose = s4 if m2_win == s2 else (s2 if m2_win == s4 else None)
    bronze_options = [m1_lose, m2_lose] if (m1_lose and m2_lose) else []
    bronze_win = st.selectbox("Bronze Win", bronze_options, index=None, placeholder="Select Bronze Winner...", key="bronze_win")
    st.markdown("</div>", unsafe_allow_html=True)

with col_l2:
    st.markdown("<div class='bracket-header' style='visibility: hidden;'>-</div>", unsafe_allow_html=True)
    st.markdown("<div class='line-straight'></div>", unsafe_allow_html=True)

with col_c:
    st.markdown("<div class='bracket-header' style='color: #00FF41;'>CHAMPION</div>", unsafe_allow_html=True)
    st.markdown("<div class='spacer-110'></div>", unsafe_allow_html=True)
    st.markdown("<div class='spacer-60'></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='match-title' style='color: #00FF41;'>🏆 TOURNAMENT WINNER</div>", unsafe_allow_html=True)
    st.markdown("<div class='champ-tier'>", unsafe_allow_html=True)
    gold_options = [m1_win, m2_win] if (m1_win and m2_win) else []
    gold_win = st.selectbox("Gold Win", gold_options, index=None, placeholder="CROWN CHAMPION...", key="gold_win")
    st.markdown("</div>", unsafe_allow_html=True)
    
    silver_win = m2_win if gold_win == m1_win else (m1_win if gold_win == m2_win else None)
    wood_win = m2_lose if bronze_win == m1_lose else (m1_lose if bronze_win == m2_lose else None)

# --- THE PODIUM RESULTS ---
st.divider()

if gold_win and silver_win and bronze_win and wood_win:
    try: rain(emoji="🏆", font_size=40, falling_speed=5, animation_length="3s")
    except: st.balloons()
    
    st.markdown("<h2 style='text-align: center; color: #FFF; letter-spacing: 2px;'>// FINAL TOURNAMENT STANDINGS //</h2>", unsafe_allow_html=True)
    st.markdown("<div class='spacer-20'></div>", unsafe_allow_html=True)
    
    pc1, pc2, pc3, pc4 = st.columns(4)
    with pc1:
        st.markdown(f"<div class='podium-box gold-box'>🥇 GOLD<br><span style='font-size: 1rem;'>{gold_win}</span></div>", unsafe_allow_html=True)
    with pc2:
        st.markdown(f"<div class='podium-box silver-box'>🥈 SILVER<br><span style='font-size: 1rem;'>{silver_win}</span></div>", unsafe_allow_html=True)
    with pc3:
        st.markdown(f"<div class='podium-box bronze-box'>🥉 BRONZE<br><span style='font-size: 1rem;'>{bronze_win}</span></div>", unsafe_allow_html=True)
    with pc4:
        st.markdown(f"<div class='podium-box wood-box'>🪵 WOOD<br><span style='font-size: 1rem;'>{wood_win}</span></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='spacer-30'></div>", unsafe_allow_html=True)
    
    # --- ACTIVATED SAVE BUTTON ---
    btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
    with btn_col2:
        st.markdown("""<style>
            .save-btn > button { background-color: #222 !important; border: 1px solid #444 !important; }
            .save-btn > button:hover { background-color: #D71313 !important; border-color: #FFF !important; }
        </style>""", unsafe_allow_html=True)
        
        st.markdown("<div class='save-btn'>", unsafe_allow_html=True)
        if st.button("💾 SAVE RESULTS & TRANSMIT CLUES", use_container_width=True):
            with st.spinner("Locking into Database..."):
                success = save_tournament_results(TOURNAMENT_NAME, gold_win, silver_win, bronze_win, wood_win)
                
            if success:
                st.success("✅ RESULTS LOCKED IN! Transmitting clues to Slack...")
                with st.spinner("Broadcasting to Squad Channels..."):
                    slack_success, slack_error = deliver_clues_to_slack(gold_win, silver_win, bronze_win, wood_win)
                    
                if slack_success:
                    try: rain(emoji="🏆", font_size=40, falling_speed=5, animation_length="3s")
                    except: st.balloons()
                    st.success("🤖 OVERRIDE COMPLETE: All squads have successfully received their next mission intel via Slack!")
                    
                    # --- THE NEW FINALE CHECK TRIGGER ---
                    with st.spinner("Checking overall tournament progress..."):
                        if check_and_broadcast_finale():
                            st.success("🎉 FINAL QUEST DETECTED! The 'Return to Main Room' blast has been automatically sent to all teams!")
                else:
                    st.error(f"⚠️ Results saved, but Slack delivery failed: {slack_error}")
            else:
                st.error("❌ ERROR: Could not connect to database. Check Secrets/Internet.")
        st.markdown("</div>", unsafe_allow_html=True)

st.caption("PHYSICAI // TOURNAMENT PROTOCOL")
