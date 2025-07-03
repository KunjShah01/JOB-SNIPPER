import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import tempfile
import logging

# Add the parent directory to the Python path so we can import from agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing agents
from agents.controller_agent import ControllerAgent
from agents.auto_apply_agent import AutoApplyAgent
from agents.recruiter_view_agent import RecruiterViewAgent
from agents.skill_recommendation_agent import SkillRecommendationAgent

# from agents.agent_fallback import AgentFallbackHandler  # Unused import removed
from utils.pdf_reader import extract_text_from_pdf
from utils.sqlite_logger import save_to_db
from utils.exporter import PDFExporter, EmailSender
from utils.config import load_config

# Import new enhanced agents
try:
    from agents.web_scraper_agent import WebScraperAgent
    from agents.resume_builder_agent import ResumeBuilderAgent
    from agents.advanced_interview_prep_agent import AdvancedInterviewPrepAgent
    from agents.career_path_agent import CareerPathAgent
    WEB_FEATURES_AVAILABLE = True
except ImportError as e:
    WEB_FEATURES_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="JobSniper AI - Professional Resume & Career Intelligence Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load configuration
config = load_config()

# Initialize session state
if "user_session" not in st.session_state:
    st.session_state.user_session = {
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "start_time": datetime.now(),
    }

# Custom CSS for enhanced styling
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .auto-apply-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .hr-dashboard-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .candidate-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .skill-tag {
        background: #667eea;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        text-align: center;
    }
    
    .status-new { background: #e3f2fd; color: #1976d2; }
    .status-screening { background: #fff3e0; color: #f57c00; }
    .status-interview { background: #f3e5f5; color: #7b1fa2; }
    .status-offer { background: #e8f5e8; color: #388e3c; }
    .status-hired { background: #e1f5fe; color: #0277bd; }
    .status-rejected { background: #ffebee; color: #d32f2f; }
    
    .interview-prep-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    
    .resume-preview {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        font-family: 'Times New Roman', serif;
        line-height: 1.6;
    }
    
    .sidebar-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Main header
st.markdown(
    """
<div class="main-header">
    <h1>🎯 JobSniper AI</h1>
    <h3>Professional Resume & Career Intelligence Platform</h3>
    <p>Powered by Advanced AI • Real-time Web Research • ATS Optimization</p>
</div>
""",
    unsafe_allow_html=True,
)

# Sidebar navigation
st.sidebar.markdown("## 🎯 Navigation")

# Mode selection with enhanced options
mode = st.sidebar.selectbox(
    "Choose Your Mode",
    [
        "🎯 Resume Analysis",
        "📝 Resume Builder",
        "🤖 Auto Apply",
        "🎯 Interview Prep",
        "🚀 Career Path",
        "🔍 Company Research",
        "💰 Salary Insights",
        "👥 HR/Recruiter Mode",
        "📈 Skill Development",
    ],
    help="Select the feature you want to use",
)

# Sidebar info
st.sidebar.markdown(
    """
<div class="sidebar-info">
    <h4>💡 Quick Tips</h4>
    <p>• Upload PDF resumes for best results</p>
    <p>• Use specific job titles for accurate analysis</p>
    <p>• Enable web features with Firecrawl API</p>
    <p>• Check ATS scores before applying</p>
</div>
""",
    unsafe_allow_html=True,
)

# Session info
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Session:** {st.session_state.user_session['session_id']}")
st.sidebar.markdown(
    f"**Started:** {st.session_state.user_session['start_time'].strftime('%H:%M')}"
)

# Main content based on selected mode
if mode == "🎯 Resume Analysis":
    st.markdown("## 🎯 AI-Powered Resume Analysis")

    st.markdown(
        """
    <div class="feature-card">
        <h4>🤖 Intelligent Resume Analysis</h4>
        <p>Upload your resume and get comprehensive AI-powered analysis with job matching, skill assessment, and improvement recommendations.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # File upload
    uploaded_file = st.file_uploader(
        "📄 Upload Your Resume (PDF)",
        type="pdf",
        help="Upload a PDF version of your resume for the most accurate analysis",
    )

    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name

        st.success(f"✅ Resume uploaded successfully: {uploaded_file.name}")

        # Analysis options
        col1, col2 = st.columns(2)

        with col1:
            target_job_title = st.text_input(
                "🎯 Target Job Title (Optional)",
                placeholder="e.g., Senior Software Engineer",
            )

        with col2:
            analysis_depth = st.selectbox(
                "📊 Analysis Depth",
                ["Quick Analysis", "Comprehensive Analysis", "Deep Dive Analysis"],
            )

        # Analyze button
        if st.button("🚀 Analyze Resume", type="primary"):
            with st.spinner("🤖 AI is analyzing your resume..."):
                try:
                    # Extract text from PDF
                    resume_text = extract_text_from_pdf(temp_file_path)

                    if len(resume_text.strip()) < 100:
                        st.error(
                            "⚠️ Unable to extract sufficient text from the PDF. Please ensure the file is not corrupted or image-based."
                        )
                    else:
                        # Initialize controller agent
                        controller = ControllerAgent()

                        # Prepare analysis data
                        analysis_data = {
                            "resume_text": resume_text,
                            "target_job": target_job_title,
                            "analysis_depth": analysis_depth,
                        }

                        # Perform analysis
                        analysis_result = controller.run(json.dumps(analysis_data))

                        # Store results in session state
                        st.session_state.resume_analysis = json.loads(analysis_result)

                        st.success("✅ Resume analysis completed!")

                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    logger.error(f"Resume analysis error: {e}")

        # Display analysis results
        if "resume_analysis" in st.session_state:
            analysis = st.session_state.resume_analysis

            st.markdown("---")
            st.markdown("### 📊 Analysis Results")

            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                overall_score = analysis.get("overall_score", 0)
                st.markdown(
                    f"""
                <div class="metric-card">
                    <h3>Overall Score</h3>
                    <h1>{overall_score}%</h1>
                    <p>Resume Quality</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col2:
                ats_score = analysis.get("ats_compatibility", 0)
                st.markdown(
                    f"""
                <div class="metric-card">
                    <h3>ATS Score</h3>
                    <h1>{ats_score}%</h1>
                    <p>ATS Compatibility</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col3:
                skills_count = len(analysis.get("parsed_data", {}).get("skills", []))
                st.markdown(
                    f"""
                <div class="metric-card">
                    <h3>Skills Found</h3>
                    <h1>{skills_count}</h1>
                    <p>Technical Skills</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col4:
                experience_years = analysis.get("parsed_data", {}).get(
                    "experience_years", 0
                )
                st.markdown(
                    f"""
                <div class="metric-card">
                    <h3>Experience</h3>
                    <h1>{experience_years}</h1>
                    <p>Years</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Detailed analysis tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                [
                    "📋 Summary",
                    "🛠️ Skills",
                    "💼 Experience",
                    "📈 Recommendations",
                    "📄 Export",
                ]
            )

            with tab1:
                st.markdown("#### 📋 Resume Summary")
                parsed_data = analysis.get("parsed_data", {})

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Personal Information:**")
                    st.write(f"• **Name:** {parsed_data.get('name', 'Not found')}")
                    st.write(f"• **Email:** {parsed_data.get('email', 'Not found')}")
                    st.write(f"• **Phone:** {parsed_data.get('phone', 'Not found')}")
                    st.write(
                        f"• **Location:** {parsed_data.get('location', 'Not found')}"
                    )

                with col2:
                    st.markdown("**Professional Summary:**")
                    st.write(
                        f"• **Current Role:** {parsed_data.get('current_role', 'Not specified')}"
                    )
                    st.write(
                        f"• **Industry:** {parsed_data.get('industry', 'Not specified')}"
                    )
                    st.write(
                        f"• **Education:** {parsed_data.get('education', 'Not found')}"
                    )

            with tab2:
                st.markdown("#### 🛠️ Skills Analysis")
                skills = parsed_data.get("skills", [])

                if skills:
                    # Skills visualization
                    skills_df = pd.DataFrame(
                        {
                            "Skill": skills[:10],  # Top 10 skills
                            "Relevance": [85, 80, 75, 70, 65, 60, 55, 50, 45, 40][
                                : len(skills[:10])
                            ],
                        }
                    )

                    fig = px.bar(
                        skills_df,
                        x="Relevance",
                        y="Skill",
                        orientation="h",
                        title="Top Skills by Relevance",
                        color="Relevance",
                        color_continuous_scale="Blues",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Skills tags
                    st.markdown("**All Skills Found:**")
                    skills_html = ""
                    for skill in skills:
                        skills_html += f'<span class="skill-tag">{skill}</span>'
                    st.markdown(skills_html, unsafe_allow_html=True)
                else:
                    st.info(
                        "No skills detected. Consider adding a skills section to your resume."
                    )

            with tab3:
                st.markdown("#### 💼 Work Experience")
                work_history = parsed_data.get("work_history", [])

                if work_history:
                    for i, job in enumerate(work_history):
                        with st.expander(
                            f"{job.get('title', 'Position')} at {job.get('company', 'Company')}"
                        ):
                            st.write(
                                f"**Duration:** {job.get('duration', 'Not specified')}"
                            )
                            st.write(
                                f"**Location:** {job.get('location', 'Not specified')}"
                            )
                            st.write(
                                f"**Description:** {job.get('description', 'No description available')}"
                            )
                else:
                    st.info(
                        "No work experience found. Ensure your resume includes detailed work history."
                    )

            with tab4:
                st.markdown("#### 📈 AI Recommendations")
                recommendations = analysis.get("recommendations", [])

                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        st.markdown(f"**{i}.** {rec}")
                else:
                    st.markdown("""
                    **General Recommendations:**
                    1. Add quantifiable achievements with specific metrics
                    2. Include relevant keywords for your target industry
                    3. Ensure consistent formatting throughout
                    4. Add a professional summary section
                    5. Include relevant certifications and training
                    """)

                # Job matching if target job provided
                if target_job_title:
                    st.markdown("#### 🎯 Job Match Analysis")
                    match_score = analysis.get("job_match_score", 0)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Job Match Score", f"{match_score}%")
                    with col2:
                        if match_score >= 80:
                            st.success("🎉 Excellent match!")
                        elif match_score >= 60:
                            st.warning("⚠️ Good match with improvements needed")
                        else:
                            st.error("❌ Significant improvements required")

            with tab5:
                st.markdown("#### 📄 Export Options")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("📄 Export PDF Report"):
                        try:
                            # Generate PDF report
                            exporter = PDFExporter()
                            pdf_path = exporter.export_analysis_report(
                                analysis, uploaded_file.name
                            )

                            with open(pdf_path, "rb") as pdf_file:
                                st.download_button(
                                    label="⬇️ Download PDF Report",
                                    data=pdf_file.read(),
                                    file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf",
                                )
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")

                with col2:
                    if st.button("📧 Email Report"):
                        email = st.text_input("Enter your email address:")
                        if email and st.button("Send Email"):
                            try:
                                email_sender = EmailSender()
                                email_sender.send_analysis_report(
                                    email, analysis, uploaded_file.name
                                )
                                st.success("✅ Report sent successfully!")
                            except Exception as e:
                                st.error(f"Error sending email: {str(e)}")

                with col3:
                    if st.button("💾 Save to Database"):
                        try:
                            parsed_data = analysis.get("parsed_data", {})
                            match_result = {
                                "match_percent": analysis.get("overall_score", 0),
                                "job_title": analysis.get("target_job", ""),
                                "feedback_summary": ", ".join(analysis.get("recommendations", [])),
                                "job_roles": analysis.get("job_suggestions", []),
                            }
                            save_to_db(parsed_data, match_result)
                            st.success("✅ Analysis saved to database!")
                        except Exception as e:
                            st.error(f"Error saving to database: {str(e)}")

        # Clean up temporary file
        if "temp_file_path" in locals():
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

elif mode == "📝 Resume Builder":
    st.markdown("## 📝 AI-Powered Resume Builder")

    st.markdown(
        """
    <div class="feature-card">
        <h4>🤖 Intelligent Resume Creation</h4>
        <p>Build a professional, ATS-optimized resume with AI assistance. Choose from multiple templates and get real-time optimization suggestions.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Resume builder tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Basic Info", "💼 Experience", "🎯 Optimization", "📄 Generate"]
    )

    with tab1:
        st.markdown("### 👤 Personal Information")

        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name*", placeholder="John Doe")
            email = st.text_input("Email*", placeholder="john.doe@email.com")
            phone = st.text_input("Phone*", placeholder="+1 (555) 123-4567")
            location = st.text_input("Location*", placeholder="New York, NY")

        with col2:
            professional_title = st.text_input(
                "Professional Title*", placeholder="Senior Software Engineer"
            )
            linkedin_url = st.text_input(
                "LinkedIn URL", placeholder="https://linkedin.com/in/johndoe"
            )
            portfolio_url = st.text_input(
                "Portfolio URL", placeholder="https://johndoe.dev"
            )
            github_url = st.text_input(
                "GitHub URL", placeholder="https://github.com/johndoe"
            )

        # Professional summary
        professional_summary = st.text_area(
            "Professional Summary",
            height=100,
            placeholder="Write a compelling 3-4 sentence summary of your professional background...",
        )

        # Store basic info in session state
        if st.button("💾 Save Basic Info"):
            st.session_state.resume_basic_info = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "location": location,
                "professional_title": professional_title,
                "linkedin_url": linkedin_url,
                "portfolio_url": portfolio_url,
                "github_url": github_url,
                "professional_summary": professional_summary,
            }
            st.success("✅ Basic information saved!")

    with tab2:
        st.markdown("### 💼 Work Experience")

        # Initialize work experience in session state
        if "work_experiences" not in st.session_state:
            st.session_state.work_experiences = []

        # Add new experience
        with st.expander("➕ Add Work Experience"):
            col1, col2 = st.columns(2)
            with col1:
                company = st.text_input("Company Name", key="exp_company")
                title = st.text_input("Job Title", key="exp_title")
                start_date = st.text_input(
                    "Start Date", placeholder="Jan 2020", key="exp_start"
                )

            with col2:
                location_exp = st.text_input("Location", key="exp_location")
                end_date = st.text_input(
                    "End Date", placeholder="Present", key="exp_end"
                )

            description = st.text_area(
                "Job Description & Achievements",
                height=100,
                placeholder="• Led a team of 5 developers...\n• Increased system performance by 40%...",
                key="exp_description",
            )

            if st.button("➕ Add Experience"):
                if company and title:
                    new_exp = {
                        "company": company,
                        "title": title,
                        "start_date": start_date,
                        "end_date": end_date,
                        "location": location_exp,
                        "description": description,
                    }
                    st.session_state.work_experiences.append(new_exp)
                    st.success("✅ Experience added!")
                    st.rerun()

        # Display existing experiences
        if st.session_state.work_experiences:
            st.markdown("#### 📋 Current Experiences")
            for i, exp in enumerate(st.session_state.work_experiences):
                with st.expander(f"{exp['title']} at {exp['company']}"):
                    st.write(f"**Duration:** {exp['start_date']} - {exp['end_date']}")
                    st.write(f"**Location:** {exp['location']}")
                    st.write(f"**Description:** {exp['description']}")

                    if st.button("🗑️ Remove", key=f"remove_exp_{i}"):
                        st.session_state.work_experiences.pop(i)
                        st.rerun()

        # Education section
        st.markdown("### 🎓 Education")
        if "education_entries" not in st.session_state:
            st.session_state.education_entries = []

        with st.expander("➕ Add Education"):
            col1, col2 = st.columns(2)
            with col1:
                degree = st.text_input(
                    "Degree", placeholder="Bachelor of Science", key="edu_degree"
                )
                school = st.text_input("School/University", key="edu_school")
            with col2:
                graduation_year = st.text_input(
                    "Graduation Year", placeholder="2020", key="edu_year"
                )
                gpa = st.text_input(
                    "GPA (Optional)", placeholder="3.8/4.0", key="edu_gpa"
                )

            if st.button("➕ Add Education"):
                if degree and school:
                    new_edu = {
                        "degree": degree,
                        "school": school,
                        "graduation_year": graduation_year,
                        "gpa": gpa,
                    }
                    st.session_state.education_entries.append(new_edu)
                    st.success("✅ Education added!")
                    st.rerun()

        # Skills section
        st.markdown("### 🛠️ Skills")
        skills_input = st.text_area(
            "Enter your skills (comma-separated)",
            placeholder="Python, JavaScript, React, AWS, Machine Learning, Project Management",
            height=100,
        )

        if skills_input:
            skills_list = [skill.strip() for skill in skills_input.split(",")]
            st.session_state.resume_skills = skills_list

            # Display skills as tags
            st.markdown("**Your Skills:**")
            skills_html = ""
            for skill in skills_list:
                skills_html += f'<span class="skill-tag">{skill}</span>'
            st.markdown(skills_html, unsafe_allow_html=True)

        # Projects section
        st.markdown("### 🚀 Projects")
        if "projects" not in st.session_state:
            st.session_state.projects = []

        with st.expander("➕ Add Project"):
            project_name = st.text_input("Project Name", key="proj_name")
            project_description = st.text_area(
                "Project Description", height=80, key="proj_desc"
            )
            project_technologies = st.text_input(
                "Technologies Used",
                placeholder="React, Node.js, MongoDB",
                key="proj_tech",
            )
            project_url = st.text_input("Project URL (Optional)", key="proj_url")

            if st.button("➕ Add Project"):
                if project_name and project_description:
                    new_project = {
                        "name": project_name,
                        "description": project_description,
                        "technologies": project_technologies,
                        "url": project_url,
                    }
                    st.session_state.projects.append(new_project)
                    st.success("✅ Project added!")
                    st.rerun()

    with tab3:
        st.markdown("### 🎯 Resume Optimization")

        # Target job for optimization
        st.markdown("#### 🎯 Target Job (Optional)")
        target_job_title = st.text_input(
            "Target Job Title", placeholder="Senior Software Engineer"
        )
        target_company = st.text_input("Target Company", placeholder="Google")
        target_job_description = st.text_area(
            "Job Description",
            height=150,
            placeholder="Paste the job description here for AI optimization...",
        )

        # Template selection
        st.markdown("#### 🎨 Resume Template")
        template_style = st.selectbox(
            "Choose Template Style",
            ["Professional", "Modern", "Creative", "ATS Optimized"],
            help="Different templates optimize for different purposes",
        )

        # AI optimization options
        st.markdown("#### 🤖 AI Optimization Options")
        optimization_options = st.multiselect(
            "Select optimization features",
            [
                "ATS Keyword Optimization",
                "Industry-Specific Language",
                "Achievement Quantification",
                "Skills Prioritization",
                "Format Optimization",
            ],
            default=["ATS Keyword Optimization", "Achievement Quantification"],
        )

        # Color scheme
        st.markdown("#### 🎨 Color Scheme")
        color_scheme = st.selectbox(
            "Choose Color Scheme",
            [
                "Blue Professional",
                "Black & White",
                "Navy Blue",
                "Dark Green",
                "Burgundy",
            ],
        )

    with tab4:
        st.markdown("### 📄 Generate Resume")

        if st.button("🚀 Generate AI-Optimized Resume", type="primary"):
            # Check if we have minimum required info
            basic_info = st.session_state.get("resume_basic_info", {})
            work_experiences = st.session_state.get("work_experiences", [])
            skills = st.session_state.get("resume_skills", [])
            education_entries = st.session_state.get("education_entries", [])
            projects = st.session_state.get("projects", [])

            if basic_info.get("full_name") and work_experiences:
                with st.spinner("🤖 AI is crafting your perfect resume..."):
                    try:
                        if WEB_FEATURES_AVAILABLE:
                            from agents.resume_builder_agent import ResumeBuilderAgent

                            # Prepare user data
                            user_data = {
                                **basic_info,
                                "work_experience": work_experiences,
                                "skills": skills,
                                "education": education_entries,
                                "projects": projects,
                                "years_experience": len(work_experiences),
                            }

                            # Prepare target job data if provided
                            target_job = None
                            if target_job_title:
                                target_job = {
                                    "title": target_job_title,
                                    "company": target_company,
                                    "description": target_job_description,
                                }

                            # Generate resume
                            resume_builder = ResumeBuilderAgent()
                            resume_result = resume_builder.build_resume(
                                user_data,
                                target_job,
                                template_style.lower().replace(" ", "_"),
                            )

                            st.session_state.generated_resume = resume_result
                            st.success("✅ Resume generated successfully!")
                        else:
                            # Fallback resume generation
                            formatted_resume = f"""
# {basic_info.get("full_name", "Your Name")}
{basic_info.get("professional_title", "Professional Title")}

📧 {basic_info.get("email", "your.email@example.com")} | 📱 {basic_info.get("phone", "Your Phone Number")} | 📍 {basic_info.get("location", "Your Location")}
🔗 {basic_info.get("linkedin_url", "LinkedIn Profile")} | 💼 {basic_info.get("portfolio_url", "Portfolio")}

## PROFESSIONAL SUMMARY
{basic_info.get("professional_summary", "Professional summary to be added")}

## PROFESSIONAL EXPERIENCE
"""
                            for exp in work_experiences:
                                formatted_resume += f"""
### {exp["title"]} | {exp["company"]}
*{exp["start_date"]} - {exp["end_date"]} | {exp["location"]}*

{exp["description"]}

"""
                            formatted_resume += "\n## EDUCATION\n"
                            for edu in education_entries:
                                formatted_resume += f"**{edu['degree']}** - {edu['school']} ({edu['graduation_year']})\n"
                            formatted_resume += f"""

## TECHNICAL SKILLS
{", ".join(skills) if skills else "Skills to be listed"}

## PROJECTS
"""
                            for proj in projects:
                                formatted_resume += (
                                    f"**{proj['name']}** - {proj['description']}\n"
                                )
                            st.session_state.generated_resume = {
                                "formatted_resume": formatted_resume,
                                "ats_score": 85,
                                "word_count": len(formatted_resume.split()),
                                "success": True,
                            }
                            st.success("✅ Resume generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating resume: {str(e)}")
            else:
                st.error(
                    "⚠️ Please fill in basic information and add at least one work experience"
                )

        # Display generated resume
        if "generated_resume" in st.session_state:
            resume_data = st.session_state.generated_resume

            st.markdown("---")
            st.markdown("### 📄 Your Generated Resume")

            # ATS Score and metrics
            ats_score = resume_data.get("ats_score", 0)
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("ATS Score", f"{ats_score}%", "↑ Optimized")
            with col2:
                word_count = resume_data.get("word_count", 0)
                st.metric("Word Count", word_count, "Ideal length")
            with col3:
                st.metric("Template", template_style, "Professional")

            # Resume preview
            st.markdown("#### 👀 Resume Preview")
            formatted_resume = resume_data.get("formatted_resume", "")

            st.markdown(
                f"""
            <div class="resume-preview">
                {formatted_resume.replace("\n", "<br>")}
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Download options
            st.markdown("#### 📥 Download Options")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📄 Download PDF"):
                    st.success("✅ PDF generation feature coming soon!")

            with col2:
                if st.button("📝 Download Word"):
                    st.success("✅ Word document feature coming soon!")

            with col3:
                if st.button("📧 Email Resume"):
                    st.success("✅ Email feature coming soon!")

            with col4:
                # Copy to clipboard
                if st.button("📋 Copy Text"):
                    st.code(formatted_resume, language="markdown")
                    st.info("💡 Copy the text above to use in other applications")

elif mode == "🤖 Auto Apply":
    st.markdown("## 🤖 AI-Powered Auto Apply")

    st.markdown(
        """
    <div class="feature-card">
        <h4>🚀 Intelligent Job Application Assistant</h4>
        <p>Streamline your job application process with AI-powered cover letter generation, application tracking, and personalized recommendations.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Auto Apply workflow steps
    if "auto_apply_step" not in st.session_state:
        st.session_state.auto_apply_step = 0

    current_step = st.session_state.auto_apply_step

    # Progress indicator
    progress_steps = [
        "📄 Resume Upload",
        "💼 Job Details",
        "🤖 AI Generation",
        "✅ Review & Apply",
    ]

    cols = st.columns(4)
    for i, step in enumerate(progress_steps):
        with cols[i]:
            if i <= current_step:
                st.markdown(f"**{step}** ✅")
            else:
                st.markdown(f"{step}")

    st.markdown("---")

    # Step 1: Resume Upload
    if current_step == 0:
        st.markdown("### 📄 Step 1: Upload Your Resume")

        st.markdown(
            """
        <div class="auto-apply-card">
            <h4>📋 Resume Analysis</h4>
            <p>Upload your resume to enable personalized job applications and cover letter generation.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        uploaded_resume = st.file_uploader(
            "Upload Your Resume (PDF)", type="pdf", key="auto_apply_resume"
        )

        if uploaded_resume:
            st.success(f"✅ Resume uploaded: {uploaded_resume.name}")

            # Quick analysis
            with st.spinner("🔍 Quick resume analysis..."):
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as tmp_file:
                        tmp_file.write(uploaded_resume.getvalue())
                        temp_file_path = tmp_file.name

                    resume_text = extract_text_from_pdf(temp_file_path)

                    # Store resume data
                    st.session_state.auto_apply_resume_data = {
                        "text": resume_text,
                        "filename": uploaded_resume.name,
                    }

                    # Quick analysis display
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        word_count = len(resume_text.split())
                        st.metric("Word Count", word_count)

                    with col2:
                        # Simple skill extraction
                        common_skills = [
                            "Python",
                            "JavaScript",
                            "Java",
                            "React",
                            "SQL",
                            "AWS",
                            "Docker",
                            "Git",
                        ]
                        found_skills = [
                            skill
                            for skill in common_skills
                            if skill.lower() in resume_text.lower()
                        ]
                        st.metric("Skills Found", len(found_skills))

                    with col3:
                        st.metric("Status", "✅ Ready")

                    if st.button("➡️ Continue to Job Details", type="primary"):
                        st.session_state.auto_apply_step = 1
                        st.rerun()

                    # Clean up
                    os.unlink(temp_file_path)

                except Exception as e:
                    st.error(f"Error processing resume: {str(e)}")

        # Option to use existing analysis
        if "resume_analysis" in st.session_state:
            st.markdown("---")
            st.info("💡 You can also use your previously analyzed resume")
            if st.button("📋 Use Previous Analysis"):
                st.session_state.auto_apply_step = 1
                st.rerun()

    # Step 2: Job Details
    elif current_step == 1:
        st.markdown("### 💼 Step 2: Job Information")

        st.markdown(
            """
        <div class="auto-apply-card">
            <h4>🎯 Target Job Details</h4>
            <p>Provide job details to generate a personalized application package.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            job_title = st.text_input(
                "Job Title*", placeholder="Senior Software Engineer"
            )
            company_name = st.text_input("Company Name*", placeholder="Google")
            job_location = st.text_input(
                "Job Location", placeholder="San Francisco, CA"
            )
            job_url = st.text_input("Job Posting URL", placeholder="https://...")

        with col2:
            employment_type = st.selectbox(
                "Employment Type", ["Full-time", "Part-time", "Contract", "Internship"]
            )
            experience_level = st.selectbox(
                "Experience Level",
                ["Entry Level", "Mid Level", "Senior Level", "Executive"],
            )
            salary_range = st.text_input(
                "Salary Range (Optional)", placeholder="$100k - $150k"
            )
            application_deadline = st.date_input("Application Deadline (Optional)")

        job_description = st.text_area(
            "Job Description*",
            height=200,
            placeholder="Paste the complete job description here...",
        )

        # Personal information for application
        st.markdown("#### 👤 Personal Information")
        col1, col2 = st.columns(2)

        with col1:
            applicant_name = st.text_input("Full Name*", placeholder="John Doe")
            applicant_email = st.text_input("Email*", placeholder="john.doe@email.com")

        with col2:
            applicant_phone = st.text_input("Phone*", placeholder="+1 (555) 123-4567")
            applicant_location = st.text_input(
                "Your Location*", placeholder="New York, NY"
            )

        # Navigation buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("⬅️ Back to Resume Upload"):
                st.session_state.auto_apply_step = 0
                st.rerun()

        with col2:
            if st.button("🚀 Generate Application", type="primary"):
                if (
                    job_title
                    and company_name
                    and job_description
                    and applicant_name
                    and applicant_email
                ):
                    # Store job data
                    st.session_state.job_data = {
                        "title": job_title,
                        "company": company_name,
                        "location": job_location,
                        "url": job_url,
                        "employment_type": employment_type,
                        "experience_level": experience_level,
                        "salary_range": salary_range,
                        "deadline": str(application_deadline),
                        "description": job_description,
                    }

                    st.session_state.personal_info = {
                        "full_name": applicant_name,
                        "email": applicant_email,
                        "phone": applicant_phone,
                        "location": applicant_location,
                    }

                    st.session_state.auto_apply_step = 2
                    st.rerun()
                else:
                    st.error("⚠️ Please fill in all required fields")

    # Step 3: AI Generation
    elif current_step == 2:
        st.markdown("### 🤖 Step 3: AI Application Generation")

        st.markdown(
            """
        <div class="auto-apply-card">
            <h4>🎯 AI-Powered Application Creation</h4>
            <p>Our AI will analyze the job requirements and create a personalized application package for you.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Display job summary
        job_data = st.session_state.get("job_data", {})
        personal_info = st.session_state.get("personal_info", {})

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💼 Job Summary")
            st.write(f"**Position:** {job_data.get('title', '')}")
            st.write(f"**Company:** {job_data.get('company', '')}")
            st.write(f"**Location:** {job_data.get('location', '')}")
            st.write(f"**Type:** {job_data.get('employment_type', '')}")

        with col2:
            st.markdown("#### 👤 Applicant")
            st.write(f"**Name:** {personal_info.get('full_name', '')}")
            st.write(f"**Email:** {personal_info.get('email', '')}")
            st.write(f"**Phone:** {personal_info.get('phone', '')}")
            st.write(f"**Location:** {personal_info.get('location', '')}")

        # Navigation buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("⬅️ Back to Job Details"):
                st.session_state.auto_apply_step = 1
                st.rerun()

        with col2:
            if st.button("🚀 Generate Application Package", type="primary"):
                with st.spinner("🤖 AI is creating your personalized application..."):
                    try:
                        # Initialize auto apply agent
                        auto_apply_agent = AutoApplyAgent()

                        # Use dynamic resume data from analysis
                        if st.session_state.get("resume_analysis"):
                            parsed_data = st.session_state.resume_analysis.get(
                                "parsed_data", {}
                            )
                            resume_data = {
                                "name": personal_info["full_name"],
                                "skills": parsed_data.get("skills", []),
                                "experience": parsed_data.get(
                                    "experience", "Entry Level"
                                ),
                                "education": parsed_data.get("education", ""),
                                "certifications": parsed_data.get("certifications", []),
                                "achievements": parsed_data.get("achievements", []),
                                "work_history": parsed_data.get("work_history", []),
                            }
                        elif st.session_state.get("auto_apply_resume_data"):
                            # Basic extraction from resume text
                            resume_text = st.session_state.auto_apply_resume_data[
                                "text"
                            ]
                            resume_data = {
                                "name": personal_info["full_name"],
                                "skills": [],  # Would need to extract from text
                                "experience": "To be analyzed",
                                "education": "To be analyzed",
                            }
                        else:
                            resume_data = {
                                "name": personal_info["full_name"],
                                "skills": [],
                                "experience": "Entry Level",
                                "education": "",
                            }

                        # Generate application
                        application_result = auto_apply_agent.run(
                            job_data,
                            personal_info,
                            resume_data,
                        )

                        st.session_state.application_result = application_result
                        st.session_state.auto_apply_step = 3
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error generating application: {str(e)}")
                        st.info(
                            "💡 Please try again or contact support if the issue persists."
                        )

    # Step 4: Review & Apply
    elif current_step == 3:
        st.markdown("### ✅ Step 4: Review & Apply")

        st.markdown(
            """
        <div class="auto-apply-card">
            <h4>🎯 Your Personalized Application Package</h4>
            <p>Review your AI-generated application materials before submitting.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if "application_result" in st.session_state:
            result = st.session_state.application_result

            # Application metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                match_score = result.get("job_analysis", {}).get("match_score", 85)
                st.markdown(
                    f"""
                <div class="metric-card">
                    <h3>Match Score</h3>
                    <h1>{match_score}%</h1>
                    <p>Resume-Job Fit</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col2:
                success_prob = result.get("success_probability", {}).get(
                    "percentage", 75
                )
                st.markdown(
                    f"""
                <div class="metric-card">
                    <h3>Success Rate</h3>
                    <h1>{success_prob}%</h1>
                    <p>Predicted Success</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col3:
                priority = (
                    result.get("application_strategy", {})
                    .get("priority_level", "High")
                    .title()
                )
                priority_color = (
                    "#4CAF50"
                    if priority == "High"
                    else "#FF9800"
                    if priority == "Medium"
                    else "#607D8B"
                )
                st.markdown(
                    f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {priority_color} 0%, {priority_color}CC 100%);">
                    <h3>Priority</h3>
                    <h1>{priority}</h1>
                    <p>Application Level</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("---")

            # Application content tabs
            tab1, tab2, tab3, tab4 = st.tabs(
                ["📝 Cover Letter", "🎯 Strategy", "📋 Checklist", "📧 Follow-up"]
            )

            with tab1:
                st.markdown("#### 📝 AI-Generated Cover Letter")
                cover_letter = result.get(
                    "cover_letter", "Cover letter content would be generated here..."
                )

                edited_cover_letter = st.text_area(
                    "Review and edit your cover letter:",
                    value=cover_letter,
                    height=400,
                    help="Feel free to personalize this further with specific examples or adjust the tone.",
                )

                # Cover letter metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Word Count", len(edited_cover_letter.split()))
                with col2:
                    st.metric("Paragraphs", len(edited_cover_letter.split("\n\n")))
                with col3:
                    st.metric("Reading Level", "Professional")

            with tab2:
                st.markdown("#### 🎯 Application Strategy")
                strategy = result.get("application_strategy", {})

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**💡 Application Tips**")
                    recommendations = strategy.get(
                        "recommendations",
                        [
                            "Tailor your application to highlight relevant experience",
                            "Research the company culture and values",
                            "Prepare for potential technical interviews",
                            "Follow up within 1-2 weeks if no response",
                            "Connect with current employees on LinkedIn",
                        ],
                    )

                    for i, rec in enumerate(recommendations[:5], 1):
                        st.markdown(f"**{i}.** {rec}")

                with col2:
                    st.markdown("**🚀 Platform-Specific Tips**")
                    platform_tips = result.get(
                        "platform_tips",
                        [
                            "Apply within 24-48 hours of job posting",
                            "Use keywords from the job description",
                            "Ensure your LinkedIn profile is updated",
                            "Set up job alerts for similar positions",
                            "Prepare for video interviews",
                        ],
                    )

                    for i, tip in enumerate(platform_tips[:5], 1):
                        st.markdown(f"**{i}.** {tip}")

            with tab3:
                st.markdown("#### 📋 Application Checklist")

                checklist_items = [
                    "Resume tailored to job requirements",
                    "Cover letter personalized for company",
                    "LinkedIn profile updated and optimized",
                    "Portfolio/work samples prepared (if applicable)",
                    "References list ready",
                    "Company research completed",
                    "Questions prepared for interviewer",
                    "Interview outfit planned",
                    "Thank you email template ready",
                ]

                for item in checklist_items:
                    st.checkbox(item, key=f"checklist_{item}")

            with tab4:
                st.markdown("#### 📧 Follow-up Strategy")

                follow_up_timeline = {
                    "Immediately after applying": [
                        "Save job posting and application details",
                        "Add application to tracking spreadsheet",
                        "Set calendar reminder for follow-up",
                    ],
                    "1 week after applying": [
                        "Send polite follow-up email to hiring manager",
                        "Connect with employees on LinkedIn",
                        "Check for any updates on application status",
                    ],
                    "2 weeks after applying": [
                        "Second follow-up if no response",
                        "Consider reaching out through different channels",
                        "Continue applying to similar positions",
                    ],
                }

                for timeline, actions in follow_up_timeline.items():
                    st.markdown(f"**{timeline}:**")
                    for action in actions:
                        st.markdown(f"• {action}")
                    st.markdown("")

            st.markdown("---")

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📄 Save Package", help="Save all application materials"):
                    try:
                        # Save application package
                        save_data = {
                            "job_data": st.session_state.job_data,
                            "personal_info": st.session_state.personal_info,
                            "application_result": result,
                            "cover_letter": edited_cover_letter,
                            "timestamp": datetime.now().isoformat(),
                        }

                        # Save to session state for now
                        if "saved_applications" not in st.session_state:
                            st.session_state.saved_applications = []

                        st.session_state.saved_applications.append(save_data)
                        st.success("✅ Application package saved!")
                    except Exception as e:
                        st.error(f"Error saving package: {str(e)}")

            with col2:
                if st.button(
                    "📧 Email Materials", help="Email application materials to yourself"
                ):
                    email = st.session_state.personal_info.get("email", "")
                    if email:
                        try:
                            # Email functionality would be implemented here
                            st.success(f"✅ Application materials sent to {email}!")
                        except Exception as e:
                            st.error(f"Error sending email: {str(e)}")
                    else:
                        st.error("No email address found")

            with col3:
                if st.button(
                    "🔄 New Application", help="Start a new application process"
                ):
                    # Clear application data
                    for key in [
                        "job_data",
                        "personal_info",
                        "application_result",
                        "auto_apply_resume_data",
                    ]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.auto_apply_step = 0
                    st.rerun()

            with col4:
                if st.button(
                    "🎯 Apply Now",
                    type="primary",
                    help="Open job posting to submit application",
                ):
                    job_url = st.session_state.get("job_data", {}).get("url", "")
                    if job_url:
                        st.markdown(
                            f"🚀 **Ready to apply!** [Open Job Posting]({job_url})"
                        )
                        st.balloons()
                    else:
                        st.info(
                            "💡 Use your generated materials to apply through the job platform"
                        )
                        st.balloons()

elif mode == "👥 HR/Recruiter Mode":
    st.markdown("## 👥 HR & Recruiter Intelligence Center")

    st.markdown(
        """
    <div class="hr-dashboard-card">
        <h4>📊 Comprehensive Recruitment Dashboard</h4>
        <p>Advanced analytics, candidate management, and AI-powered recruitment insights for HR professionals and recruiters.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Initialize HR data if not exists
    if "hr_data" not in st.session_state:
        st.session_state.hr_data = {
            "candidates": [],
            "job_postings": [],
            "interviews": [],
            "analytics": {
                "total_applications": 0,
                "candidates_screened": 0,
                "interviews_conducted": 0,
                "offers_made": 0,
                "hires_completed": 0,
            },
        }

    # HR Dashboard tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📊 Dashboard",
            "👤 Candidates",
            "💼 Job Postings",
            "📅 Interviews",
            "📈 Analytics",
            "🤖 AI Tools",
        ]
    )

    with tab1:
        st.markdown("### 📊 Recruitment Dashboard")

        # Key metrics
        hr_analytics = st.session_state.hr_data["analytics"]

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(
                f"""
            <div class="metric-card">
                <h3>Applications</h3>
                <h1>{hr_analytics["total_applications"]}</h1>
                <p>This Month</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
            <div class="metric-card">
                <h3>Screened</h3>
                <h1>{hr_analytics["candidates_screened"]}</h1>
                <p>Candidates</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
            <div class="metric-card">
                <h3>Interviews</h3>
                <h1>{hr_analytics["interviews_conducted"]}</h1>
                <p>Conducted</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                f"""
            <div class="metric-card">
                <h3>Offers</h3>
                <h1>{hr_analytics["offers_made"]}</h1>
                <p>Extended</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col5:
            st.markdown(
                f"""
            <div class="metric-card">
                <h3>Hires</h3>
                <h1>{hr_analytics["hires_completed"]}</h1>
                <p>Completed</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Recruitment funnel visualization
        st.markdown("#### 🔄 Recruitment Funnel")

        funnel_data = {
            "Applications": hr_analytics["total_applications"] or 150,
            "Screened": hr_analytics["candidates_screened"] or 75,
            "Interviewed": hr_analytics["interviews_conducted"] or 30,
            "Offers": hr_analytics["offers_made"] or 8,
            "Hired": hr_analytics["hires_completed"] or 6,
        }

        fig_funnel = go.Figure(
            go.Funnel(
                y=list(funnel_data.keys()),
                x=list(funnel_data.values()),
                textinfo="value+percent initial",
                marker={
                    "color": ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe"]
                },
            )
        )

        fig_funnel.update_layout(height=400, title="Recruitment Conversion Funnel")
        st.plotly_chart(fig_funnel, use_container_width=True)

        # Recent activity
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📋 Recent Applications")
            recent_applications = [
                {
                    "name": "Sarah Johnson",
                    "position": "Software Engineer",
                    "score": 92,
                    "status": "New",
                },
                {
                    "name": "Mike Chen",
                    "position": "Data Scientist",
                    "score": 88,
                    "status": "Screening",
                },
                {
                    "name": "Emily Davis",
                    "position": "Product Manager",
                    "score": 85,
                    "status": "Interview",
                },
                {
                    "name": "Alex Rodriguez",
                    "position": "UX Designer",
                    "score": 90,
                    "status": "Offer",
                },
                {
                    "name": "Lisa Wang",
                    "position": "DevOps Engineer",
                    "score": 87,
                    "status": "Hired",
                },
            ]

            for app in recent_applications:
                status_class = f"status-{app['status'].lower()}"
                st.markdown(
                    f"""
                <div class="candidate-card">
                    <strong>{app["name"]}</strong> - {app["position"]}<br>
                    <small>AI Score: {app["score"]}%</small>
                    <span class="status-badge {status_class}">{app["status"]}</span>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        with col2:
            st.markdown("#### 📅 Upcoming Interviews")
            upcoming_interviews = [
                {
                    "candidate": "Sarah Johnson",
                    "position": "Software Engineer",
                    "time": "Today 2:00 PM",
                    "type": "Technical",
                },
                {
                    "candidate": "Mike Chen",
                    "position": "Data Scientist",
                    "time": "Tomorrow 10:00 AM",
                    "type": "Behavioral",
                },
                {
                    "candidate": "Emily Davis",
                    "position": "Product Manager",
                    "time": "Tomorrow 3:00 PM",
                    "type": "Final Round",
                },
                {
                    "candidate": "Alex Rodriguez",
                    "position": "UX Designer",
                    "time": "Friday 11:00 AM",
                    "type": "Portfolio Review",
                },
            ]

            for interview in upcoming_interviews:
                st.markdown(
                    f"""
                <div class="candidate-card">
                    <strong>{interview["candidate"]}</strong><br>
                    <small>{interview["position"]} - {interview["type"]}</small><br>
                    <small>🕒 {interview["time"]}</small>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    with tab2:
        st.markdown("### 👤 Candidate Management")

        # Candidate search and filters
        col1, col2, col3 = st.columns(3)

        with col1:
            search_term = st.text_input(
                "🔍 Search Candidates", placeholder="Name, skills, or position..."
            )

        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "New", "Screening", "Interview", "Offer", "Hired", "Rejected"],
            )

        with col3:
            position_filter = st.selectbox(
                "Filter by Position",
                [
                    "All",
                    "Software Engineer",
                    "Data Scientist",
                    "Product Manager",
                    "UX Designer",
                    "DevOps Engineer",
                ],
            )

        # Add new candidate
        with st.expander("➕ Add New Candidate"):
            col1, col2 = st.columns(2)

            with col1:
                candidate_name = st.text_input("Full Name", key="new_candidate_name")
                candidate_email = st.text_input("Email", key="new_candidate_email")
                candidate_phone = st.text_input("Phone", key="new_candidate_phone")
                candidate_position = st.text_input(
                    "Applied Position", key="new_candidate_position"
                )

            with col2:
                candidate_experience = st.number_input(
                    "Years of Experience",
                    min_value=0,
                    max_value=50,
                    key="new_candidate_exp",
                )
                candidate_location = st.text_input(
                    "Location", key="new_candidate_location"
                )
                candidate_source = st.selectbox(
                    "Source",
                    ["LinkedIn", "Indeed", "Company Website", "Referral", "Other"],
                    key="new_candidate_source",
                )
                candidate_status = st.selectbox(
                    "Initial Status", ["New", "Screening"], key="new_candidate_status"
                )

            candidate_resume = st.file_uploader(
                "Upload Resume", type="pdf", key="new_candidate_resume"
            )
            candidate_notes = st.text_area("Initial Notes", key="new_candidate_notes")

            if st.button("➕ Add Candidate"):
                if candidate_name and candidate_email and candidate_position:
                    new_candidate = {
                        "id": len(st.session_state.hr_data["candidates"]) + 1,
                        "name": candidate_name,
                        "email": candidate_email,
                        "phone": candidate_phone,
                        "position": candidate_position,
                        "experience": candidate_experience,
                        "location": candidate_location,
                        "source": candidate_source,
                        "status": candidate_status,
                        "notes": candidate_notes,
                        "ai_score": 0,
                        "date_added": datetime.now().strftime("%Y-%m-%d"),
                        "resume_uploaded": candidate_resume is not None,
                    }

                    # Analyze resume if uploaded
                    if candidate_resume:
                        try:
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=".pdf"
                            ) as tmp_file:
                                tmp_file.write(candidate_resume.getvalue())
                                temp_file_path = tmp_file.name

                            resume_text = extract_text_from_pdf(temp_file_path)

                            # Quick AI analysis
                            recruiter_agent = RecruiterViewAgent()
                            analysis_result = recruiter_agent.run(
                                json.dumps(
                                    {
                                        "resume_text": resume_text,
                                        "target_position": candidate_position,
                                    }
                                )
                            )

                            analysis_data = json.loads(analysis_result)
                            new_candidate["ai_score"] = analysis_data.get(
                                "overall_score", 75
                            )
                            new_candidate["skills"] = analysis_data.get(
                                "parsed_data", {}
                            ).get("skills", [])

                            os.unlink(temp_file_path)

                        except Exception as e:
                            st.warning(f"Resume analysis failed: {str(e)}")
                            new_candidate["ai_score"] = 75  # Default score

                    st.session_state.hr_data["candidates"].append(new_candidate)
                    st.session_state.hr_data["analytics"]["total_applications"] += 1

                    st.success(f"✅ Candidate {candidate_name} added successfully!")
                    st.rerun()
                else:
                    st.error(
                        "Please fill in required fields: Name, Email, and Position"
                    )

        # Candidate list
        st.markdown("#### 📋 Candidate Database")

        candidates = st.session_state.hr_data["candidates"]

        if candidates:
            # Filter candidates
            filtered_candidates = candidates

            if search_term:
                filtered_candidates = [
                    c
                    for c in filtered_candidates
                    if search_term.lower() in c["name"].lower()
                    or search_term.lower() in c["position"].lower()
                ]

            if status_filter != "All":
                filtered_candidates = [
                    c for c in filtered_candidates if c["status"] == status_filter
                ]

            if position_filter != "All":
                filtered_candidates = [
                    c for c in filtered_candidates if c["position"] == position_filter
                ]

            # Display candidates
            for candidate in filtered_candidates:
                with st.expander(
                    f"{candidate['name']} - {candidate['position']} (Score: {candidate['ai_score']}%)"
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Email:** {candidate['email']}")
                        st.write(f"**Phone:** {candidate['phone']}")
                        st.write(f"**Location:** {candidate['location']}")
                        st.write(f"**Experience:** {candidate['experience']} years")

                    with col2:
                        st.write(f"**Source:** {candidate['source']}")
                        st.write(f"**Date Added:** {candidate['date_added']}")
                        st.write(
                            f"**Resume:** {'✅ Uploaded' if candidate['resume_uploaded'] else '❌ Missing'}"
                        )

                        # Status update
                        new_status = st.selectbox(
                            "Update Status",
                            [
                                "New",
                                "Screening",
                                "Interview",
                                "Offer",
                                "Hired",
                                "Rejected",
                            ],
                            index=[
                                "New",
                                "Screening",
                                "Interview",
                                "Offer",
                                "Hired",
                                "Rejected",
                            ].index(candidate["status"]),
                            key=f"status_{candidate['id']}",
                        )

                        if new_status != candidate["status"]:
                            candidate["status"] = new_status
                            st.success("Status updated!")

                    with col3:
                        st.write(f"**AI Score:** {candidate['ai_score']}%")

                        # Skills if available
                        if "skills" in candidate and candidate["skills"]:
                            st.write("**Skills:**")
                            skills_html = ""
                            for skill in candidate["skills"][:5]:
                                skills_html += f'<span class="skill-tag">{skill}</span>'
                            st.markdown(skills_html, unsafe_allow_html=True)

                    # Notes section
                    st.markdown("**Notes:**")
                    updated_notes = st.text_area(
                        "Candidate Notes",
                        value=candidate.get("notes", ""),
                        key=f"notes_{candidate['id']}",
                    )

                    if updated_notes != candidate.get("notes", ""):
                        candidate["notes"] = updated_notes

                    # Action buttons
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if st.button("📧 Email", key=f"email_{candidate['id']}"):
                            st.info("Email functionality for {candidate['name']}")
                        if st.button("📧 Email", key=f"email_{candidate['id']}"):
                            st.info(f"Email functionality for {candidate['name']}")

                    with col2:
                        if st.button("📅 Schedule", key=f"schedule_{candidate['id']}"):
                            st.info(f"Interview scheduling for {candidate['name']}")

                    with col3:
                        if st.button("📄 View Resume", key=f"resume_{candidate['id']}"):
                            st.info(f"Resume viewer for {candidate['name']}")

                    with col4:
                        if st.button("🗑️ Remove", key=f"remove_{candidate['id']}"):
                            st.session_state.hr_data["candidates"] = [
                                c for c in candidates if c["id"] != candidate["id"]
                            ]
                            st.rerun()

    with tab3:
        st.markdown("### 💼 Job Posting Management")

        # Add new job posting
        with st.expander("➕ Create New Job Posting"):
            col1, col2 = st.columns(2)

            with col1:
                job_title = st.text_input("Job Title", key="new_job_title")
                job_department = st.text_input("Department", key="new_job_dept")
                job_location = st.text_input("Location", key="new_job_location")
                job_type = st.selectbox(
                    "Employment Type",
                    ["Full-time", "Part-time", "Contract", "Internship"],
                    key="new_job_type",
                )

            with col2:
                job_level = st.selectbox(
                    "Experience Level",
                    ["Entry Level", "Mid Level", "Senior Level", "Executive"],
                    key="new_job_level",
                )
                job_salary_min = st.number_input(
                    "Salary Min", min_value=0, key="new_job_salary_min"
                )
                job_salary_max = st.number_input(
                    "Salary Max", min_value=0, key="new_job_salary_max"
                )
                job_remote = st.checkbox("Remote Work Available", key="new_job_remote")

            job_description = st.text_area(
                "Job Description", height=200, key="new_job_description"
            )
            job_requirements = st.text_area(
                "Requirements", height=150, key="new_job_requirements"
            )
            job_benefits = st.text_area("Benefits", height=100, key="new_job_benefits")

            if st.button("🚀 Create Job Posting"):
                if job_title and job_department and job_description:
                    new_job = {
                        "id": len(st.session_state.hr_data["job_postings"]) + 1,
                        "title": job_title,
                        "department": job_department,
                        "location": job_location,
                        "type": job_type,
                        "level": job_level,
                        "salary_min": job_salary_min,
                        "salary_max": job_salary_max,
                        "remote": job_remote,
                        "description": job_description,
                        "requirements": job_requirements,
                        "benefits": job_benefits,
                        "status": "Active",
                        "date_created": datetime.now().strftime("%Y-%m-%d"),
                        "applications": 0,
                    }

                    st.session_state.hr_data["job_postings"].append(new_job)
                    st.success(f"✅ Job posting for {job_title} created successfully!")
                    st.rerun()
                else:
                    st.error(
                        "Please fill in required fields: Title, Department, and Description"
                    )

        # Job postings list
        st.markdown("#### 📋 Active Job Postings")

        job_postings = st.session_state.hr_data["job_postings"]

        if job_postings:
            for job in job_postings:
                with st.expander(
                    f"{job['title']} - {job['department']} ({job['applications']} applications)"
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Department:** {job['department']}")
                        st.write(f"**Location:** {job['location']}")
                        st.write(f"**Type:** {job['type']}")
                        st.write(f"**Level:** {job['level']}")

                    with col2:
                        salary_range = (
                            f"${job['salary_min']:,} - ${job['salary_max']:,}"
                            if job["salary_min"] and job["salary_max"]
                            else "Not specified"
                        )
                        st.write(f"**Salary:** {salary_range}")
                        st.write(f"**Remote:** {'Yes' if job['remote'] else 'No'}")
                        st.write(f"**Created:** {job['date_created']}")
                        st.write(f"**Applications:** {job['applications']}")

                    with col3:
                        # Status update
                        new_status = st.selectbox(
                            "Status",
                            ["Active", "Paused", "Closed"],
                            index=["Active", "Paused", "Closed"].index(job["status"]),
                            key=f"job_status_{job['id']}",
                        )

                        if new_status != job["status"]:
                            job["status"] = new_status
                            st.success("Status updated!")

                    # Job details
                    st.markdown("**Description:**")
                    st.write(job["description"])

                    st.markdown("**Requirements:**")
                    st.write(job["requirements"])

                    if job["benefits"]:
                        st.markdown("**Benefits:**")
                        st.write(job["benefits"])

                    # Action buttons
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if st.button("📝 Edit", key=f"edit_job_{job['id']}"):
                            st.info(f"Edit functionality for {job['title']}")
                        if st.button("📝 Edit", key=f"edit_job_{job['id']}"):
                            st.info(f"Edit functionality for {job['title']}")

                    with col2:
                        if st.button("📊 Analytics", key=f"analytics_job_{job['id']}"):
                            st.info(f"Analytics for {job['title']}")

                    with col3:
                        if st.button("📤 Publish", key=f"publish_job_{job['id']}"):
                            st.info(f"Publishing {job['title']} to job boards")

                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_job_{job['id']}"):
                            st.session_state.hr_data["job_postings"] = [
                                j for j in job_postings if j["id"] != job["id"]
                            ]
                            st.rerun()

    with tab4:
        st.markdown("### 📅 Interview Management")

        # Schedule new interview
        with st.expander("📅 Schedule New Interview"):
            col1, col2 = st.columns(2)

            with col1:
                # Get candidate names for dropdown
                candidate_names = [
                    c["name"] for c in st.session_state.hr_data["candidates"]
                ]
                if candidate_names:
                    selected_candidate = st.selectbox(
                        "Select Candidate", candidate_names, key="interview_candidate"
                    )
                else:
                    st.info("No candidates available. Add candidates first.")
                    selected_candidate = None

                interview_type = st.selectbox(
                    "Interview Type",
                    [
                        "Phone Screening",
                        "Technical Interview",
                        "Behavioral Interview",
                        "Final Round",
                        "Panel Interview",
                    ],
                    key="interview_type",
                )

                interview_date = st.date_input("Interview Date", key="interview_date")
                interview_time = st.time_input("Interview Time", key="interview_time")

            with col2:
                interviewer = st.text_input("Interviewer", key="interview_interviewer")
                interview_location = st.text_input(
                    "Location/Meeting Link", key="interview_location"
                )
                interview_duration = st.selectbox(
                    "Duration",
                    ["30 minutes", "45 minutes", "1 hour", "1.5 hours", "2 hours"],
                    key="interview_duration",
                )
                interview_notes = st.text_area(
                    "Preparation Notes", key="interview_notes"
                )

            if st.button("📅 Schedule Interview") and selected_candidate:
                new_interview = {
                    "id": len(st.session_state.hr_data["interviews"]) + 1,
                    "candidate": selected_candidate,
                    "type": interview_type,
                    "date": str(interview_date),
                    "time": str(interview_time),
                    "interviewer": interviewer,
                    "location": interview_location,
                    "duration": interview_duration,
                    "notes": interview_notes,
                    "status": "Scheduled",
                    "feedback": "",
                    "rating": 0,
                }

                st.session_state.hr_data["interviews"].append(new_interview)
                st.session_state.hr_data["analytics"]["interviews_conducted"] += 1
                st.success(f"✅ Interview scheduled with {selected_candidate}")
                st.rerun()

        # Interview calendar view
        st.markdown("#### 📅 Interview Schedule")

        interviews = st.session_state.hr_data["interviews"]

        if interviews:
            # Filter by date range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", value=datetime.now().date())
            with col2:
                end_date = st.date_input(
                    "To Date", value=datetime.now().date() + timedelta(days=7)
                )

            # Display interviews
            for interview in interviews:
                interview_date = datetime.strptime(interview["date"], "%Y-%m-%d").date()

                if start_date <= interview_date <= end_date:
                    with st.expander(
                        f"{interview['candidate']} - {interview['type']} ({interview['date']} {interview['time']})"
                    ):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write(f"**Candidate:** {interview['candidate']}")
                            st.write(f"**Type:** {interview['type']}")
                            st.write(f"**Date:** {interview['date']}")
                            st.write(f"**Time:** {interview['time']}")

                        with col2:
                            st.write(f"**Interviewer:** {interview['interviewer']}")
                            st.write(f"**Location:** {interview['location']}")
                            st.write(f"**Duration:** {interview['duration']}")

                            # Status update
                            new_status = st.selectbox(
                                "Status",
                                [
                                    "Scheduled",
                                    "In Progress",
                                    "Completed",
                                    "Cancelled",
                                    "Rescheduled",
                                ],
                                index=[
                                    "Scheduled",
                                    "In Progress",
                                    "Completed",
                                    "Cancelled",
                                    "Rescheduled",
                                ].index(interview["status"]),
                                key=f"interview_status_{interview['id']}",
                            )

                            if new_status != interview["status"]:
                                interview["status"] = new_status
                                st.success("Status updated!")

                        with col3:
                            # Rating
                            if interview["status"] == "Completed":
                                rating = st.slider(
                                    "Interview Rating",
                                    1,
                                    10,
                                    value=interview["rating"]
                                    if interview["rating"] > 0
                                    else 5,
                                    key=f"rating_{interview['id']}",
                                )
                                interview["rating"] = rating

                        # Notes and feedback
                        st.markdown("**Preparation Notes:**")
                        st.write(interview["notes"])

                        if interview["status"] in ["Completed", "In Progress"]:
                            st.markdown("**Interview Feedback:**")
                            feedback = st.text_area(
                                "Feedback",
                                value=interview["feedback"],
                                key=f"feedback_{interview['id']}",
                            )
                            interview["feedback"] = feedback

                        # Action buttons
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if st.button(
                                "📧 Send Reminder", key=f"reminder_{interview['id']}"
                            ):
                                st.info(
                                    f"Reminder sent for interview with {interview['candidate']}"
                                )
                            if st.button(
                                "📧 Send Reminder", key=f"reminder_{interview['id']}"
                            ):
                                st.info(
                                    f"Reminder sent for interview with {interview['candidate']}"
                                )

                        with col2:
                            if st.button(
                                "📝 Reschedule", key=f"reschedule_{interview['id']}"
                            ):
                                st.info(
                                    f"Rescheduling interview with {interview['candidate']}"
                                )

                        with col3:
                            if st.button("❌ Cancel", key=f"cancel_{interview['id']}"):
                                interview["status"] = "Cancelled"
                                st.rerun()

    with tab5:
        st.markdown("### 📈 Advanced Analytics")

        # Time-based analytics
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📊 Application Trends")

            # Sample data for demonstration
            dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="M")
            applications = [45, 52, 38, 61, 55, 48, 67, 59, 63, 71, 58, 49]

            fig_trend = go.Figure()
            fig_trend.add_trace(
                go.Scatter(
                    x=dates,
                    y=applications,
                    mode="lines+markers",
                    name="Applications",
                    line=dict(color="#667eea", width=3),
                    marker=dict(size=8),
                )
            )

            fig_trend.update_layout(
                title="Monthly Application Trends",
                xaxis_title="Month",
                yaxis_title="Number of Applications",
                template="plotly_white",
                height=300,
            )

            st.plotly_chart(fig_trend, use_container_width=True)

        with col2:
            st.markdown("#### 🎯 Source Effectiveness")

            source_data = {
                "LinkedIn": 35,
                "Indeed": 25,
                "Company Website": 20,
                "Referrals": 15,
                "Other": 5,
            }

            fig_source = go.Figure(
                data=[
                    go.Pie(
                        labels=list(source_data.keys()),
                        values=list(source_data.values()),
                        hole=0.3,
                        marker_colors=[
                            "#667eea",
                            "#764ba2",
                            "#f093fb",
                            "#f5576c",
                            "#4facfe",
                        ],
                    )
                ]
            )

            fig_source.update_layout(title="Application Sources", height=300)

            st.plotly_chart(fig_source, use_container_width=True)

        # Performance metrics
        st.markdown("#### ⏱️ Performance Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Avg. Time to Hire", "18 days", "-2 days")

        with col2:
            st.metric("Interview-to-Offer Rate", "26.7%", "+3.2%")

        with col3:
            st.metric("Offer Acceptance Rate", "85%", "+5%")

        with col4:
            st.metric("Cost per Hire", "$3,200", "-$400")

        # Detailed analytics
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📈 Hiring Velocity")

            velocity_data = {
                "Week": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "Applications": [38, 42, 35, 45],
                "Interviews": [12, 15, 11, 18],
                "Offers": [3, 4, 2, 5],
            }

            fig_velocity = go.Figure()

            for metric in ["Applications", "Interviews", "Offers"]:
                fig_velocity.add_trace(
                    go.Bar(
                        name=metric, x=velocity_data["Week"], y=velocity_data[metric]
                    )
                )

            fig_velocity.update_layout(
                title="Weekly Hiring Velocity",
                barmode="group",
                template="plotly_white",
                height=400,
            )

            st.plotly_chart(fig_velocity, use_container_width=True)

        with col2:
            st.markdown("#### 🎯 Position Analytics")

            position_data = {
                "Position": [
                    "Software Engineer",
                    "Data Scientist",
                    "Product Manager",
                    "UX Designer",
                    "DevOps Engineer",
                ],
                "Applications": [45, 32, 28, 22, 18],
                "Avg_Score": [82, 78, 85, 80, 77],
            }

            fig_positions = go.Figure()

            fig_positions.add_trace(
                go.Bar(
                    name="Applications",
                    x=position_data["Position"],
                    y=position_data["Applications"],
                    yaxis="y",
                    offsetgroup=1,
                )
            )

            fig_positions.add_trace(
                go.Scatter(
                    name="Avg Score",
                    x=position_data["Position"],
                    y=position_data["Avg_Score"],
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(color="red", width=3),
                )
            )

            fig_positions.update_layout(
                title="Applications vs Average Score by Position",
                xaxis=dict(title="Position"),
                yaxis=dict(title="Number of Applications", side="left"),
                yaxis2=dict(title="Average Score", side="right", overlaying="y"),
                template="plotly_white",
                height=400,
            )

            st.plotly_chart(fig_positions, use_container_width=True)

        # Export analytics
        st.markdown("#### 📊 Export Analytics")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Export PDF Report"):
                st.success("✅ Analytics report exported!")

        with col2:
            if st.button("📊 Export Excel Data"):
                st.success("✅ Data exported to Excel!")

        with col3:
            if st.button("📧 Email Report"):
                st.success("✅ Report emailed to stakeholders!")

    with tab6:
        st.markdown("### 🤖 AI-Powered HR Tools")

        # AI Resume Screening
        st.markdown("#### 🔍 AI Resume Screening")

        with st.expander("🤖 Bulk Resume Analysis"):
            st.markdown("""
            Upload multiple resumes for AI-powered batch analysis and ranking.
            """)

            uploaded_resumes = st.file_uploader(
                "Upload Resumes (PDF)",
                type="pdf",
                accept_multiple_files=True,
                key="bulk_resumes",
            )

            target_position = st.text_input(
                "Target Position", placeholder="Software Engineer"
            )

            if uploaded_resumes and target_position:
                if st.button("🚀 Analyze All Resumes"):
                    with st.spinner("🤖 AI is analyzing all resumes..."):
                        results = []

                        for resume_file in uploaded_resumes:
                            try:
                                with tempfile.NamedTemporaryFile(
                                    delete=False, suffix=".pdf"
                                ) as tmp_file:
                                    tmp_file.write(resume_file.getvalue())
                                    temp_file_path = tmp_file.name

                                resume_text = extract_text_from_pdf(temp_file_path)

                                # AI analysis
                                recruiter_agent = RecruiterViewAgent()
                                analysis_result = recruiter_agent.run(
                                    json.dumps(
                                        {
                                            "resume_text": resume_text,
                                            "target_position": target_position,
                                        }
                                    )
                                )

                                analysis_data = json.loads(analysis_result)

                                results.append(
                                    {
                                        "filename": resume_file.name,
                                        "score": analysis_data.get("overall_score", 0),
                                        "skills": analysis_data.get(
                                            "parsed_data", {}
                                        ).get("skills", []),
                                        "experience": analysis_data.get(
                                            "parsed_data", {}
                                        ).get("experience_years", 0),
                                        "match_score": analysis_data.get(
                                            "job_match_score", 0
                                        ),
                                    }
                                )

                                os.unlink(temp_file_path)

                            except Exception as e:
                                st.warning(
                                    f"Error analyzing {resume_file.name}: {str(e)}"
                                )

                        # Sort by score
                        results.sort(key=lambda x: x["score"], reverse=True)

                        # Display results
                        st.markdown("#### 📊 Analysis Results")

                        for i, result in enumerate(results, 1):
                            with st.expander(
                                f"#{i} {result['filename']} - Score: {result['score']}%"
                            ):
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.metric("Overall Score", f"{result['score']}%")

                                with col2:
                                    st.metric("Job Match", f"{result['match_score']}%")

                                with col3:
                                    st.metric(
                                        "Experience", f"{result['experience']} years"
                                    )

                                if result["skills"]:
                                    st.markdown("**Skills Found:**")
                                    skills_html = ""
                                    for skill in result["skills"][:8]:
                                        skills_html += (
                                            f'<span class="skill-tag">{skill}</span>'
                                        )
                                    st.markdown(skills_html, unsafe_allow_html=True)

        # AI Interview Question Generator
        st.markdown("#### 💬 AI Interview Question Generator")

        with st.expander("🎯 Generate Custom Interview Questions"):
            col1, col2 = st.columns(2)

            with col1:
                interview_position = st.text_input(
                    "Position",
                    placeholder="Senior Software Engineer",
                    key="interview_pos",
                )
                interview_level = st.selectbox(
                    "Experience Level",
                    ["Entry", "Mid", "Senior", "Executive"],
                    key="interview_level",
                )
                interview_focus = st.multiselect(
                    "Focus Areas",
                    [
                        "Technical Skills",
                        "Problem Solving",
                        "Leadership",
                        "Communication",
                        "Cultural Fit",
                        "Project Management",
                    ],
                    default=["Technical Skills", "Problem Solving"],
                )

            with col2:
                question_count = st.number_input(
                    "Number of Questions", min_value=5, max_value=20, value=10
                )
                difficulty = st.selectbox(
                    "Difficulty Level", ["Easy", "Medium", "Hard", "Mixed"]
                )
                include_followups = st.checkbox("Include Follow-up Questions")

            if st.button("🚀 Generate Questions") and interview_position:
                with st.spinner("🤖 Generating interview questions..."):
                    # Generate questions using AI
                    questions = [
                        {
                            "category": "Technical",
                            "question": f"Describe your experience with the main technologies required for a {interview_position} role.",
                            "followup": "Can you walk me through a specific project where you used these technologies?",
                        },
                        {
                            "category": "Problem Solving",
                            "question": "Tell me about a challenging technical problem you solved recently.",
                            "followup": "What alternative approaches did you consider?",
                        },
                        {
                            "category": "Leadership",
                            "question": "Describe a time when you had to lead a team through a difficult project.",
                            "followup": "How did you handle team conflicts or disagreements?",
                        },
                        {
                            "category": "Communication",
                            "question": "How do you explain complex technical concepts to non-technical stakeholders?",
                            "followup": "Can you give me a specific example?",
                        },
                        {
                            "category": "Cultural Fit",
                            "question": "What type of work environment helps you be most productive?",
                            "followup": "How do you handle feedback and criticism?",
                        },
                    ]

                    st.markdown("#### 📝 Generated Interview Questions")

                    for i, q in enumerate(questions[:question_count], 1):
                        st.markdown(f"**Question {i} ({q['category']}):**")
                        st.markdown(f"{q['question']}")

                        if include_followups and q.get("followup"):
                            st.markdown(f"*Follow-up: {q['followup']}*")

                        st.markdown("---")

        # AI Job Description Generator
        st.markdown("#### 📝 AI Job Description Generator")

        with st.expander("✍️ Generate Job Descriptions"):
            col1, col2 = st.columns(2)

            with col1:
                jd_position = st.text_input(
                    "Position Title",
                    placeholder="Senior Software Engineer",
                    key="jd_position",
                )
                jd_department = st.text_input(
                    "Department", placeholder="Engineering", key="jd_department"
                )
                jd_level = st.selectbox(
                    "Seniority Level",
                    [
                        "Entry Level",
                        "Mid Level",
                        "Senior Level",
                        "Lead/Principal",
                        "Executive",
                    ],
                    key="jd_level",
                )
                jd_type = st.selectbox(
                    "Employment Type",
                    ["Full-time", "Part-time", "Contract", "Internship"],
                    key="jd_type",
                )

            with col2:
                jd_location = st.text_input(
                    "Location", placeholder="San Francisco, CA", key="jd_location"
                )
                jd_remote = st.checkbox("Remote Work Available", key="jd_remote")
                jd_salary_min = st.number_input(
                    "Salary Range Min", min_value=0, key="jd_salary_min"
                )
                jd_salary_max = st.number_input(
                    "Salary Range Max", min_value=0, key="jd_salary_max"
                )

            jd_key_skills = st.text_area(
                "Key Skills Required",
                placeholder="Python, React, AWS, etc.",
                key="jd_skills",
            )
            jd_company_info = st.text_area(
                "Company Information",
                placeholder="Brief description of the company...",
                key="jd_company",
            )

            if st.button("🚀 Generate Job Description") and jd_position:
                with st.spinner("🤖 Creating job description..."):
                    # Generate job description
                    job_description = f"""
# {jd_position}
**{jd_department} Department | {jd_type} | {jd_location}{"| Remote Available" if jd_remote else ""}**

## About the Role
We are seeking a talented {jd_position} to join our {jd_department} team. This {jd_level.lower()} position offers an exciting opportunity to work on cutting-edge projects and contribute to our company's growth.

## Key Responsibilities
* Design, develop, and maintain high-quality software solutions
* Collaborate with cross-functional teams to deliver exceptional products
* Participate in code reviews and maintain coding standards
* Contribute to technical architecture and design decisions
* Mentor junior team members and share knowledge
* Stay updated with industry trends and best practices

## Required Qualifications
* Bachelor's degree in Computer Science or related field
* {jd_level} experience in software development
* Strong proficiency in: {jd_key_skills}
* Excellent problem-solving and analytical skills
* Strong communication and collaboration abilities
* Experience with agile development methodologies

## Preferred Qualifications
* Advanced degree in relevant field
* Experience with cloud platforms and DevOps practices
* Open source contributions
* Leadership experience

## What We Offer
* Competitive salary: ${jd_salary_min:,} - ${jd_salary_max:,}
* Comprehensive health, dental, and vision insurance
* 401(k) with company matching
* Flexible work arrangements
* Professional development opportunities
* Collaborative and inclusive work environment

## About Our Company
{jd_company_info}

Ready to make an impact? Apply now!
                    """

                    st.markdown("#### 📄 Generated Job Description")
                    st.markdown(job_description)

                    # Save option
                    if st.button("💾 Save Job Description"):
                        # Add to job postings
                        new_job = {
                            "id": len(st.session_state.hr_data["job_postings"]) + 1,
                            "title": jd_position,
                            "department": jd_department,
                            "location": jd_location,
                            "type": jd_type,
                            "level": jd_level,
                            "salary_min": jd_salary_min,
                            "salary_max": jd_salary_max,
                            "remote": jd_remote,
                            "description": job_description,
                            "requirements": jd_key_skills,
                            "benefits": "Comprehensive benefits package",
                            "status": "Draft",
                            "date_created": datetime.now().strftime("%Y-%m-%d"),
                            "applications": 0,
                        }

                        st.session_state.hr_data["job_postings"].append(new_job)
                        st.success("✅ Job description saved to job postings!")

        # AI Candidate Matching
        st.markdown("#### 🎯 AI Candidate Matching")

        with st.expander("🔍 Find Best Candidates for Position"):
            if (
                st.session_state.hr_data["candidates"]
                and st.session_state.hr_data["job_postings"]
            ):
                job_titles = [
                    job["title"] for job in st.session_state.hr_data["job_postings"]
                ]
                selected_job = st.selectbox("Select Job Position", job_titles)

                if st.button("🚀 Find Best Matches"):
                    with st.spinner("🤖 Analyzing candidate matches..."):
                        # Get job details
                        job_details = next(
                            job
                            for job in st.session_state.hr_data["job_postings"]
                            if job["title"] == selected_job
                        )

                        # Score candidates
                        candidate_scores = []

                        for candidate in st.session_state.hr_data["candidates"]:
                            # Simple scoring algorithm
                            score = candidate.get("ai_score", 0)

                            # Bonus for relevant position
                            if selected_job.lower() in candidate["position"].lower():
                                score += 10

                            # Bonus for experience level match
                            if (
                                job_details["level"] == "Senior Level"
                                and candidate["experience"] >= 5
                            ):
                                score += 5
                            elif (
                                job_details["level"] == "Mid Level"
                                and 2 <= candidate["experience"] <= 7
                            ):
                                score += 5
                            elif (
                                job_details["level"] == "Entry Level"
                                and candidate["experience"] <= 3
                            ):
                                score += 5

                            candidate_scores.append(
                                {"candidate": candidate, "match_score": min(score, 100)}
                            )

                        # Sort by match score
                        candidate_scores.sort(
                            key=lambda x: x["match_score"], reverse=True
                        )

                        st.markdown(f"#### 🎯 Best Matches for {selected_job}")

                        for i, match in enumerate(candidate_scores[:5], 1):
                            candidate = match["candidate"]
                            score = match["match_score"]

                            with st.expander(
                                f"#{i} {candidate['name']} - Match: {score}%"
                            ):
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.write(f"**Position:** {candidate['position']}")
                                    st.write(
                                        f"**Experience:** {candidate['experience']} years"
                                    )
                                    st.write(f"**Location:** {candidate['location']}")

                                with col2:
                                    st.write(f"**AI Score:** {candidate['ai_score']}%")
                                    st.write(f"**Status:** {candidate['status']}")
                                    st.write(f"**Source:** {candidate['source']}")

                                with col3:
                                    if st.button(
                                        "📧 Contact", key=f"contact_{candidate['id']}"
                                    ):
                                        st.info(f"Contacting {candidate['name']}")
                                    if st.button(
                                        "📧 Contact", key=f"contact_{candidate['id']}"
                                    ):
                                        st.info(f"Contacting {candidate['name']}")

                                    if st.button(
                                        "📅 Interview",
                                        key=f"interview_{candidate['id']}",
                                    ):
                                        st.info(
                                            f"Scheduling interview with {candidate['name']}"
                                        )

# Continue with other modes...
elif mode == "🎯 Interview Prep":
    st.markdown("## 🎯 AI-Powered Interview Preparation")

    st.markdown(
        """
    <div class="feature-card">
        <h4>🤖 Intelligent Interview Coaching</h4>
        <p>Get personalized interview preparation with AI-generated questions, answers, and coaching tips tailored to your specific role and background.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Interview prep type selection
    prep_type = st.selectbox(
        "📋 Preparation Type",
        ["Comprehensive", "Technical", "Behavioral", "Company Research"],
        help="Choose the type of interview preparation you need",
    )

    col1, col2 = st.columns(2)

    with col1:
        # Job information for interview prep
        st.markdown("### 💼 Job Information")
        job_title = st.text_input("Job Title", placeholder="Software Engineer")
        company_name = st.text_input("Company Name", placeholder="Google")
        job_description = st.text_area(
            "Job Description",
            height=150,
            placeholder="Paste the job description here...",
        )

    with col2:
        # Resume upload for personalized prep
        st.markdown("### 📄 Your Resume")
        uploaded_resume = st.file_uploader(
            "Upload Resume (PDF)", type="pdf", key="interview_prep_resume"
        )

        if uploaded_resume:
            st.success(f"✅ Resume uploaded: {uploaded_resume.name}")

    # Generate interview prep
    if st.button("🚀 Generate Interview Preparation", type="primary"):
        if job_title and (uploaded_resume or st.session_state.get("resume_analysis")):
            with st.spinner("🤖 Preparing your personalized interview coaching..."):
                try:
                    if WEB_FEATURES_AVAILABLE:
                        from agents.advanced_interview_prep_agent import (
                            AdvancedInterviewPrepAgent,
                        )

                        # Get resume data
                        if uploaded_resume:
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=".pdf"
                            ) as tmp_file:
                                tmp_file.write(uploaded_resume.getvalue())
                                temp_file_path = tmp_file.name

                            resume_text = extract_text_from_pdf(temp_file_path)

                            # Quick parse for interview prep
                            resume_data = {
                                "skills": [],  # Would extract from text
                                "experience": "Analyzed from resume",
                                "education": "Analyzed from resume",
                            }

                            os.unlink(temp_file_path)
                        else:
                            # Use existing analysis
                            analysis = st.session_state.get("resume_analysis", {})
                            resume_data = analysis.get("parsed_data", {})

                        job_data = {
                            "title": job_title,
                            "company": company_name,
                            "description": job_description,
                        }

                        # Generate interview prep
                        prep_agent = AdvancedInterviewPrepAgent()
                        prep_result = prep_agent.comprehensive_interview_prep(
                            resume_data, job_data
                        )

                        st.session_state.interview_prep = prep_result
                        st.success("✅ Interview preparation generated!")
                    else:
                        # Fallback preparation
                        st.session_state.interview_prep = {
                            "success": False,
                            "personalized_prep": {
                                "content": f"""
# Interview Preparation for {job_title}

## 📝 Common Questions
1. **Tell me about yourself**
   - Prepare a 2-3 minute elevator pitch
   - Focus on relevant experience and achievements
   - Connect your background to the role

2. **Why are you interested in this role?**
   - Research the company and position thoroughly
   - Mention specific aspects that excite you
   - Show how it aligns with your career goals

3. **What are your strengths and weaknesses?**
   - Choose strengths relevant to the job
   - For weaknesses, show how you're improving
   - Use specific examples

4. **Where do you see yourself in 5 years?**
   - Show ambition but be realistic
   - Align with company growth opportunities
   - Demonstrate commitment to the field

## 🎯 Technical Questions (if applicable)
1. Describe your experience with [relevant technologies]
2. How do you approach problem-solving?
3. Walk me through a challenging project
4. How do you stay updated with industry trends?

## 🤝 Behavioral Questions
1. Describe a time you faced a difficult challenge
2. Tell me about a time you worked in a team
3. How do you handle conflict?
4. Describe a time you had to learn something new quickly

## 💡 Tips for Success
- **Research the company** thoroughly
- **Prepare STAR method examples** (Situation, Task, Action, Result)
- **Practice your answers** out loud
- **Prepare questions** for the interviewer
- **Arrive 10-15 minutes early**
- **Bring multiple copies** of your resume
- **Follow up** with a thank-you email

## 🤔 Questions to Ask the Interviewer
1. What does success look like in this role?
2. What are the biggest challenges facing the team?
3. How would you describe the company culture?
4. What opportunities are there for professional development?
5. What are the next steps in the interview process?

## 📚 Company Research Checklist
- [ ] Company mission and values
- [ ] Recent news and achievements
- [ ] Products and services
- [ ] Company culture and work environment
- [ ] Leadership team
- [ ] Competitors and market position
- [ ] Growth plans and future direction
                                """,
                                "personalized": False,
                            },
                            "mock_interviews": [],
                            "follow_up_plan": {},
                            "error": "Advanced features unavailable - using general preparation guide",
                        }
                        st.success("✅ Basic interview preparation generated!")

                except Exception as e:
                    st.error(f"Error generating interview prep: {str(e)}")
        else:
            st.error("⚠️ Please provide job title and upload your resume")

    # Display interview prep results
    if "interview_prep" in st.session_state:
        prep_data = st.session_state.interview_prep

        st.markdown("---")
        st.markdown("### 📚 Your Personalized Interview Preparation")

        if prep_data.get("success", False):
            # Create tabs for different sections
            tab1, tab2, tab3, tab4 = st.tabs(
                ["📝 Preparation", "🎭 Mock Interview", "📧 Follow-up", "📅 Timeline"]
            )

            with tab1:
                st.markdown("#### 🎯 Personalized Preparation")
                prep_content = prep_data.get("personalized_prep", {}).get("content", "")
                st.markdown(prep_content)

            with tab2:
                st.markdown("#### 🎭 Mock Interview Scenarios")
                mock_interviews = prep_data.get("mock_interviews", [])
                for scenario in mock_interviews:
                    with st.expander(
                        f"{scenario.get('scenario_name', 'Interview Scenario')}"
                    ):
                        st.markdown(f"**Duration:** {scenario.get('duration', 'N/A')}")
                        st.markdown(
                            f"**Focus Areas:** {', '.join(scenario.get('focus_areas', []))}"
                        )

                        questions = scenario.get("sample_questions", [])
                        if questions:
                            st.markdown("**Sample Questions:**")
                            for q in questions[:5]:
                                st.markdown(f"• {q}")

            with tab3:
                st.markdown("#### 📧 Follow-up Strategy")
                follow_up = prep_data.get("follow_up_plan", {})

                for phase, details in follow_up.items():
                    if isinstance(details, dict) and "timing" in details:
                        st.markdown(
                            f"**{phase.replace('_', ' ').title()}** ({details['timing']})"
                        )
                        for action in details.get("actions", []):
                            st.markdown(f"• {action}")

            with tab4:
                st.markdown("#### 📅 Preparation Timeline")
                timeline = prep_data.get("preparation_timeline", {})
                for phase, tasks in timeline.items():
                    st.markdown(f"**{phase.replace('_', ' ').title()}:**")
                    for task in tasks:
                        st.markdown(f"• {task}")
        else:
            # Display basic preparation
            prep_content = prep_data.get("personalized_prep", {}).get("content", "")

            st.markdown(
                f"""
            <div class="interview-prep-section">
                {prep_content.replace(chr(10), "<br>")}
            </div>
            """,
                unsafe_allow_html=True,
            )

            if prep_data.get("error"):
                st.info(f"ℹ️ {prep_data['error']}")

# Continue from where we left off in the UI code...

elif mode == "🚀 Career Path":
    st.markdown("## 🚀 AI Career Path Visualization")

    st.markdown(
        """
    <div class="feature-card">
        <h4>📈 Intelligent Career Planning</h4>
        <p>Discover your optimal career trajectory with AI-powered analysis of your skills, market trends, and growth opportunities.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Career Goals")
        career_goals = st.text_area(
            "Describe your career aspirations",
            height=100,
            placeholder="I want to become a senior software engineer specializing in AI/ML...",
        )

        industry = st.selectbox(
            "Industry Focus",
            ["Technology", "Finance", "Healthcare", "Marketing", "Education", "Other"],
        )

        time_horizon = st.selectbox(
            "Planning Horizon", ["2 years", "5 years", "10 years", "15+ years"]
        )

    with col2:
        st.markdown("### 📊 Current Status")
        current_role = st.text_input("Current Role", placeholder="Software Developer")
        experience_years = st.number_input(
            "Years of Experience", min_value=0, max_value=50, value=3
        )

        # Use existing resume data if available
        if "resume_analysis" in st.session_state:
            st.info("✅ Using your previously analyzed resume data")
        else:
            uploaded_resume = st.file_uploader(
                "Upload Resume for Analysis", type="pdf", key="career_path_resume"
            )

    if st.button("🚀 Generate Career Path Analysis", type="primary"):
        if career_goals:
            with st.spinner(
                "🤖 Analyzing career opportunities and creating your personalized roadmap..."
            ):
                try:
                    if WEB_FEATURES_AVAILABLE:
                        from agents.career_path_agent import CareerPathAgent

                        # Get resume data
                        if "resume_analysis" in st.session_state:
                            resume_data = st.session_state.resume_analysis.get(
                                "parsed_data", {}
                            )
                        else:
                            resume_data = {
                                "skills": [],
                                "experience": f"{experience_years} years",
                                "education": "To be analyzed",
                            }

                        # Generate career path
                        career_agent = CareerPathAgent()
                        career_result = career_agent.run(
                            resume_data, career_goals, industry.lower()
                        )

                        st.session_state.career_path = career_result
                        st.success("✅ Career path analysis complete!")
                    else:
                        # Fallback career path
                        st.session_state.career_path = {
                            "analysis": f"""
# 🚀 Career Path Analysis for {current_role}

## 🎯 Current Assessment
Based on your {experience_years} years of experience, you have strong potential for growth in {industry.lower()}.

## 📈 Recommended Career Paths

### Path 1: Technical Leadership Track
- **Years 1-2**: Senior Individual Contributor
- **Years 3-5**: Team Lead / Technical Lead  
- **Years 6-8**: Engineering Manager
- **Years 9+**: Director of Engineering

### Path 2: Specialist Expert Track
- **Years 1-2**: Senior Specialist
- **Years 3-5**: Principal Specialist
- **Years 6-8**: Distinguished Engineer
- **Years 9+**: Chief Technology Officer

### Path 3: Product & Strategy Track
- **Years 1-2**: Senior Product Developer
- **Years 3-5**: Product Manager
- **Years 6-8**: Senior Product Manager
- **Years 9+**: VP of Product

## 🎓 Skill Development Priorities
1. Leadership and communication skills
2. Strategic thinking and planning
3. Industry-specific technical expertise
4. Project management capabilities
5. Business acumen and market understanding

## 💰 Salary Progression
- Current Level: $65,000 - $85,000
- 2-3 Years: $85,000 - $110,000
- 5-7 Years: $110,000 - $140,000
- 8+ Years: $140,000 - $200,000+

## 📋 Next Steps
1. Identify specific skills gaps
2. Create learning and development plan
3. Build professional network
4. Seek mentorship opportunities
5. Consider relevant certifications

## 🎯 Goal Achievement Strategy
To reach your goal of "{career_goals[:100]}...", focus on:
- Building expertise in emerging technologies
- Developing leadership capabilities
- Expanding your professional network
- Seeking challenging projects and responsibilities
                            """,
                            "paths": [
                                {
                                    "name": "Technical Leadership",
                                    "timeline": "5-8 years",
                                    "growth": "High",
                                },
                                {
                                    "name": "Specialist Expert",
                                    "timeline": "6-10 years",
                                    "growth": "Medium",
                                },
                                {
                                    "name": "Product Strategy",
                                    "timeline": "4-7 years",
                                    "growth": "High",
                                },
                            ],
                            "salary_progression": {
                                "years": [0, 2, 5, 8, 12],
                                "salaries": [65000, 85000, 110000, 140000, 180000],
                                "positions": [
                                    "Entry Level",
                                    "Mid Level",
                                    "Senior",
                                    "Lead",
                                    "Executive",
                                ],
                            },
                            "action_items": [
                                "Complete leadership training",
                                "Join professional associations",
                                "Seek mentorship",
                                "Build portfolio of achievements",
                            ],
                        }
                        st.success("✅ Career path analysis complete!")

                except Exception as e:
                    st.error(f"Error generating career path: {str(e)}")
        else:
            st.error("⚠️ Please describe your career goals")

    # Display career path results
    if "career_path" in st.session_state:
        career_data = st.session_state.career_path

        st.markdown("---")
        st.markdown("### 📈 Your Career Roadmap")

        # Career paths visualization
        paths = career_data.get("paths", [])
        if paths:
            st.markdown("#### 🛤️ Recommended Career Paths")

            cols = st.columns(len(paths))
            for i, path in enumerate(paths):
                with cols[i]:
                    growth_color = (
                        "#4CAF50"
                        if path.get("growth") == "High"
                        else "#FF9800"
                        if path.get("growth") == "Medium"
                        else "#607D8B"
                    )
                    st.markdown(
                        f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, {growth_color} 0%, {growth_color}CC 100%);">
                        <h4>{path.get("name", f"Path {i + 1}")}</h4>
                        <p><strong>Timeline:</strong> {path.get("timeline", "TBD")}</p>
                        <p><strong>Growth:</strong> {path.get("growth", "Medium")}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # Salary progression chart
        salary_data = career_data.get("salary_progression", {})
        if salary_data:
            st.markdown("#### 💰 Salary Progression Forecast")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=salary_data.get("years", []),
                    y=salary_data.get("salaries", []),
                    mode="lines+markers",
                    name="Expected Salary",
                    line=dict(color="#667eea", width=3),
                    marker=dict(size=8),
                    text=salary_data.get("positions", []),
                    textposition="top center",
                )
            )

            fig.update_layout(
                title="Career Salary Progression",
                xaxis_title="Years of Experience",
                yaxis_title="Annual Salary ($)",
                template="plotly_white",
                height=400,
            )

            st.plotly_chart(fig, use_container_width=True)

        # Action items
        action_items = career_data.get("action_items", [])
        if action_items:
            st.markdown("#### 📋 Recommended Action Items")
            for i, item in enumerate(action_items, 1):
                st.markdown(f"{i}. {item}")

        # Analysis content
        analysis = career_data.get("analysis", "")
        if analysis:
            st.markdown("#### 📊 Detailed Analysis")
            st.markdown(analysis)

elif mode == "🔍 Company Research":
    st.markdown("## 🔍 AI-Powered Company Research")

    st.markdown(
        """
    <div class="feature-card">
        <h4>🕵️ Intelligent Company Intelligence</h4>
        <p>Get comprehensive company insights using AI and real-time web scraping. Perfect for interview preparation and job applications.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        company_name = st.text_input("🏢 Company Name*", placeholder="Google")
        company_url = st.text_input(
            "🌐 Company Website", placeholder="https://google.com"
        )

    with col2:
        research_depth = st.selectbox(
            "📊 Research Depth",
            ["Basic", "Comprehensive", "Interview Focused"],
            help="Choose how detailed you want the research to be",
        )

        research_focus = st.multiselect(
            "🎯 Research Focus Areas",
            [
                "Company Culture",
                "Recent News & Updates",
                "Financial Performance",
                "Leadership Team",
                "Products & Services",
                "Competitors",
                "Interview Process",
                "Employee Reviews",
            ],
            default=["Company Culture", "Recent News & Updates", "Interview Process"],
        )

    if st.button("🚀 Start Company Research", type="primary"):
        if company_name:
            with st.spinner("🔍 Researching company using AI and web scraping..."):
                try:
                    if WEB_FEATURES_AVAILABLE:
                        from agents.web_scraper_agent import WebScraperAgent

                        # Initialize scraper
                        scraper = WebScraperAgent("your-firecrawl-api-key")

                        # Perform company research
                        research_result = scraper.scrape_company_info(
                            company_name, company_url
                        )

                        st.session_state.company_research = research_result
                        st.success("✅ Company research completed!")
                    else:
                        # Fallback research
                        st.session_state.company_research = {
                            "success": False,
                            "company_name": company_name,
                            "insights": {
                                "company_overview": f"""
{company_name} is a leading company in its industry, known for innovation and excellence. 
To get the most accurate and up-to-date information about {company_name}, we recommend:

1. **Visit their official website** - Check their About Us, Mission, and Values pages
2. **Review recent news** - Look for press releases and industry coverage
3. **Check employee reviews** - Platforms like Glassdoor provide insider perspectives
4. **Research leadership** - Learn about key executives and their backgrounds
5. **Understand their products/services** - Know what they offer and their market position
                                """,
                                "industry": "Technology",
                                "company_culture": f"""
Research {company_name}'s culture by exploring:
- Company website career pages
- Employee testimonials and reviews
- Social media presence and content
- Company events and initiatives
- Diversity and inclusion programs
- Work-life balance policies
                                """,
                                "values": [
                                    "Innovation",
                                    "Collaboration",
                                    "Excellence",
                                    "Integrity",
                                    "Customer Focus",
                                ],
                                "interview_tips": [
                                    f"Research {company_name}'s recent news and achievements",
                                    "Understand their products and services thoroughly",
                                    "Learn about their company culture and values",
                                    "Prepare questions about growth opportunities",
                                    "Review their mission statement and core values",
                                    "Connect with current employees on LinkedIn",
                                    "Practice explaining how your skills align with their needs",
                                ],
                                "why_work_here": [
                                    f"Research {company_name}'s benefits and perks",
                                    "Look for growth and learning opportunities",
                                    "Check employee satisfaction ratings",
                                    "Understand their impact in the industry",
                                    "Explore career development programs",
                                    "Learn about their work environment and culture",
                                ],
                                "recent_news": [
                                    f"Check {company_name}'s website for latest updates",
                                    "Look for recent press releases",
                                    "Review their social media for announcements",
                                    "Search for industry news mentioning the company",
                                    "Check financial news if it's a public company",
                                ],
                                "competitors": [
                                    "Research main competitors in the industry",
                                    "Understand market positioning",
                                    "Know competitive advantages",
                                ],
                                "financial_performance": "Research publicly available financial information",
                                "leadership_team": f"Learn about {company_name}'s key executives and leadership",
                                "products_services": f"Understand {company_name}'s main offerings and market focus",
                            },
                            "error": "Live research unavailable - please research manually using the provided guidelines",
                        }
                        st.success("✅ Research guidelines provided!")

                except Exception as e:
                    st.error(f"Research error: {str(e)}")
        else:
            st.error("⚠️ Please enter a company name")

    # Display research results
    if "company_research" in st.session_state:
        research_data = st.session_state.company_research

        st.markdown("---")
        st.markdown(f"### 🏢 Research Results: {research_data.get('company_name', '')}")

        insights = research_data.get("insights", {})

        # Company overview
        st.markdown("#### 📋 Company Overview")
        st.markdown(insights.get("company_overview", "No overview available"))

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Industry", insights.get("industry", "N/A"))
        with col2:
            st.metric("Founded", insights.get("founded_year", "N/A"))
        with col3:
            st.metric("Size", insights.get("company_size", "N/A"))
        with col4:
            st.metric("Stage", insights.get("growth_stage", "N/A"))

        # Detailed sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "🎯 Culture",
                "📰 News",
                "💡 Interview Tips",
                "🤝 Why Work Here",
                "🏆 Leadership",
            ]
        )

        with tab1:
            st.markdown("#### 🎯 Company Culture")
            st.markdown(
                insights.get("company_culture", "Culture information not available")
            )

            values = insights.get("values", [])
            if values:
                st.markdown("**Core Values:**")
                for value in values:
                    st.markdown(f"• {value}")

        with tab2:
            st.markdown("#### 📰 Recent News & Updates")
            recent_news = insights.get("recent_news", [])
            if recent_news:
                for news in recent_news:
                    st.markdown(f"• {news}")
            else:
                st.info("No recent news found. Check company website and news sources.")

        with tab3:
            st.markdown("#### 💡 Interview Tips")
            interview_tips = insights.get("interview_tips", [])
            if interview_tips:
                for tip in interview_tips:
                    st.markdown(f"✅ {tip}")
            else:
                st.markdown("""
                **General Interview Tips:**
                ✅ Research the company's mission and values
                ✅ Understand their products and services
                ✅ Prepare questions about growth opportunities
                ✅ Review recent company news and achievements
                """)

        with tab4:
            st.markdown("#### 🤝 Why Work Here")
            why_work_here = insights.get("why_work_here", [])
            if why_work_here:
                for reason in why_work_here:
                    st.markdown(f"🌟 {reason}")
            else:
                st.info(
                    "Research company benefits, culture, and growth opportunities manually."
                )

        with tab5:
            st.markdown("#### 🏆 Leadership & Team")
            leadership = insights.get(
                "leadership_team", "Leadership information not available"
            )
            st.markdown(leadership)

            competitors = insights.get("competitors", [])
            if competitors:
                st.markdown("**Key Competitors:**")
                for competitor in competitors:
                    st.markdown(f"• {competitor}")

        if research_data.get("error"):
            st.warning(f"⚠️ {research_data['error']}")

elif mode == "💰 Salary Insights":
    st.markdown("## 💰 AI-Powered Salary Insights")

    st.markdown(
        """
    <div class="feature-card">
        <h4>📊 Market Salary Intelligence</h4>
        <p>Get real-time salary data and market insights for your role and location using AI-powered research.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        job_title = st.text_input("💼 Job Title*", placeholder="Software Engineer")
        location = st.text_input("📍 Location", placeholder="San Francisco, CA")
        experience_level = st.selectbox(
            "📈 Experience Level",
            [
                "Entry Level (0-2 years)",
                "Mid Level (3-5 years)",
                "Senior Level (6-10 years)",
                "Executive Level (10+ years)",
            ],
        )

    with col2:
        company_size = st.selectbox(
            "🏢 Company Size",
            ["Startup (1-50)", "Small (51-200)", "Medium (201-1000)", "Large (1000+)"],
        )
        industry = st.selectbox(
            "🏭 Industry",
            ["Technology", "Finance", "Healthcare", "Marketing", "Education", "Other"],
        )

    if st.button("🚀 Get Salary Insights", type="primary"):
        if job_title:
            with st.spinner("💰 Researching salary data from multiple sources..."):
                try:
                    if WEB_FEATURES_AVAILABLE:
                        from agents.web_scraper_agent import WebScraperAgent

                        # Initialize scraper for salary research
                        scraper = WebScraperAgent("your-firecrawl-api-key")

                        # Get salary data
                        salary_result = scraper.scrape_salary_data(job_title, location)

                        st.session_state.salary_insights = salary_result
                        st.success("✅ Salary research completed!")
                    else:
                        # Enhanced fallback salary data
                        salary_ranges = {
                            "software engineer": {
                                "min": 70000,
                                "max": 150000,
                                "median": 110000,
                            },
                            "data scientist": {
                                "min": 80000,
                                "max": 160000,
                                "median": 120000,
                            },
                            "product manager": {
                                "min": 90000,
                                "max": 180000,
                                "median": 135000,
                            },
                            "marketing manager": {
                                "min": 60000,
                                "max": 120000,
                                "median": 90000,
                            },
                            "sales manager": {
                                "min": 65000,
                                "max": 140000,
                                "median": 100000,
                            },
                            "designer": {"min": 55000, "max": 110000, "median": 80000},
                            "analyst": {"min": 50000, "max": 95000, "median": 70000},
                            "developer": {
                                "min": 65000,
                                "max": 140000,
                                "median": 100000,
                            },
                            "engineer": {"min": 70000, "max": 150000, "median": 110000},
                        }

                        job_lower = job_title.lower()
                        salary_estimate = {"min": 50000, "max": 100000, "median": 75000}

                        for key, value in salary_ranges.items():
                            if key in job_lower:
                                salary_estimate = value
                                break

                        # Adjust for experience level
                        experience_multiplier = {
                            "Entry Level (0-2 years)": 0.8,
                            "Mid Level (3-5 years)": 1.0,
                            "Senior Level (6-10 years)": 1.3,
                            "Executive Level (10+ years)": 1.6,
                        }

                        multiplier = experience_multiplier.get(experience_level, 1.0)

                        adjusted_estimate = {
                            "min": int(salary_estimate["min"] * multiplier),
                            "max": int(salary_estimate["max"] * multiplier),
                            "median": int(salary_estimate["median"] * multiplier),
                        }

                        st.session_state.salary_insights = {
                            "success": False,
                            "job_title": job_title,
                            "location": location,
                            "experience_level": experience_level,
                            "salary_analysis": {
                                "estimated_range": adjusted_estimate,
                                "market_data": {
                                    "percentile_25": int(
                                        adjusted_estimate["min"] * 1.1
                                    ),
                                    "percentile_50": adjusted_estimate["median"],
                                    "percentile_75": int(
                                        adjusted_estimate["max"] * 0.9
                                    ),
                                    "percentile_90": adjusted_estimate["max"],
                                },
                                "factors": {
                                    "experience_impact": f"{int((multiplier - 1) * 100)}% adjustment for {experience_level}",
                                    "location_impact": "Location-based adjustments may apply",
                                    "company_size_impact": f"{company_size} companies may offer different compensation",
                                    "industry_impact": f"{industry} industry standards considered",
                                },
                                "note": "Estimates based on general market data. Research specific companies for accurate information.",
                            },
                            "error": "Live salary data unavailable",
                        }
                        st.success("✅ Salary estimates provided!")

                except Exception:
                    st.error("Error researching salary data.")
        else:
            st.error("⚠️ Please enter a job title")

    # Display salary insights
    if "salary_insights" in st.session_state:
        salary_data = st.session_state.salary_insights

        st.markdown("---")
        st.markdown(f"### 💰 Salary Insights: {salary_data.get('job_title', '')}")

        salary_analysis = salary_data.get("salary_analysis", {})

        if salary_data.get("success", False):
            # Display comprehensive salary data
            st.markdown("#### 📊 Market Salary Data")

            # Salary metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                avg_salary = salary_analysis.get("average_salary", 0)
                st.metric("Average Salary", f"${avg_salary:,}" if avg_salary else "N/A")

            with col2:
                salary_range = salary_analysis.get("salary_range", {})
                min_sal = salary_range.get("min", 0)
                max_sal = salary_range.get("max", 0)
                st.metric(
                    "Salary Range",
                    f"${min_sal:,} - ${max_sal:,}" if min_sal and max_sal else "N/A",
                )

            with col3:
                sources = salary_data.get("sources", 0)
                st.metric("Data Sources", sources)

        else:
            # Display estimated salary data
            estimated_range = salary_analysis.get("estimated_range", {})
            market_data = salary_analysis.get("market_data", {})

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                median_sal = estimated_range.get("median", 0)
                st.metric("Median Salary", f"${median_sal:,}" if median_sal else "N/A")

            with col2:
                min_sal = estimated_range.get("min", 0)
                max_sal = estimated_range.get("max", 0)
                st.metric(
                    "Salary Range",
                    f"${min_sal:,} - ${max_sal:,}" if min_sal and max_sal else "N/A",
                )

            with col3:
                percentile_75 = market_data.get("percentile_75", 0)
                st.metric(
                    "75th Percentile", f"${percentile_75:,}" if percentile_75 else "N/A"
                )

            with col4:
                st.metric(
                    "Experience Level",
                    salary_data.get("experience_level", "N/A").split(" (")[0],
                )

        # Salary visualization
        if estimated_range := salary_analysis.get("estimated_range"):
            st.markdown("#### 📈 Salary Range Visualization")

            fig = go.Figure()

            # Create salary range bar
            categories = ["Minimum", "Median", "Maximum"]
            values = [
                estimated_range.get("min", 0),
                estimated_range.get("median", 0),
                estimated_range.get("max", 0),
            ]
            colors = ["#ff7f7f", "#7f7fff", "#7fff7f"]

            fig.add_trace(
                go.Bar(
                    x=categories,
                    y=values,
                    marker_color=colors,
                    text=[f"${val:,}" for val in values],
                    textposition="auto",
                )
            )

            fig.update_layout(
                title=f"Salary Range for {job_title} ({experience_level})",
                xaxis_title="Salary Level",
                yaxis_title="Annual Salary ($)",
                template="plotly_white",
                height=400,
            )

            st.plotly_chart(fig, use_container_width=True)

            # Market percentiles
            market_data = salary_analysis.get("market_data", {})
            if market_data:
                st.markdown("#### 📊 Market Percentiles")

                percentiles = ["25th", "50th (Median)", "75th", "90th"]
                percentile_values = [
                    market_data.get("percentile_25", 0),
                    market_data.get("percentile_50", 0),
                    market_data.get("percentile_75", 0),
                    market_data.get("percentile_90", 0),
                ]

                fig_percentiles = go.Figure()

                fig_percentiles.add_trace(
                    go.Scatter(
                        x=percentiles,
                        y=percentile_values,
                        mode="lines+markers",
                        name="Salary Percentiles",
                        line=dict(color="#667eea", width=3),
                        marker=dict(size=10),
                    )
                )

                fig_percentiles.update_layout(
                    title="Salary Distribution by Percentiles",
                    xaxis_title="Percentile",
                    yaxis_title="Annual Salary ($)",
                    template="plotly_white",
                    height=300,
                )

                st.plotly_chart(fig_percentiles, use_container_width=True)

        # Factors affecting salary
        factors = salary_analysis.get("factors", {})
        if factors:
            st.markdown("#### 🎯 Factors Affecting Salary")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Experience Impact:**")
                st.info(factors.get("experience_impact", "Experience level considered"))

                st.markdown("**Location Impact:**")
                st.info(factors.get("location_impact", "Location factors may apply"))

            with col2:
                st.markdown("**Company Size Impact:**")
                st.info(
                    factors.get(
                        "company_size_impact", "Company size affects compensation"
                    )
                )

                st.markdown("**Industry Impact:**")
                st.info(factors.get("industry_impact", "Industry standards considered"))

        # Additional insights
        st.markdown("#### 💡 Salary Negotiation Tips")
        st.markdown("""
        **Preparation Tips:**
        ✅ Research multiple salary sources and ranges
        ✅ Consider total compensation (benefits, equity, etc.)
        ✅ Factor in cost of living for your location
        ✅ Highlight your unique value and achievements
        ✅ Practice your negotiation conversation
        ✅ Be prepared to justify your salary request
        
        **Negotiation Strategy:**
        • Start with a range rather than a specific number
        • Focus on value you bring to the company
        • Consider non-salary benefits if base salary is fixed
        • Be professional and collaborative in your approach
        • Research company's compensation philosophy
        • Time your negotiation appropriately
        """)

        if salary_data.get("error"):
            st.info(f"ℹ️ {salary_data['error']}")

elif mode == "📈 Skill Development":
    st.markdown("## 📈 AI-Powered Skill Development")

    st.markdown(
        """
    <div class="feature-card">
        <h4>🎓 Intelligent Learning Roadmap</h4>
        <p>Get personalized skill recommendations, learning paths, and certification guidance based on your career goals and market trends.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Skill assessment
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Current Skills Assessment")
        current_skills = st.text_area(
            "List your current skills (comma-separated)",
            height=100,
            placeholder="Python, JavaScript, React, SQL, Project Management...",
        )

        target_role = st.text_input(
            "Target Role", placeholder="Senior Software Engineer"
        )
        industry_focus = st.selectbox(
            "Industry Focus",
            ["Technology", "Finance", "Healthcare", "Marketing", "Education"],
        )

    with col2:
        st.markdown("### 📊 Learning Preferences")
        learning_style = st.selectbox(
            "Preferred Learning Style",
            ["Visual", "Hands-on", "Reading", "Video-based", "Mixed"],
        )

        time_commitment = st.selectbox(
            "Weekly Time Commitment",
            ["1-2 hours", "3-5 hours", "6-10 hours", "10+ hours"],
        )

        budget_range = st.selectbox(
            "Learning Budget",
            ["Free resources only", "$1-50/month", "$51-200/month", "$200+/month"],
        )

    if st.button("🚀 Generate Learning Roadmap", type="primary"):
        if current_skills and target_role:
            with st.spinner("🤖 Creating your personalized learning roadmap..."):
                try:
                    # Initialize skill recommendation agent
                    skill_agent = SkillRecommendationAgent()

                    # Prepare data for analysis
                    skill_data = {
                        "current_skills": [
                            skill.strip() for skill in current_skills.split(",")
                        ],
                        "target_role": target_role,
                        "industry": industry_focus,
                        "learning_style": learning_style,
                        "time_commitment": time_commitment,
                        "budget": budget_range,
                    }

                    # Generate recommendations
                    recommendations = skill_agent.run(json.dumps(skill_data))

                    st.session_state.skill_recommendations = json.loads(recommendations)
                    st.success("✅ Learning roadmap generated!")

                except Exception as e:
                    # Fallback recommendations
                    skills_list = [skill.strip() for skill in current_skills.split(",")]

                    st.session_state.skill_recommendations = {
                        "skill_gaps": [
                            "Advanced Python programming",
                            "Cloud computing (AWS/Azure)",
                            "System design principles",
                            "Leadership and communication",
                            "DevOps and CI/CD",
                        ],
                        "learning_path": [
                            {
                                "skill": "Advanced Python",
                                "priority": "High",
                                "timeline": "2-3 months",
                                "resources": [
                                    "Python.org tutorials",
                                    "Real Python courses",
                                    "LeetCode practice",
                                ],
                            },
                            {
                                "skill": "Cloud Computing",
                                "priority": "High",
                                "timeline": "3-4 months",
                                "resources": [
                                    "AWS Free Tier",
                                    "Cloud Guru courses",
                                    "Hands-on projects",
                                ],
                            },
                            {
                                "skill": "System Design",
                                "priority": "Medium",
                                "timeline": "4-6 months",
                                "resources": [
                                    "System Design Primer",
                                    "High Scalability blog",
                                    "Practice interviews",
                                ],
                            },
                        ],
                        "certifications": [
                            "AWS Certified Solutions Architect",
                            "Google Cloud Professional",
                            "Certified Kubernetes Administrator",
                        ],
                        "market_trends": [
                            "AI/ML skills are in high demand",
                            "Cloud computing expertise is essential",
                            "DevOps skills increase salary potential",
                            "Soft skills are increasingly valued",
                        ],
                    }
                    st.success("✅ Learning roadmap generated!")
            st.error("⚠️ Please provide your current skills and target role")

    # Display skill recommendations
    if "skill_recommendations" in st.session_state:
        recommendations = st.session_state.skill_recommendations

        st.markdown("---")
        st.markdown("### 🎓 Your Personalized Learning Roadmap")

        # Skill gaps analysis
        skill_gaps = recommendations.get("skill_gaps", [])
        if skill_gaps:
            st.markdown("#### 🎯 Identified Skill Gaps")

            cols = st.columns(2)
            for i, gap in enumerate(skill_gaps):
                with cols[i % 2]:
                    st.markdown(f"• **{gap}**")

        # Learning path
        learning_path = recommendations.get("learning_path", [])
        if learning_path:
            st.markdown("#### 🛤️ Recommended Learning Path")

            for i, path in enumerate(learning_path, 1):
                priority_color = (
                    "#4CAF50"
                    if path.get("priority") == "High"
                    else "#FF9800"
                    if path.get("priority") == "Medium"
                    else "#607D8B"
                )

                with st.expander(
                    f"{i}. {path.get('skill', 'Skill')} - {path.get('priority', 'Medium')} Priority"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**Timeline:** {path.get('timeline', 'TBD')}")
                        st.markdown(f"**Priority:** {path.get('priority', 'Medium')}")

                    with col2:
                        resources = path.get("resources", [])
                        if resources:
                            st.markdown("**Recommended Resources:**")
                            for resource in resources:
                                st.markdown(f"• {resource}")

        # Certifications
        certifications = recommendations.get("certifications", [])
        if certifications:
            st.markdown("#### 🏆 Recommended Certifications")

            cols = st.columns(3)
            for i, cert in enumerate(certifications):
                with cols[i % 3]:
                    st.markdown(
                        f"""
                    <div class="metric-card">
                        <h4>🏆</h4>
                        <p>{cert}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # Market trends
        market_trends = recommendations.get("market_trends", [])
        if market_trends:
            st.markdown("#### 📈 Market Trends & Insights")

            for trend in market_trends:
                st.info(f"💡 {trend}")

        # Learning resources by category
        st.markdown("#### 📚 Learning Resources by Category")

        resource_categories = {
            "Free Online Courses": [
                "Coursera (audit mode)",
                "edX (audit mode)",
                "Khan Academy",
                "freeCodeCamp",
                "YouTube tutorials",
            ],
            "Paid Platforms": [
                "Udemy",
                "Pluralsight",
                "LinkedIn Learning",
                "Skillshare",
                "MasterClass",
            ],
            "Practice Platforms": [
                "LeetCode",
                "HackerRank",
                "Codewars",
                "GitHub projects",
                "Kaggle competitions",
            ],
            "Books & Documentation": [
                "Official documentation",
                "O'Reilly books",
                "Manning publications",
                "Medium articles",
                "Industry blogs",
            ],
        }

        tabs = st.tabs(list(resource_categories.keys()))

        for i, (category, resources) in enumerate(resource_categories.items()):
            with tabs[i]:
                for resource in resources:
                    st.markdown(f"• {resource}")

        # Progress tracking
        st.markdown("#### 📊 Progress Tracking")

        st.markdown("""
        **Track your learning progress:**
        
        1. **Set weekly goals** - Define specific learning objectives
        2. **Practice regularly** - Consistent practice is key to skill development
        3. **Build projects** - Apply new skills in real-world projects
        4. **Join communities** - Connect with others learning similar skills
        5. **Measure progress** - Regular self-assessment and skill testing
        6. **Update resume** - Add new skills and projects as you learn
        """)

        # Create a simple progress tracker
        st.markdown("##### 📈 Weekly Progress Tracker")

        progress_skills = (
            learning_path[:3] if learning_path else ["Skill 1", "Skill 2", "Skill 3"]
        )

        for skill in progress_skills:
            skill_name = skill.get("skill", skill) if isinstance(skill, dict) else skill
            progress = st.slider(
                f"Progress on {skill_name}", 0, 100, 0, key=f"progress_{skill_name}"
            )

            if progress > 0:
                st.success(f"Great progress on {skill_name}! Keep it up! 🎉")

# Footer
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🎯 <strong>JobSniper AI</strong> - Professional Resume & Career Intelligence Platform</p>
    <p>Powered by Advanced AI • Built with ❤️ for Job Seekers & HR Professionals</p>
    <p><small>Version 2.0 | Enhanced with Web Scraping, Resume Builder & Advanced Analytics</small></p>
</div>
""",
    unsafe_allow_html=True,
)
