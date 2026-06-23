import streamlit as st
import os
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import re
from openai import OpenAI, AuthenticationError, RateLimitError, OpenAIError
from resume_reader import (
    extract_text_from_pdf, 
    extract_skills, 
    compare_skills, 
    combined_match_score, 
    COMPREHENSIVE_SKILLS,
    mock_ai_suggestions,
    detect_company,
    generate_company_specific_tips
)
from resume_builder import (
    TEMPLATES,
    build_html_resume,
    build_autofix_prompt,
    wrap_autofix_as_html,
    score_ats,
    smart_offline_rewrite,
)

# ------------------ PAGE SETUP ------------------
st.set_page_config(
    page_title="Smart Resume Analyzer", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced Custom CSS with Floating Effects
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    /* Floating Background Orbs */
    .main::before {
        content: '';
        position: fixed;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.3) 0%, transparent 70%);
        border-radius: 50%;
        top: -250px;
        left: -250px;
        animation: float-orb-1 20s ease-in-out infinite;
        z-index: 0;
        pointer-events: none;
    }
    
    .main::after {
        content: '';
        position: fixed;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(118, 75, 162, 0.25) 0%, transparent 70%);
        border-radius: 50%;
        bottom: -200px;
        right: -200px;
        animation: float-orb-2 25s ease-in-out infinite;
        z-index: 0;
        pointer-events: none;
    }
    
    @keyframes float-orb-1 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(100px, 50px) scale(1.1); }
        50% { transform: translate(50px, 100px) scale(0.9); }
        75% { transform: translate(-50px, 50px) scale(1.05); }
    }
    
    @keyframes float-orb-2 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(-80px, -60px) scale(1.15); }
        66% { transform: translate(-40px, 40px) scale(0.95); }
    }
    
    /* Header Styling with Float Animation */
    h1 {
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 1rem;
        animation: fadeInDown 0.8s ease-in-out, float-title 3s ease-in-out infinite;
        position: relative;
        z-index: 1;
    }
    
    @keyframes float-title {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    /* Card Styling with Hover Float */
    div[data-testid="stFileUploader"], 
    div[data-testid="stTextArea"] {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        transition: transform 0.4s ease, box-shadow 0.4s ease;
        position: relative;
        z-index: 1;
        animation: float-card 6s ease-in-out infinite;
    }
    
    div[data-testid="stFileUploader"]:hover,
    div[data-testid="stTextArea"]:hover {
        transform: translateY(-10px);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
    }
    
    @keyframes float-card {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
    }
    
    /* Button Styling with Pulse */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        font-size: 1.1rem;
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        position: relative;
        overflow: hidden;
        z-index: 1;
    }
    
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton>button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6);
    }
    
    .stButton>button:active {
        transform: translateY(-1px) scale(0.98);
    }
    
    /* Metric Cards with Float */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border-left: 5px solid #667eea;
        transition: all 0.4s ease;
        position: relative;
        z-index: 1;
        animation: float-metric 5s ease-in-out infinite;
    }
    
    div[data-testid="stMetric"]:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    div[data-testid="stMetric"]:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes float-metric {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-10px) scale(1.03);
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.2);
        border-left-width: 8px;
    }
    
    div[data-testid="stMetric"] label {
        color: #667eea !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    div[data-testid="stMetric"] div {
        color: #2d3748 !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
    }
    
    /* Success/Warning/Error Messages with Slide-In */
    .stSuccess, .stWarning, .stError, .stInfo {
        padding: 1rem;
        border-radius: 10px;
        border: none;
        position: relative;
        z-index: 1;
        animation: slideInRight 0.5s ease-out;
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
    }
    
    .stWarning {
        background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(237, 137, 54, 0.3);
    }
    
    .stError {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(245, 101, 101, 0.3);
    }
    
    .stInfo {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(66, 153, 225, 0.3);
    }
    
    /* Expander with Bounce */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.8rem;
        transition: all 0.3s ease;
        position: relative;
        z-index: 1;
    }
    
    .streamlit-expanderHeader:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Markdown Headers */
    h2, h3 {
        color: #667eea !important;
        font-weight: 600 !important;
        position: relative;
        z-index: 1;
    }
    
    /* Section Headers with Scale Animation */
    .section-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        font-size: 1.3rem;
        text-align: center;
        margin: 2rem 0 1rem 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        position: relative;
        z-index: 1;
        animation: scaleIn 0.5s ease-out;
    }
    
    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    /* Skills List with Slide-Up */
    .stMarkdown li {
        background: white;
        margin: 0.5rem 0;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        position: relative;
        z-index: 1;
        animation: slideUp 0.4s ease-out backwards;
    }
    
    .stMarkdown li:nth-child(1) { animation-delay: 0.05s; }
    .stMarkdown li:nth-child(2) { animation-delay: 0.1s; }
    .stMarkdown li:nth-child(3) { animation-delay: 0.15s; }
    .stMarkdown li:nth-child(4) { animation-delay: 0.2s; }
    .stMarkdown li:nth-child(5) { animation-delay: 0.25s; }
    .stMarkdown li:nth-child(n+6) { animation-delay: 0.3s; }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .stMarkdown li:hover {
        transform: translateX(10px) scale(1.02);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        background: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%);
    }
    
    /* Spinner Animation */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Content Container */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        animation: fadeIn 0.6s ease-in-out;
        position: relative;
        z-index: 1;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Footer Styling */
    .footer {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin-top: 3rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        position: relative;
        z-index: 1;
        animation: fadeInUp 0.8s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Plotly Chart Container */
    .js-plotly-plot {
        transition: transform 0.3s ease;
        position: relative;
        z-index: 1;
    }
    
    .js-plotly-plot:hover {
        transform: scale(1.02);
    }
    
    /* Additional floating elements */
    .stApp > header {
        background-color: transparent;
    }
    
    /* Make sure all content is above background */
    .element-container {
        position: relative;
        z-index: 1;
    }
    </style>
""", unsafe_allow_html=True)

# Animated Header
st.title("🤖 NEXUS")
st.markdown("""
    <p style='text-align: center; font-size: 1.2rem; color: #667eea; font-weight: 500; margin-top: -1rem; position: relative; z-index: 1;'>
        Your AI-powered career toolkit — <span style='background: linear-gradient(120deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700;'>Analyze · Auto-Fix · Build</span>
    </p>
""", unsafe_allow_html=True)

tab_analyze, tab_autofix, tab_builder = st.tabs([
    "📊 Resume Analyzer & AI Suggestions",
    "🔧 Auto-Fix Resume for Job",
    "🏗️ Build Resume from Scratch",
])




# ------------------ API SETUP ------------------
from dotenv import load_dotenv
load_dotenv(override=True)   # override=True ensures .env always wins over env vars

# ── OpenAI client — validated on startup ────────────────────────────────────
@st.cache_resource
def get_openai_client():
    """
    Load API key, create client, and validate with a lightweight models list call.
    Returns (client, status_message, is_valid).
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    # Detect placeholder keys
    if not api_key or api_key.startswith("sk-your") or "here" in api_key.lower():
        return None, "⚠️ No valid API key found in .env (OPENAI_API_KEY is missing or placeholder)", False

    try:
        c = OpenAI(api_key=api_key)
        # Lightweight validation — list models costs ~0 tokens
        c.models.list()
        return c, f"✅ OpenAI connected — key ending …{api_key[-6:]}", True
    except AuthenticationError:
        return None, "❌ OpenAI key is invalid or revoked — update OPENAI_API_KEY in .env", False
    except RateLimitError:
        # Key is real but quota hit — still return the client so calls can try
        c = OpenAI(api_key=api_key)
        return c, "⚠️ OpenAI key valid but rate limit / quota exceeded", True
    except Exception as e:
        return None, f"❌ OpenAI connection error: {str(e)[:120]}", False

client, _ai_status, _ai_ok = get_openai_client()

# Show AI status banner once at top of sidebar
with st.sidebar:
    if _ai_ok:
        st.success(_ai_status)
    else:
        st.warning(_ai_status)
        st.info("Without a valid key the app uses the smart offline optimizer. "
                "All other features work normally.")

# ------------------ VISUALIZATION FUNCTIONS ------------------
def create_score_gauge(score):
    """Create an animated gauge chart for match score"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Match Score", 'font': {'size': 24, 'color': '#667eea', 'family': 'Poppins'}},
        delta = {'reference': 50, 'increasing': {'color': "#48bb78"}, 'decreasing': {'color': "#f56565"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#667eea"},
            'bar': {'color': "#667eea"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e2e8f0",
            'steps': [
                {'range': [0, 40], 'color': '#fed7d7'},
                {'range': [40, 60], 'color': '#feebc8'},
                {'range': [60, 80], 'color': '#c6f6d5'},
                {'range': [80, 100], 'color': '#9ae6b4'}
            ],
            'threshold': {
                'line': {'color': "#764ba2", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Poppins, sans-serif'}
    )
    
    return fig

def create_skills_radar_chart(matched_skills, missing_skills, all_jd_skills):
    """Create a radar chart showing skill coverage by category"""
    
    categories = {
        'Programming': ['python', 'java', 'javascript', 'c++', 'c#', 'typescript', 'go', 'rust'],
        'Web Tech': ['react', 'angular', 'vue', 'node.js', 'django', 'flask', 'html', 'css'],
        'AI/ML': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp', 'computer vision'],
        'Data': ['sql', 'mongodb', 'pandas', 'numpy', 'data analysis', 'tableau', 'power bi'],
        'Cloud/DevOps': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'ci/cd'],
    }
    
    category_scores = {}
    for cat_name, cat_skills in categories.items():
        total = sum(1 for skill in all_jd_skills if any(cs in skill.lower() for cs in cat_skills))
        matched = sum(1 for skill in matched_skills if any(cs in skill.lower() for cs in cat_skills))
        
        if total > 0:
            category_scores[cat_name] = (matched / total) * 100
        else:
            category_scores[cat_name] = 0
    
    if category_scores:
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=list(category_scores.values()),
            theta=list(category_scores.keys()),
            fill='toself',
            name='Your Skills',
            line_color='#667eea',
            fillcolor='rgba(102, 126, 234, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10),
                    gridcolor='#e2e8f0'
                ),
                angularaxis=dict(
                    gridcolor='#e2e8f0'
                )
            ),
            showlegend=False,
            title={
                'text': 'Skills Coverage by Category',
                'font': {'size': 18, 'color': '#667eea', 'family': 'Poppins'},
                'x': 0.5,
                'xanchor': 'center'
            },
            height=400,
            margin=dict(l=80, r=80, t=80, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Poppins, sans-serif'}
        )
        
        return fig
    return None

def create_keyword_frequency_chart(resume_text, job_description):
    """Create a bar chart showing top keyword matches"""
    
    jd_words = re.findall(r'\b[a-z]{4,}\b', job_description.lower())
    stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'your', 'have', 'will', 'work', 'team', 'experience', 'skills', 'required'}
    jd_keywords = [w for w in jd_words if w not in stop_words]
    
    resume_lower = resume_text.lower()
    keyword_counts = {}
    for keyword in set(jd_keywords):
        count = resume_lower.count(keyword)
        if count > 0:
            keyword_counts[keyword] = count
    
    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    if top_keywords:
        keywords, counts = zip(*top_keywords)
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(counts),
                y=list(keywords),
                orientation='h',
                marker=dict(
                    color=list(counts),
                    colorscale=[[0, '#fed7d7'], [0.5, '#feebc8'], [1, '#9ae6b4']],
                    showscale=False
                ),
                text=list(counts),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title={
                'text': 'Top Keywords from Job Description',
                'font': {'size': 18, 'color': '#667eea', 'family': 'Poppins'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Frequency in Resume',
            yaxis_title='Keywords',
            height=400,
            margin=dict(l=20, r=20, t=60, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Poppins, sans-serif'},
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='#e2e8f0'),
            yaxis=dict(gridcolor='#e2e8f0')
        )
        
        return fig
    return None

def calculate_ats_score(resume_text, job_description=""):
    """
    Accurate multi-factor ATS scoring.
    Returns (total_score, issues_list) for backward compat,
    and stores full result in st.session_state['ats_full_result'].
    """
    result = score_ats(resume_text, job_description)
    # Store full result for detailed display
    import streamlit as _st
    _st.session_state["ats_full_result"] = result
    return result["total_score"], result["issues"]


def create_improvement_timeline():
    """Create a timeline showing improvement steps"""
    steps = [
        {'phase': 'Current', 'score': 45, 'color': '#f56565'},
        {'phase': 'Add Skills', 'score': 60, 'color': '#ed8936'},
        {'phase': 'Optimize Keywords', 'score': 75, 'color': '#ecc94b'},
        {'phase': 'Quantify Results', 'score': 85, 'color': '#48bb78'},
        {'phase': 'Final Polish', 'score': 95, 'color': '#38b2ac'}
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[s['phase'] for s in steps],
        y=[s['score'] for s in steps],
        mode='lines+markers',
        line=dict(color='#667eea', width=3),
        marker=dict(
            size=15,
            color=[s['color'] for s in steps],
            line=dict(color='white', width=2)
        ),
        text=[f"{s['score']}%" for s in steps],
        textposition='top center',
        textfont=dict(size=14, color='#2d3748', family='Poppins')
    ))
    
    fig.update_layout(
        title={
            'text': 'Your Improvement Roadmap',
            'font': {'size': 18, 'color': '#667eea', 'family': 'Poppins'},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title='Improvement Phase',
        yaxis_title='Expected Match Score (%)',
        yaxis=dict(range=[0, 100], gridcolor='#e2e8f0'),
        xaxis=dict(gridcolor='#e2e8f0'),
        height=350,
        margin=dict(l=20, r=20, t=60, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Poppins, sans-serif'}
    )
    
    return fig

def create_company_badge(company_name, confidence):
    """Create a visual badge for detected company"""
    
    company_colors = {
        "Google": "#4285F4",
        "Microsoft": "#00A4EF",
        "Amazon": "#FF9900",
        "Meta (Facebook)": "#1877F2",
        "Apple": "#555555",
        "Netflix": "#E50914",
        "Startup/Generic Tech": "#667eea"
    }
    
    color = company_colors.get(company_name, "#667eea")
    
    if confidence >= 90:
        conf_text = "Very High Confidence"
        conf_color = "#48bb78"
    elif confidence >= 70:
        conf_text = "High Confidence"
        conf_color = "#38b2ac"
    elif confidence >= 50:
        conf_text = "Medium Confidence"
        conf_color = "#ecc94b"
    else:
        conf_text = "Low Confidence (Generic)"
        conf_color = "#ed8936"
    
    badge_html = f"""
        <div style='background: linear-gradient(135deg, {color} 0%, {color}dd 100%); 
                    padding: 1.5rem; border-radius: 15px; color: white; text-align: center;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.15); margin: 1rem 0;
                    animation: scaleIn 0.6s ease-out;'>
            <h2 style='color: white !important; margin: 0; font-size: 2rem;'>🏢 {company_name}</h2>
            <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;'>
                Detected Company • {conf_text} ({confidence}%)
            </p>
        </div>
    """
    
    return badge_html

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — ANALYZER  (all original content lives here)
# ══════════════════════════════════════════════════════════════════════════════
with tab_analyze:

    # ------------------ INITIALIZE SESSION STATE ------------------
    if "resume_analyzed" not in st.session_state:
        st.session_state.resume_analyzed = False

    # ------------------ FILE UPLOAD SECTION ------------------
    st.markdown("<div class='section-header'>📄 Step 1: Upload & Input</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
       st.markdown("### 📄 Resume Upload")
       uploaded_file = st.file_uploader(
           "Upload your Resume (PDF format only)", 
           type=["pdf"],
           help="Maximum file size: 200MB"
       )

       if uploaded_file:
           st.success(f"✅ File uploaded: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")

    with col2:
       st.markdown("### 💼 Job Description")
       job_description = st.text_area(
           "Paste the Job Description here",
           height=200,
           placeholder="Paste the complete job description including requirements, responsibilities, and qualifications..."
       )

       if job_description:
           word_count = len(job_description.split())
           st.info(f"📝 Word count: {word_count}")

    # ------------------ ANALYZE BUTTON ------------------
    st.markdown("---")
    col_analyze, col_suggest = st.columns(2)

    with col_analyze:
       analyze_button = st.button("🚀 Analyze Resume", use_container_width=True)

    with col_suggest:
       suggest_button = st.button("💡 Generate AI Suggestions", use_container_width=True)

    # ------------------ ANALYSIS LOGIC ------------------
    if analyze_button:
       if not uploaded_file:
           st.error("❌ Please upload your resume first.")
       elif not job_description:
           st.error("❌ Please paste the job description first.")
       else:
           with st.spinner("🔍 Analyzing your resume..."):
               try:
                   # Extract text
                   resume_text = extract_text_from_pdf(uploaded_file)

                   if not resume_text or len(resume_text.strip()) < 50:
                       st.error("❌ Unable to extract text from PDF. Please ensure it's not a scanned/image-based PDF.")
                       st.info("💡 Try converting your PDF to text-based format or use OCR software first.")
                   else:
                       # Extract skills
                       resume_skills = extract_skills(resume_text, COMPREHENSIVE_SKILLS)
                       jd_skills = extract_skills(job_description, COMPREHENSIVE_SKILLS)

                       # Detect company
                       detected_company, company_confidence = detect_company(job_description)
                       company_tips = generate_company_specific_tips(detected_company, resume_text, jd_skills)

                       # Compare and score
                       matched, missing = compare_skills(resume_skills, jd_skills)
                       match_score = combined_match_score(resume_text, job_description, resume_skills, jd_skills)

                       # Calculate ATS score
                       ats_score, ats_issues = calculate_ats_score(resume_text, job_description)

                       # Store in session state
                       st.session_state.update({
                           "resume_text": resume_text,
                           "resume_skills": resume_skills,
                           "jd_skills": jd_skills,
                           "matched_skills": matched,
                           "missing_skills": missing,
                           "match_score": match_score,
                           "job_description": job_description,
                           "resume_analyzed": True,
                           "detected_company": detected_company,
                           "company_confidence": company_confidence,
                           "company_tips": company_tips,
                           "ats_score": ats_score,
                           "ats_issues": ats_issues
                       })

                       # Display results
                       st.markdown("<div class='section-header'>📊 Analysis Results</div>", unsafe_allow_html=True)
                       st.markdown("")

                       # Row 1: Score Gauge + Quick Stats
                       gauge_col, stats_col = st.columns([1, 2], gap="large")

                       with gauge_col:
                           fig_gauge = create_score_gauge(match_score)
                           st.plotly_chart(fig_gauge, use_container_width=True)

                       with stats_col:
                           score_col1, score_col2, score_col3 = st.columns(3)

                           with score_col1:
                               if match_score >= 80:
                                   score_emoji = "🎯"
                               elif match_score >= 60:
                                   score_emoji = "⚡"
                               else:
                                   score_emoji = "📈"

                               st.metric("Overall Match", f"{score_emoji} {match_score}%")

                           with score_col2:
                               match_percentage = (len(matched) / len(jd_skills) * 100) if jd_skills else 0
                               st.metric("Matched Skills", f"{len(matched)}/{len(jd_skills)}", 
                                        delta=f"{match_percentage:.0f}% coverage")

                           with score_col3:
                               st.metric("Missing Skills", len(missing),
                                        delta=f"-{len(missing)}" if missing else "None",
                                        delta_color="inverse")

                           # ── Detailed ATS Breakdown ─────────────────────────
                           st.markdown("")
                           ats_full = st.session_state.get("ats_full_result", {})
                           grade       = ats_full.get("grade", "")
                           grade_color = ats_full.get("grade_color", "#667eea")
                           breakdown   = ats_full.get("breakdown", {})

                           st.markdown(
                               f"<div style='background:white;border-radius:14px;padding:1.4rem 1.8rem;"
                               f"box-shadow:0 4px 16px rgba(0,0,0,.08);margin-bottom:.5rem;'>"
                               f"<div style='display:flex;align-items:center;gap:16px;flex-wrap:wrap;'>"
                               f"<div style='font-size:2.4rem;font-weight:800;color:{grade_color};'>{ats_score}%</div>"
                               f"<div><div style='font-size:1.1rem;font-weight:700;color:{grade_color};'>"
                               f"ATS Score — {grade}</div>"
                               f"<div style='font-size:.85rem;color:#718096;'>Based on 8 real ATS factors</div>"
                               f"</div></div></div>",
                               unsafe_allow_html=True
                           )

                           # Factor bars
                           if breakdown:
                               st.markdown("**📊 Score Breakdown by Factor:**")
                               factor_cols = st.columns(2)
                               for idx, (fkey, fdata) in enumerate(breakdown.items()):
                                   col = factor_cols[idx % 2]
                                   pct = fdata.get("pct", 0)
                                   sc  = fdata.get("score", 0)
                                   mx  = fdata.get("max", 10)
                                   lbl = fdata.get("label", fkey)
                                   bar_color = "#38a169" if pct >= 70 else ("#d69e2e" if pct >= 40 else "#e53e3e")
                                   col.markdown(
                                       f"<div style='margin:4px 0;'>"
                                       f"<div style='display:flex;justify-content:space-between;"
                                       f"font-size:.85rem;margin-bottom:2px;'>"
                                       f"<span style='font-weight:600;'>{lbl}</span>"
                                       f"<span style='color:{bar_color};font-weight:700;'>{sc}/{mx}</span></div>"
                                       f"<div style='background:#e2e8f0;border-radius:4px;height:8px;'>"
                                       f"<div style='background:{bar_color};width:{pct}%;height:8px;"
                                       f"border-radius:4px;transition:width .6s;'></div></div></div>",
                                       unsafe_allow_html=True
                                   )

                           # Strengths & issues
                           ats_strengths = ats_full.get("strengths", [])
                           ats_sugg      = ats_full.get("suggestions", [])
                           if ats_strengths or ats_issues:
                               st.markdown("")
                               sc1_col, sc2_col = st.columns(2)
                               with sc1_col:
                                   if ats_strengths:
                                       st.markdown("**💚 Strengths:**")
                                       for s in ats_strengths:
                                           st.markdown(f"<small>{s}</small>", unsafe_allow_html=True)
                               with sc2_col:
                                   if ats_issues:
                                       st.markdown("**🔴 Issues:**")
                                       for issue in ats_issues:
                                           st.markdown(f"<small>{issue}</small>", unsafe_allow_html=True)

                           if ats_sugg:
                               with st.expander("💡 Specific Fix Recommendations", expanded=False):
                                   for i, tip in enumerate(ats_sugg, 1):
                                       st.markdown(f"**{i}.** {tip}")

                       # Row 2: Visualizations
                       st.markdown("")
                       viz_col1, viz_col2 = st.columns(2, gap="large")

                       with viz_col1:
                           fig_radar = create_skills_radar_chart(matched, missing, jd_skills)
                           if fig_radar:
                               st.plotly_chart(fig_radar, use_container_width=True)

                       with viz_col2:
                           fig_keywords = create_keyword_frequency_chart(resume_text, job_description)
                           if fig_keywords:
                               st.plotly_chart(fig_keywords, use_container_width=True)

                       # Row 3: Improvement Timeline
                       st.markdown("")
                       fig_timeline = create_improvement_timeline()
                       st.plotly_chart(fig_timeline, use_container_width=True)

                       # Skills breakdown
                       st.markdown("")
                       st.markdown("<div class='section-header'>🎯 Skills Breakdown</div>", unsafe_allow_html=True)
                       skill_col1, skill_col2 = st.columns(2, gap="large")

                       with skill_col1:
                           st.markdown("""
                               <div style='background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); 
                                           padding: 1rem; border-radius: 10px; color: white; margin-bottom: 1rem;
                                           box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);'>
                                   <h3 style='color: white !important; margin: 0;'>✅ Matched Skills</h3>
                               </div>
                           """, unsafe_allow_html=True)
                           if matched:
                               matched_sorted = sorted(matched)
                               for i, skill in enumerate(matched_sorted, 1):
                                   st.markdown(f"{i}. **{skill.title()}**")
                           else:
                               st.info("No matching skills found. Consider adding relevant skills from the job description.")

                       with skill_col2:
                           st.markdown("""
                               <div style='background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%); 
                                           padding: 1rem; border-radius: 10px; color: white; margin-bottom: 1rem;
                                           box-shadow: 0 4px 15px rgba(245, 101, 101, 0.3);'>
                                   <h3 style='color: white !important; margin: 0;'>⚠️ Missing Skills</h3>
                               </div>
                           """, unsafe_allow_html=True)
                           if missing:
                               missing_sorted = sorted(missing)
                               for i, skill in enumerate(missing_sorted, 1):
                                   st.markdown(f"{i}. **{skill.title()}** 🔴")
                           else:
                               st.success("🎉 All required skills are present!")

                       # Recommendations
                       st.markdown("")
                       st.markdown("<div class='section-header'>💡 Smart Recommendations</div>", unsafe_allow_html=True)

                       if ats_issues:
                           with st.expander("⚠️ ATS Compatibility Issues Found - Click to View", expanded=False):
                               for issue in ats_issues:
                                   st.markdown(f"- 🔴 {issue}")

                       st.markdown("")

                       if match_score >= 80:
                           st.success("🎉 **Excellent match!** Your resume aligns very well with the job requirements.")
                           st.info("**Next Steps:** Apply with confidence! Consider tailoring your cover letter to highlight your matched skills.")
                       elif match_score >= 60:
                           st.warning("⚡ **Good match!** Your resume shows potential but could be improved.")
                           st.info("**Next Steps:** Add the missing skills or reframe your experience to highlight relevant projects. Use the AI Suggestions button for detailed guidance.")
                       elif match_score >= 40:
                           st.warning("📈 **Moderate match.** Several improvements needed.")
                           st.info("**Next Steps:** Focus on acquiring or highlighting the missing skills. Consider taking courses or working on projects related to the missing skills.")
                       else:
                           st.error("🔧 **Needs significant improvement.** Low alignment with job requirements.")
                           st.info("**Next Steps:** This role might require skills you don't currently have. Consider upskilling or applying to roles that better match your current skillset.")

                       if len(resume_skills) > 0:
                           st.markdown("")
                           st.markdown(f"""
                               <div style='background: white; padding: 1.5rem; border-radius: 12px; 
                                           box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-top: 2rem;'>
                                   <h4 style='color: #667eea; margin-bottom: 1rem;'>📋 Total Skills Found in Resume: <span style='color: #764ba2;'>{len(resume_skills)}</span></h4>
                               </div>
                           """, unsafe_allow_html=True)
                           with st.expander("🔍 View all extracted resume skills"):
                               skills_display = ", ".join(sorted([s.title() for s in resume_skills]))
                               st.markdown(f"<p style='line-height: 2;'>{skills_display}</p>", unsafe_allow_html=True)

                       # Company-Specific Optimization
                       st.markdown("")
                       st.markdown("<div class='section-header'>🏢 Company-Specific Optimization</div>", unsafe_allow_html=True)

                       company_badge = create_company_badge(company_tips["company_name"], company_confidence)
                       st.markdown(company_badge, unsafe_allow_html=True)

                       comp_col1, comp_col2 = st.columns(2, gap="large")

                       with comp_col1:
                           st.markdown("""
                               <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                           padding: 1.5rem; border-radius: 12px; color: white; height: 100%;
                                           box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);'>
                                   <h4 style='color: white !important; margin-bottom: 1rem;'>🎯 Company Culture Keywords</h4>
                           """, unsafe_allow_html=True)

                           for keyword in company_tips["culture_keywords"]:
                               st.markdown(f"<p style='color: white; margin: 0.3rem 0;'>• {keyword.title()}</p>", unsafe_allow_html=True)

                           st.markdown("</div>", unsafe_allow_html=True)

                       with comp_col2:
                           st.markdown("""
                               <div style='background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); 
                                           padding: 1.5rem; border-radius: 12px; color: white; height: 100%;
                                           box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);'>
                                   <h4 style='color: white !important; margin-bottom: 1rem;'>➕ Keywords to Add</h4>
                           """, unsafe_allow_html=True)

                           if company_tips["keywords_to_add"]:
                               for keyword in company_tips["keywords_to_add"][:5]:
                                   st.markdown(f"<p style='color: white; margin: 0.3rem 0;'>• {keyword.title()}</p>", unsafe_allow_html=True)
                           else:
                               st.markdown("<p style='color: white;'>✅ Great! Your resume already includes key culture keywords.</p>", unsafe_allow_html=True)

                           st.markdown("</div>", unsafe_allow_html=True)

                       st.markdown("")
                       with st.expander(f"📌 {company_tips['company_name']} Hiring Priorities", expanded=True):
                           st.markdown("### What They Look For:")
                           for i, priority in enumerate(company_tips["priorities"], 1):
                               st.markdown(f"**{i}.** {priority}")

                       st.markdown("")
                       with st.expander(f"💡 Resume Tips for {company_tips['company_name']}", expanded=True):
                           st.markdown("### Optimization Strategies:")
                           for i, tip in enumerate(company_tips["optimization_tips"], 1):
                               st.markdown(f"**{i}.** {tip}")

                       st.markdown("")
                       with st.expander(f"⚠️ Common Mistakes to Avoid", expanded=False):
                           for mistake in company_tips["avoid"]:
                               st.markdown(f"- 🚫 {mistake}")

               except Exception as e:
                   st.error(f"❌ Error during analysis: {str(e)}")
                   st.exception(e)
                   st.info("💡 If the error persists, try re-uploading your resume or check if it's a valid PDF file.")

    # ------------------ AI SUGGESTIONS LOGIC ------------------
    if suggest_button:
       if not st.session_state.get("resume_analyzed", False):
           st.warning("⚠️ Please analyze the resume first before generating AI suggestions.")
       else:
           with st.spinner("🤔 AI is reviewing your resume and generating personalised suggestions..."):
               try:
                   resume_text    = st.session_state["resume_text"]
                   missing_skills = st.session_state["missing_skills"]
                   matched_skills = st.session_state["matched_skills"]
                   job_desc       = st.session_state["job_description"]
                   match_score    = st.session_state["match_score"]
                   ats_full       = st.session_state.get("ats_full_result", {})

                   # ── Offline fallback helper ──────────────────────────────
                   def show_offline_suggestions():
                       suggestion = mock_ai_suggestions(resume_text, job_desc, missing_skills)
                       st.markdown(
                           "<div class='section-header'>💡 Resume Improvement Suggestions (Offline Mode)</div>",
                           unsafe_allow_html=True
                       )
                       st.markdown(suggestion)

                   if not client:
                       st.info("ℹ️ No valid OpenAI API key — showing smart offline suggestions.")
                       show_offline_suggestions()
                   else:
                       # Build a rich, structured prompt
                       missing_txt = ", ".join(missing_skills[:12]) if missing_skills else "None — all key skills matched!"
                       matched_txt = ", ".join(matched_skills[:12]) if matched_skills else "None"
                       ats_issues  = "\n".join(ats_full.get("issues", [])[:6]) or "None identified"
                       ats_grade   = ats_full.get("grade", "N/A")

                       system_msg = (
                           "You are a senior ATS optimization specialist and professional resume coach "
                           "with 15 years of experience placing candidates at FAANG, McKinsey, and Fortune 500 companies. "
                           "Give specific, actionable advice with concrete examples. "
                           "Use markdown formatting: **bold** for emphasis, numbered lists, and bullet points."
                       )

                       user_msg = f"""## Resume Analysis Request

**Current ATS Score:** {match_score}% match | Grade: {ats_grade}
**Matched Skills:** {matched_txt}
**Missing Skills:** {missing_txt}

**ATS Issues Found:**
{ats_issues}

**Resume (first 2800 chars):**
{resume_text[:2800]}

**Job Description (first 1800 chars):**
{job_desc[:1800]}

---

Please provide **5 specific, actionable recommendations** to maximise this resume's ATS score for this exact job posting:

1. **Keyword Injection** — List the exact JD keywords missing and which resume section to add each one to
2. **Bullet Point Rewrites** — Rewrite 2-3 of the weakest bullets using STAR format with quantification
3. **Skills Gap Strategy** — For each missing skill, suggest how to honestly address it (reframe existing work, add project, course)
4. **Section & Structure Fixes** — Specific ATS formatting improvements based on the issues found
5. **Summary Optimisation** — Write a new 3-sentence professional summary tailored to this exact JD

Be precise. Use the actual content from the resume and JD — no generic advice."""

                       try:
                           response = client.chat.completions.create(
                               model="gpt-4o-mini",       # better + cheaper than gpt-3.5-turbo
                               messages=[
                                   {"role": "system", "content": system_msg},
                                   {"role": "user",   "content": user_msg},
                               ],
                               max_tokens=1500,
                               temperature=0.5,
                           )
                           suggestion = response.choices[0].message.content.strip()

                           st.markdown(
                               "<div class='section-header'>🧠 AI-Powered Resume Suggestions</div>",
                               unsafe_allow_html=True
                           )
                           # Render as native markdown (not broken HTML replacement)
                           st.markdown(
                               f"<div style='background:white;padding:2rem;border-radius:15px;"
                               f"box-shadow:0 5px 20px rgba(0,0,0,.1);line-height:1.8;'>"
                               f"</div>",
                               unsafe_allow_html=True
                           )
                           st.markdown(suggestion)

                       except AuthenticationError:
                           st.error("❌ OpenAI API key is invalid or has been revoked. "
                                    "Please update OPENAI_API_KEY in your .env file and restart the app.")
                           show_offline_suggestions()
                       except RateLimitError:
                           st.warning("⚠️ OpenAI rate limit or quota exceeded. Showing offline suggestions.")
                           show_offline_suggestions()
                       except OpenAIError as e:
                           st.warning(f"⚠️ OpenAI API error: {str(e)[:200]}. Showing offline suggestions.")
                           show_offline_suggestions()

                   # ── Pro Tips (always shown) ───────────────────────────────
                   st.markdown("")
                   st.markdown("<div class='section-header'>📌 Pro Tips for ATS Success</div>", unsafe_allow_html=True)

                   tip_col1, tip_col2 = st.columns(2, gap="large")

                   with tip_col1:
                       st.markdown("""
                           <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                       padding: 1.5rem; border-radius: 12px; color: white;
                                       box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);'>
                               <h4 style='color: white !important;'>✨ Top Action Verbs</h4>
                               <p style='line-height:2;margin:0;'>
                               <b>Leadership:</b> Led, Directed, Spearheaded, Orchestrated<br>
                               <b>Achievement:</b> Delivered, Exceeded, Reduced, Increased<br>
                               <b>Technical:</b> Architected, Engineered, Deployed, Automated<br>
                               <b>Collaboration:</b> Partnered, Mentored, Facilitated, Aligned
                               </p>
                           </div>
                       """, unsafe_allow_html=True)

                   with tip_col2:
                       st.markdown("""
                           <div style='background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); 
                                       padding: 1.5rem; border-radius: 12px; color: white;
                                       box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);'>
                               <h4 style='color: white !important;'>📊 Quantification Formula</h4>
                               <p style='line-height:1.9;margin:0;'>
                               ❌ "Improved system performance"<br>
                               ✅ "Reduced API latency by <b>47%</b> (800ms→420ms) serving <b>50K</b> daily users"<br><br>
                               Every bullet: <b>Verb + What + How + Result (with number)</b>
                               </p>
                           </div>
                       """, unsafe_allow_html=True)

                   st.markdown("""
                       <div style='background:white;padding:1.5rem;border-radius:12px;
                                   margin-top:1rem;box-shadow:0 4px 15px rgba(0,0,0,.08);'>
                           <h4 style='color:#667eea;margin-top:0;'>🎯 ATS Best Practices Checklist</h4>
                           <ul style='line-height:2;color:#2d3748;margin:0;'>
                               <li>Use exact section headers: <b>Experience, Education, Skills</b></li>
                               <li>Single-column layout — no tables, text boxes, or columns</li>
                               <li>Standard fonts only: Arial, Calibri, Georgia, Times New Roman</li>
                               <li>Save as <b>text-based PDF</b> (not scanned image)</li>
                               <li>Mirror <b>exact phrases</b> from the job description — ATS is literal</li>
                               <li>Put most relevant bullets <b>first</b> in each section</li>
                           </ul>
                       </div>
                   """, unsafe_allow_html=True)

               except Exception as e:
                   st.error(f"❗ Unexpected error: {str(e)}")
                   st.exception(e)

    # ------------------ FOOTER (inside tab_analyze) ------------------
    st.markdown("")
    st.markdown("""
        <div class='footer'>
            <div style='text-align: center;'>
                <h3 style='background: linear-gradient(120deg, #667eea 0%, #764ba2 100%); 
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                           margin-bottom: 1rem;'>
                    💡 Pro Tips for Best Results
                </h3>
                <p style='color: #718096; font-size: 1.1rem; line-height: 1.8;'>
                    ✅ Ensure your resume is <strong>text-based PDF</strong>, not scanned images<br>
                    🎯 <strong>Match Score Guide:</strong> 80%+ = Excellent | 60-79% = Good | 40-59% = Fair | &lt;40% = Needs Work<br>
                    🚀 For best results, tailor your resume for each specific job posting
                </p>
                <div style='margin-top: 2rem; padding-top: 1.5rem; border-top: 2px solid #e2e8f0;'>
                    <p style='color: #a0aec0;'>
                        Built with ❤️ using <strong>Streamlit</strong> &amp; <strong>BY BRAINSTROMERS</strong> | 
                        <span style='background: linear-gradient(120deg, #667eea, #764ba2); 
                                     -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                                     font-weight: 600;'>
                            Smart Resume Analyzer v2.0
                        </span>
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — AUTO-FIX RESUME
#  Upload resume + paste JD → AI rewrites resume → download improved version
# ══════════════════════════════════════════════════════════════════════════════
with tab_autofix:
    st.markdown("<div class='section-header'>🔧 Auto-Fix Resume for a Specific Job</div>", unsafe_allow_html=True)
    st.markdown("""
        <p style='text-align:center;color:#718096;margin-bottom:1.5rem;'>
            Upload your existing resume + paste a job description.<br>
            AI will <strong>rewrite your resume</strong> to maximize ATS score for that exact role.
        </p>
    """, unsafe_allow_html=True)

    af_col1, af_col2 = st.columns([1, 1], gap="large")

    with af_col1:
        st.markdown("### 📄 Your Current Resume")
        af_uploaded = st.file_uploader(
            "Upload Resume (PDF)",
            type=["pdf"],
            key="autofix_upload",
            help="Upload the resume you want to improve"
        )
        if af_uploaded:
            st.success(f"✅ {af_uploaded.name} uploaded")

    with af_col2:
        st.markdown("### 💼 Target Job Description")
        af_jd = st.text_area(
            "Paste the Job Description",
            height=200,
            key="autofix_jd",
            placeholder="Paste the full job description here..."
        )

    st.markdown("---")
    af_btn = st.button("🚀 Auto-Fix & Optimize My Resume", use_container_width=True, key="autofix_btn")

    if af_btn:
        if not af_uploaded:
            st.error("❌ Please upload your resume PDF first.")
        elif not af_jd or len(af_jd.strip()) < 50:
            st.error("❌ Please paste a job description (at least 50 characters).")
        else:
            with st.spinner("🔍 Running full ATS analysis and optimizing..."):
                try:
                    # Extract resume text
                    af_resume_text = extract_text_from_pdf(af_uploaded)
                    if not af_resume_text or len(af_resume_text.strip()) < 100:
                        st.error("❌ Could not extract text from PDF. Make sure it is not a scanned image.")
                        st.stop()

                    # Full ATS analysis BEFORE optimization
                    af_ats_before   = score_ats(af_resume_text, af_jd)
                    af_score_before = af_ats_before["total_score"]

                    # Skill analysis
                    af_resume_skills           = extract_skills(af_resume_text, COMPREHENSIVE_SKILLS)
                    af_jd_skills               = extract_skills(af_jd, COMPREHENSIVE_SKILLS)
                    af_matched, af_missing     = compare_skills(af_resume_skills, af_jd_skills)
                    af_match_score             = combined_match_score(
                        af_resume_text, af_jd, af_resume_skills, af_jd_skills
                    )

                    # Try OpenAI first; fall back to smart offline optimizer silently
                    use_ai        = False
                    improved_text = ""
                    ai_error_msg  = ""

                    if client:
                        try:
                            sys_p, usr_p = build_autofix_prompt(
                                af_resume_text, af_jd, af_missing, af_ats_before
                            )
                            ai_resp = client.chat.completions.create(
                                model="gpt-4o-mini",   # better + cheaper than gpt-3.5-turbo
                                messages=[
                                    {"role": "system", "content": sys_p},
                                    {"role": "user",   "content": usr_p},
                                ],
                                max_tokens=2500,
                                temperature=0.3,       # lower temp = more precise keyword matching
                            )
                            improved_text = ai_resp.choices[0].message.content.strip()
                            use_ai = True
                        except AuthenticationError:
                            ai_error_msg = "❌ API key invalid — using offline optimizer"
                            improved_text = ""
                        except RateLimitError:
                            ai_error_msg = "⚠️ Rate limit / quota exceeded — using offline optimizer"
                            improved_text = ""
                        except OpenAIError as e:
                            ai_error_msg = f"⚠️ OpenAI error ({str(e)[:100]}) — using offline optimizer"
                            improved_text = ""

                    if not improved_text:
                        improved_text = smart_offline_rewrite(
                            af_resume_text, af_jd, af_missing, af_ats_before
                        )

                    # Compute AFTER score on the improved text
                    af_ats_after   = score_ats(improved_text, af_jd)
                    af_score_after = af_ats_after["total_score"]

                    # Build HTML output
                    candidate_name = af_resume_text.strip().split("\n")[0][:60]
                    html_output    = wrap_autofix_as_html(improved_text, candidate_name, "#1a73e8")

                    st.markdown(
                        "<div class='section-header'>✅ Optimization Complete!</div>",
                        unsafe_allow_html=True
                    )

                    if use_ai:
                        st.success("🧠 Optimized using GPT-4o-mini AI rewriting")
                    elif ai_error_msg:
                        st.warning(ai_error_msg)
                        st.info("⚡ Resume optimized using smart offline engine instead.")
                    else:
                        st.info(
                            "⚡ Optimized using smart offline engine. "
                            "Add a valid OpenAI API key to .env for full AI rewriting."
                        )

                    # Score comparison metrics
                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.metric("ATS Score Before",  f"{af_score_before}%")
                    delta_score = af_score_after - af_score_before
                    sc2.metric("ATS Score After",   f"{af_score_after}%",
                               f"+{delta_score}%" if delta_score > 0 else "—")
                    sc3.metric("Keyword Match",     f"{af_match_score}%")
                    sc4.metric("Keywords Added",    len(af_missing[:18]))

                    # Before / After factor breakdown
                    st.markdown("")
                    st.markdown("**📊 Factor-by-Factor Improvement:**")
                    bkd_before = af_ats_before.get("breakdown", {})
                    bkd_after  = af_ats_after.get("breakdown",  {})
                    bar_cols   = st.columns(2)
                    for idx_f, (fkey, fdata) in enumerate(bkd_after.items()):
                        col_f   = bar_cols[idx_f % 2]
                        lbl_f   = fdata.get("label", fkey)
                        sc_a    = fdata.get("score", 0)
                        sc_b    = bkd_before.get(fkey, {}).get("score", 0)
                        mx_f    = fdata.get("max", 10)
                        pct_a   = round(sc_a / max(mx_f, 1) * 100)
                        dlt_f   = sc_a - sc_b
                        dlt_str = f"(+{dlt_f})" if dlt_f > 0 else (f"({dlt_f})" if dlt_f < 0 else "")
                        bar_col = "#38a169" if pct_a >= 70 else ("#d69e2e" if pct_a >= 40 else "#e53e3e")
                        col_f.markdown(
                            f"<div style='margin:4px 0;'>"
                            f"<div style='display:flex;justify-content:space-between;"
                            f"font-size:.82rem;margin-bottom:2px;'>"
                            f"<span style='font-weight:600;'>{lbl_f}</span>"
                            f"<span style='color:{bar_col};font-weight:700;'>{sc_a}/{mx_f} "
                            f"<span style='color:#38a169;font-size:.78rem;'>{dlt_str}</span></span></div>"
                            f"<div style='background:#e2e8f0;border-radius:4px;height:7px;'>"
                            f"<div style='background:{bar_col};width:{pct_a}%;height:7px;"
                            f"border-radius:4px;'></div></div></div>",
                            unsafe_allow_html=True
                        )

                    st.markdown("")
                    with st.expander("👀 Preview Optimized Resume", expanded=True):
                        st.text_area(
                            "Rewritten Resume — edit here before saving",
                            improved_text, height=420, key="af_preview"
                        )

                    st.download_button(
                        label="⬇️ Download Optimized Resume (.html)",
                        data=html_output,
                        file_name="optimized_resume.html",
                        mime="text/html",
                        use_container_width=True,
                    )
                    st.info(
                        "💡 To get a PDF: open the downloaded file in Chrome → Ctrl+P → "
                        "Save as PDF. Remove the OPTIMIZATION CHECKLIST section before submitting."
                    )

                    if af_missing:
                        st.markdown("### 🔑 Keywords Woven In")
                        kw_html = "".join(
                            f"<span style='display:inline-block;background:#f0f4ff;color:#1a73e8;"
                            f"border:1px solid #1a73e8;border-radius:12px;padding:3px 10px;"
                            f"margin:3px;font-size:.9rem;'>{k}</span>"
                            for k in af_missing[:20]
                        )
                        st.markdown(kw_html, unsafe_allow_html=True)

                    remaining = af_ats_after.get("issues", [])
                    if remaining:
                        with st.expander("⚠️ Remaining Issues to Fix Manually", expanded=False):
                            for iss in remaining:
                                st.markdown(f"- {iss}")

                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    st.exception(e)

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — RESUME BUILDER FROM SCRATCH
# ══════════════════════════════════════════════════════════════════════════════
with tab_builder:
    st.markdown("<div class='section-header'>🏗️ Build Your ATS-Friendly Resume from Scratch</div>", unsafe_allow_html=True)
    st.markdown("""
        <p style='text-align:center;color:#718096;margin-bottom:1.5rem;'>
            Fill in your details, pick a professional template, and download a polished ATS-ready resume.
        </p>
    """, unsafe_allow_html=True)

    # ── Step 1: Choose template ────────────────────────────────────────────
    st.markdown("### 🎨 Step 1 — Choose a Template")
    tmpl_cols = st.columns(len(TEMPLATES))
    selected_template = st.session_state.get("selected_template", "faang_clean")

    for i, (key, tmpl) in enumerate(TEMPLATES.items()):
        with tmpl_cols[i]:
            is_selected = selected_template == key
            border_style = "3px solid #667eea" if is_selected else "2px solid #e2e8f0"
            bg = tmpl["preview_bg"]
            st.markdown(f"""
                <div style='border:{border_style};border-radius:12px;overflow:hidden;
                            cursor:pointer;transition:all 0.3s;text-align:center;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                    <div style='background:{bg};height:80px;display:flex;
                                align-items:center;justify-content:center;
                                font-size:2rem;'>
                        {tmpl["emoji"]}
                    </div>
                    <div style='padding:8px;font-size:0.85rem;font-weight:600;
                                color:#2d3748;'>{tmpl["name"]}</div>
                    <div style='padding:0 8px 8px;font-size:0.75rem;color:#718096;'>
                        {tmpl["description"]}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select", key=f"tmpl_{key}", use_container_width=True):
                st.session_state["selected_template"] = key
                st.rerun()

    selected_template = st.session_state.get("selected_template", "faang_clean")
    st.success(f"✅ Template selected: **{TEMPLATES[selected_template]['emoji']} {TEMPLATES[selected_template]['name']}**")

    st.markdown("---")

    # ── Step 2: Fill in details ────────────────────────────────────────────
    st.markdown("### 📝 Step 2 — Fill In Your Details")

    with st.expander("👤 Personal Information", expanded=True):
        pc1, pc2 = st.columns(2)
        with pc1:
            rb_name  = st.text_input("Full Name *", placeholder="John Doe", key="rb_name")
            rb_role  = st.text_input("Target Role / Title", placeholder="Software Engineer | Data Scientist", key="rb_role")
            rb_email = st.text_input("Email *", placeholder="john@example.com", key="rb_email")
            rb_phone = st.text_input("Phone", placeholder="+91 98765 43210", key="rb_phone")
        with pc2:
            rb_linkedin = st.text_input("LinkedIn URL", placeholder="linkedin.com/in/johndoe", key="rb_linkedin")
            rb_github   = st.text_input("GitHub / Portfolio", placeholder="github.com/johndoe", key="rb_github")
            rb_location = st.text_input("Location", placeholder="Delhi, India", key="rb_location")

    with st.expander("📋 Professional Summary / Objective", expanded=True):
        st.markdown("<small style='color:#718096;'>💡 Tip: Mirror words from the job description. "
                    "3–4 sentences: who you are → what you do → key achievement → goal.</small>",
                    unsafe_allow_html=True)
        rb_summary = st.text_area(
            "Write 3–4 sentences tailored to your target role",
            height=120,
            key="rb_summary",
            placeholder="Results-driven software developer with 2+ years of experience in Python and React. "
                        "Delivered scalable REST APIs serving 50K daily users at TechCorp. "
                        "Passionate about clean code, performance optimization, and Agile collaboration. "
                        "Seeking to bring full-stack expertise to a high-impact engineering team."
        )

    with st.expander("🛠️ Technical Skills", expanded=True):
        rb_skills_raw = st.text_input(
            "Enter skills separated by commas",
            key="rb_skills",
            placeholder="Python, React, SQL, AWS, Docker, Machine Learning..."
        )
        rb_skills = [s.strip() for s in rb_skills_raw.split(",") if s.strip()]
        if rb_skills:
            badges = "".join(
                f"<span style='display:inline-block;background:#f0f4ff;color:#667eea;"
                f"border:1px solid #667eea;border-radius:12px;padding:2px 10px;"
                f"margin:3px;font-size:0.85rem;'>{s}</span>"
                for s in rb_skills
            )
            st.markdown(badges, unsafe_allow_html=True)

    with st.expander("💼 Work Experience", expanded=True):
        num_exp = st.number_input("Number of experience entries", min_value=0, max_value=6, value=1, key="rb_num_exp")
        rb_experiences = []
        for i in range(int(num_exp)):
            st.markdown(f"**Experience #{i+1}**")
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                title = st.text_input("Job Title", key=f"exp_title_{i}", placeholder="Software Engineer")
            with ec2:
                company = st.text_input("Company", key=f"exp_company_{i}", placeholder="TechCorp Pvt Ltd")
            with ec3:
                duration = st.text_input("Duration", key=f"exp_dur_{i}", placeholder="Jun 2023 – Present")
            bullets_raw = st.text_area(
                "Bullet points (one per line — start each with an action verb)",
                key=f"exp_bullets_{i}",
                height=100,
                placeholder="Developed REST APIs reducing response time by 35%\nLed a team of 4 engineers to deliver product on time"
            )
            bullets = [b.strip() for b in bullets_raw.split("\n") if b.strip()]
            if title or company:
                rb_experiences.append({"title": title, "company": company, "duration": duration, "bullets": bullets})
            st.markdown("---")

    with st.expander("🎓 Education", expanded=True):
        num_edu = st.number_input("Number of education entries", min_value=1, max_value=4, value=1, key="rb_num_edu")
        rb_educations = []
        for i in range(int(num_edu)):
            ec1, ec2, ec3, ec4 = st.columns(4)
            with ec1:
                deg = st.text_input("Degree", key=f"edu_deg_{i}", placeholder="B.Tech Computer Science")
            with ec2:
                inst = st.text_input("Institution", key=f"edu_inst_{i}", placeholder="ABC University")
            with ec3:
                yr = st.text_input("Year", key=f"edu_yr_{i}", placeholder="2022 – 2026")
            with ec4:
                gpa = st.text_input("CGPA / GPA", key=f"edu_gpa_{i}", placeholder="8.7/10")
            if deg or inst:
                rb_educations.append({"degree": deg, "institution": inst, "year": yr, "gpa": gpa})

    with st.expander("🚀 Projects"):
        num_proj = st.number_input("Number of projects", min_value=0, max_value=8, value=2, key="rb_num_proj")
        rb_projects = []
        for i in range(int(num_proj)):
            pc1, pc2 = st.columns(2)
            with pc1:
                pname = st.text_input("Project Name", key=f"proj_name_{i}", placeholder="E-Commerce Recommendation Engine")
            with pc2:
                ptech = st.text_input("Tech Stack", key=f"proj_tech_{i}", placeholder="Python, Flask, PostgreSQL")
            pbullets_raw = st.text_area(
                "Description (one bullet per line)",
                key=f"proj_bullets_{i}",
                height=80,
                placeholder="Built a collaborative filtering model achieving 89% precision\nDeployed on AWS EC2 with CI/CD pipeline"
            )
            pbullets = [b.strip() for b in pbullets_raw.split("\n") if b.strip()]
            if pname:
                rb_projects.append({"name": pname, "tech": ptech, "bullets": pbullets})
            st.markdown("---")

    with st.expander("🏆 Certifications & Achievements"):
        rb_certs_raw = st.text_area("Certifications (one per line)", key="rb_certs", height=80,
            placeholder="AWS Certified Developer – Associate\nGoogle Data Analytics Certificate")
        rb_certs = [c.strip() for c in rb_certs_raw.split("\n") if c.strip()]

        rb_ach_raw = st.text_area("Achievements & Awards (one per line)", key="rb_ach", height=80,
            placeholder="1st Place – National Hackathon 2024\nPublished paper on NLP in IEEE")
        rb_achievements = [a.strip() for a in rb_ach_raw.split("\n") if a.strip()]

    st.markdown("---")

    # ── Step 3: Generate ──────────────────────────────────────────────────
    st.markdown("### ⚡ Step 3 — Generate & Download")
    gen_btn = st.button("🎉 Generate My ATS Resume", use_container_width=True, key="gen_resume_btn")

    if gen_btn:
        if not rb_name.strip():
            st.error("❌ Please enter your full name.")
        elif not rb_email.strip():
            st.error("❌ Please enter your email address.")
        else:
            resume_data = {
                "full_name":   rb_name,
                "role_title":  rb_role if 'rb_role' in dir() else "",
                "email":       rb_email,
                "phone":       rb_phone,
                "linkedin":    rb_linkedin,
                "github":      rb_github,
                "location":    rb_location,
                "summary":     rb_summary,
                "skills":      rb_skills,
                "experience":  rb_experiences,
                "education":   rb_educations,
                "projects":    rb_projects,
                "certifications": rb_certs,
                "achievements":   rb_achievements,
            }

            html_resume = build_html_resume(resume_data, selected_template)

            st.markdown("<div class='section-header'>🎉 Your Resume is Ready!</div>", unsafe_allow_html=True)
            st.success("✅ Resume generated successfully!")

            st.download_button(
                label="⬇️ Download Resume (.html)",
                data=html_resume,
                file_name=f"{rb_name.replace(' ','_')}_resume.html",
                mime="text/html",
                use_container_width=True,
            )

            with st.expander("👀 Preview Resume HTML", expanded=False):
                st.components.v1.html(html_resume, height=700, scrolling=True)

            st.info("💡 **To save as PDF:** Open the downloaded file in Chrome → Ctrl+P → Save as PDF → uncheck headers/footers for a clean look.")

            # ATS tips for the generated resume
            st.markdown("### ✅ ATS Checklist for Your Resume")
            checks = [
                ("✅" if rb_email else "❌", "Contact email included"),
                ("✅" if rb_phone else "⚠️", "Phone number included"),
                ("✅" if len(rb_skills) >= 5 else "⚠️", f"5+ skills listed ({len(rb_skills)} added)"),
                ("✅" if len(rb_experiences) > 0 else "⚠️", "Work experience section present"),
                ("✅" if len(rb_educations) > 0 else "❌", "Education section present"),
                ("✅" if rb_summary.strip() else "⚠️", "Professional summary included"),
                ("✅" if len(rb_projects) > 0 else "⚠️", "Projects section present"),
            ]
            for icon, label in checks:
                st.markdown(f"{icon} {label}")
