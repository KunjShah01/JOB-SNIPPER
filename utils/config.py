import os
from dotenv import load_dotenv
import dotenv

# Load environment variables
load_dotenv()

# Get configuration values
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
COOKIE_KEY = os.getenv("COOKIE_KEY")

# Email Configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Determine which AI provider to use
# Priority: Gemini > Mistral > Fallback Mode
GEMINI_AVAILABLE = (
    GEMINI_API_KEY
    and GEMINI_API_KEY != "your_actual_gemini_api_key_here"
    and GEMINI_API_KEY.strip() != ""
    and len(GEMINI_API_KEY.strip()) >= 30
    and GEMINI_API_KEY.startswith("AIza")
)

MISTRAL_AVAILABLE = (
    MISTRAL_API_KEY
    and MISTRAL_API_KEY != "your_actual_mistral_api_key_here"
    and MISTRAL_API_KEY.strip() != ""
    and len(MISTRAL_API_KEY.strip()) >= 20
)

# Email availability check
EMAIL_AVAILABLE = (
    SENDER_EMAIL
    and SENDER_PASSWORD
    and SENDER_EMAIL != "your_gmail@gmail.com"
    and SENDER_PASSWORD != "your_app_password"
    and SENDER_EMAIL.strip() != ""
    and SENDER_PASSWORD.strip() != ""
)

# Set AI provider priority
if GEMINI_AVAILABLE:
    AI_PROVIDER = "gemini"
elif MISTRAL_AVAILABLE:
    AI_PROVIDER = "mistral"
else:
    AI_PROVIDER = "fallback"


def update_email_config(email, password):
    """Updates the email configuration in the .env file"""
    dotenv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

    # Update the .env file
    dotenv.set_key(dotenv_file, "SENDER_EMAIL", email)
    dotenv.set_key(dotenv_file, "SENDER_PASSWORD", password)

    # Also update the global variables
    global SENDER_EMAIL, SENDER_PASSWORD, EMAIL_AVAILABLE
    SENDER_EMAIL = email
    SENDER_PASSWORD = password

    # Check if email is now configured
    EMAIL_AVAILABLE = (
        SENDER_EMAIL
        and SENDER_PASSWORD
        and SENDER_EMAIL != "your_gmail@gmail.com"
        and SENDER_PASSWORD != "your_app_password"
        and SENDER_EMAIL.strip() != ""
        and SENDER_PASSWORD.strip() != ""
    )

    return EMAIL_AVAILABLE


# Explicitly define what's available for import
__all__ = [
    "GEMINI_API_KEY",
    "MISTRAL_API_KEY",
    "COOKIE_KEY",
    "SENDER_EMAIL",
    "SENDER_PASSWORD",
    "SMTP_SERVER",
    "SMTP_PORT",
    "GEMINI_AVAILABLE",
    "MISTRAL_AVAILABLE",
    "EMAIL_AVAILABLE",
    "AI_PROVIDER",
    "update_email_config",
]
