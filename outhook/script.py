from typing import BinaryIO, Callable

type Callback = Callable[[bytes], None]


def main():
    import sys

    command = sys.argv[1:]
    if not command:
        return

    import importlib
    import subprocess
    import threading
    from pathlib import Path

    no_call: Callback = lambda x: None
    current_dir = Path.cwd().absolute().as_posix()
    sys.path.append(current_dir)
    try:
        module = importlib.import_module("hook")
        func = getattr(module, "callback", None) or getattr(module, "__callback__", no_call)
    except ImportError:
        print("Module 'hook' not found in the current working directory. hook will not be applied.")
        func = no_call
    finally:
        sys.path.remove(current_dir)

    def io_forward(source: BinaryIO, target: BinaryIO, callback: Callback) -> None:
        while content := source.readline():
            try:
                callback(content)
            except Exception:
                print(f"ERROR OCCURRED")
                import traceback

                traceback.print_exc()
            target.write(content)
            target.flush()

    proc = subprocess.Popen(
        command,
        stdin=sys.stdin,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        shell=True,
    )
    assert proc.stdout
    thread = threading.Thread(target=io_forward, args=(proc.stdout, sys.stdout.buffer, func), daemon=True)
    thread.start()
    return_code = proc.wait()
    thread.join()
    return return_code
