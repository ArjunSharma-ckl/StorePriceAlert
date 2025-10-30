#!/usr/bin/env python3
"""
Run the DealScout application.
This script ensures proper Python path setup before launching the Streamlit app.
"""
import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.absolute()

# Add the project root to the Python path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set the working directory to the project root
os.chdir(project_root)

# Print debug information
print(f"Project root: {project_root}")
print(f"Python path: {sys.path}")

# Run the Streamlit app
if __name__ == "__main__":
    # Simple approach - let Streamlit handle the rest
    os.system(f"streamlit run {project_root}/code/main.py")
    
    # Alternative approach if the above doesn't work
    # import subprocess
    # subprocess.run(["streamlit", "run", "code/main.py"], cwd=project_root)
