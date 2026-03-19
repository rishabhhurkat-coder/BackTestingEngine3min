import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_PATH = BASE_DIR / "streamlit_app.py"

cmd = [sys.executable, "-m", "streamlit", "run", str(APP_PATH)]
subprocess.run(cmd, cwd=BASE_DIR)
