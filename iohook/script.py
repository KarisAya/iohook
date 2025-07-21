import sys
import subprocess
import threading
import importlib
import logging
from typing import TextIO, Callable

type Hook = Callable[[str], str]


direct_hook = lambda x: x
input_hook: Hook = direct_hook
output_hook: Hook = direct_hook

try:
    module = importlib.import_module("hook")
    input_hook = getattr(module, "input_hook", direct_hook)
    output_hook = getattr(module, "output_hook", direct_hook)
except ImportError:
    logging.warning("'hook.py' not found in the current working directory. Hooks will not be applied.")


def io_forward(source: TextIO, target: TextIO, hook: Hook) -> None:
    try:
        while content := source.readline():
            content = hook(content)
            target.write(content)
            target.flush()
    except Exception:
        logging.exception("ERROR OCCURRED")
    finally:
        source.close()
        target.close()


def main():
    command = sys.argv[1:]
    if not command:
        return
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # 行缓冲
        universal_newlines=True,
    )
    threading.Thread(target=io_forward, args=(sys.stdin, proc.stdin, input_hook), daemon=True).start()
    threading.Thread(target=io_forward, args=(proc.stdout, sys.stdout, output_hook), daemon=True).start()
    proc.wait()
    return proc.returncode
