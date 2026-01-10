from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import json
import subprocess
import sys

@dataclass
class EmailContext:
    subject: str
    src: str
    dst: list[str]
    body_text: str
    attachments: list[Path]
    date: datetime | None
    
def ensure_venv(plugin_dir):
    venv = Path("plugin") / plugin_dir.name
    requirements_path = plugin_dir / "requirements.txt"
    if venv.exists() or not requirements_path.exists():
        return

    subprocess.run([sys.executable, "-m", "venv", venv], check=True)
    subprocess.run(
        [venv / "bin" / "pip", "install", "-r", plugin_dir / "requirements.txt"],
        check=True,
    )
    
def run_plugin(plugin_dir, ctx_json: str):
    ensure_venv(plugin_dir)
    
    venv = Path("plugin_envs") / plugin_dir.name
    python = venv / "bin" / "python"
    
    if not venv.exists() or not python.exists():
        python = sys.executable

    subprocess.run(
        [python, "plugin.py"],
        input=ctx_json,
        text=True,
        cwd=plugin_dir,
        check=False,
    )
    
def execute_plugins(ctx: EmailContext):
    ctx_json = json.dumps({
        "subject": ctx.subject,
        "src": ctx.src,
        "dst": ctx.dst,
        "date": ctx.date.isoformat() if ctx.date else None,
        "body_text": ctx.body_text,
        "attachments": [str(p) for p in ctx.attachments],
    })
    plugins_dir = Path("plugins")
    for plugin_dir in plugins_dir.iterdir():
        if plugin_dir.is_dir() and (plugin_dir / "plugin.py").exists():
            run_plugin(plugin_dir, ctx_json)