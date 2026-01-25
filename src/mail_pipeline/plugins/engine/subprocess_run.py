import subprocess
import time


def subprocess_run(cmd, input=None, cwd=None, env=None, expect_success=False) -> tuple[str, str, int, int]:
    start_time = time.perf_counter_ns()
    result = subprocess.run(
        cmd,
        input=input,
        text=True,
        cwd=cwd,
        capture_output=True,
        env=env
    )
    elapsed_ns = time.perf_counter_ns() - start_time

    if expect_success:
        result.check_returncode()

    return result.stdout, result.stderr, result.returncode, elapsed_ns
