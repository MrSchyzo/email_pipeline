from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import json
import subprocess
import sys

from mail_pipeline.env import load_env

__plugins_path = Path("plugins")
__plugin_venvs_path = Path("plugin_envs")

@dataclass
class EmailContext:
    uid: str
    subject: str
    src: str
    dst: list[str]
    body_text: str
    attachments: list[Path]
    date: datetime | None

def execute_plugins(ctx: EmailContext):
    ctx_json = json.dumps({
        "subject": ctx.subject,
        "src": ctx.src,
        "dst": ctx.dst,
        "date": ctx.date.isoformat() if ctx.date else None,
        "body_text": ctx.body_text,
        "attachments": [str(p) for p in ctx.attachments],
    })
    for plugin_dir in __plugins_path.iterdir():
        if plugin_dir.is_dir() and (plugin_dir / "plugin.py").exists():
            run_plugin(plugin_dir, ctx_json)
    
def run_plugin(plugin_dir, ctx_json: str):
    ensure_venv(plugin_dir)
    
    venv = (__plugin_venvs_path / plugin_dir.name).resolve()
    python = venv / "bin" / "python"
    
    if not venv.exists() or not python.exists():
        python = sys.executable

    subprocess_run(
        [python, "plugin.py"],
        ctx_json,
        plugin_dir,
        load_env(plugin_dir / ".env")
    )
    
def ensure_venv(plugin_dir):
    venv = __plugin_venvs_path / plugin_dir.name
    requirements_path = plugin_dir / "requirements.txt"
    if venv.exists() or not requirements_path.exists():
        return

    subprocess_run([sys.executable, "-m", "venv", venv])
    subprocess_run([venv / "bin" / "pip", "install", "-r", plugin_dir / "requirements.txt"])
    subprocess_run([venv / "bin" / "pip", "install", "--upgrade", "certifi"])
    
def subprocess_run(cmd, input=None, cwd=None, env=None):
    result = subprocess.run(
        cmd,
        input=input,
        text=True,
        cwd=cwd,
        capture_output=True,
        env=env
    )
    print(result.stdout, file=sys.stdout) if result.stdout else None
    print(result.stderr, file=sys.stderr) if result.stderr else None
    result.check_returncode()