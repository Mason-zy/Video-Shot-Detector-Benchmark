# 镜头分割算法对比工具

> 一个用于对比分析多种镜头分割（Shot Boundary Detection）算法的 Python 工具

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 简介

本工具集成了三种主流的视频镜头分割算法，帮助你快速对比不同算法的检测效果：

| 算法 | 类型 | 特点 |
|------|------|------|
| **PySceneDetect** | 传统算法 | 基于 OpenCV，快速稳定 |
| **FFmpeg** | 传统算法 | 使用场景检测滤镜，高效轻量 |
| **TransNet V2** | 深度学习 | SOTA 模型，精度最高 |

## 核心功能

- ✅ **一键对比** - 同时运行多个算法，自动生成对比报告
- ✅ **物理切割** - 自动将视频按镜头边界切分为独立片段
- ✅ **参数可调** - 支持自定义各算法的检测阈值和参数
- ✅ **详细报告** - 生成 CSV、JSON、TXT 多种格式的分析报告
- ✅ **模块化设计** - 每个算法独立封装，易于扩展

## 快速开始

### 安装依赖

```bash
# 克隆项目
git clone <repository_url>
cd videoFen

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 FFmpeg (Ubuntu/WSL)
sudo apt update && sudo apt install ffmpeg -y
```

### 基础使用

```bash
# 运行所有算法
python src/main.py your_video.mp4

# 只运行指定算法
python src/main.py your_video.mp4 -a pyscene

# 同时运行 PySceneDetect 和 TransNet V2
python src/main.py your_video.mp4 -a pyscene transnet
```
【已经内置无需自己找模型文件】
<!-- ### TransNet V2 配置（可选）

如需使用 TransNet V2 深度学习算法，请参考 [TransNetV2 安装指南](TRANSNETV2_SETUP_GUIDE.md)。 

```bash
# 创建模型目录
mkdir -p models/transnetv2

# 从官方仓库下载模型文件
# https://github.com/soCzech/TransNetV2
``` -->

## 使用说明

### 命令行参数

```bash
python src/main.py VIDEO_PATH [OPTIONS]
```

**基本参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-a, --algorithms` | 选择算法（pyscene/ffmpeg/transnet） | 全部 |
| `-o, --output-dir` | 输出目录 | output |
| `--first-only` | 只运行第一个成功的算法 | False |

**PySceneDetect 参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--pyscene-threshold` | 内容变化阈值（越小越敏感） | 27.0 |
| `--pyscene-min-scene-len` | 最小镜头长度（帧） | 15 |

**FFmpeg 参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--ffmpeg-threshold` | 场景变化阈值（0.0-1.0） | 0.3 |
| `--ffmpeg-min-scene-len` | 最小镜头长度（秒） | 1.0 |

**TransNet V2 参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--transnet-model-dir` | 模型文件路径 | ./models/transnetv2 |

### 使用示例

**示例 1：快速测试单个算法**
```bash
python src/main.py data/test_video.mp4 -a pyscene
```

**示例 2：对比两个算法**
```bash
python src/main.py data/test_video.mp4 -a pyscene ffmpeg
```

**示例 3：调整检测灵敏度**
```bash
python src/main.py data/test_video.mp4 \
  --pyscene-threshold 20.0 \
  --ffmpeg-threshold 0.2
```

**示例 4：使用深度学习算法**
```bash
python src/main.py data/test_video.mp4 -a transnet \
  --transnet-model-dir ./models/transnetv2
```

## 输出结果

运行后会生成带时间戳的输出目录：

```
output/shot_comparison_20241126_1430/
├── pyscene/                    # PySceneDetect 切割结果
│   ├── shot_01_00m00s_to_00m05s.mp4
│   ├── shot_02_00m05s_to_00m12s.mp4
│   └── ...
├── ffmpeg/                     # FFmpeg 切割结果
│   └── ...
├── transnet/                   # TransNet V2 切割结果
│   └── ...
├── report.csv                  # 基本对比报告
├── detailed_report.json        # 详细报告（含每个镜头信息）
└── analysis_summary.txt        # 分析摘要
```

### 报告内容

**report.csv** - 算法对比概览：

| 字段 | 说明 |
|------|------|
| 算法名称 | 使用的算法 |
| 检测镜头数 | 检测到的镜头边界数量 |
| 处理时间 | 算法运行耗时 |
| 平均镜头时长 | 所有镜头的平均时长 |
| 成功率 | 处理成功率 |

**detailed_report.json** - 每个镜头的详细信息：
- 起始/结束帧号
- 起始/结束时间
- 镜头持续时间
- 输出文件名

## 项目结构

```
videoFen/
├── src/                        # 源代码
│   ├── main.py                # 主程序入口
│   ├── shot_detector.py       # 基础检测器抽象类
│   ├── pyscene_detector.py    # PySceneDetect 实现
│   ├── ffmpeg_detector.py     # FFmpeg 实现
│   ├── transnet_detector.py   # TransNet V2 实现
│   ├── output_manager.py      # 输出管理器
│   └── config.py              # 配置管理
├── tools/                      # 工具脚本
│   └── create_test_video.py   # 测试视频生成器
├── data/                       # 测试数据
├── models/                     # 模型文件
│   └── transnetv2/            # TransNet V2 模型
├── output/                     # 输出目录（自动创建）
├── requirements.txt            # Python 依赖
└── README.md                   # 本文件
```

## 算法调优建议

### PySceneDetect

- **适用场景**：通用场景，快速检测
- **threshold**：降低值提高敏感度（建议 15-35）
- **min_scene_len**：避免过短镜头（建议 10-30 帧）

### FFmpeg

- **适用场景**：需要快速处理大量视频
- **threshold**：0.2-0.4 之间通常效果较好
- **min_scene_len**：建议 0.5-2.0 秒

### TransNet V2

- **适用场景**：高精度要求的专业应用
- **优点**：检测精度高，泛化能力强
- **缺点**：需要 TensorFlow，处理速度较慢

## 系统要求

### 必需
- Python 3.7 或更高版本
- FFmpeg（命令行工具）
- 至少 4GB RAM（使用 TransNet V2 时建议 8GB+）

### Python 依赖
- opencv-python >= 4.5.0
- numpy >= 1.19.0
- scenedetect >= 0.6.0
- tensorflow >= 2.8.0（仅 TransNet V2）
- tqdm >= 4.62.0

详见 [requirements.txt](requirements.txt)

## 常见问题

<details>
<summary><b>FFmpeg 未找到</b></summary>

确保 FFmpeg 已正确安装并添加到系统 PATH：

```bash
# 检查 FFmpeg 是否安装
ffmpeg -version

# Ubuntu/WSL 安装
sudo apt install ffmpeg

# 验证安装
which ffmpeg
```
</details>

<details>
<summary><b>TransNet V2 模型文件不存在</b></summary>

从官方仓库下载模型文件：

1. 访问 [TransNetV2 GitHub](https://github.com/soCzech/TransNetV2)
2. 下载预训练权重文件
3. 放置到 `models/transnetv2/` 目录

或者只使用传统算法：`-a pyscene ffmpeg`
</details>

<details>
<summary><b>内存不足错误</b></summary>

对于大视频文件：
- 使用传统算法：`-a pyscene ffmpeg`
- 分段处理视频
- 增加系统交换空间
</details>

<details>
<summary><b>检测到的镜头过多/过少</b></summary>

调整检测阈值：

```bash
# 降低灵敏度（检测更少镜头）
python src/main.py video.mp4 --pyscene-threshold 35.0

# 提高灵敏度（检测更多镜头）
python src/main.py video.mp4 --pyscene-threshold 15.0
```
</details>

## 开发计划

- [ ] 支持批量处理多个视频
- [ ] 添加 GUI 界面
- [ ] 支持更多算法（Katna、PyAV 等）
- [ ] 优化大视频文件处理性能
- [ ] 添加视频预览功能

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 相关资源

- [PySceneDetect 文档](https://scenedetect.com/)
- [FFmpeg 官方网站](https://ffmpeg.org/)
- [TransNet V2 论文](https://arxiv.org/abs/2008.04838)
- [TransNet V2 GitHub](https://github.com/soCzech/TransNetV2)

## 致谢

- PySceneDetect 团队
- TransNet V2 作者
- FFmpeg 社区

---

**如有问题或建议，欢迎提交 [Issue](../../issues)**
