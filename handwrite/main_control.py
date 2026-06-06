# -*- coding: utf-8 -*-
"""Three-file style runtime entry for MG400 + DobotVisionStudio + YOLO.

Run from the repository root:
    python handwrite/main_control.py

This public template intentionally contains no real competition coordinates.
Fill POINT before connecting a real robot.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from vision_motion_kit import *  # noqa: E402,F403

TXT = {
    "title": "RAICOM MG400 Vision Open",
    "robot_frame": "robot",
    "vision_frame": "vision",
    "monitor_frame": "monitor",
    "new_photo": "waiting new photo...",
    "missing_image": "image missing/waiting",
    "btn_home": "Home",
    "btn_photo": "Photo",
    "err": "ERR:",
    "photo_pose": "photo pose",
    "release": "release",
    "detect_image": "detect image",
}

RPORT, VPORT = 5001, 5002
MODEL = "models/best.pt"
CLS = ORDER = "GPS WIFI CHIP Square_red Square_yellow Square_silver".split()
BAD = ()
TIME, DIST = 20, 160

POINT = {
    "PHOTO": (),
    "SAFE_Z": -90.0,
    "PICK_Z": -170.0,
    "PICK_DX": 0.0,
    "PICK_DY": 0.0,
    "PLACE": {
        "CHIP": (),
        "WIFI": (),
        "GPS": (),
        "Square_silver": (),
        "Square_yellow": (),
        "Square_red": (),
    },
    "RELEASE_DO": 2,
    "RELEASE_BLOW": 0.35,
    "RELEASE_WAIT": 0.4,
    "RELEASE_RETRY": 2,
    "DVS_CLEAR_DIRS": ["images"],
    "DVS_WAIT": 6.0,
}

CFG = rcfg(POINT)
PLACE = CFG.place_map(ORDER)
box = SocketBox()


def clear_predict():
    p = Path("images/predict_result")
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)


def ensure_points_configured():
    missing = []
    if not POINT["PHOTO"]:
        missing.append("POINT['PHOTO']")
    for label, value in POINT["PLACE"].items():
        if not value:
            missing.append(f"POINT['PLACE']['{label}']")
    if missing:
        raise RuntimeError(
            "请先把示例点位替换为你的标定坐标: " + ", ".join(missing)
        )


def run_once():
    ensure_points_configured()
    r = box.robot()
    panel.clear_image(TXT["new_photo"])
    clear_predict()
    clear_dvs_image_cache(CFG.dvs_clear_dirs, log)
    cfg_log(CFG, log, TXT)
    photo_wait(r, CFG.photo_pose, TIME, log)

    f = trigger_frame(
        box.vision(),
        "TRIGGER",
        TIME,
        log=log,
        image_wait_s=CFG.dvs_image_wait_s,
    )
    panel.show_image(f.image_path)

    model = load_detector(MODEL)
    dets = detect_objects(model, f.image_path, CLS, conf=0.70)
    dets = best_labels(dets, ORDER)
    show_yolo_image(panel, f.image_path, dets, log, text=TXT)

    if not check_count(f.poses, 6, strict=False):
        log(f"WARN:DVS POINT count is {len(f.poses)}, continue with actual points")

    plan = match_points(dets, f.poses, DIST)
    plan = filter_by_label(plan, BAD)

    for t in sort_labels(plan, ORDER):
        log(target_summary(t, CFG))  # 类型,置信度,X坐标,Y坐标
        execute_pick_place(r, t, PLACE[t.label], CFG, TIME, log)

    end_wait(r, TIME, log)
    log("End")


panel = make_panel(box, RPORT, VPORT, TXT)
log = panel.log
j = RobotJogger(box.robot, log, step=10)
panel.buttons(
    [
        ("X+", lambda: j.jog(10)),
        ("X-", lambda: j.jog(-10)),
        ("Y+", lambda: j.jog(0, 10)),
        ("Y-", lambda: j.jog(0, -10)),
        ("Z+", lambda: j.jog(0, 0, 10)),
        ("Z-", lambda: j.jog(0, 0, -10)),
        (TXT["btn_home"], j.home),
        (TXT["btn_photo"], lambda: start_thread(run_once, log, TXT["err"])),
    ]
)
panel.run()
