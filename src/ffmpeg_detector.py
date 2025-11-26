#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg 镜头分割实现
FFmpeg Shot Boundary Detection Implementation

基于 FFmpeg select 滤镜的场景检测
"""

import subprocess
import re
import time
from typing import List
from shot_detector import ShotDetector, ShotBoundary


class FFmpegDetector(ShotDetector):
    """基于 FFmpeg 的镜头分割检测器"""

    def __init__(self, video_path: str, threshold: float = 0.3, min_scene_len: float = 1.0):
        """
        初始化 FFmpeg 检测器

        Args:
            video_path: 视频文件路径
            threshold: 场景变化阈值 (0.0-1.0, 默认: 0.3)
            min_scene_len: 最小镜头长度 (秒, 默认: 1.0)
        """
        super().__init__(video_path)
        self.threshold = threshold
        self.min_scene_len = min_scene_len

        print(f"🔧 FFmpeg 配置:")
        print(f"   - 场景阈值: {threshold}")
        print(f"   - 最小镜头长度: {min_scene_len} 秒")

    def detect_shots(self, **kwargs) -> List[ShotBoundary]:
        """
        使用 FFmpeg 检测镜头边界

        Returns:
            List[ShotBoundary]: 检测到的镜头边界列表
        """
        print(f"🎬 开始使用 FFmpeg 检测镜头...")

        try:
            start_time = time.time()

            # 构建 FFmpeg 命令来检测场景变化
            cmd = [
                'ffmpeg',
                '-i', self.video_path,
                '-vf', f"select='gt(scene,{self.threshold})+eq(n\\,0)',showinfo",
                '-f', 'null',
                '-'
            ]

            # 执行 FFmpeg 命令并捕获输出
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg 执行失败: {result.stderr}")

            # 解析输出中的时间戳
            scene_times = self._parse_scene_timestamps(result.stderr)

            # 将时间戳转换为镜头边界
            shots = self._create_shot_boundaries(scene_times)

            processing_time = time.time() - start_time
            print(f"✅ FFmpeg 检测完成，共检测到 {len(shots)} 个镜头，耗时 {processing_time:.2f} 秒")

            return shots

        except Exception as e:
            print(f"❌ FFmpeg 检测失败: {e}")
            raise

    def _parse_scene_timestamps(self, ffmpeg_output: str) -> List[float]:
        """
        解析 FFmpeg 输出中的场景变化时间戳

        Args:
            ffmpeg_output: FFmpeg 的标准错误输出

        Returns:
            List[float]: 场景变化时间点列表(秒)
        """
        scene_times = []

        # 正则表达式匹配时间戳
        # 格式示例: [info] n:100 pts:1234567 pts_time:12.3456
        time_pattern = r'pts_time:(\d+\.\d+)'

        lines = ffmpeg_output.split('\n')
        for line in lines:
            if 'showinfo' in line and 'select:' in line:
                match = re.search(time_pattern, line)
                if match:
                    timestamp = float(match.group(1))
                    scene_times.append(timestamp)

        # 添加视频开始时间 (0秒)
        if not scene_times or scene_times[0] > 0:
            scene_times.insert(0, 0.0)

        # 添加视频结束时间
        scene_times.append(self.video_info['duration'])

        # 应用最小镜头长度过滤
        filtered_times = self._filter_by_min_length(scene_times)

        return filtered_times

    def _filter_by_min_length(self, scene_times: List[float]) -> List[float]:
        """
        根据最小镜头长度过滤时间戳

        Args:
            scene_times: 原始时间戳列表

        Returns:
            List[float]: 过滤后的时间戳列表
        """
        if len(scene_times) <= 1:
            return scene_times

        filtered = [scene_times[0]]  # 保留第一个时间戳

        for i in range(1, len(scene_times)):
            current_diff = scene_times[i] - filtered[-1]
            if current_diff >= self.min_scene_len:
                filtered.append(scene_times[i])
            else:
                # 如果间隔太短，跳过这个时间戳
                print(f"   跳过时间戳 {scene_times[i]:.2f}s (间隔 {current_diff:.2f}s < {self.min_scene_len}s)")

        return filtered

    def _create_shot_boundaries(self, scene_times: List[float]) -> List[ShotBoundary]:
        """
        根据时间戳创建镜头边界对象

        Args:
            scene_times: 场景变化时间点列表

        Returns:
            List[ShotBoundary]: 镜头边界列表
        """
        shots = []

        for i in range(len(scene_times) - 1):
            start_time = scene_times[i]
            end_time = scene_times[i + 1]

            # 转换为帧号
            start_frame = int(start_time * self.video_info['fps'])
            end_frame = int(end_time * self.video_info['fps'])

            shot = ShotBoundary(
                start_frame=start_frame,
                end_frame=end_frame,
                start_time=start_time,
                end_time=end_time
            )
            shots.append(shot)

            print(f"   镜头 {i+1}: {shot.to_time_string(start_time)} -> {shot.to_time_string(end_time)}")

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
            'name': 'FFmpeg',
            'type': 'Traditional (Filter-based)',
            'threshold': self.threshold,
            'min_scene_len': self.min_scene_len,
            'description': '基于 FFmpeg select 滤镜的场景分割算法'
        }