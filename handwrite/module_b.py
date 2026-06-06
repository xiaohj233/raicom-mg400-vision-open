# -*- coding: utf-8 -*-
"""Module B style YOLO training / prediction entry.

Run from the repository root:
    python handwrite/module_b.py
    python handwrite/module_b.py --predict

Public repository note: dataset images, labels and model weights are not included.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import vision_motion_kit as v  # noqa: E402

CLASSES = ["GPS", "CHIP", "WIFI", "Square_red", "Square_yellow", "Square_silver"]
DATASET = "dataset"
START_MODEL = "models/yolo11n.pt"
BEST_MODEL = "models/best.pt"
PREDICT_IMAGES = "images"
DRY = "--dry" in sys.argv


def train():
    params = v.train_params(cpu="--cpu" in sys.argv)
    data = v.auto_dataset(DATASET, CLASSES)
    v.print_plan(data, CLASSES, params)
    if DRY:
        print("dry-run: dataset prepared, training skipped")
        return
    result = v.train_yolo(START_MODEL, data, project="dataset/runs/train", **params)
    print("best.pt:", v.copy_best(result, BEST_MODEL))


def predict():
    model = v.load_detector(BEST_MODEL)
    for img in v.find_images(PREDICT_IMAGES):
        dets = v.detect_objects(model, img, CLASSES, conf=0.70)
        dets = v.keep_best_per_label(dets, CLASSES)
        out = v.save_visualization(img, dets, "images/predict_result/" + img.stem + "_result.jpg")
        print("IMG", img, "SAVE", out)
        for d in dets:
            print(d.label, f"{d.confidence:.2f}")


try:
    predict() if "--predict" in sys.argv or "-p" in sys.argv else train()
except Exception as e:
    print("ModuleB error:", e)
