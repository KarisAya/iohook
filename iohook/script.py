from typing import BinaryIO, Callable

type Callback = Callable[[bytes], None]


def main():
    import sys

    command = sys.argv[1:]
    if not command:
        return

    import logging
    import importlib
    import subprocess
    import threading
    from pathlib import Path

    logger = logging.getLogger("iohook")
    pass_hook: Callback = lambda x: None
    current_dir = Path.cwd().absolute().as_posix()
    sys.path.append(current_dir)
    try:
        module = importlib.import_module("hook")
        hook = getattr(module, "callback", None) or getattr(module, "__callback__", pass_hook)
    except ImportError:
        logger.warning("Module 'hook' not found in the current working directory. Hooks will not be applied.")
        hook = pass_hook
    finally:
        sys.path.remove(current_dir)

    def io_forward(source: BinaryIO, target: BinaryIO, callback: Callback) -> None:
        try:
            while content := source.readline():
                callback(content)
                target.write(content)
                target.flush()
        except Exception:
            logger.exception("ERROR OCCURRED")

    proc = subprocess.Popen(
        command,
        stdin=sys.stdin,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
    )
    assert proc.stdout
    thread = threading.Thread(target=io_forward, args=(proc.stdout, sys.stdout.buffer, hook), daemon=True)
    thread.start()
    return_code = proc.wait()
    thread.join()
    return return_code
