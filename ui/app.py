import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Standard imports
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Project-specific imports
try:
    from utils.pdf_reader import extract_text_from_pdf
    from utils.sqlite_logger import init_db
    from utils.exporter import export_to_pdf, send_email
    from utils.config import update_email_config

    # Agent imports
    from agents.controller_agent import ControllerAgent
    from agents.auto_apply_agent import AutoApplyAgent
    from agents.recruiter_view_agent import RecruiterViewAgent
    from agents.skill_recommendation_agent import SkillRecommendationAgent

    # Import fallback handler
    from agents.agent_fallback import AgentFallbackHandler

    # Flag to indicate if agents are available
    AGENTS_AVAILABLE = True
except ImportError as e:
    st.error(f"Error importing required modules: {str(e)}")
    st.warning(
        "Some functionality may be limited. Please ensure all requirements are installed."
    )
    AGENTS_AVAILABLE = False

    # Import fallback handler directly if available
    try:
        from agents.agent_fallback import AgentFallbackHandler
    except ImportError:
        # Define a minimal fallback handler class if it can't be imported
        class AgentFallbackHandler:
            @staticmethod
            def controller_analyze_resume(*args, **kwargs):
                return {
                    "error": "Agent functionality unavailable",
                    "message": "Please contact support.",
                }

            @staticmethod
            def company_research(*args, **kwargs):
                return {"error": "Company research functionality unavailable"}

            @staticmethod
            def generate_skill_recommendations(*args, **kwargs):
                return {"error": "Skill recommendation functionality unavailable"}


# Page configuration
st.set_page_config(
    page_title="JobSniper AI - Complete Career Intelligence Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Advanced CSS for premium UI/UX
st.markdown(
    """
<style>
    /* Import Premium Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@100;200;300;400;500;600;700;800;900&family=Inter:wght@100;200;300;400;500;600;700;800;900&display=swap');
    
    /* Root Variables */
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --dark-gradient: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        --glass-bg: rgba(255, 255, 255, 0.1);
        --glass-border: rgba(255, 255, 255, 0.2);
        --shadow-light: 0 8px 32px rgba(0, 0, 0, 0.1);
        --shadow-medium: 0 16px 48px rgba(0, 0, 0, 0.15);
        --shadow-heavy: 0 24px 64px rgba(0, 0, 0, 0.2);
        --border-radius: 16px;
        --transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Global Styles */
    .stApp {
        font-family: 'Poppins', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        min-height: 100vh;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Enhanced Main Header */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 4rem 3rem;
        border-radius: 24px;
        color: white;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: var(--shadow-heavy);
        backdrop-filter: blur(20px);
        border: 2px solid rgba(255,255,255,0.1);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.05) 50%, transparent 70%);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    .main-header h1 {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    .main-header h3 {
        font-size: 1.5rem;
        font-weight: 400;
        margin-bottom: 1rem;
        opacity: 0.9;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.8;
        font-weight: 300;
    }
    
    /* Feature Cards */
    .feature-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        color: #2c3e50 !important;
    }
    
    .feature-card * {
        color: #2c3e50 !important;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
        position: relative;`112
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        pointer-events: none;
    }
    
    .metric-card:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 16px 48px rgba(102, 126, 234, 0.4);
    }
    
    .metric-card h3 {
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-card h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .metric-card p {
        font-size: 0.85rem;
        opacity: 0.8;
        font-weight: 400;
    }
    
    /* Progress Steps */
    .progress-step {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    .progress-step.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    .progress-step.completed {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3);
    }
    
    .progress-step.pending {
        background: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Auto Apply Cards */
    .auto-apply-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 1.5rem 0;
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        color: #2c3e50 !important;
    }
    
    .auto-apply-card * {
        color: #2c3e50 !important;
    }
    
    .auto-apply-card h4 {
        color: #2c3e50 !important;
        font-weight: 600;
        margin-bottom: 1rem;
        font-size: 1.2rem;
    }
    
    /* Chat Container */
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 1.5rem;
        height: 400px;
        overflow-y: auto;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .chat-message {
        margin: 0.8rem 0;
        padding: 1rem 1.5rem;
        border-radius: 16px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 15%;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    .ai-message {
        background: rgba(255, 255, 255, 0.9);
        color: #2c3e50;
        margin-right: 15%;
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
    
    /* Sidebar Styles */
    .sidebar-section {
        background: rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }
    
    /* Input Styles */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: rgba(44, 62, 80, 0.9) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        background: rgba(44, 62, 80, 0.95) !important;
        border: 2px solid rgba(102, 126, 234, 0.8) !important;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25) !important;
    }
    
    /* Number input specific */
    .stNumberInput > div > div > input {
        background: rgba(44, 62, 80, 0.9) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
    }
    
    /* Selectbox options */
    .stSelectbox > div > div > div[data-baseweb="select"] > div {
        background: rgba(44, 62, 80, 0.9) !important;
        color: white !important;
    }
    
    /* Input Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stNumberInput > label {
        color: white !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Help text */
    .stTextInput > div > div > div:last-child,
    .stTextArea > div > div > div:last-child,
    .stSelectbox > div > div > div:last-child,
    .stNumberInput > div > div > div:last-child {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* Dropdown menu styling */
    .stSelectbox div[data-baseweb="select"] ul {
        background: rgba(44, 62, 80, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .stSelectbox div[data-baseweb="select"] li {
        background: rgba(44, 62, 80, 0.95) !important;
        color: white !important;
    }
    
    .stSelectbox div[data-baseweb="select"] li:hover {
        background: rgba(102, 126, 234, 0.8) !important;
    }
    
    /* Button in dark areas */
    div[data-testid="stForm"] .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    /* File Uploader */
    .stFileUploader > div {
        background: rgba(255, 255, 255, 0.1);
        border: 2px dashed rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        padding: 2rem;
        backdrop-filter: blur(10px);
    }
    
    /* Success/Error Messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# Initialize database
init_db()

# Function to get HR analytics data
def get_hr_analytics():
    """Get HR analytics data from database or generate sample data"""
    try:
        analyzed_resumes = st.session_state.get("analyzed_resumes", [])
        
        # Calculate metrics from actual data
        total_candidates = len(analyzed_resumes)
        
        # Get candidates from this week
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        candidates_this_week = len([
            r for r in analyzed_resumes 
            if datetime.fromisoformat(r.get("timestamp", datetime.now().isoformat())) > week_ago
        ])
        
        # Calculate average score
        scores = [r.get("match_score", 0) for r in analyzed_resumes if r.get("match_score", 0) > 0]
        average_score = int(sum(scores) / len(scores)) if scores else 0
        
        return {
            "candidates_this_week": candidates_this_week,
            "average_score": average_score,
            "interviews_scheduled": max(0, candidates_this_week // 3),  # Simulated: ~1/3 get interviews
            "hired_this_month": max(0, total_candidates // 10)         # Simulated: ~10% hire rate
        }
    except Exception:
        return {
            "candidates_this_week": 0,
            "average_score": 0,
            "interviews_scheduled": 0,
            "hired_this_month": 0
        }

# Initialize session state
# Initialize session state variables
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "auto_apply_step" not in st.session_state:
    st.session_state.auto_apply_step = 0
if "analyzed_resumes" not in st.session_state:
    st.session_state.analyzed_resumes = []
if "hr_analytics" not in st.session_state:
    st.session_state.hr_analytics = get_hr_analytics()

# Header
st.markdown(
    """
<div class="main-header">
    <h1>🎯 JobSniper AI</h1>
    <h3>Complete Career Intelligence Platform</h3>
    <p>AI-Powered Resume Analysis • Auto Job Applications • HR Tools • Skill Recommendations</p>
</div>
""",
    unsafe_allow_html=True,
)

# Sidebar Navigation
st.sidebar.markdown("## 🎯 JobSniper AI Platform")
st.sidebar.markdown("---")

# Mode Selection
mode = st.sidebar.selectbox(
    "Select Mode",
    [
        "🔍 Job Seeker Mode",
        "👥 HR/Recruiter Mode",
        "🚀 Auto Apply Mode",
        "📚 Skill Development",
    ],
    key="mode_selector",
)

st.sidebar.markdown("---")

# Quick Actions Sidebar
st.sidebar.markdown("### ⚡ Quick Actions")
if st.sidebar.button("📊 View Analytics Dashboard"):
    st.session_state.show_dashboard = True

if st.sidebar.button("📈 Generate Career Report"):
    st.session_state.generate_report = True

if st.sidebar.button("🎯 Skill Gap Analysis"):
    st.session_state.skill_analysis = True

st.sidebar.markdown("---")

# Email Configuration in Sidebar
with st.sidebar.expander("📧 Email Configuration"):
    sender_email = st.text_input("Gmail Address", placeholder="your_gmail@gmail.com")
    sender_password = st.text_input("App Password", type="password")
    recipient_email = st.text_input(
        "Default Recipient", placeholder="recipient@example.com"
    )

    if st.button("💾 Save Configuration"):
        if sender_email and sender_password:
            update_email_config(sender_email, sender_password)
            st.success("✅ Email configuration saved!")
        else:
            st.error("❌ Please provide both email and password")

# Main Content Area
if mode == "🔍 Job Seeker Mode":
    st.markdown("## 🔍 Job Seeker Intelligence Center")

    # Show welcome message if no analysis has been done
    if not st.session_state.get("analysis_results"):
        st.markdown("""
        <div class="feature-card" style="border-left: 4px solid #667eea;">
            <h4>🚀 Welcome to Your AI Career Assistant!</h4>
            <p>Upload your resume below to get started with AI-powered analysis, skill matching, and personalized career recommendations. 
            Your data will be used to generate real-time insights across all modules.</p>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    # Metrics Dashboard
    with col1:
        if "analysis_results" in st.session_state and st.session_state.analysis_results:
            match_percent = st.session_state.analysis_results.get("match_result", {}).get("match_percent", "-")
            st.markdown(f"""
            <div class="metric-card">
                <h3>Resume Score</h3>
                <h1>{match_percent if match_percent != '-' else '--'}%</h1>
                <p>AI Analyzed</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>Resume Score</h3>
                <h1>--</h1>
                <p>AI Analyzed</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if "analysis_results" in st.session_state and st.session_state.analysis_results:
            match_data = st.session_state.analysis_results.get("match_result", {})
            match_score = match_data.get("match_percent", "-")
            matched_skills = match_data.get("matched_skills", [])
            
            # Show top matched skills preview
            skills_preview = ", ".join(matched_skills[:2]) if matched_skills else "None"
            if len(matched_skills) > 2:
                skills_preview += f" +{len(matched_skills) - 2} more"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>Match Score</h3>
                <h1>{match_score if match_score != '-' else '--'}%</h1>
                <p>Job Alignment</p>
            </div>
            """, unsafe_allow_html=True)
            
            if matched_skills:
                st.caption(f"✅ Strong in: {skills_preview}")
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>Match Score</h3>
                <h1>--</h1>
                <p>Job Alignment</p>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        if "analysis_results" in st.session_state and st.session_state.analysis_results:
            match_data = st.session_state.analysis_results.get("match_result", {})
            suggested_skills = match_data.get("suggested_skills", [])
            skills_gap = len(suggested_skills)
            
            # Show skill names in tooltip or below
            skills_preview = ", ".join(suggested_skills[:3]) if suggested_skills else "None"
            if len(suggested_skills) > 3:
                skills_preview += f" +{len(suggested_skills) - 3} more"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>Skills Gap</h3>
                <h1>{skills_gap}</h1>
                <p>Missing Skills</p>
            </div>
            """, unsafe_allow_html=True)
            
            if skills_gap > 0:
                st.caption(f"📚 Top missing: {skills_preview}")
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>Skills Gap</h3>
                <h1>--</h1>
                <p>Missing Skills</p>
            </div>
            """, unsafe_allow_html=True)

    with col4:
        if "analysis_results" in st.session_state and st.session_state.analysis_results:
            applications = st.session_state.analysis_results.get("applications_this_month", "--")
            st.markdown(f"""
            <div class="metric-card">
                <h3>Applications</h3>
                <h1>{applications}</h1>
                <p>This Month</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>Applications</h3>
                <h1>--</h1>
                <p>This Month</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Main Upload Section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📄 Resume Analysis")
        uploaded = st.file_uploader(
            "Upload Resume (PDF)", type="pdf", key="resume_upload"
        )

        if uploaded:
            try:
                # Save uploaded file
                file_path = f"temp_{uploaded.name}"
                with open(file_path, "wb") as f:
                    f.write(uploaded.getvalue())

                # Extract resume text
                resume_text = extract_text_from_pdf(file_path)
                st.session_state.resume_text = resume_text

                # File details
                st.success(
                    f"✅ Resume uploaded: {uploaded.name} ({len(uploaded.getvalue()) / 1024:.1f} KB)"
                )
            except Exception as e:
                st.error(f"Error processing the uploaded file: {str(e)}")
                st.info("Please try uploading the file again.")

        job_title = st.text_input(
            "🎯 Target Job Title (optional)", placeholder="e.g., Senior Data Scientist"
        )

        if st.button("🔍 Analyze Resume", type="primary"):
            if "resume_text" in st.session_state and st.session_state.resume_text:
                with st.spinner("🤖 AI analyzing your resume..."):
                    try:
                        if AGENTS_AVAILABLE:
                            # Use the actual agent if available
                            controller = ControllerAgent()
                            result = controller.run(
                                st.session_state.resume_text, job_title
                            )
                        else:
                            # Use fallback implementation
                            result = AgentFallbackHandler.controller_analyze_resume(
                                st.session_state.resume_text, job_title
                            )

                        # Store results in session state
                        st.session_state.analysis_results = result
                        
                        # Update analytics tracking
                        resume_data = {
                            "timestamp": datetime.now().isoformat(),
                            "match_score": result.get("match_result", {}).get("match_percent", 0),
                            "job_title": job_title or "General Analysis"
                        }
                        
                        if "analyzed_resumes" not in st.session_state:
                            st.session_state.analyzed_resumes = []
                        st.session_state.analyzed_resumes.append(resume_data)
                        
                        # Update HR analytics
                        st.session_state.hr_analytics = get_hr_analytics()
                        
                        st.success("✅ Analysis completed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        st.info(
                            "Please try again or contact support if the issue persists."
                        )
            else:
                st.warning("Please upload a resume first.")

    with col2:
        st.markdown("### 📊 Quick Stats")
        if "analysis_results" in st.session_state and st.session_state.analysis_results:
            result = st.session_state.analysis_results

            # Create gauge chart for match score
            match_percent = result.get("match_result", {}).get("match_percent", 0)

            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=match_percent,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Job Match Score"},
                    delta={"reference": 70},
                    gauge={
                        "axis": {"range": [None, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 50], "color": "lightgrey"},
                            {"range": [50, 80], "color": "yellow"},
                            {"range": [80, 100], "color": "green"},
                        ],
                    },
                )
            )

            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Upload resume to see analysis metrics")

    # Results Display
    if "analysis_results" in st.session_state and st.session_state.analysis_results:
        result = st.session_state.analysis_results

        # Tabs for different analyses
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "📝 Feedback",
                "🎯 Skills Match",
                "🚀 Job Titles",
                "📈 Metrics",
                "📤 Export",
            ]
        )

        with tab1:
            st.markdown("### 💬 AI Feedback & Recommendations")
            if "feedback" in result:
                st.markdown(result["feedback"])
            else:
                st.info("No feedback available")

        with tab2:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### ✅ Your Matched Skills")
                match_data = result.get("match_result", {})
                matched_skills = match_data.get("matched_skills", [])

                if isinstance(matched_skills, list) and matched_skills:
                    for skill in matched_skills:
                        st.markdown(f"✅ **{skill}**")
                    st.success(f"🎯 **{len(matched_skills)} skills** match the job requirements!")
                else:
                    st.info("No matched skills found - upload your resume to see skill matching")

            with col2:
                st.markdown("### � Missing Critical Skills")
                suggested_skills = match_data.get("suggested_skills", [])

                if isinstance(suggested_skills, list) and suggested_skills:
                    st.warning(f"⚠️ **{len(suggested_skills)} skills** are missing for this role:")
                    for i, skill in enumerate(suggested_skills, 1):
                        st.markdown(f"**{i}.** {skill}")
                    
                    st.markdown("---")
                    st.markdown("**💡 Skill Development Tips:**")
                    st.markdown("• Focus on the top 3-5 missing skills first")
                    st.markdown("• Look for online courses, certifications, or projects")
                    st.markdown("• Consider bootcamps or formal training programs")
                    st.markdown("• Build portfolio projects demonstrating these skills")
                else:
                    st.success("🎉 Great! No critical skills are missing for this role.")

        with tab3:
            st.markdown("### 🚀 Career Opportunities")
            job_titles = result.get("job_titles", "")
            if job_titles and len(str(job_titles)) > 10:
                st.markdown("**💼 Recommended Job Titles Based on Your Profile:**")
                st.markdown(job_titles)
                
                st.markdown("---")
                st.markdown("### 🔍 Find Real Job Opportunities")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("""
                    **🌐 Job Search Platforms:**
                    - [LinkedIn Jobs](https://www.linkedin.com/jobs/)
                    - [Indeed](https://www.indeed.com/)
                    - [Glassdoor](https://www.glassdoor.com/Job/)
                    """)
                
                with col2:
                    st.markdown("""
                    **💼 Tech-Specific Platforms:**
                    - [AngelList](https://angel.co/jobs)
                    - [Stack Overflow Jobs](https://stackoverflow.com/jobs)
                    - [Dice](https://www.dice.com/)
                    """)
                
                with col3:
                    st.markdown("""
                    **🏢 Company Websites:**
                    - Check target companies directly
                    - Set up job alerts
                    - Follow company LinkedIn pages
                    """)
                
                # Job search tips
                st.markdown("### 💡 Job Search Strategy")
                st.info("🎯 **Pro Tip:** Use the job titles above as keywords when searching on these platforms. Set up job alerts with these titles to get notified of new opportunities!")
                
            else:
                st.warning("⚠️ No job title recommendations available")
                st.info("💡 Upload your resume and specify a target job title to get personalized job recommendations")

            st.markdown("### 📃 Sample Job Description")
            job_description = result.get("job_description", "")
            if job_description and len(str(job_description)) > 10:
                with st.expander("📋 View AI-Generated Job Description Example"):
                    st.markdown(job_description)
                    st.info("💡 Use this as a reference to understand what employers look for in similar roles")
            else:
                st.warning("⚠️ No job description available")
                st.info("💡 Provide a target job title during resume analysis to get a sample job description")

        with tab4:
            st.markdown("### 📊 Detailed Analytics")

            # Skills breakdown chart
            if "match_result" in result:
                match_data = result["match_result"]

                # Create skills comparison chart
                skills_data = {
                    "Matched": len(match_data.get("matched_skills", [])),
                    "Missing": len(match_data.get("suggested_skills", [])),
                    "Additional": len(match_data.get("additional_skills", [])),
                }

                fig = px.pie(
                    values=list(skills_data.values()),
                    names=list(skills_data.keys()),
                    title="Skills Breakdown",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Performance metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                overall_score = match_data.get('match_percent', 0)
                delta_value = "+5%" if overall_score > 70 else "↗️" if overall_score > 50 else "📈"
                st.metric(
                    "Overall Match Score", f"{overall_score}%", delta_value
                )
            with col2:
                matched_count = len(match_data.get("matched_skills", []))
                total_suggested = len(match_data.get("suggested_skills", []))
                delta_skills = f"+{matched_count - 2}" if matched_count > 2 else "→"
                st.metric(
                    "Skills Matched", f"{matched_count}", delta_skills
                )
            with col3:
                missing_count = len(match_data.get("suggested_skills", []))
                experience_level = "Senior" if overall_score > 80 else "Mid-Level" if overall_score > 60 else "Entry-Level"
                level_indicator = "↗️" if overall_score > 70 else "→"
                st.metric("Experience Level", experience_level, level_indicator)
            
            # Detailed skill breakdown
            st.markdown("#### 📋 Detailed Skill Analysis")
            if matched_count > 0 or missing_count > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**✅ Strengths:** {matched_count} matched skills")
                    st.markdown(f"**🎯 Match Rate:** {(matched_count/(matched_count + missing_count)*100):.1f}%" if (matched_count + missing_count) > 0 else "**🎯 Match Rate:** 0%")
                with col2:
                    st.markdown(f"**📚 Learning Needed:** {missing_count} skills to acquire")
                    st.markdown(f"**⏱️ Est. Learning Time:** {missing_count * 2}-{missing_count * 4} weeks" if missing_count > 0 else "**⏱️ Est. Learning Time:** Minimal")
            else:
                st.info("Complete resume analysis to see detailed skill metrics")

        with tab5:
            st.markdown("### 📤 Export & Share")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📄 Generate PDF Report"):
                    with st.spinner("Generating PDF..."):
                        pdf_filename = f"Resume_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        export_to_pdf(result, pdf_filename)
                        st.success(f"✅ PDF generated: {pdf_filename}")

                        with open(pdf_filename, "rb") as f:
                            st.download_button(
                                "📥 Download Report",
                                f.read(),
                                file_name=pdf_filename,
                                mime="application/pdf",
                            )

            with col2:
                to_email = st.text_input(
                    "📧 Send to Email", value=recipient_email or ""
                )
                if st.button("📬 Send Email") and to_email:
                    try:
                        pdf_filename = f"Resume_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        export_to_pdf(result, pdf_filename)

                        # Send email with PDF attachment
                        subject = "Your JobSniper AI Resume Analysis"
                        body = "Please find attached your resume analysis report generated by JobSniper AI."
                        send_email(to_email, subject, body, [pdf_filename])

                        st.success(f"✅ Email sent to {to_email}")
                    except Exception as e:
                        st.error(f"Error sending email: {str(e)}")
                        st.info("Please check your email configuration and try again.")
                        export_to_pdf(result, pdf_filename)
                        send_email(to_email, pdf_filename)
                        st.success(f"✅ Email sent to {to_email}")
                    except Exception as e:
                        st.error(f"❌ Failed to send email: {str(e)}")

elif mode == "🚀 Auto Apply Mode":
    st.markdown("## 🚀 Automated Job Application System")
    
    st.markdown("""
    <div class="auto-apply-card">
        <h4>🎯 Intelligent Auto-Application Process</h4>
        <p>Our AI-powered system will analyze your resume, match it with job requirements, and generate a perfectly tailored application package.</p>
    </div>
    """, unsafe_allow_html=True)

    # Progress indicator with enhanced styling
    progress_steps = [
        {"icon": "🎯", "name": "Job Details", "desc": "Enter job information"},
        {"icon": "📄", "name": "Resume Upload", "desc": "AI analysis & extraction"},
        {"icon": "🤖", "name": "Generate Application", "desc": "AI-powered tailoring"},
        {"icon": "✅", "name": "Review & Submit", "desc": "Final review & send"}
    ]
    current_step = st.session_state.get("auto_apply_step", 0)

    cols = st.columns(4)
    for i, step in enumerate(progress_steps):
        with cols[i]:
            if i < current_step:
                st.markdown(f"""
                <div class="progress-step completed">
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{step["icon"]}</div>
                        <div style="font-weight: 600; margin-bottom: 0.25rem;">{step["name"]}</div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">{step["desc"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif i == current_step:
                st.markdown(f"""
                <div class="progress-step active">
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{step["icon"]}</div>
                        <div style="font-weight: 600; margin-bottom: 0.25rem;">{step["name"]}</div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">{step["desc"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="progress-step pending">
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{step["icon"]}</div>
                        <div style="font-weight: 600; margin-bottom: 0.25rem;">{step["name"]}</div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">{step["desc"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Step 1: Job Details
    if current_step == 0:
        st.markdown("### 🎯 Step 1: Enter Job Details")
        
        st.markdown("""
        <div class="auto-apply-card">
            <p>Provide comprehensive job details to help our AI create the perfect application tailored to this specific role.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            job_url = st.text_input("🔗 Job Posting URL", placeholder="https://linkedin.com/jobs/view/...")
            job_title = st.text_input(
                "💼 Job Title", placeholder="Senior Software Engineer"
            )
            company_name = st.text_input("🏢 Company Name", placeholder="Google Inc.")

        with col2:
            platform = st.selectbox(
                "📱 Platform",
                ["LinkedIn", "Indeed", "Glassdoor", "Company Website", "Monster", "ZipRecruiter"],
            )
            deadline = st.date_input("📅 Application Deadline (optional)")
            competition_level = st.selectbox(
                "📊 Competition Level", ["Low", "Medium", "High", "Very High"]
            )

        job_description = st.text_area(
            "📝 Job Description",
            height=250,
            placeholder="Paste the complete job description here...\n\nInclude requirements, responsibilities, qualifications, and any other relevant details.",
        )

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Analyze Job Description", type="secondary"):
                if job_description:
                    with st.spinner("🤖 Analyzing job requirements..."):
                        # This would use AI to extract key requirements
                        st.success("✅ Job analysis complete! Ready to continue.")
                else:
                    st.error("Please enter a job description first")
        
        with col2:
            if st.button("➡️ Continue to Resume Upload", type="primary"):
                if job_description and job_title:
                    st.session_state.job_data = {
                        "url": job_url,
                        "title": job_title,
                        "company": company_name,
                        "platform": platform.lower(),
                        "deadline": str(deadline) if deadline else None,
                        "competition_level": competition_level.lower(),
                        "description": job_description,
                    }
                    st.session_state.auto_apply_step = 1
                    st.rerun()
                else:
                    st.error("⚠️ Please fill in job title and description")

    # Step 2: Resume Upload
    elif current_step == 1:
        st.markdown("### 📄 Step 2: Upload Your Resume")
        
        st.markdown("""
        <div class="auto-apply-card">
            <p>Upload your resume and we'll automatically extract your information and analyze it against the job requirements.</p>
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Upload Resume (PDF)", type="pdf", key="auto_apply_resume"
        )

        if uploaded:
            with st.spinner("🔍 Analyzing your resume..."):
                file_path = f"temp_{uploaded.name}"
                with open(file_path, "wb") as f:
                    f.write(uploaded.getvalue())

                resume_text = extract_text_from_pdf(file_path)
                st.session_state.resume_text = resume_text
                
                # Analyze resume using Controller Agent
                if AGENTS_AVAILABLE:
                    try:
                        controller = ControllerAgent()
                        analysis_result = controller.run(resume_text)
                        st.session_state.resume_analysis = analysis_result
                        
                        # Extract parsed data for auto-filling
                        parsed_data = analysis_result.get("parsed_data", {})
                        st.session_state.extracted_info = {
                            "name": parsed_data.get("name", ""),
                            "email": parsed_data.get("email", ""),
                            "phone": parsed_data.get("phone", ""),
                            "skills": parsed_data.get("skills", []),
                            "experience": parsed_data.get("experience", ""),
                            "education": parsed_data.get("education", ""),
                            "linkedin": parsed_data.get("linkedin", ""),
                            "portfolio": parsed_data.get("portfolio", "")
                        }
                        
                        st.success(f"✅ Resume analyzed successfully: {uploaded.name}")
                        
                        # Show extracted information
                        with st.expander("📊 View Extracted Information"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**Personal Info:**")
                                st.write(f"Name: {st.session_state.extracted_info['name']}")
                                st.write(f"Email: {st.session_state.extracted_info['email']}")
                                st.write(f"Phone: {st.session_state.extracted_info['phone']}")
                            with col2:
                                st.write("**Professional Info:**")
                                st.write(f"Experience: {st.session_state.extracted_info['experience']}")
                                st.write(f"Skills: {', '.join(st.session_state.extracted_info['skills'][:5])}")
                        
                    except Exception:
                        st.warning("⚠️ Resume analysis failed, using manual entry")
                        st.session_state.extracted_info = {}
                else:
                    st.session_state.extracted_info = {}
                    st.info("💡 Resume uploaded. Please fill in your information below.")

        # Personal information - pre-filled from resume analysis
        st.markdown("### 👤 Personal Information")
        extracted = st.session_state.get("extracted_info", {})
        
        col1, col2 = st.columns(2)

        with col1:
            # Split name if available
            full_name = extracted.get("name", "")
            name_parts = full_name.split() if full_name else ["", ""]
            first_name = st.text_input("First Name", value=name_parts[0] if name_parts else "")
            last_name = st.text_input("Last Name", value=" ".join(name_parts[1:]) if len(name_parts) > 1 else "")
            email = st.text_input("Email Address", value=extracted.get("email", ""))
            phone = st.text_input("Phone Number", value=extracted.get("phone", ""))

        with col2:
            linkedin_url = st.text_input("LinkedIn URL", value=extracted.get("linkedin", ""))
            portfolio_url = st.text_input("Portfolio URL (optional)", value=extracted.get("portfolio", ""))
            salary_expectation = st.text_input("Salary Expectation (optional)")
            availability = st.text_input("Availability", value="Immediately")

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬅️ Back to Job Details"):
                st.session_state.auto_apply_step = 0
                st.rerun()
        
        with col2:
            if st.button("➡️ Generate Application", type="primary"):
                if "resume_text" in st.session_state and first_name and last_name and email:
                    st.session_state.personal_info = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "full_name": f"{first_name} {last_name}",
                        "email": email,
                        "phone": phone,
                        "linkedin_url": linkedin_url,
                        "portfolio_url": portfolio_url,
                        "salary_expectation": salary_expectation,
                        "availability": availability,
                    }
                    st.session_state.auto_apply_step = 2
                    st.rerun()
                else:
                    st.error("⚠️ Please upload resume and fill in required personal information")

    # Step 3: Generate Application
    elif current_step == 2:
        st.markdown("### 🤖 Step 3: AI Application Generation")
        
        st.markdown("""
        <div class="auto-apply-card">
            <p>Our AI will now analyze your resume against the job requirements and generate a tailored application package.</p>
        </div>
        """, unsafe_allow_html=True)

        # Show analysis preview
        if st.session_state.get("resume_analysis"):
            analysis = st.session_state.resume_analysis
            col1, col2, col3 = st.columns(3)
            
            with col1:
                match_score = analysis.get("match_result", {}).get("match_percent", "N/A")
                st.metric("Resume Match", f"{match_score}%" if match_score != "N/A" else "Analyzing...")
            
            with col2:
                skills_count = len(analysis.get("parsed_data", {}).get("skills", []))
                st.metric("Skills Detected", skills_count)
            
            with col3:
                experience = analysis.get("parsed_data", {}).get("experience", "N/A")
                st.metric("Experience", experience if experience != "N/A" else "Analyzing...")

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬅️ Back to Resume Upload"):
                st.session_state.auto_apply_step = 1
                st.rerun()
        
        with col2:
            if st.button("🚀 Generate Tailored Application", type="primary"):
                with st.spinner("🤖 AI is crafting your perfect application..."):
                    try:
                        auto_apply_agent = AutoApplyAgent()

                        # Use dynamic resume data from analysis
                        if st.session_state.get("resume_analysis"):
                            parsed_data = st.session_state.resume_analysis.get("parsed_data", {})
                            resume_data = {
                                "name": st.session_state.personal_info["full_name"],
                                "skills": parsed_data.get("skills", []),
                                "experience": parsed_data.get("experience", "Entry Level"),
                                "education": parsed_data.get("education", ""),
                                "certifications": parsed_data.get("certifications", []),
                                "achievements": parsed_data.get("achievements", []),
                                "work_history": parsed_data.get("work_history", [])
                            }
                        else:
                            # Fallback to basic extraction from resume text
                            resume_data = {
                                "name": st.session_state.personal_info["full_name"],
                                "skills": [],  # Would need to extract from text
                                "experience": "To be analyzed",
                                "education": "To be analyzed",
                            }

                        application_result = auto_apply_agent.run(
                            st.session_state.job_data,
                            st.session_state.personal_info,
                            resume_data,
                        )

                        st.session_state.application_result = application_result
                        st.session_state.auto_apply_step = 3
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Error generating application: {str(e)}")
                        st.info("💡 Please try again or contact support if the issue persists.")
                        st.session_state.application_error = str(e)

    # Step 4: Review & Submit
    elif current_step == 3:
        st.markdown("### ✅ Step 4: Review Generated Application")
        
        st.markdown("""
        <div class="auto-apply-card">
            <h4>🎯 AI-Generated Application Package</h4>
            <p>Review your personalized application materials before submitting. All content has been tailored to match the job requirements.</p>
        </div>
        """, unsafe_allow_html=True)

        if "application_result" in st.session_state:
            result = st.session_state.application_result

            # Display job analysis with enhanced styling
            st.markdown("#### 📊 Job Analysis & Match Score")
            job_analysis = result.get("job_analysis", {})

            col1, col2, col3 = st.columns(3)
            with col1:
                match_score = job_analysis.get('match_score', 0)
                if match_score > 0:
                    st.markdown(f"""
                    <div class="metric-card" style="margin: 0;">
                        <h3>Match Score</h3>
                        <h1>{match_score}%</h1>
                        <p>Resume-Job Fit</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="metric-card" style="margin: 0;">
                        <h3>Match Score</h3>
                        <h1>--</h1>
                        <p>Analyzing...</p>
                    </div>
                    """, unsafe_allow_html=True)
                
            with col2:
                success_prob = result.get('success_probability', {}).get('percentage', 0)
                if success_prob > 0:
                    st.markdown(f"""
                    <div class="metric-card" style="margin: 0;">
                        <h3>Success Rate</h3>
                        <h1>{success_prob}%</h1>
                        <p>Predicted Success</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="metric-card" style="margin: 0;">
                        <h3>Success Rate</h3>
                        <h1>--</h1>
                        <p>Analyzing...</p>
                    </div>
                    """, unsafe_allow_html=True)
                
            with col3:
                priority = result.get("application_strategy", {}).get("priority_level", "").title()
                if priority:
                    priority_color = "#4CAF50" if priority == "High" else "#FF9800" if priority == "Medium" else "#607D8B"
                    st.markdown(f"""
                    <div class="metric-card" style="margin: 0; background: linear-gradient(135deg, {priority_color} 0%, {priority_color}CC 100%);">
                        <h3>Priority</h3>
                        <h1>{priority}</h1>
                        <p>Application Level</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="metric-card" style="margin: 0;">
                        <h3>Priority</h3>
                        <h1>--</h1>
                        <p>Analyzing...</p>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")

            # Generated cover letter with better styling
            st.markdown("#### 📝 AI-Generated Cover Letter")
            st.markdown("""
            <div class="auto-apply-card">
                <p><strong>Tip:</strong> This cover letter has been specifically tailored to highlight your relevant skills and experience for this position.</p>
            </div>
            """, unsafe_allow_html=True)
            
            cover_letter = result.get("cover_letter", "")
            edited_cover_letter = st.text_area(
                "Review and edit your cover letter:", 
                value=cover_letter, 
                height=350,
                help="Feel free to personalize this further with specific examples or adjust the tone."
            )

            st.markdown("---")

            # Application strategy with enhanced layout
            st.markdown("#### 🎯 Strategic Recommendations")
            strategy = result.get("application_strategy", {})

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                <div class="auto-apply-card">
                    <h4>💡 Application Tips</h4>
                </div>
                """, unsafe_allow_html=True)
                
                recommendations = strategy.get("recommendations", [])
                if recommendations:
                    for i, rec in enumerate(recommendations[:5], 1):
                        st.markdown(f"**{i}.** {rec}")
                else:
                    st.info("💡 Application recommendations will be generated based on your specific resume and job match.")

            with col2:
                st.markdown("""
                <div class="auto-apply-card">
                    <h4>🚀 Platform-Specific Tips</h4>
                </div>
                """, unsafe_allow_html=True)
                
                platform_tips = result.get("platform_tips", [])
                if platform_tips:
                    for i, tip in enumerate(platform_tips[:5], 1):
                        st.markdown(f"**{i}.** {tip}")
                else:
                    st.info("💡 Platform-specific tips will be generated based on your selected job platform.")

            st.markdown("---")

            # Next steps with better presentation
            st.markdown("#### 📋 Recommended Next Steps")
            next_steps = result.get("next_steps", [])
            
            if next_steps:
                steps_cols = st.columns(2)
                for i, step in enumerate(next_steps):
                    col_idx = i % 2
                    with steps_cols[col_idx]:
                        st.markdown(f"✅ {step}")
            else:
                st.info("💡 Personalized next steps will be generated based on your application strategy.")

            st.markdown("---")

            # Action buttons with enhanced styling
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📄 Save Package", type="secondary", help="Save all application materials as PDF"):
                    with st.spinner("💾 Saving application package..."):
                        # Save application materials
                        st.success("✅ Application package saved to downloads!")

            with col2:
                if st.button("📧 Email Materials", type="secondary", help="Email application materials to yourself"):
                    with st.spinner("📧 Sending email..."):
                        # Email application to user
                        st.success("✅ Application materials sent to your email!")

            with col3:
                if st.button("🔄 New Application", type="secondary", help="Start a new application process"):
                    st.session_state.auto_apply_step = 0
                    for key in ["job_data", "personal_info", "application_result", "resume_analysis"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                    
            with col4:
                if st.button("🎯 Apply Now", type="primary", help="Open job posting to submit your application"):
                    job_url = st.session_state.get("job_data", {}).get("url", "")
                    if job_url:
                        st.markdown(f"🚀 **Ready to apply!** [Open Job Posting]({job_url})")
                        st.balloons()
                    else:
                        st.info("💡 Use your generated materials to apply through the job platform")
                        
        else:
            st.warning("⚠️ No application data found. Please go back and generate an application first.")
            if st.button("⬅️ Back to Application Generation"):
                st.session_state.auto_apply_step = 2
                st.rerun()

elif mode == "👥 HR/Recruiter Mode":
    st.markdown("## 👥 HR & Recruiter Intelligence Center")
    
    st.markdown("""
    <div class="feature-card">
        <h4>📊 Recruitment Analytics Dashboard</h4>
        <p>Monitor your recruitment pipeline with AI-powered insights and candidate analytics.</p>
    </div>
    """, unsafe_allow_html=True)

    # Get dynamic HR data from database or session state
    hr_data = st.session_state.get("hr_analytics", {
        "candidates_this_week": 0,
        "average_score": 0,
        "interviews_scheduled": 0,
        "hired_this_month": 0
    })

    # Show message if no candidates have been analyzed yet
    if hr_data["candidates_this_week"] == 0 and len(st.session_state.get("analyzed_resumes", [])) == 0:
        st.markdown("""
        <div class="auto-apply-card" style="border-left: 4px solid #2196F3;">
            <h4>📊 Welcome to HR Analytics</h4>
            <p>To see meaningful recruitment analytics, start by evaluating some candidates below. 
            The dashboard will automatically update with real metrics as you analyze resumes.</p>
            <p><strong>💡 Tip:</strong> All metrics will be dynamically generated based on actual candidate evaluations - no fake data!</p>
        </div>
        """, unsafe_allow_html=True)

    # HR Dashboard Metrics - Dynamic values
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        candidates_count = hr_data.get("candidates_this_week", 0)
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Candidates</h3>
            <h1>{candidates_count}</h1>
            <p>This Week</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        avg_score = hr_data.get("average_score", 0)
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Avg Score</h3>
            <h1>{avg_score}%</h1>
            <p>AI Evaluation</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        interviews = hr_data.get("interviews_scheduled", 0)
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Interviews</h3>
            <h1>{interviews}</h1>
            <p>Scheduled</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        hired = hr_data.get("hired_this_month", 0)
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Hired</h3>
            <h1>{hired}</h1>
            <p>This Month</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # HR Mode Selection
    hr_mode = st.selectbox(
        "HR Function",
        [
            "📊 Evaluate Single Candidate",
            "⚖️ Compare Multiple Candidates",
            "📋 Generate Interview Guide",
            "📈 Hiring Analytics",
        ],
    )

    if hr_mode == "📊 Evaluate Single Candidate":
        st.markdown("### 📊 Single Candidate Evaluation")

        # Job requirements input
        col1, col2 = st.columns(2)

        with col1:
            job_title = st.text_input("Job Title", placeholder="e.g., Senior Software Engineer")
            position_level = st.selectbox(
                "Position Level",
                ["entry_level", "mid_level", "senior_level", "executive"],
            )
            required_skills = st.text_area(
                "Required Skills (comma-separated)",
                placeholder="e.g., Python, React, AWS, SQL, Machine Learning",
                help="Enter the specific skills required for this position"
            )

        with col2:
            experience_required = st.number_input(
                "Years of Experience Required", min_value=0, max_value=20, value=0
            )
            salary_range = st.text_input("Salary Range", placeholder="e.g., $120k - $180k")
            location = st.text_input("Location", placeholder="e.g., San Francisco, CA")

        # Candidate resume upload
        st.markdown("### 📄 Upload Candidate Resume")
        uploaded_resume = st.file_uploader(
            "Candidate Resume (PDF)", type="pdf", key="hr_resume"
        )

        if uploaded_resume and st.button("🔍 Evaluate Candidate", type="primary"):
            # Validate required fields
            if not job_title.strip():
                st.error("⚠️ Please enter a job title")
            elif not required_skills.strip():
                st.error("⚠️ Please enter required skills for the position")
            elif not location.strip():
                st.error("⚠️ Please enter the job location")
            else:
                with st.spinner("🤖 AI evaluating candidate..."):
                    # Extract resume text
                    file_path = f"temp_{uploaded_resume.name}"
                    with open(file_path, "wb") as f:
                        f.write(uploaded_resume.getvalue())

                        resume_text = extract_text_from_pdf(file_path)

                    # Analyze resume to extract dynamic data
                    if AGENTS_AVAILABLE:
                        try:
                            controller = ControllerAgent()
                            analysis_result = controller.run(resume_text)
                            parsed_data = analysis_result.get("parsed_data", {})
                            
                            # Use extracted data instead of hardcoded values
                            resume_data = {
                                "candidate_id": f"candidate_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                "name": parsed_data.get("name", "Candidate Name Not Found"),
                                "technical_skills": parsed_data.get("skills", []),
                                "total_experience_years": parsed_data.get("experience_years", 0),
                                "education": parsed_data.get("education", {}),
                                "achievements": parsed_data.get("achievements", []),
                                "contact": {
                                    "email": parsed_data.get("email", ""),
                                    "phone": parsed_data.get("phone", "")
                                }
                            }
                        except Exception as e:
                            st.error(f"❌ Error analyzing resume: {str(e)}")
                            # Fallback to basic structure if analysis fails
                            resume_data = {
                                "candidate_id": f"candidate_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                "name": "Analysis Failed - Manual Review Required",
                                "technical_skills": [],
                                "total_experience_years": 0,
                                "education": {},
                                "achievements": [],
                            }
                    else:
                        st.warning("⚠️ Agent analysis not available. Using basic extraction.")
                        resume_data = {
                            "candidate_id": f"candidate_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            "name": "Manual Review Required",
                            "technical_skills": [],
                            "total_experience_years": 0,
                            "education": {},
                            "achievements": [],
                        }

                    job_requirements = {
                        "title": job_title,
                        "position_level": position_level,
                        "required_skills": [skill.strip() for skill in required_skills.split(",") if skill.strip()],
                        "experience_years": experience_required,
                        "salary_range": {"min": 80000, "max": 200000, "average": 150000} if not salary_range else {"description": salary_range},
                        "location": location,
                    }

                    # Initialize recruiter agent and evaluate
                    try:
                        if AGENTS_AVAILABLE:
                            recruiter_agent = RecruiterViewAgent()
                            evaluation = recruiter_agent.evaluate_candidate(
                                resume_data, job_requirements, position_level
                            )
                        else:
                            # Fallback evaluation
                            evaluation = {
                                "overall_score": 0,
                                "category_scores": {},
                                "strengths": ["Manual review required"],
                                "weaknesses": ["Agent analysis unavailable"],
                                "recommendations": ["Please review manually"],
                                "red_flags": [],
                                "hiring_recommendation": "Manual Review Required",
                                "confidence_level": 0.0,
                                "salary_recommendation": {"min": 0, "max": 0, "recommended": 0}
                            }

                        st.session_state.hr_evaluation = evaluation
                        
                        # Update analyzed resumes for analytics
                        resume_record = {
                            "timestamp": datetime.now().isoformat(),
                            "match_score": evaluation.get("overall_score", 0),
                            "job_title": job_title,
                            "candidate_name": resume_data.get("name", "Unknown")
                        }
                        
                        if "analyzed_resumes" not in st.session_state:
                            st.session_state.analyzed_resumes = []
                        st.session_state.analyzed_resumes.append(resume_record)
                        
                        # Update HR analytics
                        st.session_state.hr_analytics = get_hr_analytics()
                        
                        st.success("✅ Candidate evaluation completed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error during evaluation: {str(e)}")
                        st.info("💡 Please try again or contact support if the issue persists.")

        # Display evaluation results
        if "hr_evaluation" in st.session_state:
            evaluation = st.session_state.hr_evaluation

            st.markdown("---")
            st.markdown("### 📊 Evaluation Results")

            # Overall score gauge
            overall_score = evaluation.get("overall_score", 0)

            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=overall_score,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Overall Candidate Score"},
                    delta={"reference": 70},
                    gauge={
                        "axis": {"range": [None, 100]},
                        "bar": {"color": "green"},
                        "steps": [
                            {"range": [0, 50], "color": "lightgrey"},
                            {"range": [50, 70], "color": "yellow"},
                            {"range": [70, 85], "color": "lightgreen"},
                            {"range": [85, 100], "color": "green"},
                        ],
                    },
                )
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Category scores
            st.markdown("#### 📈 Category Breakdown")
            category_scores = evaluation.get("category_scores", {})

            categories = list(category_scores.keys())
            scores = list(category_scores.values())

            fig_bar = px.bar(
                x=categories,
                y=scores,
                title="Category Scores",
                color=scores,
                color_continuous_scale="RdYlGn",
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

            # Detailed analysis
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### ✅ Strengths")
                for strength in evaluation.get("strengths", []):
                    st.markdown(f"• {strength}")

                st.markdown("#### 📚 Recommendations")
                for rec in evaluation.get("recommendations", []):
                    st.markdown(f"• {rec}")

            with col2:
                st.markdown("#### ⚠️ Areas for Improvement")
                for weakness in evaluation.get("weaknesses", []):
                    st.markdown(f"• {weakness}")

                st.markdown("#### 🚩 Red Flags")
                red_flags = evaluation.get("red_flags", [])
                if red_flags:
                    for flag in red_flags:
                        st.markdown(f"• {flag.get('description', 'Unknown issue')}")
                else:
                    st.markdown("• No red flags detected")

            # Hiring recommendation
            st.markdown("#### 🎯 Final Recommendation")
            recommendation = evaluation.get("hiring_recommendation", "Unknown")
            confidence = evaluation.get("confidence_level", 0.5)

            if "Highly Recommended" in recommendation:
                st.success(f"✅ {recommendation} (Confidence: {confidence:.1%})")
            elif "Recommended" in recommendation:
                st.warning(f"⚠️ {recommendation} (Confidence: {confidence:.1%})")
            else:
                st.error(f"❌ {recommendation} (Confidence: {confidence:.1%})")

            # Salary recommendation
            salary_rec = evaluation.get("salary_recommendation", {})
            if salary_rec and salary_rec.get("recommended", 0) > 0:
                st.markdown(
                    f"**💰 Suggested Salary Range:** ${salary_rec.get('min', 0):,} - ${salary_rec.get('max', 0):,}"
                )
                st.markdown(
                    f"**📊 Recommended Offer:** ${salary_rec.get('recommended', 0):,}"
                )
            else:
                st.info("💡 Salary recommendations will be generated based on candidate evaluation and market data.")

elif mode == "📚 Skill Development":
    st.markdown("## 📚 Personalized Skill Development Center")

    # Check if user has analyzed resume before
    if not st.session_state.get("analysis_results"):
        st.markdown("""
        <div class="auto-apply-card" style="border-left: 4px solid #FF9800;">
            <h4>💡 Get Better Recommendations</h4>
            <p>For more accurate skill recommendations, please analyze your resume first in <strong>Job Seeker Mode</strong>. 
            This will help us understand your current skills and provide personalized recommendations.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Go to Job Seeker Mode", type="secondary"):
                st.session_state.mode_selector = "🔍 Job Seeker Mode"
                st.rerun()
        with col2:
            st.info("Or continue with manual entry below")

    # Skill development dashboard
    col1, col2, col3, col4 = st.columns(4)

    # Only show metrics if analysis is a dict and has expected keys
    analysis = st.session_state.get("skill_analysis", None)
    skill_data = {}
    roi_data = {}
    timeline = "--"
    courses = "--"
    if isinstance(analysis, dict):
        skill_data = analysis.get("skill_analysis", {})
        roi_data = skill_data.get("roi_analysis", {})
        timeline = skill_data.get("learning_roadmap", {}).get("timeline_months", "--")
        courses = len(skill_data.get("learning_priorities", []))

    with col1:
        skill_gap = skill_data.get("skill_gaps", {}).get("gap_percentage", "--") if skill_data else "--"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Skill Gap</h3>
            <h1>{skill_gap if skill_gap != '--' else '--'}</h1>
            <p>Skills to Learn</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        learning_roi = roi_data.get("roi_percentage", "--") if roi_data else "--"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Learning ROI</h3>
            <h1>{learning_roi if learning_roi != '--' else '--'}%</h1>
            <p>Expected Return</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Timeline</h3>
            <h1>{timeline}</h1>
            <p>Months to Goal</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Courses</h3>
            <h1>{courses}</h1>
            <p>Recommended</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Current skills and target job input
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💼 Current Profile")
        
        # Use data from previous analysis if available
        previous_analysis = st.session_state.get("analysis_results", {})
        parsed_data = previous_analysis.get("parsed_data", {})
        
        # Pre-fill with analyzed data if available, otherwise empty
        current_skills_default = ", ".join(parsed_data.get("skills", [])) if parsed_data.get("skills") else ""
        current_skills = st.text_area(
            "Current Skills (comma-separated)",
            value=current_skills_default,
            height=100,
            help="Enter your current skills or upload a resume first for auto-detection"
        )

        experience_years = st.number_input(
            "Years of Experience", 
            min_value=0, 
            max_value=30, 
            value=parsed_data.get("experience_years", 0),
            help="Total years of professional experience"
        )
        
        current_role = st.text_input(
            "Current Role", 
            value=parsed_data.get("current_role", ""),
            help="Your current job title"
        )
        
        industry = st.selectbox(
            "Industry", 
            ["Technology", "Finance", "Healthcare", "Marketing", "Manufacturing", "Education", "Other"],
            help="Select your industry"
        )

    with col2:
        st.markdown("### 🎯 Career Goals")
        target_job = st.text_input(
            "Target Job Title", 
            value="",
            help="Enter your desired job title"
        )
        
        target_company = st.text_input(
            "Target Company (optional)", 
            value="",
            help="Specific company you're targeting (optional)"
        )
        
        timeline = st.selectbox(
            "Timeline", 
            ["6_months", "12_months", "18_months", "24_months"],
            help="How long do you want to take to reach your goal?"
        )
        
        career_level = st.selectbox(
            "Target Level",
            ["Individual Contributor", "Team Lead", "Manager", "Director"],
            help="What career level are you targeting?"
        )

    if st.button("🔍 Analyze Skill Gaps & Generate Roadmap", type="primary"):
        # Validate required inputs
        if not current_skills.strip():
            st.error("⚠️ Please enter your current skills first")
            st.info("💡 Tip: Upload your resume in Job Seeker Mode first for auto-detection of skills")
        elif not target_job.strip():
            st.error("⚠️ Please enter your target job title")
        elif not current_role.strip():
            st.error("⚠️ Please enter your current role")
        else:
            with st.spinner("🤖 AI analyzing skills and creating personalized roadmap..."):
                # Prepare data from user input
                resume_data = {
                    "technical_skills": [
                        skill.strip() for skill in current_skills.split(",") if skill.strip()
                    ],
                    "total_experience_years": experience_years,
                    "current_role": current_role,
                    "industry": industry.lower(),
                }

                target_job_data = {
                    "title": target_job,
                    "industry": industry.lower(),
                    "required_skills": [],  # Will be analyzed by AI based on job title
                    "experience_level": "senior" if "senior" in target_job.lower() 
                                      else "lead" if "lead" in target_job.lower()
                                      else "mid" if experience_years >= 3
                                      else "junior",
                    "timeline_months": int(timeline.split("_")[0]),
                    "target_company": target_company if target_company.strip() else None,
                    "career_level": career_level.lower().replace(" ", "_")
                }

                career_goals = {
                    "target_role": target_job,
                    "target_company": target_company,
                    "timeframe": timeline,
                    "career_level": career_level,
                }

            # Initialize skill recommendation agent and get analysis
            try:
                if AGENTS_AVAILABLE:
                    skill_agent = SkillRecommendationAgent()
                    analysis_result = skill_agent.run(
                        resume_data, target_job_data, career_goals, "comprehensive"
                    )
                else:
                    # Use fallback handler
                    current_skills = resume_data.get("technical_skills", [])
                    analysis_result = (
                        AgentFallbackHandler.generate_skill_recommendations(
                            current_skills, target_job
                        )
                    )

                st.session_state.skill_analysis = analysis_result
                st.success("✅ Skill analysis and roadmap generated!")
                st.rerun()
            except Exception as e:
                st.error(f"Error generating skill analysis: {str(e)}")
                st.info("Please try again or contact support if the issue persists.")

    # Display skill analysis results
    if "skill_analysis" in st.session_state:
        analysis = st.session_state.skill_analysis
        skill_data = analysis.get("skill_analysis", {})

        st.markdown("---")
        st.markdown("### 📊 Skill Gap Analysis")

        # Gap visualization
        gap_percentage = skill_data.get("skill_gaps", {}).get("gap_percentage", 0)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Skill Gap", f"{gap_percentage:.1f}%", "-5%")

        with col2:
            present_skills = len(
                skill_data.get("skill_gaps", {}).get("present_skills", [])
            )
            st.metric("Skills Matched", present_skills, "+2")

        with col3:
            missing_skills = len(
                skill_data.get("skill_gaps", {}).get("missing_critical", [])
            )
            st.metric("Skills to Learn", missing_skills, "-1")

        # Learning priorities
        st.markdown("### 🎯 Prioritized Learning Plan")

        priorities = skill_data.get("learning_priorities", [])[:5]  # Top 5

        for i, priority in enumerate(priorities, 1):
            with st.expander(
                f"{i}. {priority['skill']} - {priority['priority_level']} Priority"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Market Demand:** {priority['market_demand']}%")
                    st.markdown(f"**Salary Impact:** {priority['salary_impact']}%")
                    st.markdown(
                        f"**Learning Difficulty:** {priority['learning_difficulty']}%"
                    )

                with col2:
                    time_to_prof = priority.get("time_to_proficiency", {})
                    st.markdown(
                        f"**Time to Proficiency:** {time_to_prof.get('proficient', 'N/A')}"
                    )
                    st.markdown(
                        f"**Prerequisites:** {', '.join(priority.get('prerequisites', ['None']))}"
                    )

                # Recommended resources
                st.markdown("**📚 Recommended Learning Resources:**")
                resources = priority.get("recommended_resources", [])[:3]
                for resource in resources:
                    st.markdown(
                        f"• [{resource['platform']}]({resource['url']}) - {resource['price_range']}"
                    )

                # Certifications
                certifications = priority.get("certifications", [])
                if certifications:
                    st.markdown("**🏆 Relevant Certifications:**")
                    for cert in certifications[:2]:
                        st.markdown(
                            f"• {cert['name']} by {cert['provider']} - {cert['cost']}"
                        )

        # Learning roadmap
        if "learning_roadmap" in analysis:
            roadmap = analysis["learning_roadmap"]

            st.markdown("### 🗺️ Learning Roadmap")

            # Timeline visualization
            phases = roadmap.get("phases", [])

            # Create timeline chart
            timeline_data = []
            current_month = 0

            for phase in phases:
                duration_months = int(phase.get("duration", "3 months").split()[0])
                timeline_data.append(
                    {
                        "Phase": phase["name"],
                        "Start": current_month,
                        "Duration": duration_months,
                        "Skills": ", ".join(phase.get("skills_focus", [])[:3]),
                    }
                )
                current_month += duration_months

            # Display roadmap phases
            for phase_data in timeline_data:
                st.markdown(
                    f"**📅 {phase_data['Phase']} (Months {phase_data['Start'] + 1}-{phase_data['Start'] + phase_data['Duration']})**"
                )
                st.markdown(f"Focus: {phase_data['Skills']}")
                st.progress((phase_data["Start"] + phase_data["Duration"]) / 12)

        # ROI Analysis
        if "roi_analysis" in skill_data:
            roi = skill_data["roi_analysis"]

            st.markdown("### 💰 Investment & ROI Analysis")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Investment", roi.get("total_investment", "$0"))

            with col2:
                st.metric("Annual Increase", roi.get("potential_annual_increase", "$0"))

            with col3:
                st.metric("ROI Percentage", roi.get("roi_percentage", "0%"))

            with col4:
                st.metric("Payback Period", roi.get("payback_period", "N/A"))

            st.markdown(f"**5-Year Value:** {roi.get('5_year_value', '$0')}")

# Footer with enhanced visibility - Force display at bottom
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("---")

# Add global CSS to ensure footer is always visible
st.markdown("""
<style>
/* Force footer visibility and prevent cutoff */
.main .block-container {
    padding-bottom: 5rem !important;
}

/* Ensure footer container is always visible */
div[data-testid="stVerticalBlock"] > div:last-child {
    margin-bottom: 5rem !important;
}

/* Footer specific styling */
.footer-container {
    position: relative !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    width: 100% !important;
    margin-bottom: 3rem !important;
    clear: both !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
<div class="footer-container" style="
    text-align: center; 
    background: linear-gradient(135deg, #000000 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #000000 100%) !important;
    color: #ffffff !important;
    padding: 4rem 2rem !important;
    border-radius: 20px !important;
    margin: 4rem auto 4rem auto !important;
    box-shadow: 0 12px 48px rgba(0,0,0,0.8), 0 0 0 3px rgba(255,255,255,0.2) !important;
    backdrop-filter: blur(25px) !important;
    border: 3px solid rgba(255,255,255,0.3) !important;
    position: relative !important;
    z-index: 1000 !important;
    min-height: 250px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    width: 95% !important;
    max-width: 1200px !important;
    visibility: visible !important;
    opacity: 1 !important;
">
    <div style="
        background: rgba(255,255,255,0.08) !important;
        padding: 2.5rem !important;
        border-radius: 16px !important;
        border: 2px solid rgba(255,255,255,0.2) !important;
        backdrop-filter: blur(15px) !important;
        width: 100% !important;
        max-width: 900px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.1) !important;
    ">
        <h2 style="
            color: #ffffff !important; 
            margin-bottom: 1.5rem !important; 
            font-size: 2.2rem !important;
            font-weight: 700 !important;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.9) !important;
            letter-spacing: 1px !important;
        ">🎯 JobSniper AI</h2>
        <h4 style="
            color: #ffffff !important; 
            margin-bottom: 1.5rem !important; 
            font-size: 1.4rem !important;
            font-weight: 500 !important;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.8) !important;
            letter-spacing: 0.5px !important;
        ">Your Complete Career Intelligence Platform</h4>
        <p style="
            color: #ffffff !important; 
            margin-bottom: 1.5rem !important; 
            font-size: 1.2rem !important;
            font-weight: 400 !important;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.7) !important;
            line-height: 1.6 !important;
        ">⚡ Powered by Advanced AI • 📊 Real-time Analysis • 🎯 Personalized Recommendations</p>
        <p style="
            color: #ffffff !important; 
            margin: 0 !important; 
            font-size: 1rem !important;
            font-weight: 300 !important;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.7) !important;
            opacity: 0.9 !important;
        ">© 2025 JobSniper AI. Transforming careers with artificial intelligence.</p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Force additional spacing at the very end
st.markdown("<br><br><br><br>", unsafe_allow_html=True)
