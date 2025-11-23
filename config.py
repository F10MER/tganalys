import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# AI Provider Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai, openrouter, agentrouter

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

# AgentRouter Configuration
AGENTROUTER_API_KEY = os.getenv("AGENTROUTER_API_KEY")

# Whisper API URL
WHISPER_API_URL = os.getenv("WHISPER_API_URL", "http://whisper:9000")

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Admin User IDs
ADMIN_USER_IDS = [
    int(user_id) for user_id in os.getenv("ADMIN_USER_IDS", "").split(",") if user_id
]

# Validate required environment variables
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")

# Validate AI provider configuration
if AI_PROVIDER == "openai" and not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set for OpenAI provider")

if AI_PROVIDER == "openrouter" and not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set for OpenRouter provider")

if AI_PROVIDER == "agentrouter" and not AGENTROUTER_API_KEY:
    raise ValueError("AGENTROUTER_API_KEY is not set for AgentRouter provider")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")
