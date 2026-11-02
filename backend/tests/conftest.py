import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["ANTHROPIC_API_KEY"] = ""          # force mock mode
os.environ["DB_PATH"] = str(ROOT / "data" / "test.db")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "")   # set to run the suite against Supabase
