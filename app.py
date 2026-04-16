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
if 'reveal_stage' not in st.session_state: st.session_state['reveal_stage'] = 0 # 0=Locked, 1=4th, 2=3rd, 3=2nd, 4=Champion

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

    # Sort: Highest F1 -> Highest Gold -> Highest Silver -> Highest Bronze
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
    
    # 2ND PLACE (SILVER)
    with r_col1:
        if stage >= 3:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #111; border-radius: 15px; border: 1px solid #333;">
                <div style="color: #C0C0C0; font-weight: 900; letter-spacing: 2px; margin-bottom: 15px; font-size: 1.2rem;">2ND PLACE</div>
                {get_team_img_html(ranking_data[1]["Team"], 150, '#C0C0C0', 15)}
                <div style="color: #FFF; font-weight: 900; margin-top: 15px; font-size: 1.1rem;">{ranking_data[1]["Team"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(get_locked_html(260, "#C0C0C0", "2ND PLACE"), unsafe_allow_html=True)
            
    # 3RD PLACE (BRONZE)
    with r_col2:
        if stage >= 2:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #111; border-radius: 15px; border: 1px solid #333;">
                <div style="color: #CD7F32; font-weight: 900; letter-spacing: 2px; margin-bottom: 15px; font-size: 1.2rem;">3RD PLACE</div>
                {get_team_img_html(ranking_data[2]["Team"], 150, '#CD7F32', 15)}
                <div style="color: #FFF; font-weight: 900; margin-top: 15px; font-size: 1.1rem;">{ranking_data[2]["Team"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(get_locked_html(260, "#CD7F32", "3RD PLACE"), unsafe_allow_html=True)

    # 4TH PLACE (WOOD)
    with r_col3:
        if stage >= 1:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #111; border-radius: 15px; border: 1px solid #333;">
                <div style="color: #8B4513; font-weight: 900; letter-spacing: 2px; margin-bottom: 15px; font-size: 1.2rem;">4TH PLACE</div>
                {get_team_img_html(ranking_data[3]["Team"], 150, '#8B4513', 15)}
                <div style="color: #FFF; font-weight: 900; margin-top: 15px; font-size: 1.1rem;">{ranking_data[3]["Team"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(get_locked_html(260, "#8B4513", "4TH PLACE"), unsafe_allow_html=True)

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
                st.session_state['reveal_stage'] = 0 # Reset the reveal stage on wipe
                st.success("CLEAN SLATE.")
                time.sleep(1)
                st.rerun()
        
        if st.button("LOG OUT"):
            st.session_state['admin_logged_in'] = False
            st.rerun()

# --- AUTO REFRESH LOOP ---
time.sleep(60)
st.rerun()
