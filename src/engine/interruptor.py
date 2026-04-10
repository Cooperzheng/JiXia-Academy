# src/engine/interruptor.py
from __future__ import annotations

import sys
import threading
from dataclasses import dataclass, field

__all__ = ["Interruptor"]

_TAB = "\t"


def _is_windows() -> bool:
    return sys.platform == "win32"


@dataclass
class Interruptor:
    """
    后台守护线程，监听 Tab 键。
    检测到 Tab 时 set interrupt_flag，主线程轮询此 flag 决定是否暂停输出。
    """
    interrupt_flag: threading.Event = field(default_factory=threading.Event)
    _stop_flag: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread = field(init=False)

    def __post_init__(self) -> None:
        self._thread = threading.Thread(
            target=self._listen,
            daemon=True,
            name="interruptor",
        )

    def start(self) -> None:
        """启动监听线程。"""
        self._stop_flag.clear()
        self._thread.start()

    def stop(self) -> None:
        """停止监听线程。"""
        self._stop_flag.set()

    def clear(self) -> None:
        """清除中断标志（插话处理完后调用）。"""
        self.interrupt_flag.clear()

    def _listen(self) -> None:
        if _is_windows():
            self._listen_windows()
        else:
            self._listen_unix()

    def _listen_windows(self) -> None:
        import msvcrt
        while not self._stop_flag.is_set():
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch == _TAB:
                    self.interrupt_flag.set()
            self._stop_flag.wait(timeout=0.05)

    def _listen_unix(self) -> None:
        import select
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while not self._stop_flag.is_set():
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    ch = sys.stdin.read(1)
                    if ch == _TAB:
                        self.interrupt_flag.set()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
