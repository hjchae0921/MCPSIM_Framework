"""Keep the accepted solve namespace alive while the coder writes stage six."""

import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import types

from codegen import worker_environment
from codegen.runner import write_json as write


def field_arrays(namespace):
    from dolfinx.fem import Function

    found, seen = [], set()

    def visit(value, depth=0):
        if id(value) in seen or depth > 3:
            return
        seen.add(id(value))
        if isinstance(value, Function):
            found.append(value.x.array)
        elif isinstance(value, (list, tuple, dict)):
            for item in (value.values() if isinstance(value, dict) else value):
                visit(item, depth + 1)
        elif type(value).__module__ == "dolfinx.fem.petsc":
            visit(getattr(value, "u", None), depth + 1)

    for value in list(namespace.values()):
        visit(value)
    return found


def child(config):
    import numpy as np

    spec = json.loads(Path(config).read_text())
    home = Path(spec["home"])
    module = types.ModuleType("__main__")
    module.__dict__.update(__package__=None, __spec__=None)
    namespace = module.__dict__
    sys.modules["__main__"] = module
    start = time.monotonic()
    try:
        for filename in spec["sources"]:
            path = Path(filename)
            namespace["__file__"] = str(path)
            exec(compile(path.read_text(), str(path), "exec"), namespace)
        snapshots = [(a, a.copy()) for a in field_arrays(namespace)]
        baseline = dict(namespace)
        write(
            home / "ready.json",
            {
                "status": "ready",
                "pid": os.getpid(),
                "replay_seconds": time.monotonic() - start,
                "tracked_arrays": len(snapshots),
            },
        )
    except BaseException:
        write(
            home / "ready.json",
            {"status": "replay_failed", "error": traceback.format_exc(), "pid": os.getpid()},
        )
        return
    for line in sys.stdin:
        command = json.loads(line)
        if command.get("stop"):
            break
        source = Path(command["source"])
        output = Path(command["output"])
        output.mkdir(parents=True, exist_ok=True)
        namespace.clear()
        namespace.update(baseline)
        namespace["POSTPROCESS_OUTPUT_DIR"] = str(output)
        os.environ["POSTPROCESS_OUTPUT_DIR"] = str(output)
        namespace["__file__"] = str(source)
        started = time.monotonic()
        error = None
        previous = Path.cwd()
        try:
            tree = ast.parse(source.read_text(), filename=str(source))
            if any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "solve"
                for n in ast.walk(tree)
            ):
                raise ValueError(
                    "Postprocessing must use the existing solution without calling solve again."
                )
            os.chdir(output)
            exec(compile(tree, str(source), "exec"), namespace)
            if any(not np.array_equal(a, b, equal_nan=True) for a, b in snapshots):
                raise ValueError(
                    "Postprocessing modified a solved field. The original arrays have been restored."
                )
        except BaseException:
            error = traceback.format_exc()
        finally:
            for array, stored in snapshots:
                array[:] = stored
            os.chdir(previous)
        write(
            command["response"],
            {
                "status": "failed" if error else "executed",
                "error": error,
                "pid": os.getpid(),
                "seconds": time.monotonic() - started,
            },
        )


class Session:
    def __init__(self, sources, home, python=sys.executable, replay_timeout=3600):
        self.home = Path(home).resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        write(
            self.home / "session.json",
            {"home": str(self.home), "sources": [str(Path(p).resolve()) for p in sources]},
        )
        env = {
            **worker_environment(),
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "XDG_CACHE_HOME": str(self.home / "cache"),
        }
        for key in ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "CODER_API_KEY"):
            env.pop(key, None)
        self.log = (self.home / "process.log").open("w")
        (self.home / "ready.json").unlink(missing_ok=True)
        self.process = subprocess.Popen(
            [
                python,
                "-B",
                "-m",
                "codegen.session",
                "--config",
                str(self.home / "session.json"),
            ],
            stdin=subprocess.PIPE,
            stdout=self.log,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=self.home,
            env=env,
            start_new_session=True,
        )
        try:
            self.ready = self.wait(self.home / "ready.json", replay_timeout)
            if self.ready["status"] != "ready":
                raise RuntimeError(self.ready["error"])
        except BaseException:
            self.close()
            raise

    def wait(self, path, timeout):
        deadline = time.monotonic() + timeout
        while not path.exists():
            if self.process.poll() is not None:
                raise RuntimeError(
                    f"Persistent process exited ({self.process.returncode}); see {self.home}/process.log"
                )
            if time.monotonic() > deadline:
                raise TimeoutError(f"Persistent process exceeded {timeout}s")
            time.sleep(0.1)
        return json.loads(path.read_text())

    def execute(self, source, output, response, timeout=120):
        response = Path(response).resolve()
        response.unlink(missing_ok=True)
        self.process.stdin.write(
            json.dumps(
                {
                    "source": str(Path(source).resolve()),
                    "output": str(Path(output).resolve()),
                    "response": str(response),
                }
            )
            + "\n"
        )
        self.process.stdin.flush()
        return self.wait(response, timeout)

    def close(self):
        import signal

        if self.process.poll() is None:
            try:
                self.process.stdin.write('{"stop":true}\n')
                self.process.stdin.flush()
                self.process.wait(timeout=5)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait()
        self.process.stdin.close()
        self.log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    child(parser.parse_args().config)
