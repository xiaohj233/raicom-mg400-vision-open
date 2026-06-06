from __future__ import annotations
from dataclasses import dataclass
from math import hypot

@dataclass(frozen=True)
class Target:
    label: str; conf: float; px: float; py: float; robot_x: float; robot_y: float; angle: float

def match_by_nearest_center(dets, poses, max_dist=160):
    out=[]; used=set()
    for d in dets:
        best=None; bi=None; bd=10**9
        for i,p in enumerate(poses):
            if i in used: continue
            dist=hypot(d.center_x-p.px, d.center_y-p.py)
            if dist<bd: best=p; bi=i; bd=dist
        if best is not None and bd<=max_dist:
            used.add(bi); out.append(Target(d.label,d.confidence,d.center_x,d.center_y,best.robot_x,best.robot_y,best.angle))
    return out

def sort_by_label_order(items, order):
    rank={v:i for i,v in enumerate(order)}
    return sorted(items,key=lambda x:rank.get(x.label,999))

def filter_by_label(items,bad=()):
    bad=set(bad or [])
    return [x for x in items if x.label not in bad]

def target_summary(t, cfg=None):
    dx = getattr(cfg, 'pick_dx', 0.0) if cfg is not None else 0.0
    dy = getattr(cfg, 'pick_dy', 0.0) if cfg is not None else 0.0
    x = t.robot_x + dx
    y = t.robot_y + dy
    return f'{t.label},{t.conf:.2f},{x:.2f},{y:.2f}'

def ensure_same_image(frame_image,dets):
    return None
