from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from .protocol import dec
from .runtime import normalize_project_path
from .transport import recv_line, send_line

IMG_SUFFIX = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class VisionPose:
    px: float
    py: float
    robot_x: float
    robot_y: float
    angle: float = 0.0
    raw: str = ""


@dataclass(frozen=True)
class DvsFrame:
    image_path: Path | None
    poses: tuple[VisionPose, ...]
    raw_lines: tuple[str, ...]
    ended: bool = False


def parse_pose(line):
    m = dec(line)
    fs = m.fields if m.head in {"POINT", "P"} else tuple(str(line).split(","))
    if len(fs) < 5:
        raise ValueError("POINT 字段不足:" + str(line))
    return VisionPose(float(fs[0]), float(fs[1]), float(fs[2]), float(fs[3]), float(fs[4] or 0), str(line))


def parse_dvs(lines):
    if isinstance(lines, str):
        lines = lines.splitlines()
    img = None
    poses = []
    ended = False
    raw = []
    for line in [str(x).strip() for x in lines if str(x).strip()]:
        raw.append(line)
        m = dec(line)
        if m.head == "CLEAR":
            img = None
            poses.clear()
        elif m.head in {"IMG", "IMAGE"}:
            if not m.fields:
                raise ValueError("IMG 缺少路径:" + line)
            img = Path(m.fields[0])
        elif m.head in {"POINT", "P"}:
            poses.append(parse_pose(line))
        elif m.head in {"END", "DONE"}:
            ended = True
        elif m.head == "ERR":
            raise RuntimeError("DVS 返回错误:" + line)
        else:
            raise ValueError("DVS 未知消息:" + line)
    return DvsFrame(img, tuple(poses), tuple(raw), ended)


def _fresh(p: Path, mt=None):
    if mt is not None and p.stat().st_mtime < mt - 0.05:
        raise RuntimeError("DVS 图片未更新:" + str(p))
    return p


def _imgs(folder: Path):
    if not folder.exists() or not folder.is_dir():
        return []
    return sorted(
        [x for x in folder.iterdir() if x.is_file() and x.suffix.lower() in IMG_SUFFIX],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )


def _resolve_once(path, mt=None):
    p = normalize_project_path(path)
    if p.is_file():
        return _fresh(p, mt)
    if p.is_dir():
        for name in ("current.bmp", "current.jpg", "current.jpeg", "current.png"):
            c = p / name
            if c.exists():
                return _fresh(c, mt)
        imgs = _imgs(p)
        if imgs:
            return _fresh(imgs[0], mt)
        raise FileNotFoundError("DVS IMG 返回的是目录，但目录下没有图片:" + str(p))
    if not p.suffix:
        for suf in (".bmp", ".jpg", ".jpeg", ".png"):
            c = Path(str(p) + suf)
            if c.exists():
                return _fresh(c, mt)
    raise FileNotFoundError("DVS IMG 图片不存在:" + str(p))


def resolve_image(path, mt=None, wait_s=6, log=None):
    end = time.monotonic() + wait_s
    once = False
    last = None
    while True:
        try:
            return _resolve_once(path, mt)
        except Exception as e:
            last = e
            if log and not once:
                log("等待 DVS 图片落盘:" + str(path))
                once = True
            if time.monotonic() >= end:
                raise last
            time.sleep(0.15)


def read_frame_after_trigger(sock, trigger="TRIGGER", timeout=20, log=None, image_wait_s=6):
    t = time.time()
    send_line(sock, trigger)
    if log:
        log("=> DVS " + trigger)
    lines = []
    while True:
        line = recv_line(sock, timeout)
        lines.append(line)
        if log:
            log("vision: " + line)
        if dec(line).head in {"END", "DONE"}:
            break
    f = parse_dvs(lines)
    if not f.image_path:
        raise RuntimeError("DVS 没有返回 IMG 路径")
    img = resolve_image(f.image_path, t, image_wait_s, log)
    return DvsFrame(img, f.poses, f.raw_lines, f.ended)


def validate_pose_count(poses, expected=6, strict=False):
    n = len(list(poses))
    ok = n == expected
    if strict and not ok:
        raise ValueError(f"DVS POINT 数量异常: 期望 {expected} 实际 {n}")
    return ok


def clear_dvs_image_cache(paths, log=None):
    if isinstance(paths, str):
        paths = [paths]
    count = 0
    for item in paths or []:
        p = normalize_project_path(item)
        if not p.exists() or not p.is_dir():
            continue
        for f in p.iterdir():
            if f.is_file() and f.suffix.lower() in IMG_SUFFIX:
                try:
                    f.unlink()
                    count += 1
                except OSError as e:
                    if log:
                        log(f"WARN: 清理旧图失败 {f}: {e}")
    if log and count:
        log(f"已清空 DVS 旧图片:{count} 张")
    return count
