import os
import shutil
import subprocess
import tempfile
from typing import Dict, Any, List
from pydantic import BaseModel
from langchain_core.tools import tool
from config.settings import OUTPUT_DIR

class PresentationInput(BaseModel):
    code: str

@tool(args_schema=PresentationInput)
def create_presentation(code: str) -> Dict[str, Any]:
    """Execute provided Python code locally to create PowerPoint presentations.

    This replaces E2B sandbox execution with a local subprocess run. Any occurrences
    of '/home/user' in the provided code are rewritten to a temporary working
    directory to avoid OS-specific path issues.
    """
    # Prepare working directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    temp_root_dir = tempfile.mkdtemp(prefix="pptx_exec_")
    home_user_dir = os.path.join(temp_root_dir, "home", "user")
    os.makedirs(home_user_dir, exist_ok=True)

    # Rewrite code to use the temporary 'home/user' directory
    adjusted_code = code.replace("/home/user", home_user_dir)

    script_path = os.path.join(home_user_dir, "script.py")
    stdout_text = ""
    stderr_text = ""
    pptx_local_paths: List[str] = []

    try:
        # Write the adjusted code to disk
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(adjusted_code)

        # Execute the script in a subprocess
        completed = subprocess.run(
            ["python", script_path],
            cwd=home_user_dir,
            capture_output=True,
            text=True,
            check=False
        )
        stdout_text = completed.stdout or ""
        stderr_text = completed.stderr or ""

        # Discover generated .pptx files under the working directory
        generated_files: List[str] = []
        for root, _dirs, files in os.walk(temp_root_dir):
            for file_name in files:
                if file_name.lower().endswith(".pptx"):
                    generated_files.append(os.path.join(root, file_name))

        # Copy found files into OUTPUT_DIR for Streamlit download
        for src_path in generated_files:
            try:
                dest_path = os.path.join(OUTPUT_DIR, os.path.basename(src_path))
                shutil.copy2(src_path, dest_path)
                pptx_local_paths.append(dest_path)
            except Exception as copy_err:
                if stderr_text:
                    stderr_text += "\n"
                stderr_text += f"Copy error for {src_path}: {copy_err}"

        return {
            "results": [{
                "type": "pptx_files",
                "local_paths": pptx_local_paths
            }],
            "stdout": stdout_text,
            "stderr": stderr_text
        }
    except Exception as e:
        return {
            "results": [],
            "stdout": stdout_text,
            "stderr": str(e) if str(e) else repr(e)
        }
    finally:
        # Best-effort cleanup of temporary working directory
        try:
            shutil.rmtree(temp_root_dir, ignore_errors=True)
        except Exception:
            pass