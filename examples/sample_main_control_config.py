# Copy these values into handwrite/main_control.py and replace examples with your own calibration result.

POINT = {
    "PHOTO": (0.0, 0.0, -90.0, 0.0),
    "SAFE_Z": -90.0,
    "PICK_Z": -170.0,
    "PICK_DX": 0.0,
    "PICK_DY": 0.0,
    "PLACE": {
        "CHIP": (0.0, 0.0, -150.0, 0.0),
        "WIFI": (0.0, 0.0, -150.0, 0.0),
        "GPS": (0.0, 0.0, -150.0, 0.0),
        "Square_silver": (0.0, 0.0, -150.0, 0.0),
        "Square_yellow": (0.0, 0.0, -150.0, 0.0),
        "Square_red": (0.0, 0.0, -150.0, 0.0),
    },
    "RELEASE_DO": 2,
    "RELEASE_BLOW": 0.35,
    "RELEASE_WAIT": 0.4,
    "RELEASE_RETRY": 2,
    "DVS_CLEAR_DIRS": ["images"],
    "DVS_WAIT": 6.0,
}
