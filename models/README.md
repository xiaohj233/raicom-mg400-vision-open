# models

公开仓库不包含真实模型权重。

请自行准备：

```text
models/yolo11n.pt   # 起始模型
models/best.pt      # 训练后模型，由 handwrite/module_b.py 生成或复制
```

`.gitignore` 会忽略 `*.pt`、`*.onnx`、`*.engine` 等模型产物。
