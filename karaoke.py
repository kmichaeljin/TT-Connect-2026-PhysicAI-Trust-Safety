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
st.set_page_config(page_title="Karaoke Relay", page_icon="🎤", layout="wide")

TOURNAMENT_NAME = "QUEST 3: KARAOKE RELAY"

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

# 🚨 LIVE KARAOKE CLUES 🚨
CLUE_VAULT = {
    "🥇 GOLD": f"{CB}across heaviest evenly manageable feels when The burden shoulders. distributed surprisingly dedicated{CB}",
    "🥈 SILVER": f"{CB}ehT vhsteaei rndeub slfee isgnruipylsr gembaanael hnwe iidutedbrts nvyeel csaors cdeedtiad duhorsles.{CB}",
    "🥉 BRONZE": f"{CB}T_e | h_ _ _ _ _ _t | b_ _ _ _n | f _ _ _ s | s _ _ _ _ _ _ _ _ _ _ y | m_ _ _ _ _ _ _ _e | w_ _n | d_ _ _ _ _ _ _ _ _d | e_ _ _ _y | a_ _ _ _s |  d_ _ _ _ _ _ _d | s_ _ _ _ _ _ _s.\n\nThe | acts as a space, when decoding, make sure to remove the |{CB}",
    "🪵 WOOD": f"{CB}• Length: 12 words\n• Punctuation: Period at the end.\n• Meaning: Difficult tasks feel easier when shared fairly among committed people.\n• Wording clues: Includes the exact phrases “surprisingly manageable” and “distributed evenly.”\n• Ending clue: The sentence ends with “dedicated shoulders.”{CB}"
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
                    f"Congratulations on finishing Quest 3: Karaoke! Your team placed: {tier}\n\n"
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
def reset_scores():
    for team in TEAMS_LIST:
        if team in st.session_state:
            st.session_state[team] = 0.0

# --- SESSION STATE INIT ---
for team in TEAMS_LIST:
    if team not in st.session_state:
        st.session_state[team] = 0.0

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
        max-width: 1100px;
    }}
    
    /* Number Input Styling */
    div[data-baseweb="input"] {{
        background-color: rgba(0, 0, 0, 1) !important;
        border: 2px solid #444 !important;
        border-radius: 8px;
    }}
    div[data-baseweb="input"]:focus-within {{ border-color: #D71313 !important; box-shadow: 0 0 10px rgba(215, 19, 19, 0.5); }}
    
    input[type="number"] {{
        color: #00FF41 !important;
        font-size: 2rem !important;
        font-weight: 900 !important;
        text-align: center !important;
    }}
    
    .team-label {{ text-align: center; font-weight: 900; font-size: 1.2rem; letter-spacing: 2px; color: #FFF; margin-bottom: 5px; margin-top: 15px; text-transform: uppercase; }}
    
    .stButton > button {{
        background-color: #222;
        color: #FFF;
        border: 1px solid #444;
        transition: all 0.3s;
    }}
    .stButton > button:hover {{ background-color: #D71313; border: 1px solid #FFF; }}
    
    .podium-box {{ padding: 20px; border-radius: 10px; font-weight: 900; font-size: 1.2rem; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.8); text-shadow: 1px 1px 2px rgba(0,0,0,0.8); margin-top: 10px; }}
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
        <div style='font-weight: 400; letter-spacing: 2px; font-size: 1rem; color: #D71313; margin-top: 5px;'>LIVE SCORING DASHBOARD</div>
    </div>
    """, unsafe_allow_html=True)

# --- RESET BUTTON ---
r1, r2, r3 = st.columns([2, 1, 2])
with r2:
    st.button("🔄 RESET SCORES", on_click=reset_scores, use_container_width=True)

st.divider()

# --- SCORING GRID ---
sc1, sc2 = st.columns(2, gap="large")

with sc1:
    st.markdown(f"<div class='team-label'>🔵 {TEAMS_LIST[0]}</div>", unsafe_allow_html=True)
    st.number_input("Score 1", min_value=0.0, max_value=100.0, step=0.1, key=TEAMS_LIST[0], label_visibility="collapsed")
    
    st.markdown(f"<div class='team-label'>🟢 {TEAMS_LIST[2]}</div>", unsafe_allow_html=True)
    st.number_input("Score 3", min_value=0.0, max_value=100.0, step=0.1, key=TEAMS_LIST[2], label_visibility="collapsed")

with sc2:
    st.markdown(f"<div class='team-label'>⚪ {TEAMS_LIST[1]}</div>", unsafe_allow_html=True)
    st.number_input("Score 2", min_value=0.0, max_value=100.0, step=0.1, key=TEAMS_LIST[1], label_visibility="collapsed")
    
    st.markdown(f"<div class='team-label'>🟣 {TEAMS_LIST[3]}</div>", unsafe_allow_html=True)
    st.number_input("Score 4", min_value=0.0, max_value=100.0, step=0.1, key=TEAMS_LIST[3], label_visibility="collapsed")

# --- CALCULATION LOGIC ---
st.divider()

# Gather current scores from session state
team_scores = {team: st.session_state[team] for team in TEAMS_LIST}
total_score_entered = sum(team_scores.values())

# Only attempt to rank if at least one team has a score > 0
if total_score_entered > 0:
    # Check for ties
    unique_scores = set(team_scores.values())
    
    if len(unique_scores) < 4:
        st.warning("⚠️ **TIE DETECTED!** The system requires a distinct winner for each placement. Please adjust tied scores (e.g., use decimals like 95.1 and 95.0) to break the tie.")
    else:
        # Sort teams by score (Highest to Lowest)
        sorted_teams = sorted(team_scores.items(), key=lambda item: item[1], reverse=True)
        
        gold_win = sorted_teams[0][0]
        silver_win = sorted_teams[1][0]
        bronze_win = sorted_teams[2][0]
        wood_win = sorted_teams[3][0]

        st.markdown("<h2 style='text-align: center; color: #FFF; letter-spacing: 2px;'>// FINAL PLACEMENTS //</h2>", unsafe_allow_html=True)
        st.write("")
        
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            st.markdown(f"<div class='podium-box gold-box'>🥇 GOLD<br><span style='font-size: 1rem;'>{gold_win}</span><br><span style='font-size: 0.8rem; color:#222;'>{sorted_teams[0][1]} pts</span></div>", unsafe_allow_html=True)
        with pc2:
            st.markdown(f"<div class='podium-box silver-box'>🥈 SILVER<br><span style='font-size: 1rem;'>{silver_win}</span><br><span style='font-size: 0.8rem; color:#222;'>{sorted_teams[1][1]} pts</span></div>", unsafe_allow_html=True)
        with pc3:
            st.markdown(f"<div class='podium-box bronze-box'>🥉 BRONZE<br><span style='font-size: 1rem;'>{bronze_win}</span><br><span style='font-size: 0.8rem; color:#DDD;'>{sorted_teams[2][1]} pts</span></div>", unsafe_allow_html=True)
        with pc4:
            st.markdown(f"<div class='podium-box wood-box'>🪵 WOOD<br><span style='font-size: 1rem;'>{wood_win}</span><br><span style='font-size: 0.8rem; color:#DDD;'>{sorted_teams[3][1]} pts</span></div>", unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
        # --- SAVE BUTTON ---
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
                        try: rain(emoji="🎤", font_size=40, falling_speed=5, animation_length="3s")
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
else:
    st.info("Awaiting score inputs... The podium will appear automatically once scores are entered.")

st.write("")
st.caption("PHYSICAI // TOURNAMENT PROTOCOL")
