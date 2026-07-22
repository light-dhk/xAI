# run_app.py
import os
import sys
from streamlit.web import cli as stcli

def resource_path(relative_path):
    """PyInstaller onefile 모드에서도 경로를 올바르게 찾기 위한 함수"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    target_script = resource_path("xAIPM.py")

    sys.argv = [
        "streamlit",
        "run",
        target_script,
        "--global.developmentMode=false",
        "--server.headless=false",
        "--browser.gatherUsageStats=false",
    ]
    sys.exit(stcli.main())