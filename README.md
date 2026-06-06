# raicom-mg400-vision-open

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)

一个用于 **MG400 + DobotVisionStudio + YOLO** 的机器视觉抓取开源示例项目。

本项目提供 Python 控制界面、Lua 机器人执行脚本、DobotVisionStudio TCP 通信协议、YOLO 训练/推理入口，以及可复用的 `vision_motion_kit` 源码库。仓库只包含自写代码和说明文档，不包含第三方官方资料、商业软件、授权文件、私有数据、标定文件或训练权重。

## 文档导航

- [项目简介](#项目简介)
- [适用硬件与软件](#适用硬件与软件)
- [仓库结构](#仓库结构)
- [安装方法](#安装方法)
- [运行流程](#运行流程)
- [DobotVisionStudio 使用教程](#dobotvisionstudio-使用教程)
- [DVS 协议说明](#dvs-协议说明)
- [监控框显示要求](#监控框显示要求)
- [坐标微调说明](#坐标微调说明)
- [脚本说明](#脚本说明)
- [常见问题](#常见问题)
- [免责声明](#免责声明)
- [许可证](#许可证)

## 项目简介

`raicom-mg400-vision-open` 是一个面向桌面机械臂视觉抓取的最小可运行工程模板，核心流程如下：

1. Python 控制界面向 MG400 Lua 端发送拍照位、移动、吸气、放气和结束命令；
2. Python 向 DobotVisionStudio 发送 `TRIGGER`，触发视觉流程；
3. DobotVisionStudio 返回图片路径和多个视觉点位；
4. Python 使用 YOLO 对当前图片进行识别；
5. 程序将 YOLO 检测框中心与 DVS 点位进行匹配；
6. MG400 按类别执行抓取、放置、放气释放和收尾流程。

仓库包含两层代码：

- `handwrite/`：三个短入口文件，适合快速理解整套流程；
- `vision_motion_kit/`：项目配套源码库，封装 TCP、协议、视觉解析、YOLO、点位匹配、动作流程和 UI 逻辑。

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
  .gitignore                        忽略数据、模型、标定和运行产物

  handwrite/
    main_control.py                 控制入口：UI、DVS、YOLO、抓放流程
    module_b.py                     YOLO 训练与推理入口
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

7. 在 DobotVisionStudio 中配置 TCP 输出流程，让 Python 触发后返回 `CLEAR / IMG / POINT / END`。详细流程见 [DobotVisionStudio 使用教程](#dobotvisionstudio-使用教程)。
8. 在 `handwrite/robot_executor.lua` 中把 `IP` 改成你的 Python 电脑 IP，然后在 MG400 端运行 Lua 脚本。
9. 在 `handwrite/main_control.py` 中填写 `POINT`：拍照位、抓取 Z、放置点、吸气/放气参数。
10. 运行控制界面：

    ```bat
    python handwrite\main_control.py
    ```

11. 点击界面的 `Photo`，Python 会让机器人到拍照位，然后向 DVS 发送 `TRIGGER`。
12. 检查监控框输出，正常格式为 `类型,置信度,X坐标,Y坐标`，最后输出 `End`。

## DobotVisionStudio 使用教程

本节说明如何在 DobotVisionStudio 中制作一个可被 Python 自动触发的视觉流程。DVS 负责拍照、保存当前图片、提取目标点位、把图像坐标转换为机器人坐标，并通过 TCP 发回 Python；YOLO 类别识别和机器人抓放逻辑由 Python 完成。

### 1. 最终流程总览

推荐的 DVS 结构如下：

```text
通信管理：TCP 客户端连接 Python 5002
通信管理：接收事件解析 TRIGGER
响应配置 / 全局触发：收到 TRIGGER 后执行目标流程

目标流程：
图像源1
↓
输出图像1
↓
图像二值化1
↓
形态学处理1
↓
BLOB分析1
↓
标定转换1
↓
协议组装_CLEAR
↓
发送数据_CLEAR
↓
协议组装_IMG
↓
发送数据_IMG
↓
协议组装_POINT0
↓
发送数据_POINT0
↓
协议组装_POINT1
↓
发送数据_POINT1
↓
协议组装_POINT2
↓
发送数据_POINT2
↓
协议组装_POINT3
↓
发送数据_POINT3
↓
协议组装_POINT4
↓
发送数据_POINT4
↓
协议组装_POINT5
↓
发送数据_POINT5
↓
协议组装_END
↓
发送数据_END
```

DVS 最终发给 Python 的内容应类似：

```text
CLEAR
IMG,images/current.bmp
POINT,px,py,robot_x,robot_y,angle
POINT,px,py,robot_x,robot_y,angle
POINT,px,py,robot_x,robot_y,angle
POINT,px,py,robot_x,robot_y,angle
POINT,px,py,robot_x,robot_y,angle
POINT,px,py,robot_x,robot_y,angle
END
```

字段含义：

- `px,py`：DVS 原图坐标，用来和 YOLO 检测框中心匹配；
- `robot_x,robot_y`：通过手眼标定或变量计算得到的机器人抓取坐标；
- `angle`：目标角度。优先使用标定转换输出角度；如果暂时没有角度输出，可以先用 BLOB 角度或 `0`，再在抓取端补偿。

### 2. 文件路径约定

开源模板统一使用仓库内相对路径：

```text
images/current.bmp
```

如果 DVS 软件界面必须填写绝对保存目录，可以选择你的仓库实际路径下的 `images` 目录，但不要把个人电脑路径写死到代码或提交到仓库。推荐：

```text
保存目录：<repo>\images
文件名：current
格式：bmp
覆盖保存：开启
```

最终 Python 侧收到的 `IMG` 推荐为：

```text
IMG,images/current.bmp
```

不要使用时间戳文件名，不要自动编号，否则 Python 可能读到旧图或找不到图片。

### 3. 通信设备设置

打开：

```text
系统 → 通信管理 → 设备管理
```

新建或选择一个 TCP 客户端：

```text
设备类型：TCP客户端
目标 IP：Python 电脑 IP
目标端口：5002
```

如果 DVS 和 Python 在同一台电脑，可以使用：

```text
目标 IP：127.0.0.1
目标端口：5002
```

如果不在同一台电脑，目标 IP 填 Python 电脑的局域网 IP。Python 端会监听 `5002`，DVS 连接成功后，控制界面日志应出现 DVS 已连接的提示。

### 4. 接收事件设置：让 Python 的 TRIGGER 触发 DVS

Python 点击 `Photo` 后会给 DVS 发送：

```text
TRIGGER
```

DVS 需要配置成：

```text
收到 TRIGGER → 自动运行目标流程
```

创建接收事件：

```text
系统 → 通信管理 → 接收事件
```

建议参数：

```text
处理方式：文本
处理类型：协议解析
绑定设备：前面创建的 TCP 客户端
分隔符：,
字符长度比较：关
```

输出列表添加一行：

```text
名称：cmd
类型：字符串 / 文本
数据结果：接收内容 / 第1段 / 索引0
```

因为 Python 只发送 `TRIGGER`，所以把整条文本解析成 `cmd` 即可。

接着打开：

```text
通信管理 → 响应配置
```

或：

```text
系统 → 全局触发
```

新增规则：

```text
触发源：接收事件的文本协议解析结果
条件：cmd == TRIGGER
触发动作：运行流程 / 执行流程
目标流程：包含图像源、BLOB、标定转换和发送数据的流程
执行方式：执行一次
```

如果软件界面没有条件判断，也可以设置为收到该接收事件后直接执行目标流程。配置完成后，测试时不要手动点 DVS 的运行按钮，应由 Python 自动触发。

### 5. 图像源1

添加模块：

```text
图像采集 → 图像源
```

建议：

```text
名称：图像源1
输入：工业相机
触发方式：稳定可重复的触发方式
曝光：固定曝光
增益：固定增益
光源：固定亮度
输出：图像源1.输出图像
```

目标是让所有目标都在视野范围内，图像清晰，光照稳定，目标和背景对比明显。

### 6. 输出图像1

添加模块：

```text
图像采集 → 输出图像
```

建议参数：

```text
名称：输出图像1
输入源：图像源1.输出图像
保存目录：<repo>\images
文件名：current
格式：bmp
覆盖保存：开启
```

最终图片对应仓库相对路径：

```text
images/current.bmp
```

这个文件会给 Python 调用 YOLO 推理使用。

### 7. 图像二值化1

添加模块：

```text
图像处理 → 图像二值化
```

可从以下参数开始调试：

```text
名称：图像二值化1
输入源：图像源1.输出图像
二值化类型：硬阈值二值化
低阈值：23
高阈值：255
```

目标效果：目标主体为白色，背景为黑色，多个目标都能被分出来。若漏检深色目标，可把低阈值从 `23` 降到 `20` 或 `18`；若噪点太多，可把低阈值升到 `25` 或 `28`。光照变化明显时，优先固定光源和曝光，再考虑自动二值化方案。

### 8. 形态学处理1

添加模块：

```text
图像处理 → 形态学处理
```

可从以下参数开始：

```text
名称：形态学处理1
输入源：图像二值化1.输出图像
处理类型：开运算
形状：矩形 / 椭圆
核宽：3
核高：3
迭代次数：1
```

目标是去掉小噪点，同时保持目标彼此独立。不要让相邻目标粘连，也不要把目标腐蚀消失。如果目标内部破碎严重，可以尝试闭运算，核宽和核高仍从 `3 × 3` 开始。

### 9. BLOB分析1

添加模块：

```text
定位 → BLOB分析
```

建议参数：

```text
名称：BLOB分析1
输入源：形态学处理1.输出图像
ROI创建：绘制
ROI形状：矩形
ROI范围：框住目标随机可能出现的整个识别区
极性：亮于背景
阈值方式：单阈值
低阈值：100
查找个数：6
孔洞最小面积：0
面积使能：开
面积范围：8000 ~ 30000
轮廓输出使能：开
Blob图像输出：开
```

面积范围需要按你的实际相机高度、分辨率和目标大小微调。漏检时可以先扩大到 `5000 ~ 40000`；噪点进入时可以收紧到 `10000 ~ 30000`。ROI 应该是一个覆盖整个识别区域的大矩形，不是分别框每个目标。

需要用到的输出字段：

```text
质心X[]
质心Y[]
质心点[]
角度[]
面积[]
```

### 10. 标定转换1

添加模块：

```text
运算工具 → 标定转换
```

或先添加标定加载，再接标定转换。建议参数：

```text
名称：标定转换1
输入方式：按点
坐标点：BLOB分析1.质心点[]
角度：BLOB分析1.角度[]
坐标类型：图像坐标
标定文件：选择你自己完成的手眼标定文件
```

输出应包含：

```text
转换坐标X[]
转换坐标Y[]
转换角度[]
```

检查重点：转换后的 `X/Y` 应该是机器人坐标，通常是毫米量级；不应该仍是 `1542,1178` 这种像素值，也不应该是 `0,0`、`NaN` 或明显离谱的大数。若找不到 `转换角度[]`，POINT 的第 6 项可先使用 `BLOB分析1.角度[]` 或临时填 `0`。

### 11. 协议组装与发送

每一条消息建议用一个“协议组装”模块和一个“发送数据”模块，便于排查。不要把 `CLEAR`、`IMG`、多个 `POINT`、`END` 写在同一个发送模块里。

#### CLEAR

协议组装：

```text
名称：协议组装_CLEAR
方式选择：文本组装
分隔符：,
组装列表：
1 CLEAR
```

发送数据：

```text
名称：发送数据_CLEAR
输出至：通信设备
通信设备：前面创建的 TCP 客户端
16进制发送：关
结束符：开
发送数据1：绑定 协议组装_CLEAR.组装结果[]
```

Python 应收到：

```text
vision: CLEAR
```

#### IMG

协议组装：

```text
名称：协议组装_IMG
方式选择：文本组装
分隔符：,
组装列表：
1 IMG
2 images/current.bmp
```

如果你希望绑定 DVS 的保存路径结果，也可以把第 2 项绑定到 `输出图像1.原图保存路径[]`。开源模板更推荐 Python 侧统一使用 `images/current.bmp`。

发送数据：

```text
名称：发送数据_IMG
输出至：通信设备
通信设备：前面创建的 TCP 客户端
16进制发送：关
结束符：开
发送数据1：绑定 协议组装_IMG.组装结果[]
```

Python 应收到：

```text
vision: IMG,images/current.bmp
```

#### POINT0

协议组装：

```text
名称：协议组装_POINT0
方式选择：文本组装
分隔符：,
组装列表：
1 POINT
2 BLOB分析1.质心X[0]
3 BLOB分析1.质心Y[0]
4 标定转换1.转换坐标X[0]
5 标定转换1.转换坐标Y[0]
6 标定转换1.转换角度[0]
```

如果找不到 `转换角度[0]`，第 6 项可先用：

```text
BLOB分析1.角度[0]
```

或者临时填：

```text
0
```

发送数据：

```text
名称：发送数据_POINT0
输出至：通信设备
通信设备：前面创建的 TCP 客户端
16进制发送：关
结束符：开
发送数据1：绑定 协议组装_POINT0.组装结果[]
```

Python 应收到类似：

```text
vision: POINT,1542.326,1178.479,235.200,-118.600,85.462
```

#### POINT1 到 POINT5

复制 `POINT0` 的协议组装和发送数据模块，只改索引：

```text
POINT1：质心X[1]、质心Y[1]、转换坐标X[1]、转换坐标Y[1]、转换角度[1]
POINT2：质心X[2]、质心Y[2]、转换坐标X[2]、转换坐标Y[2]、转换角度[2]
POINT3：质心X[3]、质心Y[3]、转换坐标X[3]、转换坐标Y[3]、转换角度[3]
POINT4：质心X[4]、质心Y[4]、转换坐标X[4]、转换坐标Y[4]、转换角度[4]
POINT5：质心X[5]、质心Y[5]、转换坐标X[5]、转换坐标Y[5]、转换角度[5]
```

如果你的场景目标数量不是 6 个，可以按实际数量增删 POINT 模块，并同步调整 Python 侧逻辑。

#### END

协议组装：

```text
名称：协议组装_END
方式选择：文本组装
分隔符：,
组装列表：
1 END
```

发送数据：

```text
名称：发送数据_END
输出至：通信设备
通信设备：前面创建的 TCP 客户端
16进制发送：关
结束符：开
发送数据1：绑定 协议组装_END.组装结果[]
```

`END` 必须放在最后。Python 收到 `END` 后，才会把这一帧视觉结果交给 YOLO 和抓放流程处理。

### 12. 和 Python 代码的关系

当前 Python 流程是：

```text
发送 PHOTO 给 Lua
等待 READY_PHOTO
发送 TRIGGER 给 DVS
等待 DVS 回 CLEAR / IMG / POINT / END
调用 YOLO 识别 current.bmp
匹配 YOLO 类别与 DVS POINT
控制机器人抓放
```

DVS 不负责识别类别，也不负责决定放置位置。类别由 YOLO 给，放置位置由 `handwrite/main_control.py` 顶部的 `POINT["PLACE"]` 表给。DVS 只需要保证收到 `TRIGGER` 后回传完整视觉帧。

### 13. YOLO 和 DVS 点如何对应

DVS 的 `POINT` 里有：

```text
px,py
```

YOLO 识别结果也有检测框中心：

```text
px,py
```

Python 会做最近邻匹配：

```text
YOLO 检测框中心
↓
找最近的 DVS BLOB 质心
↓
得到该类别对应的 robot_x、robot_y、angle
```

所以必须保证 DVS 的 `px,py` 和 YOLO 的 `px,py` 来自同一张 `images/current.bmp` 原图，且没有缩放坐标不一致的问题。经验判断：`0 ~ 50` 像素误差较好，`50 ~ 100` 像素通常仍可用，超过 `100` 像素就需要排查旧图、ROI、分辨率或坐标缩放。

### 14. 自动触发测试流程

建议按这个顺序测试：

```text
1. 启动 Python 控制界面
2. Python 显示等待 Lua:5001、等待 DVS:5002
3. 启动 Lua
4. Python 显示 Lua 已连接
5. DVS TCP 客户端连接 Python 5002
6. Python 显示 DVS 已连接
7. 不手动点 DVS 运行
8. 点击 Python 的 Photo
```

正确日志应类似：

```text
=> PHOTO
<= READY_PHOTO
=> DVS TRIGGER
vision: CLEAR
vision: IMG,images/current.bmp
vision: POINT,...
vision: POINT,...
vision: POINT,...
vision: POINT,...
vision: POINT,...
vision: POINT,...
vision: END
```

如果停在 `=> DVS TRIGGER`，说明 DVS 的接收事件没有正确触发流程。如果有 `CLEAR / IMG / END` 但没有 `POINT`，说明 BLOB 或标定转换失败。如果 YOLO 报找不到图片，优先检查 `输出图像1` 是否保存了 `images/current.bmp`。

### 15. DVS 常见问题排查

#### 协议组装报“未找到绑定数据”

常见原因：绑定了不存在的模块结果，前面的 BLOB / 标定转换没有成功执行，协议组装里有空白绑定行，或索引越界。先确认 BLOB 和标定转换都有足够结果，再重新绑定 `[0] ~ [5]`。

#### POINT 里 robot_x / robot_y 还是像素坐标

错误示例：

```text
POINT,1542.326,1178.479,1542.326,1178.479,0
```

第 4、第 5 项应绑定 `标定转换1.转换坐标X[i]` 和 `标定转换1.转换坐标Y[i]`，不要继续绑定 BLOB 质心。

#### Python 收到 CLEARIMGPOINT 连成一行

通常是发送数据模块没有启用结束符，或者把字面量 `\n` 写进了内容。发送数据模块应开启结束符，不要在协议组装内容里手打 `\n`。

#### Python 发 TRIGGER 后 DVS 不动

接收事件创建后，还需要在响应配置或全局触发里绑定“收到 TRIGGER → 执行目标流程”。同时确认 DVS TCP 客户端已连接 Python 的 `5002`。

#### BLOB 不是 6 个

常见原因是二值化阈值不合适、面积范围太窄、ROI 没框全、目标粘连或噪点进入。先确认 ROI 覆盖整个识别区，再微调低阈值和面积范围。

#### 角度不稳定

近似正方形目标的 BLOB 角度可能跳 `90°` 或 `180°`。如果槽位对方向不敏感，可以先固定角度；若必须严格方向，建议增加更稳定的定位方法，例如模板匹配或几何特征判断。

### 16. DVS 最终检查清单

```text
[ ] Python 已运行，监听 5001 / 5002
[ ] Lua 已连接 Python 5001
[ ] DVS TCP 客户端已连接 Python 5002
[ ] Python 点击 Photo 后 DVS 能自动触发目标流程
[ ] 输出图像1 能保存 images/current.bmp
[ ] BLOB 稳定输出目标点
[ ] 标定转换输出 robot_x / robot_y
[ ] POINT 第 4、第 5 项是机器人坐标，不是像素坐标
[ ] POINT 第 6 项有角度，或已明确临时使用 0
[ ] DVS 发出 CLEAR / IMG / POINT / END
[ ] Python 能调用 YOLO 识别 images/current.bmp
[ ] Python 能匹配类别、置信度、机器人坐标和角度
[ ] POINT["PLACE"] 已填入真实放置点
[ ] 单目标低速抓放成功
[ ] 全流程抓放成功
[ ] 最后 Python 显示 End
```

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

- `PHOTO`：拍照位，通常为 `(x, y, z, r)`；
- `SAFE_Z`：平移前后的安全高度；
- `PICK_Z`：抓取下降到物料表面的 Z 值；
- `PICK_DX` / `PICK_DY`：对 DVS 返回的机器人 X/Y 做统一偏移；
- `PLACE`：每个类别对应的放置点，通常为 `(x, y, z, r)`；
- `RELEASE_DO`：放气或释放动作使用的数字输出端口；
- `RELEASE_BLOW`：放气持续时间，物料放不下来时可适当加大；
- `RELEASE_WAIT`：放气/断吸后的等待时间；
- `RELEASE_RETRY`：释放重试次数；
- `DVS_CLEAR_DIRS`：触发前需要清理的图片目录；
- `DVS_WAIT`：等待 DVS 图片落盘的最长秒数。

公开模板中不提供真实设备点位。连接真实设备前，需要自行完成标定并填写坐标。

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

仓库不上传训练权重。请先准备基础模型 `models/yolo11n.pt`，放入训练数据后运行：

```bat
python handwrite\module_b.py
```

训练完成后应生成 `models/best.pt`。

### 抓取 X/Y 偏

先检查 DVS 标定和变量计算，再微调 `PICK_DX` / `PICK_DY`。不要直接把 YOLO 图像坐标当机器人坐标。

### 抓取 Z 不准

调整 `PICK_Z`。建议先用较安全的高度试运行，再逐步下降到可吸取物料的位置。

### 物料放不下来

适当增加 `RELEASE_BLOW`、`RELEASE_WAIT` 或 `RELEASE_RETRY`，并检查 Lua 中 `BLOW` 对应的 DO 口是否接对。

### Lua 连不上 Python

确认 `handwrite/robot_executor.lua` 里的 `IP` 是 Python 电脑 IP，并确认 Windows 防火墙允许 Python 监听 `5001`。

### Python 连不上 DVS

确认 DVS TCP 客户端连接到 Python 电脑的 `5002`，并且 Python 控制界面已经启动。

### YOLO 类别和 DVS 点位对应不上

本项目默认用 YOLO 框中心点与 DVS `POINT` 的图像坐标 `px,py` 做最近距离匹配。需要确保 DVS 输出的 `px,py` 与 YOLO 使用的是同一张图片、同一分辨率、同一坐标系。

## 免责声明

本项目不是 Dobot 官方项目。仓库不包含第三方官方资料、商业软件、授权文件、私有图片、私有标注、训练权重、设备标定文件或视觉工程文件。使用者需要自行准备硬件、软件、相机标定、数据集和模型。

本项目仅用于学习、教学演示和二次开发。Dobot、MG400、DobotVisionStudio、YOLO 等名称归各自权利方所有。第三方依赖遵循其各自许可证。

## 许可证

本仓库自写代码和文档使用 MIT License，详见 [LICENSE](LICENSE)。
