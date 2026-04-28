import streamlit as st
import pandas as pd
import gspread
import base64
import os
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
st.set_page_config(page_title="MVP Voting Terminal", page_icon="⭐", layout="centered")

TEAMS_LIST = [
    "BLUE ANALYSTS", 
    "GRAY SHIELDS", 
    "GREEN DETECTIVES", 
    "VIOLET STRATEGISTS"
]

# --- THE ROSTER DATABASE (NUMERICALLY SORTED, SINGLE DIGITS) ---
TEAM_ROSTERS = {
    "BLUE ANALYSTS": [
        "2 - Gasacao", "4 - Licayan", "7 - Ryan", "7 - Ukaigwe", "8 - Echo", 
        "8 - Rance", "8 - Zoe", "9 - Delos Santos", "9 - Ingrid", 
        "14 - Caballero", "21 - Corcoran", "26 - Gonzales", "85 - Tomes"
    ],
    "GRAY SHIELDS": [
        "1 - Dianne", "4 - Adi", "4 - Eduarte", "4 - Ryser", "7 - Cruise", 
        "8 - Agliam", "8 - Kath", "9 - Fernando", "13 - Keito", 
        "14 - Tyler Bailey", "21 - Mona", "25 - Veronica", "96 - Josh"
    ],
    "GREEN DETECTIVES": [
        "4 - Pablico", "4 - Paulino", "7 - MG", "7 - Rai", "7 - Rissa", 
        "8 - Bonete", "8 - Nelson", "11 - Angeles", "13 - Nulud", 
        "27 - Garo", "27 - Jenver", "37 - Jay-es", "43 - San Juan"
    ],
    "VIOLET STRATEGISTS": [
        "2 - Boy Bangis", "6 - Win", "7 - Jhen", "7 - Miko", "8 - Ramos", 
        "8 - Rei", "11 - Rombough", "14 - Armie", "15 - Marj", 
        "19 - Amigo", "19 - Tine", "23 - Louise", "25 - Anlap"
    ]
}

SHEET_NAME = "PhysicAI_Leaderboard"
WORKSHEET_MVP = "MVP_Votes"

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

def submit_vote(team, nominee):
    sheet = connect_to_sheet(WORKSHEET_MVP)
    if sheet:
        sheet.append_row([team, nominee])

# --- SESSION STATE ---
if 'voted' not in st.session_state: st.session_state['voted'] = False

# --- THEME & ASSETS ---
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

# --- CSS ---
st.markdown(f"""
    <style>
    .stApp {{ {background_style} color: #FFFFFF; }}
    
    /* Hide top header and footer for cinematic look */
    #MainMenu {{visibility: hidden;}} header {{visibility: hidden;}} footer {{visibility: hidden;}}
    
    div[data-testid="block-container"] {{ 
        background-color: rgba(0, 0, 0, 0.85); /* Slightly darker overlay for readability */
        border: 1px solid #333; 
        border-radius: 15px; 
        padding: 2rem; 
        margin-top: 2rem; 
        box-shadow: 0 0 20px rgba(215, 19, 19, 0.1);
    }}
    
    /* Input Styling to match the Main Dashboard's Red/Dark theme */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {{ 
        background-color: #111 !important; 
        color: #FFF !important; 
        border: 1px solid #444 !important; 
        text-align: center; 
    }}
    
    .stSelectbox div[data-baseweb="select"]:focus-within {{
        border-color: #D71313 !important;
        box-shadow: 0 0 5px rgba(215, 19, 19, 0.5) !important;
    }}

    .stButton > button {{ 
        background: linear-gradient(135deg, #8a0000 0%, #D71313 100%) !important; 
        color: #FFF !important; 
        font-weight: 900 !important; 
        letter-spacing: 2px !important;
        width: 100% !important; 
        height: 60px !important; 
        border-radius: 8px !important; 
        border: none !important;
        transition: 0.3s !important; 
    }}
    
    .stButton > button:hover {{ 
        box-shadow: 0 0 15px rgba(215, 19, 19, 0.8) !important; 
        transform: scale(1.02) !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- UI ---
c1, c2, c3 = st.columns([1,2,1])
with c2:
    if os.path.exists("physicai_logo.png"): 
        st.image("physicai_logo.png", use_container_width=True)
    elif os.path.exists("company_logo.png"): 
        st.image("company_logo.png", use_container_width=True)

st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1 style='color: #D71313; letter-spacing: 4px; font-weight: 900; margin-bottom: 5px; margin-top: 10px;'>SQUAD MVP POLL</h1>
        <p style='color: #888; letter-spacing: 1px;'>Cast your final vote for the player who carried the team.</p>
    </div>
""", unsafe_allow_html=True)

if not st.session_state['voted']:
    team = st.selectbox("Select Your Squad:", TEAMS_LIST, index=None, placeholder="WHO DO YOU FIGHT FOR?")
    st.write("")
    
    if team:
        nominee = st.selectbox("MVP Nominee:", TEAM_ROSTERS[team], index=None, placeholder="SELECT YOUR MVP")
        st.write("")
        
        if st.button("LOCK IN VOTE"):
            if team and nominee:
                with st.spinner("Encrypting and transmitting vote..."):
                    submit_vote(team, nominee)
                st.session_state['voted'] = True
                st.rerun()
            else:
                st.error("⚠️ PLEASE SELECT A NOMINEE")
    else:
        st.selectbox("MVP Nominee:", ["Awaiting squad selection..."], disabled=True)

else:
    st.markdown("""
    <div style="text-align: center; border: 2px solid #D71313; border-radius: 15px; padding: 40px; background-color: rgba(26, 0, 0, 0.8);">
        <h1 style="color: #D71313; font-size: 4rem; margin: 0;">✅</h1>
        <h2 style="color: #FFF; letter-spacing: 2px; margin-top: 10px; font-weight: 900;">VOTE SECURED</h2>
        <p style="color: #888;">Return your attention to the Main Dashboard.</p>
    </div>
    """, unsafe_allow_html=True)
