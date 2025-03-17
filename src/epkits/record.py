__all__ = ["record_t"]

import time
import math
import os
import json
from dataclasses import dataclass

from .level import level_t


@dataclass
class record_t:
    ts: float = 0
    seq: int = 0
    level: int = level_t.N
    nid: int = 0
    nname: str = ""
    pid: int = -1
    pname: str = ""
    tid: int = -1
    tname: str = ""
    file: str = ""
    lineno: int = -1
    func: str = ""
    message: str = ""

    def __str__(self) -> str:
        st = time.gmtime(self.ts)
        μs = int(math.modf(self.ts)[0] * 1_000_000)

        text = (
            f"[{st.tm_year:04d}{st.tm_mon:02d}{st.tm_mday:02d}.{st.tm_hour:02d}{st.tm_min:02d}{st.tm_sec:02d}.{μs:06d} {self.seq:6d}]"
            f"[{level_t(self.level).name}]"
            f"[{self.nid:012x} {self.pid:6d} {self.tid:6d}]"
            f"[{self.nname} {self.pname} {self.tname}]"
            f"[{os.path.basename(self.file)}:{self.lineno} {self.func}]"
            f"{self.message}"
            "\n"
        )

        return text

    def __repr__(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False) + "\n"
