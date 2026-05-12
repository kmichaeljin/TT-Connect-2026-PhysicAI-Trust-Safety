import streamlit as st
import base64
import os
import time
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
st.set_page_config(page_title="Blind Golfer Timer", page_icon="⛳", layout="wide")
TOURNAMENT_NAME = "QUEST 5: BLIND GOLFER"

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

# Safely generate Slack's Markdown triple-backticks
CB = "`" * 3 

# 🚨 LIVE BLIND GOLFER CLUES 🚨
CLUE_VAULT = {
    "🥇 GOLD": f"{CB}shatter perceived the victory. cohesive secure moving ultimate limits Only as one unit we by and our can{CB}",
    "🥈 SILVER": f"{CB}ylnO yb vmnigo sa eno csioeehv ntui nac ew tahtesr uro eicdpeevr tlmsii adn srueec eht itulaemt oiyrtcv.{CB}",
    "🥉 BRONZE": f"{CB}O_ _y | b_  | m_ _ _ _g | a_ | o_e | c_h_ _ _ _e | u_ _t | c_n | w_ | s_ _ _ _ _r | o_r | p_ _ _ _ _ _ _d | l_ _ _ _s | a_d | s_ _ _ _e | t_e | u_ _ _ _ _ _e | v_ _ _ _ _y.\n\nThe | acts as a space, when decoding, make sure to remove the |{CB}",
    "🪵 WOOD": f"{CB}• Length: 17 words\n• Punctuation: Period at the end.\n• Meaning: Victory comes from total unity, not individual action.\n• Wording clues: Includes the exact phrases “one cohesive unit” and “perceived limits.”\n• Ending clue: The final two words are “ultimate victory.”{CB}"
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
        # 🚨 LOUD ERROR HANDLER 🚨
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
                # STANDARDIZED MESSAGE FORMAT
                message = (
                    f"Congratulations on finishing Quest 5: Blind Golfer! Your team placed: {tier}\n\n"
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

# --- SESSION STATE INIT (STOPWATCHES) ---
for team in TEAMS_LIST:
    if f"{team}_running" not in st.session_state:
        st.session_state[f"{team}_running"] = False
    if f"{team}_start_time" not in st.session_state:
        st.session_state[f"{team}_start_time"] = 0.0
    if f"{team}_elapsed" not in st.session_state:
        st.session_state[f"{team}_elapsed"] = 0.0

def reset_all_timers():
    for team in TEAMS_LIST:
        st.session_state[f"{team}_running"] = False
        st.session_state[f"{team}_start_time"] = 0.0
        st.session_state[f"{team}_elapsed"] = 0.0

def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 100)
    return f"{mins:02d}:{secs:02d}.{ms:02d}"

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
    
    /* Stopwatch Display */
    .timer-display {{
        font-size: 3rem;
        font-weight: 900;
        color: #00FF41;
        text-align: center;
        font-family: 'Courier New', Courier, monospace;
        background-color: #111;
        border: 2px solid #444;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 15px;
        box-shadow: inset 0 0 10px #000;
    }}
    
    .timer-running {{
        color: #FFD700 !important;
        border-color: #FFD700 !important;
        box-shadow: inset 0 0 15px rgba(255, 215, 0, 0.3) !important;
    }}
    
    /* Number Input Styling */
    div[data-baseweb="input"] {{
        background-color: rgba(0, 0, 0, 1) !important;
        border: 1px solid #444 !important;
        border-radius: 5px;
    }}
    div[data-baseweb="input"]:focus-within {{ border-color: #D71313 !important; }}
    input[type="number"] {{ color: #FFF !important; text-align: center !important; font-weight: bold !important; }}
    
    .team-label {{ text-align: center; font-weight: 900; font-size: 1.2rem; letter-spacing: 2px; color: #FFF; margin-bottom: 5px; margin-top: 15px; text-transform: uppercase; }}
    
    /* Timer Buttons */
    .btn-start > button {{ background-color: #00FF41 !important; color: #000 !important; font-weight: 900; border-radius: 5px; border: none; width: 100%; }}
    .btn-stop > button {{ background-color: #D71313 !important; color: #FFF !important; font-weight: 900; border-radius: 5px; border: none; width: 100%; }}
    .btn-reset > button {{ background-color: #444 !important; color: #FFF !important; font-weight: 900; border-radius: 5px; border: none; width: 100%; }}
    
    /* Standard Buttons */
    .stButton > button {{ transition: all 0.3s; }}
    
    /* Expander CSS */
    div[data-testid="stExpander"] {{ background-color: #111 !important; border: 1px solid #444 !important; border-radius: 8px !important; margin-top: 20px; }}
    div[data-testid="stExpander"] details summary {{ color: #888 !important; font-weight: bold !important; }}
    div[data-testid="stExpander"] div[data-testid="stExpanderContent"] {{ background-color: #000 !important; border-top: 1px solid #333 !important; padding: 20px !important; }}
    
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
        <div style='font-weight: 400; letter-spacing: 2px; font-size: 1rem; color: #D71313; margin-top: 5px;'>LIVE TIMING DASHBOARD</div>
    </div>
    """, unsafe_allow_html=True)

# --- RESET BUTTON ---
r1, r2, r3 = st.columns([2, 1, 2])
with r2:
    st.button("🔄 RESET ALL TIMERS", on_click=reset_all_timers, use_container_width=True)

st.divider()

# --- STOPWATCH GRID ---
def render_team_timer(team, icon):
    st.markdown(f"<div class='team-label'>{icon} {team}</div>", unsafe_allow_html=True)
    
    # Calculate display time
    if st.session_state[f"{team}_running"]:
        display_time = time.time() - st.session_state[f"{team}_start_time"]
        timer_class = "timer-display timer-running"
    else:
        display_time = st.session_state[f"{team}_elapsed"]
        timer_class = "timer-display"
        
    st.markdown(f"<div class='{timer_class}'>{format_time(display_time)}</div>", unsafe_allow_html=True)
    
    bc1, bc2 = st.columns(2)
    with bc1:
        if not st.session_state[f"{team}_running"]:
            st.markdown("<div class='btn-start'>", unsafe_allow_html=True)
            if st.button("▶️ START", key=f"start_{team}"):
                st.session_state[f"{team}_start_time"] = time.time() - st.session_state[f"{team}_elapsed"]
                st.session_state[f"{team}_running"] = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='btn-stop'>", unsafe_allow_html=True)
            if st.button("⏹️ STOP", key=f"stop_{team}"):
                st.session_state[f"{team}_elapsed"] = time.time() - st.session_state[f"{team}_start_time"]
                st.session_state[f"{team}_running"] = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    
    with bc2:
        st.markdown("<div class='btn-reset'>", unsafe_allow_html=True)
        if st.button("🔄 RESET", key=f"reset_btn_{team}"):
            st.session_state[f"{team}_elapsed"] = 0.0
            st.session_state[f"{team}_running"] = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

sc1, sc2 = st.columns(2, gap="large")

with sc1:
    render_team_timer(TEAMS_LIST[0], "🔵")
    st.write("---")
    render_team_timer(TEAMS_LIST[2], "🟢")

with sc2:
    render_team_timer(TEAMS_LIST[1], "⚪")
    st.write("---")
    render_team_timer(TEAMS_LIST[3], "🟣")

# --- SECURE MANUAL OVERRIDE SECTION ---
st.write("")
any_running = any(st.session_state[f"{t}_running"] for t in TEAMS_LIST)

with st.expander("⚙️ MANUAL TIME ADJUSTMENTS"):
    if any_running:
        st.warning("⚠️ **TIMERS ARE CURRENTLY RUNNING.** Stop all stopwatches to manually adjust times.")
    else:
        st.info("Input exact seconds (e.g. 15.5) and click SET TIME.")
        mac1, mac2, mac3, mac4 = st.columns(4)
        for team, col in zip(TEAMS_LIST, [mac1, mac2, mac3, mac4]):
            with col:
                st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 0.9rem; color: #888;'>{team}</div>", unsafe_allow_html=True)
                # Safely captures value without binding on_change
                new_val = st.number_input(f"Secs for {team}", min_value=0.0, step=0.1, value=float(st.session_state[f"{team}_elapsed"]), key=f"man_inp_{team}", label_visibility="collapsed")
                
                # Button strictly executes the overwrite
                if st.button("SET TIME", key=f"set_btn_{team}", use_container_width=True):
                    st.session_state[f"{team}_elapsed"] = new_val
                    st.rerun()

# --- CALCULATION LOGIC (LOWEST TIME WINS) ---
st.divider()

completed_teams = {
    team: st.session_state[f"{team}_elapsed"] 
    for team in TEAMS_LIST 
    if st.session_state[f"{team}_elapsed"] > 0 and not st.session_state[f"{team}_running"]
}

if len(completed_teams) == 4:
    sorted_teams = sorted(completed_teams.items(), key=lambda item: item[1], reverse=False)
    unique_times = set(completed_teams.values())
    
    if len(unique_times) < 4:
        st.warning("⚠️ **TIE DETECTED!** The system requires a distinct winner. Use the Manual Adjustments section to break the tie (e.g., adding 0.1s).")
    else:
        gold_win = sorted_teams[0][0]
        silver_win = sorted_teams[1][0]
        bronze_win = sorted_teams[2][0]
        wood_win = sorted_teams[3][0]

        st.markdown("<h2 style='text-align: center; color: #FFF; letter-spacing: 2px;'>// FINAL PLACEMENTS //</h2>", unsafe_allow_html=True)
        st.write("")
        
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            st.markdown(f"<div class='podium-box gold-box'>🥇 GOLD<br><span style='font-size: 1rem;'>{gold_win}</span><br><span style='font-size: 0.8rem; color:#222;'>{format_time(sorted_teams[0][1])}</span></div>", unsafe_allow_html=True)
        with pc2:
            st.markdown(f"<div class='podium-box silver-box'>🥈 SILVER<br><span style='font-size: 1rem;'>{silver_win}</span><br><span style='font-size: 0.8rem; color:#222;'>{format_time(sorted_teams[1][1])}</span></div>", unsafe_allow_html=True)
        with pc3:
            st.markdown(f"<div class='podium-box bronze-box'>🥉 BRONZE<br><span style='font-size: 1rem;'>{bronze_win}</span><br><span style='font-size: 0.8rem; color:#DDD;'>{format_time(sorted_teams[2][1])}</span></div>", unsafe_allow_html=True)
        with pc4:
            st.markdown(f"<div class='podium-box wood-box'>🪵 WOOD<br><span style='font-size: 1rem;'>{wood_win}</span><br><span style='font-size: 0.8rem; color:#DDD;'>{format_time(sorted_teams[3][1])}</span></div>", unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
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
                        try: rain(emoji="⏱️", font_size=40, falling_speed=5, animation_length="3s")
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
    st.info(f"Awaiting times... The podium will appear automatically once all 4 teams have a recorded time. ({len(completed_teams)}/4 completed)")

st.write("")
st.caption("PHYSICAI // TOURNAMENT PROTOCOL")

# --- LIVE TICKER ENGINE ---
if any_running:
    time.sleep(0.1)  # Refresh rate (10 frames per second)
    st.rerun()
