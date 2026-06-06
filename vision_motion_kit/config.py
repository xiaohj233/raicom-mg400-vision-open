from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PlaceTarget:
    label: str
    x: float
    y: float
    z: float
    r: float = 0.0
    air_drop: bool = False

    def as_tuple(self):
        return self.x, self.y, self.z, self.r


@dataclass(frozen=True)
class RaceConfig:
    safe_z: float
    pick_z: float
    photo_pose: tuple[float, float, float, float]
    place: dict[str, PlaceTarget]
    release_do: int = 2
    release_blow_s: float = 0.35
    release_wait_s: float = 0.4
    release_retry: int = 2
    dvs_clear_dirs: tuple[str, ...] = ()
    dvs_image_wait_s: float = 6.0
    pick_delta: float = 10.0
    place_delta: float = 10.0
    pick_dx: float = 0.0
    pick_dy: float = 0.0

    def place_map(self, labels: Iterable[str]):
        return {x: self.place[x] for x in labels if x in self.place}


def rcfg(d: dict) -> RaceConfig:
    safe = float(d.get("SAFE_Z", -90.0))
    pick = float(d.get("PICK_Z", -170.0))
    photo = tuple(float(x) for x in d.get("PHOTO", ()) or ())
    place = {}
    for label, vals in d.get("PLACE", {}).items():
        if vals in (None, "", [], ()):  # empty placeholder in public template
            x, y, z, r = 0.0, 0.0, safe, 0.0
            place[label] = PlaceTarget(label, x, y, z, r, True)
        else:
            if len(vals) == 2:
                x, y = vals
                z = float(d.get("PLACE_Z", pick))
                r = 0.0
            else:
                x, y, z, r = vals[:4]
            place[label] = PlaceTarget(label, float(x), float(y), float(z), float(r), False)
    return RaceConfig(
        safe_z=safe,
        pick_z=pick,
        photo_pose=photo,
        place=place,
        release_do=int(d.get("RELEASE_DO", 2)),
        release_blow_s=float(d.get("RELEASE_BLOW", 0.35)),
        release_wait_s=float(d.get("RELEASE_WAIT", 0.4)),
        release_retry=max(1, int(d.get("RELEASE_RETRY", 2))),
        dvs_clear_dirs=tuple(str(x) for x in d.get("DVS_CLEAR_DIRS", ())),
        dvs_image_wait_s=float(d.get("DVS_WAIT", 6.0)),
        pick_delta=float(d.get("PICK_DELTA", 10.0)),
        place_delta=float(d.get("PLACE_DELTA", 10.0)),
        pick_dx=float(d.get("PICK_DX", 0.0)),
        pick_dy=float(d.get("PICK_DY", 0.0)),
    )


def cfg_log(c: RaceConfig, log=print, text=None):
    t = {
        "photo_pose": "photo pose",
        "release": "release",
    }
    if text:
        t.update(text)
    log(f"{t['photo_pose']}:{c.photo_pose}")
    log(f"Z: safe={c.safe_z} pick={c.pick_z}")
    log(f"pick offset: dx={c.pick_dx} dy={c.pick_dy}")
    log(
        f"{t['release']}: DO={c.release_do} "
        f"blow={c.release_blow_s}s wait={c.release_wait_s}s retry={c.release_retry}"
    )
