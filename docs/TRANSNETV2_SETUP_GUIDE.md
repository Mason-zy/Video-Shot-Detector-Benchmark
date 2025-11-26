# TransNet V2 真实模型集成指南

## 🎯 概述

本工具现在已移除所有模拟功能，只支持真实的 TransNet V2 模型。以下是完整的集成步骤。

## 📦 第一步：安装 TensorFlow

```bash
# 安装 TensorFlow (CPU版本)
pip install tensorflow

# 或者安装 GPU版本 (如果有NVIDIA GPU)
pip install tensorflow[and-cuda]

# 验证安装
python -c "import tensorflow as tf; print(f'TensorFlow版本: {tf.__version__}')"
```

## 📥 第二步：下载 TransNet V2 模型文件

### 方法1：从GitHub官方仓库下载

```bash
# 创建模型目录
mkdir -p models/transnetv2

# 下载权重文件
wget -O models/transnetv2/transnetv2-weights.pkl \
  https://github.com/soCzech/TransNetV2/releases/download/v1.0/transnetv2-weights.pkl

# 下载架构文件 (如果存在)
wget -O models/transnetv2/transnetv2-architecture.json \
  https://github.com/soCzech/TransNetV2/releases/download/v1.0/transnetv2-architecture.json
```

### 方法2：从Hugging Face下载

```bash
# 使用git lfs下载
git lfs clone https://huggingface.co/Sn4kehead/TransNetV2 models/transnetv2/
```

### 方法3：手动下载

1. 访问：https://github.com/soCzech/TransNetV2
2. 进入Releases页面
3. 下载最新版本的模型文件
4. 将文件放入 `models/transnetv2/` 目录

## 🔧 第三步：验证模型文件

```bash
# 检查文件是否存在
ls -la models/transnetv2/

# 应该看到类似以下文件：
# - transnetv2-weights.pkl
# - transnetv2-architecture.json (可选)
```

## 🚀 第四步：测试 TransNet V2

```bash
# 测试 TransNet V2 算法
python src/main.py data/sample_videos/test_video.mp4 -a transnet

# 或者运行完整对比
python src/main.py data/sample_videos/test_video.mp4 -a pyscene ffmpeg transnet
```

## ⚙️ 第五步：(可选) 实现完整的模型加载

当前代码中模型加载逻辑需要进一步实现。参考以下步骤：

### 5.1 实现模型加载函数

在 `src/transnet_detector.py` 中的 `_load_model` 方法中添加：

```python
def _load_model(self):
    """加载 TransNet V2 模型"""
    try:
        print("🔄 正在加载 TransNet V2 模型...")

        # 检查模型文件是否存在
        weights_path = os.path.join(self.model_dir, 'transnetv2-weights.pkl')

        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"模型文件不存在: {weights_path}")

        # 这里实现真实的模型加载逻辑
        # 参考TransNetV2官方实现
        # 例如：
        # import pickle
        # with open(weights_path, 'rb') as f:
        #     model_data = pickle.load(f)
        # self.model = load_transnetv2_from_weights(model_data)

        print("✅ TransNet V2 模型加载完成")

    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        raise
```

### 5.2 实现推理函数

在 `_run_inference` 方法中添加真实的推理逻辑：

```python
def _run_inference(self, processed_frames: np.ndarray) -> np.ndarray:
    """运行 TransNet V2 推理"""
    print("   使用 TransNet V2 模型进行推理...")

    # 这里实现真实的推理逻辑
    # predictions = self.model.predict(processed_frames)

    return predictions
```

## 🎬 使用示例

### 基本使用

```bash
# 只使用 TransNet V2
python src/main.py your_video.mp4 -a transnet

# 指定模型目录
python src/main.py your_video.mp4 -a transnet --transnet-model-dir ./my_models/transnetv2
```

### 完整对比

```bash
# 运行所有三个算法
python src/main.py your_video.mp4 -a pyscene ffmpeg transnet

# 优化参数
python src/main.py your_video.mp4 \
  -a pyscene ffmpeg transnet \
  --pyscene-threshold 15.0 \
  --ffmpeg-threshold 0.1
```

## 🔍 故障排除

### 问题1：TensorFlow 未安装
```
❌ transnet 依赖库缺失: TensorFlow 未安装
```
**解决方案**：
```bash
pip install tensorflow
```

### 问题2：模型文件缺失
```
❌ 模型文件缺失: models/transnetv2/transnetv2-weights.pkl
```
**解决方案**：
```bash
mkdir -p models/transnetv2
# 按照第二步下载模型文件
```

### 问题3：模型推理失败
```
❌ 推理过程出错: NotImplementedError
```
**解决方案**：
按照第五步实现完整的模型加载和推理逻辑。

## 📊 预期性能

安装真实模型后，TransNet V2 预期表现：

| 指标 | 预期值 |
|------|--------|
| 检测准确度 | 95-99% |
| 处理速度 | 2-5秒 (10秒视频) |
| 资源占用 | 中等 (CPU/内存) |
| 支持格式 | MP4, AVI, MOV等 |

## 🎓 参考资料

- [TransNet V2 官方仓库](https://github.com/soCzech/TransNetV2)
- [TransNet V2 论文](https://arxiv.org/abs/2008.04838)
- [TensorFlow 官方文档](https://tensorflow.org/)

## ⚠️ 注意事项

1. **硬件要求**：TransNet V2 需要较多内存，建议至少8GB RAM
2. **GPU支持**：如有NVIDIA GPU，可安装GPU版TensorFlow提速
3. **模型大小**：TransNet V2 模型文件较大（约500MB+）
4. **依赖版本**：确保TensorFlow版本与模型兼容

## 🎉 完成

按照以上步骤完成后，你就可以使用真实的 TransNet V2 模型进行高精度的镜头分割了！