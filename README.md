# raicom-mg400-vision-open

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)

赛后整理的 **MG400 + DobotVisionStudio + YOLO** 机器视觉抓取开源示例，保留“三文件比赛版”的最小入口，同时提供可复用的 `vision_motion_kit` 源码。

> 这不是官方项目；仓库不包含官方资料、真实比赛数据、训练权重、真实标定文件、现场截图或商业软件文件。使用者需要自行准备设备、软件、相机标定、数据集和模型。

## 文档导航

- [项目简介](#项目简介)
- [适用硬件与软件](#适用硬件与软件)
- [仓库结构](#仓库结构)
- [安装方法](#安装方法)
- [运行流程](#运行流程)
- [DVS 协议说明](#dvs-协议说明)
- [监控框显示要求](#监控框显示要求)
- [坐标微调说明](#坐标微调说明)
- [脚本说明](#脚本说明)
- [常见问题](#常见问题)
- [免责声明](#免责声明)
- [许可证](#许可证)

## 项目简介

本仓库是一个赛后复盘版示例，用来演示：

- Python 控制界面；
- Lua 机器人执行脚本；
- Python 与 DobotVisionStudio 之间的 TCP 按行通信；
- YOLO 训练与推理；
- DVS 点位与 YOLO 检测结果的最近中心匹配；
- 抓取、放置、放气释放和 End 收尾流程；
- 适合现场手写复现的 `handwrite/` 三文件入口；
- 适合二次开发复用的 `vision_motion_kit/` 源码库。

`vision_motion_kit/` 是本项目配套的自写源码库。开源版直接以源码目录维护；历史比赛包里的 wheel 仅是打包产物，不作为仓库主内容提交。

## 适用硬件与软件

- MG400 机械臂；
- DobotStudio Pro；
- DobotVisionStudio；
- Python 3.11；
- Ultralytics YOLO；
- Windows 10/11。

## 仓库结构

```text
raicom-mg400-vision-open/
  README.md                         项目说明
  LICENSE                           MIT License，仅覆盖本仓库自写代码和文档
  VERSION                           当前版本号
  requirements.txt                  Python 依赖
  pyproject.toml                    可编辑安装 / 打包元信息
  .gitignore                        忽略真实数据、模型、运行产物

  handwrite/
    main_control.py                 模块 C/D 风格控制入口：UI、DVS、YOLO、抓放
    module_b.py                     模块 B 风格训练与推理入口
    robot_executor.lua              MG400 Lua 执行端脚本

  vision_motion_kit/
    __init__.py                     统一导出
    transport.py                    TCP 监听、收发、ACK 等
    protocol.py                     MOVE/JOG/SUCK/BLOW/PHOTO/END 协议命令
    vision.py                       DVS 消息解析、图片等待落盘、POINT 解析
    motion.py                       抓取、放置、放气释放流程
    geometry.py                     YOLO 与 DVS 点位匹配
    yolo.py                         YOLO 训练、推理、可视化
    ui.py                           Tkinter 控制面板
    runtime.py                      路径辅助
    config.py                       点位与运行参数配置

  examples/
    sample_dvs_protocol.txt         DVS TCP 协议样例
    sample_project_tree.txt         仓库结构样例
    sample_main_control_config.py   main_control.py 点位配置模板
    sample_robot_points.md          点位记录模板

  dataset/
    README.md                       数据集说明
    images/.gitkeep                 用户自行放训练图片
    labels/.gitkeep                 用户自行放 YOLO txt 标注

  models/
    README.md                       模型说明

  images/
    README.md                       DVS 当前图片与推理结果目录说明
    .gitkeep

  scripts/
    10-create-repo-and-push.ps1     创建 GitHub 仓库并 push
    70-release-version.ps1          打 tag、生成 zip、创建 Release

  一键创建并上传仓库.cmd
  一键发布版本.cmd
```

## 安装方法

在仓库根目录运行：

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

可选：用可编辑模式安装本地库。

```bat
pip install -e .
```

## 运行流程

1. 克隆或解压仓库，并进入仓库根目录。
2. 创建 `.venv`。
3. 安装依赖。
4. 准备 YOLO 起始模型，例如把 `yolo11n.pt` 放到 `models/yolo11n.pt`。
5. 把训练图片放到 `dataset/images/`，把同名 YOLO 标注放到 `dataset/labels/`。
6. 运行训练入口：

   ```bat
   python handwrite\module_b.py
   ```

   训练完成后会把 `best.pt` 复制到 `models/best.pt`。

7. 在 DobotVisionStudio 中配置 TCP 输出流程，让 Python 触发后返回 `CLEAR / IMG / POINT / END`。
8. 在 `handwrite/robot_executor.lua` 中把 `IP` 改成你的 Python 电脑 IP，然后在 MG400 端运行 Lua 脚本。
9. 在 `handwrite/main_control.py` 中填写 `POINT`：拍照位、抓取 Z、放置点、吸气/放气参数。
10. 运行控制界面：

    ```bat
    python handwrite\main_control.py
    ```

11. 点击界面的 `Photo`，Python 会让机器人到拍照位，然后向 DVS 发送 `TRIGGER`。
12. 检查监控框输出，正常格式为 `类型,置信度,X坐标,Y坐标`，最后输出 `End`。

## DVS 协议说明

Python -> DVS：

```text
TRIGGER
```

DVS -> Python：

```text
CLEAR
IMG,images/current.bmp
POINT,px,py,robot_x,robot_y,angle
END
```

说明：

- `IMG` 必须带图片路径；
- 推荐保存为 `images/current.bmp`；
- 如果 `IMG` 返回的是目录，Python 会等待目录下图片落盘，但更推荐 DVS 直接发送完整图片路径；
- `POINT` 可以发送多个，每行一个点；
- `END` 表示本次视觉结果发送结束；
- `POINT` 中的 `px,py` 是图像坐标，`robot_x,robot_y,angle` 是通过标定或变量计算得到的机器人坐标。

## 监控框显示要求

控制界面监控框中，每个抓取目标输出：

```text
类型,置信度,X坐标,Y坐标
End
```

示例：

```text
WIFI,0.86,120.50,-35.20
CHIP,0.91,135.10,-18.40
End
```

## 坐标微调说明

`handwrite/main_control.py` 顶部的 `POINT` 是主要配置区：

- `PICK_Z`：抓取下降到物料表面的 Z 值；
- `PICK_DX` / `PICK_DY`：对 DVS 返回的机器人 X/Y 做统一偏移；
- `PLACE`：每个类别对应的放置点，格式通常为 `(x, y, z, r)`；
- `RELEASE_BLOW`：放气持续时间，芯片放不下来时可适当加大；
- `RELEASE_WAIT`：放气/断吸后的等待时间；
- `RELEASE_RETRY`：释放重试次数；
- `DVS_WAIT`：等待 DVS 图片落盘的最长秒数。

公开模板里所有真实点位都已置空。连接真实设备前必须自行完成标定并填写坐标。

## 脚本说明

### 一键创建并上传仓库

根目录入口：

```bat
一键创建并上传仓库.cmd
```

实际逻辑在：

```text
scripts/10-create-repo-and-push.ps1
```

默认仓库名：`raicom-mg400-vision-open`。默认 GitHub 用户：`xiaohj233`。remote 使用 SSH：

```text
git@github.com:xiaohj233/raicom-mg400-vision-open.git
```

脚本会优先使用 GitHub CLI 创建公开仓库。如果没有安装 `gh`，请先安装 GitHub CLI，或手动在 GitHub 创建仓库后再运行 push。脚本不包含 token，使用当前 GitHub CLI 登录态或用户已有 SSH key。

### 一键发布版本

根目录入口：

```bat
一键发布版本.cmd
```

实际逻辑在：

```text
scripts/70-release-version.ps1
```

脚本会读取 `VERSION`，生成类似下面的 zip：

```text
raicom-mg400-vision-open-v0.1.0.zip
```

然后创建 `v0.1.0` tag，并尝试 push tag。若已安装并登录 GitHub CLI，会继续创建 GitHub Release；否则只生成 tag 和 zip，并提示手动上传。

## 常见问题

### DVS 收到 `PHOTO` 而不是 `TRIGGER`

`PHOTO` 是 Python 发给 Lua 的机器人拍照位命令，不应该发给 DVS。DVS 侧应监听 Python 发送的 `TRIGGER`。检查端口：Lua 默认连 `5001`，DVS 默认连 `5002`。

### `IMG` 缺少路径

DVS 必须返回类似：

```text
IMG,images/current.bmp
```

如果只返回 `IMG`，Python 无法知道要读取哪张图片。

### DVS 图片目录为空

如果 DVS 返回 `IMG,images`，Python 会等待目录中出现 `current.bmp` 或最新图片。更稳定的做法是让 DVS 直接保存并发送完整路径：`IMG,images/current.bmp`。

### 找不到 `best.pt`

公开仓库不上传真实权重。请先准备基础模型 `models/yolo11n.pt`，放入训练数据后运行：

```bat
python handwrite\module_b.py
```

训练完成后应生成 `models/best.pt`。

### 抓取 X/Y 偏

先检查 DVS 标定和变量计算，再微调 `PICK_DX` / `PICK_DY`。不要直接把 YOLO 图像坐标当机器人坐标。

### 抓取 Z 不准

调整 `PICK_Z`。建议先用较安全的高度试运行，再逐步下降到可吸取物料的位置。

### 芯片放不下来

适当增加 `RELEASE_BLOW`、`RELEASE_WAIT` 或 `RELEASE_RETRY`，并检查 Lua 中 `BLOW` 对应的 DO 口是否接对。

### Lua 连不上 Python

确认 `handwrite/robot_executor.lua` 里的 `IP` 是 Python 电脑 IP，并确认 Windows 防火墙允许 Python 监听 `5001`。

### Python 连不上 DVS

确认 DVS TCP 客户端连接到 Python 电脑的 `5002`，并且 Python 控制界面已经启动。

### YOLO 类别和 DVS 点位对应不上

本项目默认用 YOLO 框中心点与 DVS `POINT` 的图像坐标 `px,py` 做最近距离匹配。需要确保 DVS 输出的 `px,py` 与 YOLO 使用的是同一张图片、同一分辨率、同一坐标系。

## 免责声明

本项目不包含官方赛题资料、评分表、Dobot/DVS 官方软件、商业许可文件、现场标定文件、真实比赛数据和训练权重。使用者需自行准备设备、软件、相机标定、数据集和模型。

本项目仅用于学习、复盘和二次开发。Dobot、MG400、DobotVisionStudio、YOLO 等名称归各自权利方所有。第三方依赖遵循其各自许可证。

## 许可证

本仓库自写代码和文档使用 MIT License，详见 [LICENSE](LICENSE)。
