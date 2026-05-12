import streamlit as st
import pandas as pd
import base64
import os
import time
import ssl

# --- GOOGLE SHEETS & SLACK IMPORTS ---
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# --- CONFIGURATION ---
st.set_page_config(page_title="PHYSICAI Main Dashboard", page_icon="🛡️", layout="wide")

# --- GLOBAL SETTINGS ---
TEAMS_LIST = [
    "BLUE ANALYSTS",
    "GRAY SHIELDS",
    "GREEN DETECTIVES",
    "VIOLET STRATEGISTS"
]

SQUADS_DATA = [
    {"name": "BLUE ANALYSTS", "img": "blue_team.png"},
    {"name": "GRAY SHIELDS", "img": "gray_team.png"},
    {"name": "GREEN DETECTIVES", "img": "green_team.png"},
    {"name": "VIOLET STRATEGISTS", "img": "violet_team.png"}
]

ADMIN_PASSWORD = "COMMUNITY"

SHEET_NAME = "PhysicAI_Leaderboard"
WORKSHEET_SCORES = "Sheet1"
WORKSHEET_MEDALS = "Medals"
WORKSHEET_MVP = "MVP_Votes"

# --- SLACK CONFIGURATION ---
SLACK_CHANNEL_IDS = {
    "BLUE ANALYSTS": "C0B37MCBMC5",
    "GRAY SHIELDS": "C0B34PKDQNP",
    "GREEN DETECTIVES": "C0B37PS0HBP",
    "VIOLET STRATEGISTS": "C0B45EACJCQ"
}
POST_EVENT_SURVEY_LINK = "https://forms.gle/6NqWJGfTCVh2oquH8"
MVP_VOTING_LINK = "https://tt-connect-2026-physicai-trust-safety-mvp-voting.streamlit.app/"

# --- CACHED CONNECTION ---
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

# --- CACHED DATA LOADING (AUTO-REFRESHING) ---
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
    return pd.DataFrame(columns=["Quest", "Gold", "Silver", "Bronze", "Wood"])

@st.cache_data(ttl=5)
def get_cached_mvps():
    sheet = connect_to_sheet(WORKSHEET_MVP)
    if sheet:
        try:
            data = sheet.get_all_records()
            if data:
                return pd.DataFrame(data)
        except:
            pass
    return pd.DataFrame(columns=["Team", "Nominee"])

def record_medal_winners(quest_name, gold_team, silver_team, bronze_team, wood_team):
    sheet = connect_to_sheet(WORKSHEET_MEDALS)
    if sheet:
        sheet.append_row([quest_name, gold_team, silver_team, bronze_team, wood_team])
    get_cached_medals.clear()

def wipe_data():
    sheet1 = connect_to_sheet(WORKSHEET_SCORES)
    if sheet1:
        sheet1.clear()
        sheet1.append_row(["Team", "Score"])
    
    sheet2 = connect_to_sheet(WORKSHEET_MEDALS)
    if sheet2:
        sheet2.clear()
        sheet2.append_row(["Quest", "Gold", "Silver", "Bronze", "Wood"])
        
    sheet3 = connect_to_sheet(WORKSHEET_MVP)
    if sheet3:
        sheet3.clear()
        sheet3.append_row(["Team", "Nominee"])
    
    get_cached_leaderboard.clear()
    get_cached_medals.clear()
    get_cached_mvps.clear()

def get_medal_standings(medal_df):
    if medal_df.empty:
        return pd.DataFrame(columns=["Team", "🥇", "🥈", "🥉", "🪵"])
    
    has_wood = "Wood" in medal_df.columns
    all_teams = set(medal_df.get("Gold", [])).union(set(medal_df.get("Silver", []))).union(set(medal_df.get("Bronze", [])))
    if has_wood:
        all_teams = all_teams.union(set(medal_df["Wood"]))
    if "" in all_teams: all_teams.remove("")
    
    standings = []
    for team in all_teams:
        golds = len(medal_df[medal_df["Gold"] == team]) if "Gold" in medal_df else 0
        silvers = len(medal_df[medal_df["Silver"] == team]) if "Silver" in medal_df else 0
        bronzes = len(medal_df[medal_df["Bronze"] == team]) if "Bronze" in medal_df else 0
        woods = len(medal_df[medal_df["Wood"] == team]) if has_wood else 0
        
        sort_score = (golds * 3) + (silvers * 2) + (bronzes * 1)
        standings.append({"Team": team, "🥇": golds, "🥈": silvers, "🥉": bronzes, "🪵": woods, "Sort": sort_score})
    
    df = pd.DataFrame(standings)
    if not df.empty:
        df = df.sort_values(by=["Sort", "🥇", "🥈"], ascending=False).drop(columns=["Sort"])
    return df

# --- SLACK BLAST FUNCTIONS ---
def blast_rules_to_slack():
    if "slack_bot_token" not in st.secrets: return False
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    client = WebClient(token=st.secrets["slack_bot_token"], ssl=ssl_context)
    
    rules_text = (
        "🚨 *ATTENTION T&S!* 🚨\n\n"
        "I am PhysicAI: Game Master. Welcome to TT Connect 2026's Trust & Safety Breakout Session. Our event is called PhysicAI: Trust & Safety.\n\n"
        "Before we begin, you must memorize the rules of engagement:\n\n"
        "🏆 *THE ULTIMATE GOAL*\n"
        "Your objective is to achieve the highest F1 Score by accurately recreating a 'Secret Paragraph' that embodies our event theme: _Accomplish More_. You will earn the fragments of this paragraph by dominating a mix of physical and low-physical quests.\n\n"
        "⚔️ *THE QUESTS & CLUES*\n"
        "There are 5 quests. Your placement in each quest (Gold, Silver, Bronze, or Wood) dictates the quality of the clue you receive. The better your physical performance, the easier it will be to decode the secret paragraph.\n\n"
        "📋 *SQUAD ROSTERS (13 Players)*\n"
        "Divide your roster strategically based on physical and analytical strengths:\n"
        "• *Quest 1: Volleyball* – 3 Players\n"
        "• *Quest 2: Badminton* – 1 Player\n"
        "• *Quest 3: Karaoke Relay* – 3 Players\n"
        "• *Quest 4: Bottle Flip Tic-Tac-Toe* – 2 Players\n"
        "• *Quest 5: Blind Golfer* – 2 Players\n"
        "• *Main AI Decoders* – 2 Players (Main POCs for piecing together the final text)\n\n"
        "🔄 *THE 'IMPORT' RULE*\n"
        "Missing a player? Draft an 'Import' (community member). Limit: 1 Import for 1 game only per team. (Special cases may apply).\n\n"
        "⏱️ *THE FINALE & SUBMISSION*\n"
        "After all 5 quests, regroup in the main function room. You have exactly 30 minutes to collaborate, refine your text, and lock in your final answer on the main checker app.\n\n"
        "👑 *CROWNING THE CHAMPION (TIE-BREAKERS)*\n"
        "1. *The Gold Standard:* The tied team with the most Gold Medals across the quests takes the crown.\n"
        "2. *Sudden Death:* If teams are still tied, they face off in a special, sudden-death physical quest.\n\n"
        "_*NOTE:* The complete, in-depth rules will be explained during the breakout session. For reference, you can view this: https://canva.link/wo8hmv5w4ej14e8_"
    )
    
    success_count = 0
    for team, channel_id in SLACK_CHANNEL_IDS.items():
        if channel_id.startswith("C"):  
            try:
                client.chat_postMessage(channel=channel_id, text=rules_text)
                success_count += 1
            except SlackApiError as e:
                st.error(f"Error sending to {team} ({channel_id}): {e.response['error']}")
    return success_count > 0

def blast_survey_to_slack():
    if "slack_bot_token" not in st.secrets:
        st.error("⚠️ Slack Bot Token not found in Streamlit secrets!")
        return False
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    client = WebClient(token=st.secrets["slack_bot_token"], ssl=ssl_context)
    
    message = (
        "📣 Thank you for joining and participating in our breakout session - PhysicAI: Trust & Safety 📣\n\n"
        "To continue creating awesome breakout sessions or any engagement activities for our department, WE NEED YOUR VOICE 🗣️\n\n"
        f"Please answer our POST-EVENT SURVEY, we would appreciate your honesty and feedback. Here's our survey link: {POST_EVENT_SURVEY_LINK}\n\n"
        "Thank you so much! 🎊"
    )
    
    success_count = 0
    for team, channel_id in SLACK_CHANNEL_IDS.items():
        if channel_id.startswith("C"):  
            try:
                client.chat_postMessage(channel=channel_id, text=message)
                success_count += 1
            except SlackApiError as e:
                st.error(f"Error sending to {team} ({channel_id}): {e.response['error']}")
    
    return success_count > 0

def blast_mvp_link_to_slack():
    """Broadcasts the MVP voting link to all squads."""
    if "slack_bot_token" not in st.secrets:
        st.error("⚠️ Slack Bot Token not found in Streamlit secrets!")
        return False
        
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    client = WebClient(token=st.secrets["slack_bot_token"], ssl=ssl_context)
    
    message = (
        "🚨 *ATTENTION SQUADS: IT'S TIME TO VOTE FOR YOUR MVP!* 🚨\n\n"
        "Who carried the team? Who cracked the hardest codes? Who had the best energy? \n\n"
        f"Cast your vote for your Squad MVP here: {MVP_VOTING_LINK}\n\n"
        "Make sure to submit your vote before the polls close! ⭐"
    )
    
    success_count = 0
    for team, channel_id in SLACK_CHANNEL_IDS.items():
        if channel_id.startswith("C"):  
            try:
                client.chat_postMessage(channel=channel_id, text=message)
                success_count += 1
            except SlackApiError as e:
                st.error(f"Error sending to {team} ({channel_id}): {e.response['error']}")
                
    return success_count > 0

# --- SESSION STATE ---
if 'admin_logged_in' not in st.session_state: st.session_state['admin_logged_in'] = False
if 'reveal_stage' not in st.session_state: st.session_state['reveal_stage'] = 0 
if 'reveal_mvp' not in st.session_state: st.session_state['reveal_mvp'] = False

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
    
    #MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}
    
    th {{ background-color: #262626 !important; color: #D71313 !important; border-bottom: 2px solid #D71313 !important; }}
    td {{ background-color: #111 !important; color: white !important; border-bottom: 1px solid #333 !important; }}
    
    div[data-testid="stExpander"] {{ background-color: #111111 !important; border: 1px solid #444 !important; border-radius: 8px !important; margin-top: 20px; }}
    div[data-testid="stExpander"] details summary {{ color: #888888 !important; font-weight: bold !important; }}
    div[data-testid="stExpander"] details[open] summary {{ color: #D71313 !important; }}
    div[data-testid="stExpander"] div[data-testid="stExpanderContent"] {{ background-color: #000000 !important; color: white !important; padding: 20px !important; border-top: 1px solid #333 !important; }}
    
    .stButton > button {{
        font-weight: 900 !important;
        letter-spacing: 2px !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        height: 60px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LAYOUT: TOP SECTION ---
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("physicai_logo.png"): st.image("physicai_logo.png", use_container_width=True) 
        elif os.path.exists("company_logo.png"): st.image("company_logo.png", width=100)
    
    st.write("")
    st.write("")
    st.markdown("""
        <div style='text-align: center; margin-bottom: 30px;'>
            <div style='font-weight: 900; letter-spacing: 3px; font-size: 2.5rem; color: #FFFFFF;'>MAIN DASHBOARD</div>
            <div style='font-weight: 400; letter-spacing: 1px; font-size: 0.9rem; color: #D71313; margin-top: 5px;'>current build made by kmichaeljin | FB</div>
        </div>
        """, unsafe_allow_html=True)

with right_col:
    st.write("")
    st.markdown("<h3 style='text-align: center; color: #888; letter-spacing: 2px; font-size:1.2rem; margin-bottom: 15px;'>// SQUADS //</h3>", unsafe_allow_html=True)
    
    img_cols = st.columns(4)
    
    for i, squad in enumerate(SQUADS_DATA):
        with img_cols[i]:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            if os.path.exists(squad["img"]):
                bin_str = get_base64_of_bin_file(squad["img"])
                st.markdown(f"<img src='data:image/png;base64,{bin_str}' style='width: 150px; height: 150px; object-fit: cover; border-radius: 10px; border: 2px solid #444;'>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='width: 150px; height: 150px; background-color: #222; border-radius: 10px; border: 2px solid #444; display: inline-flex; align-items: center; justify-content: center; color: #555; margin: 0 auto; font-size: 0.8rem;'>PENDING</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div style='margin-top: 10px; font-weight: 900; font-size: 0.8rem; color: #FFF; letter-spacing: 1px;'>{squad['name']}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- SCOREBOARDS SECTION ---
lb_col1, lb_col2 = st.columns(2, gap="large")

with lb_col1:
    st.markdown("<h3 style='text-align: center; color: #888; letter-spacing: 2px; font-size:1.2rem;'>// LIVE TEAM LEADERBOARD //</h3>", unsafe_allow_html=True)
    df_scores = get_cached_leaderboard() 
    if not df_scores.empty:
        st.dataframe(df_scores.sort_values(by="Score", ascending=False), hide_index=True, use_container_width=True, column_config={"Team": st.column_config.TextColumn("SQUAD"), "Score": st.column_config.ProgressColumn("F1 SCORE", format="%d%%", min_value=0, max_value=100)})
    else: st.caption("AWAITING DATA...")

with lb_col2:
    st.markdown("<h3 style='text-align: center; color: #888; letter-spacing: 2px; font-size:1.2rem;'>// MEDAL STANDINGS //</h3>", unsafe_allow_html=True)
    df_medals_raw = get_cached_medals()
    df_medals = get_medal_standings(df_medals_raw) 
    if not df_medals.empty: st.dataframe(df_medals, hide_index=True, use_container_width=True, column_config={"Team": st.column_config.TextColumn("SQUAD")})
    else: st.caption("AWAITING QUEST RESULTS...")

# --- QUEST ARCHIVE LOG ---
st.write("")
st.markdown("<h3 style='text-align: center; color: #888; letter-spacing: 2px; font-size:1.2rem;'>// QUEST ARCHIVE //</h3>", unsafe_allow_html=True)

if not df_medals_raw.empty and len(df_medals_raw) > 0:
    df_sorted_archive = df_medals_raw.sort_values(by="Quest", ascending=True)
    st.dataframe(
        df_sorted_archive, hide_index=True, use_container_width=True,
        column_config={
            "Quest": st.column_config.TextColumn("ACTIVITY"),
            "Gold": st.column_config.TextColumn("🥇 GOLD"),
            "Silver": st.column_config.TextColumn("🥈 SILVER"),
            "Bronze": st.column_config.TextColumn("🥉 BRONZE"),
            "Wood": st.column_config.TextColumn("🪵 WOOD")
        }
    )
else:
    st.caption("NO QUEST LOGS DETECTED...")

# --- CHAMPION SHOWCASE & PROGRESSIVE RANKINGS ---
st.write("")
st.write("")
st.markdown("<h3 style='text-align: center; color: #FFD700; letter-spacing: 2px; font-size:1.5rem;'>// TOURNAMENT RANKINGS //</h3>", unsafe_allow_html=True)

teams_with_scores = df_scores["Team"].tolist() if not df_scores.empty else []
all_teams_finished = all(team in teams_with_scores for team in TEAMS_LIST)

all_quests_finished = False
if not df_medals_raw.empty:
    all_quests_finished = len(df_medals_raw["Quest"].unique()) >= 5

if all_teams_finished and all_quests_finished:
    
    stage = st.session_state['reveal_stage']

    # --- Reveal Controller Buttons ---
    c_btn1, c_btn2, c_btn3 = st.columns([1,2,1])
    with c_btn2:
        if stage == 0:
            if st.button("🪵 REVEAL 4TH PLACE", use_container_width=True):
                st.session_state['reveal_stage'] = 1
                st.rerun()
        elif stage == 1:
            if st.button("🥉 REVEAL 3RD PLACE", use_container_width=True):
                st.session_state['reveal_stage'] = 2
                st.rerun()
        elif stage == 2:
            if st.button("🥈 REVEAL 2ND PLACE", use_container_width=True):
                st.session_state['reveal_stage'] = 3
                st.rerun()
        elif stage == 3:
            if st.button("🏆 REVEAL TOURNAMENT CHAMPION 🏆", use_container_width=True):
                st.session_state['reveal_stage'] = 4
                st.rerun()
        elif stage == 4:
            if st.button("🔒 HIDE RANKINGS (RESET)", use_container_width=True):
                st.session_state['reveal_stage'] = 0
                st.rerun()
    st.write("")

    # --- Data Sorting ---
    ranking_data = []
    for team in TEAMS_LIST:
        score = 0
        if not df_scores.empty and team in df_scores["Team"].values:
            score = df_scores.loc[df_scores["Team"] == team, "Score"].max()
            
        g, s, b = 0, 0, 0
        if not df_medals.empty and team in df_medals["Team"].values:
            team_row = df_medals[df_medals["Team"] == team].iloc[0]
            g, s, b = team_row.get("🥇", 0), team_row.get("🥈", 0), team_row.get("🥉", 0)
            
        ranking_data.append({"Team": team, "Score": score, "G": g, "S": s, "B": b})

    ranking_data.sort(key=lambda x: (x["Score"], x["G"], x["S"], x["B"]), reverse=True)
    
    # HTML Generators
    def get_team_img_html(team_name, size, border_color, glow_size):
        img_path = next((sq["img"] for sq in SQUADS_DATA if sq["name"] == team_name), "")
        if os.path.exists(img_path):
            bin_str = get_base64_of_bin_file(img_path)
            return f"<img src='data:image/png;base64,{bin_str}' style='width: {size}px; height: {size}px; object-fit: cover; border-radius: 15px; border: 4px solid {border_color}; box-shadow: 0 0 {glow_size}px {border_color}88;'>"
        return f"<div style='width: {size}px; height: {size}px; background-color: #222; border-radius: 15px; border: 4px solid {border_color}; display: inline-flex; align-items: center; justify-content: center; color: {border_color}; font-weight: 900;'>PENDING</div>"

    def get_locked_html(height, border_color, title):
        return f"""
        <div style="border: 2px dashed {border_color}; border-radius: 15px; padding: 20px; text-align: center; height: {height}px; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: rgba(0,0,0,0.4);">
            <div style="color: {border_color}; font-size: 3rem; margin-bottom: 10px; opacity: 0.5;">🔒</div>
            <div style="color: #666; font-weight: 900; letter-spacing: 2px;">{title} LOCKED</div>
        </div>
        """

    # --- 1ST PLACE BANNER (GOLD) ---
    if stage >= 4:
        first_place = ranking_data[0]["Team"]
        st.markdown(f"""
        <div style="border: 2px solid #FFD700; border-radius: 15px; padding: 40px; background: linear-gradient(135deg, #1a1a00 0%, #000000 100%); display: flex; align-items: center; justify-content: center; margin-top: 10px; margin-bottom: 30px; box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);">
            <div style="flex: 1; text-align: right; padding-right: 50px; border-right: 2px solid #333;">
                {get_team_img_html(first_place, 300, '#FFD700', 30)}
            </div>
            <div style="flex: 2; padding-left: 50px; text-align: left;">
                <div style="color: #FFD700; font-size: 4rem; margin: 0; font-weight: 900; letter-spacing: 4px; line-height: 1.1;">CONGRATULATIONS</div>
                <div style="color: #FFFFFF; font-size: 3rem; margin-top: 15px; font-weight: 900; letter-spacing: 2px;">🏆 {first_place} 🏆</div>
                <div style="color: #FFD700; font-size: 1.5rem; margin-top: 10px; font-weight: 700; letter-spacing: 1px;">1ST PLACE CHAMPION</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(get_locked_html(300, "#FFD700", "CHAMPION"), unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # --- 2ND, 3RD, 4TH PLACE PODIUM ROW ---
    r_col1, r_col2, r_col3 = st.columns(3)
    
    with r_col1:
        if stage >= 3:
            st.markdown(f"""<div style="text-align: center; padding: 20px; background-color: #111; border-radius: 15px; border: 1px solid #333;"><div style="color: #C0C0C0; font-weight: 900; letter-spacing: 2px; margin-bottom: 15px; font-size: 1.2rem;">2ND PLACE</div>{get_team_img_html(ranking_data[1]["Team"], 150, '#C0C0C0', 15)}<div style="color: #FFF; font-weight: 900; margin-top: 15px; font-size: 1.1rem;">{ranking_data[1]["Team"]}</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown(get_locked_html(260, "#C0C0C0", "2ND PLACE"), unsafe_allow_html=True)
            
    with r_col2:
        if stage >= 2:
            st.markdown(f"""<div style="text-align: center; padding: 20px; background-color: #111; border-radius: 15px; border: 1px solid #333;"><div style="color: #CD7F32; font-weight: 900; letter-spacing: 2px; margin-bottom: 15px; font-size: 1.2rem;">3RD PLACE</div>{get_team_img_html(ranking_data[2]["Team"], 150, '#CD7F32', 15)}<div style="color: #FFF; font-weight: 900; margin-top: 15px; font-size: 1.1rem;">{ranking_data[2]["Team"]}</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown(get_locked_html(260, "#CD7F32", "3RD PLACE"), unsafe_allow_html=True)

    with r_col3:
        if stage >= 1:
            st.markdown(f"""<div style="text-align: center; padding: 20px; background-color: #111; border-radius: 15px; border: 1px solid #333;"><div style="color: #8B4513; font-weight: 900; letter-spacing: 2px; margin-bottom: 15px; font-size: 1.2rem;">4TH PLACE</div>{get_team_img_html(ranking_data[3]["Team"], 150, '#8B4513', 15)}<div style="color: #FFF; font-weight: 900; margin-top: 15px; font-size: 1.1rem;">{ranking_data[3]["Team"]}</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown(get_locked_html(260, "#8B4513", "4TH PLACE"), unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="border: 2px dashed #444; border-radius: 15px; padding: 40px; text-align: center; margin-top: 10px; margin-bottom: 20px;">
        <h2 style="color: #555; letter-spacing: 2px; margin: 0;">AWAITING ALL 5 QUESTS & FINAL PROMPT SUBMISSIONS...</h2>
    </div>
    """, unsafe_allow_html=True)

st.write(""); st.write("")
st.divider()

# =====================================================================
# --- SQUAD MVPS SECTION (ALWAYS VISIBLE - NOT TIED TO RANKINGS) ---
# =====================================================================
st.write("")
st.markdown("<h3 style='text-align: center; color: #D71313; letter-spacing: 2px; font-size:1.5rem;'>// LIVE MVP POLL TALLY //</h3>", unsafe_allow_html=True)

df_mvp = get_cached_mvps()
tally_cols = st.columns(4)
top_mvps = {}

for i, team in enumerate(TEAMS_LIST):
    with tally_cols[i]:
        st.markdown(f"<div style='text-align: center; color: #FFF; font-weight: 900; letter-spacing: 1px; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 10px;'>{team}</div>", unsafe_allow_html=True)
        
        # Render the votes if the dataframe isn't entirely empty
        team_votes = pd.DataFrame()
        if not df_mvp.empty and "Team" in df_mvp.columns and "Nominee" in df_mvp.columns:
            team_votes = df_mvp[df_mvp["Team"] == team]
        
        if not team_votes.empty:
            vote_counts = team_votes["Nominee"].value_counts().reset_index()
            vote_counts.columns = ["Nominee", "Votes"]
            
            top_mvps[team] = {"name": vote_counts.iloc[0]["Nominee"], "votes": vote_counts.iloc[0]["Votes"]}
            top_3 = vote_counts.head(3)
            
            for index, row in top_3.iterrows():
                color = "#FFD700" if index == 0 else "#C0C0C0" if index == 1 else "#CD7F32"
                st.markdown(f"""
                <div style='display: flex; justify-content: space-between; align-items: center; background-color: #111; padding: 10px 15px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid {color};'>
                    <span style='color: #FFF; font-weight: bold; font-size: 0.9rem;'>{row["Nominee"]}</span>
                    <span style='color: #D71313; font-weight: 900; font-size: 0.9rem;'>{row["Votes"]}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; color: #555; padding: 10px; border: 1px dashed #333; border-radius: 8px;'>Awaiting votes...</div>", unsafe_allow_html=True)
            top_mvps[team] = None

st.write("")
st.write("")

if not st.session_state['reveal_mvp']:
    _, c_btn, _ = st.columns([1,2,1])
    with c_btn:
        if st.button("⭐ LOCK POLLS & REVEAL SQUAD MVPs ⭐", use_container_width=True):
            st.session_state['reveal_mvp'] = True
            st.rerun()
else:
    st.markdown("<h3 style='text-align: center; color: #FFD700; letter-spacing: 2px; font-size:2rem; margin-top: 30px; margin-bottom: 30px;'>// OFFICIAL SQUAD MVPs //</h3>", unsafe_allow_html=True)
    showcase_cols = st.columns(4)
    
    for i, team in enumerate(TEAMS_LIST):
        with showcase_cols[i]:
            winner = top_mvps.get(team)
            if winner:
                st.markdown(f"""
                <div style='text-align: center; background: linear-gradient(135deg, #1a0000 0%, #000000 100%); padding: 30px 20px; border-radius: 15px; border: 2px solid #D71313; box-shadow: 0 0 25px rgba(215,19,19,0.3);'>
                    <div style='color: #888; font-size: 0.9rem; margin-bottom: 15px; letter-spacing: 1px; font-weight: bold;'>{team}</div>
                    <div style='font-size: 4rem; margin-bottom: 10px; line-height: 1;'>⭐</div>
                    <div style='color: #FFF; font-weight: 900; font-size: 1.2rem; text-transform: uppercase; margin-bottom: 5px;'>{winner["name"]}</div>
                    <div style='color: #D71313; font-weight: bold; font-size: 1rem;'>{winner["votes"]} VOTES</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='text-align: center; background-color: #111; padding: 30px 20px; border-radius: 15px; border: 1px dashed #444;'>
                    <div style='color: #888; font-size: 0.9rem; margin-bottom: 15px; letter-spacing: 1px; font-weight: bold;'>{team}</div>
                    <div style='color: #444; font-size: 3rem; margin-bottom: 10px;'>🔒</div>
                    <div style='color: #666; font-weight: bold;'>NO VOTES CAST</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.write("")
    _, c_hide, _ = st.columns([1,2,1])
    with c_hide:
        if st.button("🔓 HIDE MVPs (BACK TO LIVE POLL)", use_container_width=True):
            st.session_state['reveal_mvp'] = False
            st.rerun()

st.write(""); st.write("")

# --- UPDATED ADMIN PANEL ---
with st.expander("⚙️ ADMIN PROTOCOLS (RESTRICTED)"):
    if not st.session_state['admin_logged_in']:
        c_pass, c_btn = st.columns([3, 1])
        with c_pass:
            admin_pass_input = st.text_input("ENTER ADMIN KEY:", type="password", key="login_pass")
        with c_btn:
            st.write(""); st.write("") 
            if st.button("🔓 LOGIN", use_container_width=True):
                if admin_pass_input == ADMIN_PASSWORD:
                    st.session_state['admin_logged_in'] = True
                    st.rerun()
                else:
                    st.error("❌ INVALID KEY")
    else:
        st.success("✅ SYSTEM ACCESS GRANTED")
        tab1, tab2, tab3 = st.tabs(["🏅 AWARD MEDALS", "🔴 DANGER ZONE", "📣 COMM CENTER"])
        
        with tab1:
            st.info("Award Medals (Auto-filters previously selected teams)")
            
            quest_select = st.selectbox("Select Quest:", [
                "QUEST 1: BEACH VOLLEYBALL", 
                "QUEST 2: BADMINTON", 
                "QUEST 3: KARAOKE RELAY", 
                "QUEST 4: BOTTLE FLIP TIC TAC TOE", 
                "QUEST 5: BLIND GOLFER",
                "🚨 SUDDEN DEATH: TIE-BREAKER 🚨"
            ])
            
            col_g, col_s, col_b, col_w = st.columns(4)
            with col_g: gold = st.selectbox("🥇 GOLD", TEAMS_LIST, index=None, placeholder="1st")
            silver_options = [t for t in TEAMS_LIST if t != gold] if gold else TEAMS_LIST
            with col_s: silver = st.selectbox("🥈 SILVER", silver_options, index=None, placeholder="2nd")
            bronze_options = [t for t in silver_options if t != silver] if silver else silver_options
            with col_b: bronze = st.selectbox("🥉 BRONZE", bronze_options, index=None, placeholder="3rd")
            wood_options = [t for t in bronze_options if t != bronze] if bronze else bronze_options
            with col_w: wood = st.selectbox("🪵 WOOD", wood_options, index=None, placeholder="4th")
            
            if st.button("SUBMIT MEDAL RESULTS", use_container_width=True):
                if gold and silver and bronze and wood:
                    with st.spinner("Writing to Database..."):
                        record_medal_winners(quest_select, gold, silver, bronze, wood)
                    st.success(f"Saved: {quest_select}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("⚠️ Select all 4 placements first.")

        with tab2:
            st.warning("This action cannot be undone.")
            if st.button("🔴 WIPE EVERYTHING"):
                with st.spinner("Purging Systems..."):
                    wipe_data()
                st.session_state['reveal_stage'] = 0 
                st.session_state['reveal_mvp'] = False
                st.success("CLEAN SLATE.")
                time.sleep(1)
                st.rerun()

        with tab3:
            st.info("Broadcast final messages and links to all team channels simultaneously.")
            
            # --- WELCOME & RULES BLAST ---
            st.markdown("#### 📜 Welcome & Rules Blast")
            if st.button("🚀 INITIATE RULES BLAST", use_container_width=True):
                with st.spinner("Transmitting rules to Slack via xoxb- token..."):
                    if blast_rules_to_slack():
                        st.success("✅ Rules successfully transmitted to all active squads!")
                    else:
                        st.error("❌ Transmission failed. Check the error logs above.")
            
            st.divider()

            # --- MVP VOTING BLAST ---
            st.markdown("#### 🏆 MVP Voting Blast")
            st.code(MVP_VOTING_LINK, language="text")
            if st.button("🚀 INITIATE MVP VOTING BLAST", use_container_width=True):
                with st.spinner("Transmitting MVP link to Slack via xoxb- token..."):
                    if blast_mvp_link_to_slack():
                        st.success("✅ MVP Voting link successfully transmitted to all active squads!")
                    else:
                        st.error("❌ Transmission failed. Check the error logs above.")
            
            st.divider()
            
            # --- POST EVENT SURVEY BLAST ---
            st.markdown("#### 📝 Post-Event Survey Blast")
            st.code(POST_EVENT_SURVEY_LINK, language="text")
            if st.button("🚀 INITIATE SURVEY BLAST", use_container_width=True):
                with st.spinner("Transmitting Survey link to Slack via xoxb- token..."):
                    if blast_survey_to_slack():
                        st.success("✅ Survey successfully transmitted to all active squads!")
                    else:
                        st.error("❌ Transmission failed. Check the error logs above.")
        
        st.divider()
        if st.button("LOG OUT"):
            st.session_state['admin_logged_in'] = False
            st.rerun()

# --- AUTO REFRESH LOOP ---
time.sleep(60)
st.rerun()
