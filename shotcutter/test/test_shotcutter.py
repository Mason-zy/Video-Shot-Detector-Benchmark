#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shotcutter 简单测试脚本

测试真实的视频分段功能。
"""

import sys
import os

# 添加shotcutter到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def main():
    """简单测试"""
    print("🎬 shotcutter 测试")
    print("=" * 30)

    try:
        from shotcutter import segment_video

        # 测试真实视频
        video_url = "https://kinores.tvjoy.cn/background/1762412811986_动画_美人首.mp4"
        max_duration = 30

        print(f"🎯 测试目标: 动画视频, 最大时长: {max_duration}秒")
        print(f"📹 视频地址: {video_url}")
        print()

        # 执行分段
        print("🔄 开始处理...")
        segments = segment_video(video_url, max_duration=max_duration)

        # 显示结果
        print(f"✅ 处理完成: {len(segments)}个片段")
        print()

        for i, (start, end) in enumerate(segments):
            duration = end - start
            print(f"片段{i+1:2d}: {start:6.1f}s - {end:6.1f}s (时长: {duration:5.1f}s)")

        # 统计信息
        if segments:
            total_duration = sum(end - start for start, end in segments)
            avg_duration = total_duration / len(segments)
            print(f"\n📊 统计:")
            print(f"  - 总片段数: {len(segments)}")
            print(f"  - 总时长: {total_duration:.1f}秒")
            print(f"  - 平均时长: {avg_duration:.1f}秒")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()