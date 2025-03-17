__all__ = ["get_frame"]

import inspect
import types


def get_frame(back: int = 0) -> types.FrameType | None:
    frame = inspect.currentframe()
    for i in range(back + 1):
        if frame is not None and frame.f_back is not None:
            frame = frame.f_back
        else:
            frame = None
            break

    return frame
