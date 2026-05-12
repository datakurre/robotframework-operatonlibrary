from functools import wraps
from typing import Any

import sys

try:
    import java  # pyright: ignore
except ImportError:
    # Fix typechecks outside graalpy
    class java:
        @staticmethod
        def type(klass: str) -> Any:
            pass


Variables = java.type("org.operaton.bpm.engine.variable.Variables")


def except_interop_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:  # noqa
            exc_type, exc_value, exc_traceback = sys.exc_info()
            message = str(exc_value) if exc_value else "Unknown error"
            try:
                if hasattr(exc_value, 'getMessage'):
                    java_msg = exc_value.getMessage()
                    if java_msg:
                        message = str(java_msg)
                if hasattr(exc_value, 'getStackTrace'):
                    trace = exc_value.getStackTrace()
                    if trace:
                        frames = []
                        for elem in trace:
                            frames.append(str(elem))
                            if len(frames) >= 5:
                                break
                        if frames:
                            message += "\nJava stack trace:\n  " + "\n  ".join(frames)
            except Exception:
                pass
            assert False, message
    return wrapper
