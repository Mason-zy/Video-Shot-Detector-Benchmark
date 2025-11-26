#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
镜头分割算法对比工具
Shot Boundary Detection Comparison Tool

作者: Assistant
日期: 2024-11-25
"""

import os
import sys
import time
import csv
import subprocess
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

# 数据类，用于存储镜头边界信息
@dataclass
class ShotBoundary:
    """镜头边界信息"""
    start_frame: int  # 起始帧号
    end_frame: int    # 结束帧号
    start_time: float # 起始时间(秒)
    end_time: float   # 结束时间(秒)

    @property
    def duration(self) -> float:
        """镜头持续时间(秒)"""
        return self.end_time - self.start_time

    def to_time_string(self, seconds: float) -> str:
        """将秒数转换为 MMmSSs 格式"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}m{secs:02d}s"

    def to_precise_time_string(self, seconds: float) -> str:
        """将秒数转换为精确的 MMmSSsXXXms 格式（毫秒级）"""
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        secs = int(remaining_seconds)
        milliseconds = int((remaining_seconds - secs) * 1000)
        return f"{minutes:02d}m{secs:02d}s{milliseconds:03d}ms"


class ShotDetector:
    """镜头分割检测器基类"""

    def __init__(self, video_path: str):
        self.video_path = video_path
        self.video_info = self._get_video_info()

    def _get_video_info(self) -> Dict:
        """获取视频基本信息"""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {self.video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps

        cap.release()

        return {
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration,
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }

    def detect_shots(self, **kwargs) -> List[ShotBoundary]:
        """检测镜头边界，子类需要实现此方法"""
        raise NotImplementedError("子类必须实现 detect_shots 方法")

    def extract_shots(self, shots: List[ShotBoundary], output_dir: str) -> List[str]:
        """提取镜头片段到指定目录"""
        output_files = []

        for i, shot in enumerate(shots, 1):
            # 生成毫秒级精确的输出文件名
            start_time_str = shot.to_precise_time_string(shot.start_time)
            end_time_str = shot.to_precise_time_string(shot.end_time)
            filename = f"shot_{i:02d}_{start_time_str}_to_{end_time_str}.mp4"
            output_path = os.path.join(output_dir, filename)

            # 使用 FFmpeg 提取片段
            self._extract_segment(shot.start_time, shot.end_time, output_path)

            if os.path.exists(output_path):
                output_files.append(output_path)
                # 显示精确的毫秒级时间信息
                print(f"✓ 提取镜头 {i}: {start_time_str} -> {end_time_str} (时长: {shot.duration:.3f}s)")
            else:
                print(f"✗ 提取镜头 {i} 失败")

        return output_files

    def _extract_segment(self, start_time: float, end_time: float, output_path: str):
        """使用 FFmpeg 提取视频片段"""
        duration = end_time - start_time

        # 确保时长不为负数或零
        if duration <= 0:
            print(f"⚠️  跳过无效片段: {start_time}s -> {end_time}s (时长: {duration}s)")
            return

        # 使用重新编码方式确保精确分割
        # 这种方法虽然较慢，但能保证时间精确
        cmd = [
            'ffmpeg', '-y',  # 覆盖输出文件
            '-ss', str(start_time),
            '-i', self.video_path,
            '-t', str(duration),
            '-c:v', 'libx264',  # 重新编码视频
            '-c:a', 'aac',      # 重新编码音频
            '-preset', 'ultrafast',  # 快速预设
            '-crf', '23',       # 合理的质量
            '-avoid_negative_ts', 'make_zero',
            output_path
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            # 验证输出文件
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                print(f"⚠️  分割的文件为空: {output_path}")
                return
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg 提取失败: {e}")
            print(f"错误输出: {e.stderr}")
            raise


def create_output_directory(base_dir: str = "output") -> Tuple[str, str]:
    """创建带时间戳的输出目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_main_dir = os.path.join(base_dir, f"shot_comparison_{timestamp}")

    # 创建子目录
    subdirs = ['pyscene', 'ffmpeg', 'transnet']
    for subdir in subdirs:
        os.makedirs(os.path.join(output_main_dir, subdir), exist_ok=True)

    # 创建报告文件路径
    report_path = os.path.join(output_main_dir, "report.csv")

    return output_main_dir, report_path


def generate_report(report_path: str, results: Dict[str, Dict]):
    """生成对比报告 CSV"""
    with open(report_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['算法', '检测到的镜头数量', '处理时间(秒)', '平均镜头时长(秒)', '备注']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for algorithm, data in results.items():
            avg_duration = 0
            if data['shot_count'] > 0 and 'total_duration' in data:
                avg_duration = data['total_duration'] / data['shot_count']

            writer.writerow({
                '算法': algorithm,
                '检测到的镜头数量': data['shot_count'],
                '处理时间(秒)': f"{data['processing_time']:.2f}",
                '平均镜头时长(秒)': f"{avg_duration:.2f}",
                '备注': data.get('notes', '')
            })

    print(f"📊 报告已生成: {report_path}")


if __name__ == "__main__":
    # 主程序将在后续实现
    print("镜头分割算法对比工具")
    print("Shot Boundary Detection Comparison Tool")