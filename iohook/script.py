from typing import IO, Callable

type Hook = Callable[[str], str]


def main():
    import sys

    command = sys.argv[1:]
    if not command:
        return

    import logging
    import importlib
    import importlib.util
    import subprocess
    import threading
    from pathlib import Path

    logger = logging.getLogger("iohook")
    pass_hook: Hook = lambda x: x

    try:
        if not ((hook_path := Path("hook/__init__.py")).exists() or (hook_path := Path("hook.py")).exists()):
            raise ImportError
        spec = importlib.util.spec_from_file_location("iohook.hook", hook_path)
        if spec is None or spec.loader is None:
            raise ImportError
        hook = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hook)
        input_hook = getattr(hook, "input_hook", pass_hook)
        output_hook = getattr(hook, "output_hook", pass_hook)
    except ImportError:
        logger.warning("Module 'hook' not found in the current working directory. Hooks will not be applied.")
        input_hook = pass_hook
        output_hook = pass_hook

    def io_forward(source: IO[str], target: IO[str], hook: Hook) -> None:
        try:
            while content := source.readline():
                content = hook(content)
                if content:
                    target.write(content)
                    target.flush()
        except Exception:
            logger.exception("ERROR OCCURRED")

    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # 行缓冲
        universal_newlines=True,
    )
    assert proc.stdin and proc.stdout
    input_thread = threading.Thread(target=io_forward, args=(sys.stdin, proc.stdin, input_hook), daemon=True)
    output_thread = threading.Thread(target=io_forward, args=(proc.stdout, sys.stdout, output_hook), daemon=True)
    input_thread.start()
    output_thread.start()
    return_code = proc.wait()
    # 输入监听应该和主线程一起结束，所以不需要执行 join()
    # 输出监听应该决定主线程何时结束。因为子程序结束后可能主线程还没有输出完毕。
    output_thread.join()
    return return_code
