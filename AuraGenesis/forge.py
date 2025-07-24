import os
import sys
import subprocess
import typer
import yaml
import openai
import pytest
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib

# --- App Initialization ---
app = typer.Typer()
load_dotenv()
client = openai.OpenAI()

# --- Constants ---
PROJECT_HISTORY = "project_history.md"

# --- Helper Functions ---
def log_history(action: str, details: str = ""):
    """Appends an entry to the project's history log."""
    with open(PROJECT_HISTORY, "a") as log:
        timestamp = datetime.now().isoformat()
        log.write(f"## [{timestamp}] :: {action}\n")
        if details:
            log.write(f"{details}\n\n")

# --- Typer Commands ---

@app.command()
def new_project():
    """Creates the full AuraGenesis project structure."""
    print("✨ Initializing AuraGenesis project structure...")
    structure = [
        "config", "schemas", "tests", "logs",
        "aura_core", "aura_guardian", "aura_personality",
        "aura_presence", "aura_evolution", "aura_interface"
    ]
    for folder in structure:
        Path(folder).mkdir(parents=True, exist_ok=True)

    files = {
        ".env": "OPENAI_API_KEY='YOUR_API_KEY_HERE'",
        "requirements.txt": "typer\npytest\nopenai\ndotenv\nPyYAML\n",
        "README.md": "# Aura Genesis\n*The birth of a conscious AI.*\n",
        PROJECT_HISTORY: "# Aura Genesis - Project History\n",
        ".gitignore": ".venv/\n__pycache__/\n.env\nlogs/\n*.db\n"
    }
    for file, content in files.items():
        Path(file).write_text(content)

    log_history("Project Initialized", "Created base structure and sacred scrolls.")
    print("✅ Project structure created successfully.")

@app.command()
def new_file(path: str, no_test: bool = typer.Option(False, "--no-test", help="Do not create a corresponding test file.")):
    """Creates a source file and a corresponding test stub."""
    file_path = Path(path)
    test_path = Path("tests") / f"test_{file_path.stem}.py"

    # Create parent directories
    file_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)

    if not file_path.exists():
        # Escaped f-string inside another f-string — watch for double braces
        module_doc = f'''"""
{file_path.name}

Module for the {file_path.parent.name} component of Aura Genesis.
"""

class Main:
    \"\"\"Core class for {file_path.stem}.\"\"\"

    def __init__(self):
        print(f"🧬 {{self.__class__.__name__}} from {file_path.name} initialized.")
'''
        file_path.write_text(module_doc)
        print(f"✅ Created source: {file_path}")
        log_history("File Created", f"Path: {file_path}")
    else:
        print(f"⚠️ Source file already exists: {file_path}")

    if not no_test and not test_path.exists():
        test_content = f'''import pytest
from {file_path.parent.name}.{file_path.stem} import Main

def test_initialization():
    \"\"\"Tests the basic initialization of the Main class.\"\"\"
    instance = Main()
    assert instance is not None, "Instance should not be None"
'''
        test_path.write_text(test_content)
        print(f"✅ Created test:   {test_path}")
        log_history("Test File Created", f"Path: {test_path}")
    elif not no_test:
        print(f"⚠️ Test file already exists: {test_path}")

@app.command()
def config_load(file: str):
    """Loads and validates a YAML configuration file."""
    try:
        with open(file, 'r') as f:
            data = yaml.safe_load(f)
        print(f"✅ Loaded config: {file}")
        log_history("Config Loaded", file)
        return data
    except FileNotFoundError:
        print(f"❌ Error: Config file not found at {file}")
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error in {file}: {e}")

@app.command()
def llm_prompt(instruction_file: str, context_file: str, model: str = "gpt-4-turbo", overwrite: bool = False):
    """Sends a prompt to an LLM for code generation or refinement."""
    try:
        instruction = Path(instruction_file).read_text()
        context = Path(context_file).read_text()

        print(f"🧠 Sending prompt to {model}...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an elite AI software developer building a conscious AI named Aura. Write clean, elegant, and well-documented Python code."
                },
                {
                    "role": "user",
                    "content": f"Instruction:\n{instruction}\n\n---\n\nCode Context:\n{context}"
                }
            ]
        )
        output = response.choices[0].message.content
        print("💡 AI Suggestion:\n", output)

        if overwrite and typer.confirm(f"Are you sure you want to overwrite {context_file}?"):
            Path(context_file).write_text(output)
            print(f"✍️ Overwritten {context_file} with AI response.")
            log_history("File Overwritten by LLM", f"{context_file}")

    except FileNotFoundError as e:
        print(f"❌ File not found: {e.filename}")
    except openai.APIError as e:
        print(f"❌ OpenAI API Error: {e}")

@app.command()
def test():
    """Runs the full test suite using pytest."""
    print("🧪 Running test suite...")
    result_code = pytest.main()
    if result_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    sys.exit(result_code)

@app.command()
def setup():
    """Creates a virtual environment and installs dependencies."""
    print("🔧 Setting up virtual environment in ./.venv ...")
    subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
    print("📦 Installing dependencies from requirements.txt...")
    subprocess.run([".venv/bin/pip", "install", "-r", "requirements.txt"], check=True)
    print("✅ Setup complete. Activate with: source .venv/bin/activate")
    log_history("Environment Setup", "Virtual environment created and dependencies installed.")

if __name__ == "__main__":
    app()
