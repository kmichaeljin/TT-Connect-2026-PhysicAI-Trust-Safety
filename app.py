import streamlit as st
import string
from collections import Counter  # <--- MAKE SURE THIS IS HERE

# --- CONFIGURATION (EDIT THESE LATER) ---
# You can change these two lines whenever you have the final text.
TARGET_PROMPT = "The strength of the team is each individual member"
WINNING_RESULT = "🚀 WINNING CODE: 'BLUE-OCEAN-2024'"

from collections import Counter

# --- F1 SCORE LOGIC (The "Brain") ---
def calculate_f1(prediction, ground_truth):
    # 1. Normalize text (lowercase, remove punctuation)
    def normalize(text):
        return text.lower().translate(str.maketrans('', '', string.punctuation)).split()
    
    pred_tokens = normalize(prediction)
    truth_tokens = normalize(ground_truth)
    
    if not pred_tokens or not truth_tokens:
        return 0.0, 0.0, 0.0

    # 2. Count words (handles duplicates like "the")
    pred_counts = Counter(pred_tokens)
    truth_counts = Counter(truth_tokens)
    
    # 3. Calculate Intersection (Shared words accounting for count)
    common_tokens = pred_counts & truth_counts
    num_common = sum(common_tokens.values())
    
    # 4. Calculate Precision & Recall
    precision = num_common / len(pred_tokens)
    recall = num_common / len(truth_tokens)
    
    # 5. Calculate F1
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)
        
    return f1, precision, recall

# --- USER INTERFACE ---
st.set_page_config(page_title="AI Validator", page_icon="🤖")

st.title("🤖 Code Phrase Validator")
st.markdown("### Status: `WAITING FOR INPUT`")
st.info("Enter the recovered phrase below to authenticate.")

# Input Box
user_input = st.text_input("Input Phrase:", placeholder="Type the secret phrase here...")

# Authentication Button
if st.button("Analyze & Authenticate"):
    if not user_input:
        st.warning("⚠️ Input is empty.")
    else:
        # Run the F1 Logic
        f1_score, precision, recall = calculate_f1(user_input, TARGET_PROMPT)
        
        # Display Metrics (The "Data Science" part)
        col1, col2, col3 = st.columns(3)
        col1.metric("F1 Score", f"{f1_score:.2f}")
        col2.metric("Precision", f"{precision:.2f}")
        col3.metric("Recall", f"{recall:.2f}")
        
        # --- DECISION LOGIC ---
        if f1_score == 1.0:
            # PERFECT MATCH
            st.success("✅ AUTHENTICATION APPROVED")
            st.balloons()
            st.divider()
            st.markdown(f"## {WINNING_RESULT}")
            
        elif f1_score >= 0.8:
            # HIGH CONFIDENCE
            st.warning("⚠️ High Confidence Match (Approx 80%). Check word order or spelling.")
            
        elif f1_score >= 0.5:
            # MEDIUM CONFIDENCE
            st.info("⚠️ Medium Confidence. You found about half the correct words.")
            
        else:
            # LOW CONFIDENCE
            st.error("❌ Authentication Failed. Low similarity.")

# --- FOOTER ---
st.divider()
st.caption("AI Agent v1.0 | Metric: Token-Based F1 Score")