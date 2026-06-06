from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Message:
    head: str
    fields: tuple[str, ...]
    raw: str

def norm(x) -> str:
    return str(x).replace('\r','').strip()

def cmd(name, *fields) -> str:
    parts=[str(name).strip().upper()]+[str(v).strip() for v in fields]
    return ','.join(parts)

def dec(line) -> Message:
    raw=norm(line)
    if not raw:
        return Message('',(), '')
    ps=[p.strip() for p in raw.split(',')]
    return Message(ps[0].upper(), tuple(ps[1:]), raw)

def move_cmd(x,y,z,r=0): return cmd('MOVE', f'{float(x):.3f}', f'{float(y):.3f}', f'{float(z):.3f}', f'{float(r):.3f}')
def jog_cmd(dx=0,dy=0,dz=0,dr=0): return cmd('JOG', f'{float(dx):.3f}', f'{float(dy):.3f}', f'{float(dz):.3f}', f'{float(dr):.3f}')
def suck_cmd(on): return cmd('SUCK', 1 if bool(on) else 0)
def blow_cmd(do=2, seconds=0.35): return cmd('BLOW', int(do), f'{float(seconds):.3f}')
def photo_cmd(pose=None): return cmd('PHOTO', *(pose or ()))
def home_cmd(): return cmd('HOME')
def end_cmd(): return cmd('END')
