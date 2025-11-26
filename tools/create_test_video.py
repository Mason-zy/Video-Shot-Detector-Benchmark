#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试视频文件的脚本
由于没有 FFmpeg，我们使用 OpenCV 创建一个简单的测试视频
"""

import cv2
import numpy as np
import os

def create_test_video(output_path: str = "data/sample_videos/test_video.mp4", duration: int = 10, fps: int = 30):
    """
    创建一个包含多个场景的测试视频

    Args:
        output_path: 输出视频文件路径
        duration: 视频时长（秒）
        fps: 帧率
    """
    print(f"正在创建测试视频: {output_path}")
    print(f"时长: {duration}秒, 帧率: {fps}")

    # 视频参数
    width, height = 640, 480
    total_frames = duration * fps

    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # 场景1: 红色背景 (0-3秒)
    for i in range(3 * fps):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = [0, 0, 255]  # 红色
        # 添加时间戳
        cv2.putText(frame, f"Scene 1: Red", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Time: {i//fps:02d}:{i%fps:02d}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        out.write(frame)

    # 场景2: 绿色背景 (3-6秒)
    for i in range(3 * fps):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = [0, 255, 0]  # 绿色
        cv2.putText(frame, f"Scene 2: Green", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, f"Time: {3+i//fps:02d}:{i%fps:02d}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        out.write(frame)

    # 场景3: 蓝色背景 (6-8秒)
    for i in range(2 * fps):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = [255, 0, 0]  # 蓝色
        cv2.putText(frame, f"Scene 3: Blue", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Time: {6+i//fps:02d}:{i%fps:02d}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        out.write(frame)

    # 场景4: 黄色背景 (8-10秒)
    for i in range(2 * fps):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = [0, 255, 255]  # 黄色
        cv2.putText(frame, f"Scene 4: Yellow", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, f"Time: {8+i//fps:02d}:{i%fps:02d}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        out.write(frame)

    # 释放资源
    out.release()

    print(f"测试视频创建完成: {output_path}")
    print(f"文件大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    print("视频包含 4 个场景:")
    print("  - 场景1: 红色背景 (0:00-0:03)")
    print("  - 场景2: 绿色背景 (0:03-0:06)")
    print("  - 场景3: 蓝色背景 (0:06-0:08)")
    print("  - 场景4: 黄色背景 (0:08-0:10)")

if __name__ == "__main__":
    try:
        output_path = "data/sample_videos/test_video.mp4"
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        create_test_video(output_path, duration=10, fps=30)
        print("\n测试视频创建成功！")
        print("现在可以使用以下命令运行对比测试:")
        print("python3 src/main.py data/sample_videos/test_video.mp4")
        print("或者使用运行脚本:")
        print("./run.sh data/sample_videos/test_video.mp4")
    except Exception as e:
        print(f"创建测试视频失败: {e}")
        print("请确保已安装 opencv-python")