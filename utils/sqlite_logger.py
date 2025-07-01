import sqlite3
import datetime
import logging


def init_db():
    """Initialize the database with a more comprehensive schema"""
    try:
        conn = sqlite3.connect("history.db")
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS resume_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            name TEXT,
            skills TEXT,
            education TEXT,
            experience TEXT,
            match_percent INTEGER,
            job_title TEXT,
            feedback_summary TEXT,
            suggested_jobs TEXT
        )""")
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Database initialization error: {e}")


def save_to_db(parsed_data, match_result):
    """Save resume analysis results to database with improved error handling"""
    try:
        conn = sqlite3.connect("history.db")
        c = conn.cursor()

        # Handle missing fields with defaults
        name = parsed_data.get("name", "Unknown")
        skills = parsed_data.get("skills", [])
        skills_str = ",".join(skills) if isinstance(skills, list) else str(skills)
        education = parsed_data.get("education", "Unknown")
        experience = parsed_data.get("experience", "Unknown")

        # Handle match result with defaults
        match_percent = 0
        if isinstance(match_result, dict):
            match_percent = match_result.get("match_percent", 0)

            # Store additional match information
            suggested_jobs = ",".join(match_result.get("job_roles", []))
        else:
            suggested_jobs = ""

        c.execute(
            """
            INSERT INTO resume_logs 
            (timestamp, name, skills, education, experience, match_percent, suggested_jobs) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.datetime.now().isoformat(),
                name,
                skills_str,
                education,
                experience,
                match_percent,
                suggested_jobs,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving to database: {e}")
    except Exception as e:
        logging.error(f"Error saving to database: {e}")


def get_history(limit=10):
    """Retrieve resume analysis history with improved error handling"""
    try:
        conn = sqlite3.connect("history.db")
        c = conn.cursor()
        c.execute("SELECT * FROM resume_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logging.error(f"Error retrieving history: {e}")
        return []


def get_resume_details(resume_id):
    """Get detailed information for a specific resume analysis"""
    try:
        conn = sqlite3.connect("history.db")
        c = conn.cursor()
        c.execute("SELECT * FROM resume_logs WHERE id = ?", (resume_id,))
        row = c.fetchone()
        conn.close()

        if row:
            # Convert row to dictionary for easier access
            columns = [
                "id",
                "timestamp",
                "name",
                "skills",
                "education",
                "experience",
                "match_percent",
                "job_title",
                "feedback_summary",
                "suggested_jobs",
            ]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        logging.error(f"Error retrieving resume details: {e}")
        return None


def log_interaction(agent_name, action, input_data, output_data):
    """Log agent interactions for debugging and analysis"""
    try:
        conn = sqlite3.connect("history.db")
        c = conn.cursor()
        
        # Create interactions table if it doesn't exist
        c.execute("""CREATE TABLE IF NOT EXISTS agent_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            agent_name TEXT,
            action TEXT,
            input_data TEXT,
            output_data TEXT
        )""")
        
        # Insert the interaction log
        c.execute("""
            INSERT INTO agent_interactions 
            (timestamp, agent_name, action, input_data, output_data) 
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.datetime.now().isoformat(),
            agent_name,
            action,
            str(input_data)[:5000],  # Limit input data length
            str(output_data)[:5000]  # Limit output data length
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error logging interaction: {e}")
