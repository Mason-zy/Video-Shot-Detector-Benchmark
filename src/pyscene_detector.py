#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySceneDetect 镜头分割实现
PySceneDetect Shot Boundary Detection Implementation

基于 OpenCV 的传统场景检测算法
"""

import time
from typing import List
from shot_detector import ShotDetector, ShotBoundary

try:
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    from scenedetect.stats_manager import StatsManager
except ImportError:
    print("⚠️  PySceneDetect 未安装，请运行: pip install scenedetect")
    exit(1)


class PySceneDetector(ShotDetector):
    """基于 PySceneDetect 的镜头分割检测器"""

    def __init__(self, video_path: str, threshold: float = 27.0, min_scene_len: int = 15):
        """
        初始化 PySceneDetect 检测器

        Args:
            video_path: 视频文件路径
            threshold: 内容变化阈值 (默认: 27.0)
            min_scene_len: 最小镜头长度 (帧数, 默认: 15)
        """
        super().__init__(video_path)
        self.threshold = threshold
        self.min_scene_len = min_scene_len

        print(f"🔧 PySceneDetect 配置:")
        print(f"   - 阈值: {threshold}")
        print(f"   - 最小镜头长度: {min_scene_len} 帧")

    def detect_shots(self, **kwargs) -> List[ShotBoundary]:
        """
        使用 PySceneDetect 检测镜头边界

        Returns:
            List[ShotBoundary]: 检测到的镜头边界列表
        """
        print(f"🎬 开始使用 PySceneDetect 检测镜头...")

        try:
            # 创建视频管理器
            video_manager = VideoManager([self.video_path])

            # 设置视频解码器参数
            video_manager.set_downscale_factor()  # 自动缩放以提高性能

            # 开始时间戳检测
            start_time = time.time()

            # 创建统计管理器和场景管理器
            stats_manager = StatsManager()
            scene_manager = SceneManager(stats_manager)

            # 添加内容检测器
            content_detector = ContentDetector(
                threshold=self.threshold,
                min_scene_len=self.min_scene_len
            )
            scene_manager.add_detector(content_detector)

            # 开始检测
            video_manager.start()
            scene_manager.detect_scenes(video_manager)

            # 获取检测到的场景列表
            scene_list = scene_manager.get_scene_list()

            # 转换为 ShotBoundary 格式
            shots = []
            for i, (start_time_pts, end_time_pts) in enumerate(scene_list):
                # 转换 PTS 为秒数
                start_seconds = start_time_pts.get_seconds()
                end_seconds = end_time_pts.get_seconds()

                # 转换为帧号
                start_frame = int(start_seconds * self.video_info['fps'])
                end_frame = int(end_seconds * self.video_info['fps'])

                shot = ShotBoundary(
                    start_frame=start_frame,
                    end_frame=end_frame,
                    start_time=start_seconds,
                    end_time=end_seconds
                )
                shots.append(shot)

                # 显示更精确的时间信息
                start_min = int(shot.start_time // 60)
                start_sec = shot.start_time % 60
                end_min = int(shot.end_time // 60)
                end_sec = shot.end_time % 60
                duration = shot.end_time - shot.start_time

                print(f"   镜头 {i+1}: {start_min:02d}m{start_sec:05.2f}s -> {end_min:02d}m{end_sec:05.2f}s (时长: {duration:.2f}s)")

            processing_time = time.time() - start_time
            print(f"✅ PySceneDetect 检测完成，共检测到 {len(shots)} 个镜头，耗时 {processing_time:.2f} 秒")

            # 释放资源
            video_manager.release()

            return shots

        except Exception as e:
            print(f"❌ PySceneDetect 检测失败: {e}")
            raise

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
            'name': 'PySceneDetect',
            'type': 'Traditional (OpenCV-based)',
            'threshold': self.threshold,
            'min_scene_len': self.min_scene_len,
            'description': '基于内容检测的传统场景分割算法'
        }