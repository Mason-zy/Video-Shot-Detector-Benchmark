"""
TransNetV2镜头检测器

基于深度学习的镜头边界检测算法，支持批处理和流式处理模式。

依赖：
- transnetv2
- opencv-python
- numpy
"""

import cv2
import numpy as np
import os
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Shot:
    """镜头信息数据类"""
    start_frame: int     # 起始帧号
    end_frame: int       # 结束帧号
    start_time: float    # 起始时间(秒)
    end_time: float      # 结束时间(秒)
    duration: float      # 镜头时长(秒)


class TransNetDetector:
    """TransNetV2镜头检测器封装"""

    def __init__(self, model_dir: str = None, streaming: bool = False, device: str = 'auto'):
        """
        初始化检测器

        Args:
            model_dir: TransNetV2模型目录路径(可选，自动查找)
            streaming: 是否使用流式处理模式
            device: 设备类型('auto'/'cuda'/'cpu')
        """
        if model_dir is None:
            model_dir = self._find_model_directory()

        self.model_dir = model_dir
        self.streaming = streaming
        self.device = device
        self._model = None
        # 延迟检查模型，不在初始化时打印警告

    def _find_model_directory(self) -> str:
        """自动查找TransNetV2模型目录"""
        possible_paths = [
            "./models/transnetv2",
            "../models/transnetv2",
            "../../models/transnetv2",
            "/home/yong/project/videoFen/models/transnetv2",
            os.path.expanduser("~/transnetv2_weights"),
            # 尝试使用pip安装的包
            os.path.expanduser("~/.transnetv2")
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 如果都找不到，返回默认路径
        return "./models/transnetv2"

    def detect_shots(self, video_path: str) -> List[Shot]:
        """
        检测视频中的镜头边界

        Args:
            video_path: 视频文件路径

        Returns:
            List[Shot]: 镜头列表

        Raises:
            FileNotFoundError: 视频文件不存在
            RuntimeError: 模型加载或处理失败
        """
        # 检查视频文件
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        # 加载模型
        model = self._get_model()

        try:
            if self.streaming:
                return self._detect_streaming(video_path, model)
            else:
                return self._detect_batch(video_path, model)
        except Exception as e:
            raise RuntimeError(f"镜头检测处理失败: {str(e)}")

    def _get_model(self):
        """延迟加载TransNetV2模型"""
        if self._model is None:
            # 1. 优先尝试使用本地的PyTorch实现
            if self._try_local_pytorch():
                return self._model

            # 2. 尝试安装的 transnetv2 包
            try:
                from transnetv2 import TransNetV2
                self._model = TransNetV2(model_dir=self.model_dir)
                print(f"✅ TransNetV2模型加载成功: {self.model_dir}")
                return self._model
            except ImportError:
                pass
            except Exception:
                pass

            # 3. 尝试使用本地复制的权重
            if self._try_local_weights():
                return self._model

            # 4. 所有方式都失败，打印帮助信息
            print(f"❌ 模型加载失败")
            print(f"💡 请从 https://github.com/soCzech/TransNetV2 下载模型文件")
            print(f"💡 或使用 pip install transnetv2-pytorch 安装预编译包")
            raise ImportError("无法加载TransNetV2模型，请检查安装")

        return self._model

    def _try_local_pytorch(self):
        """尝试使用本地PyTorch实现"""
        try:
            import sys
            import os
            import torch

            # 确定设备类型
            if self.device == 'auto':
                if torch.cuda.is_available():
                    device = 'cuda'
                    gpu_name = torch.cuda.get_device_name(0)
                    gpu_count = torch.cuda.device_count()
                    print(f"🚀 检测到CUDA: {gpu_count}个GPU设备")
                    print(f"🎯 主GPU: {gpu_name}")
                    print(f"⚡ 使用GPU加速处理")
                else:
                    device = 'cpu'
                    cpu_count = os.cpu_count()
                    print(f"💻 未检测到CUDA，使用CPU处理")
                    print(f"🔢 CPU核心数: {cpu_count}")
                    print(f"⚠️  处理速度可能较慢，建议在有GPU的环境下运行")
            else:
                device = self.device
                if device == 'cuda':
                    print(f"🚀 强制使用CUDA设备")
                elif device == 'cpu':
                    print(f"💻 强制使用CPU设备")
                else:
                    print(f"🔧 使用指定设备: {device}")

            # 添加本地模型路径
            model_path = os.path.join(os.path.dirname(__file__), 'models')
            sys.path.insert(0, model_path)

            from transnetv2_pytorch import TransNetV2
            self._model = TransNetV2(device=device)  # 传递设备参数
            print(f"✅ 使用本地PyTorch模型: {device.upper()}设备")
            return True

        except Exception as e:
            print(f"⚠️  本地PyTorch模型加载失败: {str(e)}")
            return False

    def _try_local_weights(self):
        """尝试使用本地权重文件"""
        try:
            weights_file = os.path.join(os.path.dirname(__file__), 'models', 'transnetv2-pytorch-weights.pth')

            if os.path.exists(weights_file):
                print(f"✅ 找到本地权重文件: {weights_file}")
                # 这里需要实现一个简单的权重加载器
                print("💡 请安装 transnetv2-pytorch 来使用此权重文件")
                return False
            else:
                return False

        except Exception:
            return False

    def _detect_batch(self, video_path: str, model) -> List[Shot]:
        """
        批处理模式检测镜头

        适合小文件，一次性处理所有帧
        """
        print(f"🎬 开始批处理模式检测: {video_path}")

        # 1. 使用TransNetV2预测
        video_frames, single_frame_predictions, _ = \
            model.predict_video(video_path)

        # 2. 获取镜头边界 (本地实现的API)
        scenes = model.predictions_to_scenes(single_frame_predictions)

        # 3. 获取视频属性
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        # 4. 转换为Shot对象
        shots = []
        for start_frame, end_frame in scenes:
            start_time = start_frame / fps
            end_time = end_frame / fps
            duration = end_time - start_time

            shot = Shot(
                start_frame=start_frame,
                end_frame=end_frame,
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )
            shots.append(shot)

        print(f"✅ 批处理检测完成，发现 {len(shots)} 个镜头")
        return shots

    def _detect_streaming(self, video_path: str, model, batch_size: int = 100) -> List[Shot]:
        """
        流式处理模式检测镜头

        适合大文件，分批处理以节省内存
        """
        print(f"🎬 开始流式模式检测: {video_path} (批次大小: {batch_size})")

        # 1. 打开视频流
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"📹 视频信息: {total_frames}帧, {fps:.2f}fps, {total_frames/fps:.1f}秒")

        # 2. 流式处理变量
        frame_buffer = []
        predictions = []
        shot_boundaries = []
        frame_idx = 0

        # 3. 逐帧读取和处理
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 预处理帧（resize到27x48）
            processed_frame = cv2.resize(frame, (48, 27))
            frame_buffer.append(processed_frame)

            # 累积到batch_size时进行预测
            if len(frame_buffer) == batch_size or frame_idx == total_frames - 1:
                # 批量预测
                batch_frames = np.array(frame_buffer)
                batch_predictions = model.predict_frames(batch_frames)[0]  # 单帧预测

                predictions.extend(batch_predictions.tolist())

                # 检测镜头边界
                for i, pred in enumerate(batch_predictions):
                    if pred > 0.5:  # 镜头边界阈值
                        boundary_frame = frame_idx - len(batch_predictions) + i + 1
                        if boundary_frame > 0:
                            shot_boundaries.append(boundary_frame)

                # 清空缓冲区
                frame_buffer = []

                # 显示进度
                if frame_idx % 1000 == 0:
                    progress = (frame_idx / total_frames) * 100
                    print(f"⏳ 处理进度: {progress:.1f}% ({frame_idx}/{total_frames})")

            frame_idx += 1

        # 4. 构建镜头列表
        shots = self._build_shots_from_boundaries(shot_boundaries, fps, total_frames)

        cap.release()
        print(f"✅ 流式检测完成，发现 {len(shots)} 个镜头")
        return shots

    def _build_shots_from_boundaries(self, boundaries: List[int], fps: float, total_frames: int) -> List[Shot]:
        """从镜头边界构建镜头列表"""
        shots = []

        if not boundaries:
            # 没有检测到镜头边界，整个视频作为一个镜头
            shots.append(Shot(
                start_frame=0,
                end_frame=total_frames - 1,
                start_time=0.0,
                end_time=(total_frames - 1) / fps,
                duration=(total_frames - 1) / fps
            ))
            return shots

        # 第一个镜头：从开始到第一个边界
        start_frame = 0
        for boundary_frame in boundaries:
            end_frame = boundary_frame

            shot = Shot(
                start_frame=start_frame,
                end_frame=end_frame,
                start_time=start_frame / fps,
                end_time=end_frame / fps,
                duration=(end_frame - start_frame) / fps
            )
            shots.append(shot)
            start_frame = end_frame

        # 最后一个镜头：从最后一个边界到视频结束
        if start_frame < total_frames:
            shot = Shot(
                start_frame=start_frame,
                end_frame=total_frames - 1,
                start_time=start_frame / fps,
                end_time=(total_frames - 1) / fps,
                duration=(total_frames - 1 - start_frame) / fps
            )
            shots.append(shot)

        return shots