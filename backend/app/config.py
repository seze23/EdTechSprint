import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
DRAFT_MODEL = os.getenv("DRAFT_MODEL", "claude-haiku-5-5")
N_DRAFTS = int(os.getenv("N_DRAFTS", "4"))
DRAFT_TEMPERATURE = float(os.getenv("DRAFT_TEMPERATURE", "0.9"))
DB_PATH = Path(os.getenv("DB_PATH", str(ROOT / "backend" / "data" / "edtech.db")))
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()   # postgresql://... switches the log store to Supabase
STRIPE_PAYMENT_LINK = os.getenv("STRIPE_PAYMENT_LINK", "https://buy.stripe.com/test_placeholder")
MOCK_MODE = ANTHROPIC_API_KEY == ""
