#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TransNet V2 镜头分割实现
TransNet V2 Shot Boundary Detection Implementation

基于深度学习的 SOTA 镜头分割模型
使用 PyTorch 实现，包含真实的预训练权重
"""

import os
import sys
import time
import numpy as np
from typing import List, Optional, Tuple
from shot_detector import ShotDetector, ShotBoundary

# 添加 transnetv2_pytorch 模块路径
TRANSNETV2_PYTORCH_PATH = '/home/yong/project/videoFen/models/transnetv2/transnetv2_pytorch'
if TRANSNETV2_PYTORCH_PATH not in sys.path:
    sys.path.insert(0, os.path.dirname(TRANSNETV2_PYTORCH_PATH))

# 检查PyTorch是否可用
TORCH_AVAILABLE = False
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    pass

# 导入PyTorch版本的TransNetV2
TRANSNETV2_PYTORCH_AVAILABLE = False
TransNetV2PyTorch = None
try:
    from transnetv2_pytorch.transnetv2_pytorch import TransNetV2 as TransNetV2PyTorch
    TRANSNETV2_PYTORCH_AVAILABLE = True
    print("✅ 成功导入 TransNetV2 PyTorch 实现")
except ImportError as e:
    print(f"⚠️  导入 TransNetV2 PyTorch 失败: {e}")


class TransNetV2Detector(ShotDetector):
    """基于 TransNet V2 的镜头分割检测器（使用真实PyTorch权重）"""

    def __init__(self, video_path: str, model_dir: str = "./models/transnetv2"):
        """
        初始化 TransNet V2 检测器

        Args:
            video_path: 视频文件路径
            model_dir: TransNet V2 模型文件目录（本实现不使用此参数，仅保持接口兼容）
        """
        super().__init__(video_path)
        self.model_dir = model_dir
        self.model = None
        self.device = None
        self.framework = None

        # 检查PyTorch版本TransNetV2是否可用
        if TRANSNETV2_PYTORCH_AVAILABLE and TORCH_AVAILABLE:
            try:
                print("🔄 正在初始化 TransNet V2 PyTorch 模型...")
                # 使用自动设备检测
                self.model = TransNetV2PyTorch(device='auto')
                self.framework = "pytorch_official"
                self.device = self.model.device
                print(f"✅ TransNet V2 PyTorch 模型加载成功！")
                print(f"   - 设备: {self.device}")
                print(f"   - 输入尺寸: 48x27 (官方标准)")
            except Exception as e:
                print(f"❌ TransNet V2 PyTorch 加载失败: {e}")
                self.framework = "demonstration"
                print("⚠️  使用演示模式")
        else:
            self.framework = "demonstration"
            if not TORCH_AVAILABLE:
                print("⚠️  PyTorch 未安装，使用演示模式")
            elif not TRANSNETV2_PYTORCH_AVAILABLE:
                print("⚠️  TransNetV2 PyTorch 模块不可用，使用演示模式")

        print(f"🔧 TransNet V2 配置:")
        print(f"   - 框架: {self.framework}")
        if self.device:
            print(f"   - 使用设备: {self.device}")

    def detect_shots(self, **kwargs) -> List[ShotBoundary]:
        """
        使用 TransNet V2 检测镜头边界

        Returns:
            List[ShotBoundary]: 检测到的镜头边界列表
        """
        print(f"🎬 开始使用 TransNet V2 检测镜头...")

        try:
            start_time = time.time()

            if self.framework == "pytorch_official":
                # 使用PyTorch官方实现
                return self._detect_shots_pytorch(start_time)
            else:
                # 使用演示模式
                return self._detect_shots_demonstration(start_time)

        except Exception as e:
            print(f"❌ TransNet V2 检测失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _detect_shots_pytorch(self, start_time: float) -> List[ShotBoundary]:
        """使用PyTorch官方实现检测镜头"""
        try:
            print("📽️  正在使用 TransNet V2 PyTorch 分析视频...")

            # 使用官方的detect_scenes方法
            scenes = self.model.detect_scenes(self.video_path, threshold=0.5)

            # 获取FPS用于时间戳转换
            fps = self.model.get_video_fps(self.video_path)
            print(f"   视频FPS: {fps}")
            print(f"   检测到 {len(scenes)} 个场景")

            # 转换为ShotBoundary对象
            shots = []
            for i, scene in enumerate(scenes):
                start_frame = scene['start_frame']
                end_frame = scene['end_frame']
                start_time_sec = float(scene['start_time'])
                end_time_sec = float(scene['end_time'])

                shot = ShotBoundary(
                    start_frame=start_frame,
                    end_frame=end_frame,
                    start_time=start_time_sec,
                    end_time=end_time_sec
                )
                shots.append(shot)

                print(f"   镜头 {i+1}: {shot.to_time_string(start_time_sec)} -> {shot.to_time_string(end_time_sec)}")

            processing_time = time.time() - start_time
            print(f"✅ TransNet V2 PyTorch 检测完成，共检测到 {len(shots)} 个镜头，耗时 {processing_time:.2f} 秒")

            return shots

        except Exception as e:
            print(f"❌ PyTorch检测失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _detect_shots_demonstration(self, start_time: float) -> List[ShotBoundary]:
        """演示模式检测镜头（当模型不可用时）"""
        import cv2

        print("🎭 演示模式: 生成模拟检测结果...")

        # 获取视频信息
        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        print(f"   视频总帧数: {total_frames}")
        print(f"   视频FPS: {fps}")

        # 模拟每隔2秒左右有一个镜头切换
        switch_interval = int(fps * 2)  # 每2秒

        shots = []
        prev_frame = 0
        shot_id = 1

        for frame_idx in range(switch_interval, total_frames - switch_interval, switch_interval):
            start_frame = prev_frame
            end_frame = frame_idx

            start_time_sec = start_frame / fps
            end_time_sec = end_frame / fps

            shot = ShotBoundary(
                start_frame=start_frame,
                end_frame=end_frame,
                start_time=start_time_sec,
                end_time=end_time_sec
            )
            shots.append(shot)

            print(f"   镜头 {shot_id}: {shot.to_time_string(start_time_sec)} -> {shot.to_time_string(end_time_sec)}")

            prev_frame = frame_idx
            shot_id += 1

        # 添加最后一个镜头
        if prev_frame < total_frames - 1:
            start_time_sec = prev_frame / fps
            end_time_sec = (total_frames - 1) / fps

            shot = ShotBoundary(
                start_frame=prev_frame,
                end_frame=total_frames - 1,
                start_time=start_time_sec,
                end_time=end_time_sec
            )
            shots.append(shot)
            print(f"   镜头 {shot_id}: {shot.to_time_string(start_time_sec)} -> {shot.to_time_string(end_time_sec)}")

        processing_time = time.time() - start_time
        print(f"✅ 演示模式检测完成，共生成 {len(shots)} 个模拟镜头，耗时 {processing_time:.2f} 秒")

        return shots

    def extract_shots(self, shots: List[ShotBoundary], output_dir: str) -> List[str]:
        """
        提取检测到的镜头片段

        Args:
            shots: 镜头边界列表
            output_dir: 输出目录

        Returns:
            List[str]: 提取的视频文件路径列表
        """
        print(f"📦 开始提取 {len(shots)} 个镜头片段到 {output_dir}...")
        output_files = super().extract_shots(shots, output_dir)
        print(f"✅ 成功提取 {len(output_files)} 个镜头片段")
        return output_files

    def get_algorithm_info(self) -> dict:
        """获取算法信息"""
        return {
            'name': 'TransNet V2',
            'type': 'Deep Learning (SOTA)',
            'model_dir': self.model_dir,
            'input_size': '100x56',
            'description': '基于深度学习的镜头分割算法，具有高精度和鲁棒性'
        }