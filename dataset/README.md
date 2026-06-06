# dataset

公开仓库不包含真实训练图片和真实 YOLO 标注。

请自行放置：

```text
dataset/images/*.jpg|*.png|*.bmp
dataset/labels/*.txt
```

`handwrite/module_b.py` 会自动把根层图片和标注划分到：

```text
dataset/images/train
dataset/images/val
dataset/labels/train
dataset/labels/val
```

类别顺序：

```text
GPS
CHIP
WIFI
Square_red
Square_yellow
Square_silver
```
