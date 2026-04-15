import streamlit as st
import pandas as pd
import base64
import os
import time

# --- GOOGLE SHEETS IMPORTS ---
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
    
    get_cached_leaderboard.clear()
    get_cached_medals.clear()

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

# --- SESSION STATE ---
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
    
    #MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}
    
    th {{ background-color: #262626 !important; color: #D71313 !important; border-bottom: 2px solid #D71313 !important; }}
    td {{ background-color: #111 !important; color: white !important; border-bottom: 1px solid #333 !important; }}
    
    div[data-testid="stExpander"] {{ background-color: #111111 !important; border: 1px solid #444 !important; border-radius: 8px !important; margin-top: 20px; }}
    div[data-testid="stExpander"] details summary {{ color: #888888 !important; font-weight: bold !important; }}
    div[data-testid="stExpander"] details[open] summary {{ color: #D71313 !important; }}
    div[data-testid="stExpander"] div[data-testid="stExpanderContent"] {{ background-color: #000000 !important; color: white !important; padding: 20px !important; border-top: 1px solid #333 !important; }}
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
    
    # EXACTLY 1 ROW, 4 COLUMNS
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

# --- CHAMPION SHOWCASE WITH TIE-BREAKER LOGIC ---
st.write("")
st.write("")
st.markdown("<h3 style='text-align: center; color: #FFD700; letter-spacing: 2px; font-size:1.5rem;'>// TOURNAMENT CHAMPION //</h3>", unsafe_allow_html=True)

winning_team = None
tie_breaker_mode = False
tied_teams_list = []

# ONLY trigger the Champion logic if ALL 4 teams have locked in an F1 score AND ALL 5 Quests are logged
teams_with_scores = df_scores["Team"].tolist() if not df_scores.empty else []
all_teams_finished = all(team in teams_with_scores for team in TEAMS_LIST)

all_quests_finished = False
if not df_medals_raw.empty:
    all_quests_finished = len(df_medals_raw["Quest"].unique()) >= 5

if all_teams_finished and all_quests_finished:
    max_f1 = df_scores["Score"].max()
    top_f1_teams = df_scores[df_scores["Score"] == max_f1]["Team"].tolist()
    
    if len(top_f1_teams) == 1:
        winning_team = top_f1_teams[0]
    else:
        # Tie-breaker 1: Highest Gold Medals
        gold_counts = {}
        for t in top_f1_teams:
            if not df_medals.empty and t in df_medals["Team"].values:
                golds = df_medals.loc[df_medals["Team"] == t, "🥇"].values[0]
            else:
                golds = 0
            gold_counts[t] = golds
        
        max_golds = max(gold_counts.values()) if gold_counts else 0
        top_gold_teams = [t for t, g in gold_counts.items() if g == max_golds]
        
        if len(top_gold_teams) == 1:
            winning_team = top_gold_teams[0]
        else:
            tie_breaker_mode = True
            tied_teams_list = top_gold_teams

if winning_team:
    winning_img_path = ""
    for sq in SQUADS_DATA:
        if sq["name"] == winning_team:
            winning_img_path = sq["img"]
            break
    
    img_tag = ""
    if os.path.exists(winning_img_path):
        bin_str = get_base64_of_bin_file(winning_img_path)
        img_tag = f"<img src='data:image/png;base64,{bin_str}' style='width: 300px; height: 300px; object-fit: cover; border-radius: 15px; border: 4px solid #FFD700; box-shadow: 0 0 25px rgba(255,215,0,0.6);'>"
    else:
        img_tag = "<div style='width: 300px; height: 300px; background-color: #222; border-radius: 15px; border: 4px solid #FFD700; display: inline-flex; align-items: center; justify-content: center; color: #FFD700; font-weight: 900; font-size: 1.5rem;'>PENDING</div>"

    st.markdown(f"""
    <div style="border: 2px solid #FFD700; border-radius: 15px; padding: 40px; background: linear-gradient(135deg, #1a1a1a 0%, #000000 100%); display: flex; align-items: center; justify-content: center; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);">
        <div style="flex: 1; text-align: right; padding-right: 50px; border-right: 2px solid #333;">
            {img_tag}
        </div>
        <div style="flex: 2; padding-left: 50px; text-align: left;">
            <div style="color: #FFD700; font-size: 4rem; margin: 0; font-weight: 900; letter-spacing: 4px; line-height: 1.1;">CONGRATULATIONS</div>
            <div style="color: #FFFFFF; font-size: 3rem; margin-top: 15px; font-weight: 900; letter-spacing: 2px;">🏆 {winning_team} 🏆</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif tie_breaker_mode:
    tied_teams_str = " VS ".join(f"<span style='color: #FFF;'>{t}</span>" for t in tied_teams_list)
    st.markdown(f"""
    <div style="border: 2px solid #D71313; border-radius: 15px; padding: 40px; text-align: center; background: linear-gradient(135deg, #2a0000 0%, #000000 100%); margin-top: 10px; margin-bottom: 20px; box-shadow: 0 0 30px rgba(215, 19, 19, 0.4);">
        <h1 style="color: #D71313; letter-spacing: 4px; margin: 0; font-size: 3rem; font-weight: 900;">🚨 SUDDEN DEATH REQUIRED 🚨</h1>
        <h3 style="color: #AAA; letter-spacing: 2px; margin-top: 15px; margin-bottom: 25px;">F1 SCORES AND GOLD MEDALS ARE DEADLOCKED</h3>
        <h2 style="font-size: 2.5rem; margin: 0;">{tied_teams_str}</h2>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="border: 2px dashed #444; border-radius: 15px; padding: 40px; text-align: center; margin-top: 10px; margin-bottom: 20px;">
        <h2 style="color: #555; letter-spacing: 2px; margin: 0;">AWAITING ALL 5 QUESTS & FINAL PROMPT SUBMISSIONS...</h2>
    </div>
    """, unsafe_allow_html=True)

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
        tab1, tab2 = st.tabs(["🏅 AWARD MEDALS", "🔴 DANGER ZONE"])
        
        with tab1:
            st.info("Award Medals (Auto-filters previously selected teams)")
            quest_select = st.selectbox("Select Quest:", ["QUEST 1: BEACH VOLLEYBALL", "QUEST 2: BADMINTON", "QUEST 3: KARAOKE RELAY", "QUEST 4: BOTTLE FLIP TIC TAC TOE", "QUEST 5: BLIND GOLFER"])
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
                st.success("CLEAN SLATE.")
                time.sleep(1)
                st.rerun()
        
        if st.button("LOG OUT"):
            st.session_state['admin_logged_in'] = False
            st.rerun()

# --- AUTO REFRESH LOOP ---
time.sleep(60)
st.rerun()
