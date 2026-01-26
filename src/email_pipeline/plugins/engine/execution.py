import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from email_pipeline.env import load_env
from email_pipeline.logger import logger
from email_pipeline.plugins.engine.data import EmailContext
from email_pipeline.plugins.engine.subprocess_run import subprocess_run
from email_pipeline.plugins.engine.venv import ensure_venv
from email_pipeline.plugins.filesystem import find_paths_by_glob

__plugins_path = Path("plugins")


def execute_plugins(ctx: EmailContext):
    ctx_json = json.dumps({
        "uid": ctx.uid,
        "subject": ctx.subject,
        "src": ctx.src,
        "dst": ctx.dst,
        "date": ctx.date.isoformat() if ctx.date else None,
        "body_text": ctx.body_text,
        "attachments": [str(p) for p in ctx.attachments],
    })
    with ThreadPoolExecutor(max_workers=int(os.getenv("PARALLELISM", "8"))) as executor:
        futures = []
        for plugin_dir in __plugins_path.iterdir():
            if plugin_dir.is_dir() and (plugin_dir / "plugin.py").exists():
                futures.append(executor.submit(run_plugin, plugin_dir, ctx_json, ctx.uid))
        for future in as_completed(futures, timeout=60):
            future.result()


def run_plugin(plugin_dir: Path, ctx_json: str, uid: str):
    venv, python = ensure_venv(plugin_dir)

    paths = [str(x) for x in find_paths_by_glob(venv, "lib/**/site-packages")]
    env = load_env(plugin_dir / ".env")
    env["PYTHONPATH"] = os.pathsep.join(paths + [str(plugin_dir.resolve()), os.getenv("PYTHONPATH", "")])
    env["PATH"] = os.getenv("PATH", "")

    logger.debug("Running plugin", extra={"plugin": plugin_dir.name, "env": env, "mail_uid": uid})
    out, err, code, elapsed = subprocess_run([python, "plugin.py"], ctx_json, plugin_dir, env, expect_success=False)
    _log_subprocess_text(out, plugin=plugin_dir.name, mail_uid=uid, stream="stdout", level="INFO")
    _log_subprocess_text(err, plugin=plugin_dir.name, mail_uid=uid, stream="stderr", level="WARNING")
    if code != 0:
        logger.error("Plugin failed",
                     extra={"env": env, "plugin": plugin_dir.name, "mail_uid": uid, "elapsed_ms": elapsed / 1e6,
                            "return_code": code})
        raise RuntimeError(f"Plugin {plugin_dir.name} failed with return code {code}")

    logger.debug("Plugin finished", extra={"plugin": plugin_dir.name, "mail_uid": uid, "elapsed_ms": elapsed / 1e6})


def _log_subprocess_text(
        text: str | None,
        *,
        plugin: str,
        mail_uid: str,
        stream: str,
        level="INFO"
) -> None:
    if not text:
        return

    def _is_json_obj_line(line: str) -> dict | None:
        line = line.strip()
        if not line:
            return None
        try:
            obj = json.loads(line)
        except Exception:
            return None
        return obj if isinstance(obj, dict) else None

    def _write_json(obj: dict) -> None:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
        sys.stdout.flush()

    meta = {
        "plugin": plugin,
        "mail_uid": mail_uid,
        "stream": stream,
        "level": level,
        "timestamp": datetime.now().isoformat(),
    }

    buffer_lines: list[str] = []

    def _flush_buffer() -> None:
        if not buffer_lines:
            return
        _write_json({**meta, "message": "\n".join(buffer_lines)})
        buffer_lines.clear()

    for raw_line in text.splitlines():
        json_obj = _is_json_obj_line(raw_line)
        if json_obj is not None:
            _flush_buffer()
            _write_json({**meta, **json_obj})
        else:
            buffer_lines.append(raw_line.rstrip("\n"))

    _flush_buffer()
