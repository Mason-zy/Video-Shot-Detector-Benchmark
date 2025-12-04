#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shotcutter 完整测试脚本

测试功能：
1. segment_video: 只返回分段时间点
2. process_video: 识别 → 切割 → 上传OSS（一站式）

作者: zhouzhiyong


  # 运行全部测试
  python utils/shotcutter/test/test_shotcutter.py

  # 只测试分段（不切割上传）
  python utils/shotcutter/test/test_shotcutter.py --test 1

  # 测试完整流程（识别→切割→上传）
  python utils/shotcutter/test/test_shotcutter.py --test 2

  # 自定义视频测试
  python utils/shotcutter/test/test_shotcutter.py --url "https://xxx.mp4"
  --name "mytest" --duration 30

"""

import sys
import os

# 动态获取项目根目录（往上3级：test/ -> shotcutter/ -> utils/ -> 项目根目录）
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def test_segment_only():
    """测试1: 只获取分段时间点（不切割不上传）"""
    print("=" * 50)
    print("📋 测试1: segment_video (只返回时间点)")
    print("=" * 50)

    from utils.shotcutter import segment_video

    video_url = "https://kinores.tvjoy.cn/background/1762412811986_动画_美人首.mp4"
    max_duration = 30

    print(f"视频: {video_url}")
    print(f"最大时长: {max_duration}秒\n")

    segments = segment_video(video_url, max_duration=max_duration)

    print(f"\n📊 结果: {len(segments)}个片段")
    for i, (start, end) in enumerate(segments):
        print(f"   片段{i+1:2d}: {start:6.1f}s - {end:6.1f}s (时长: {end-start:5.1f}s)")

    return segments


def test_process_full():
    """测试2: 完整流程（识别 → 切割 → 上传）"""
    print("\n" + "=" * 50)
    print("🎬 测试2: process_video (完整流程)")
    print("=" * 50)

    from utils.shotcutter import process_video

    video_url = "https://kinores.tvjoy.cn/background/1762412811986_动画_美人首.mp4"
    name = "test_shot"  # 命名前缀: test_shot-1, test_shot-2, ...
    max_duration = 60

    print(f"视频: {video_url}")
    print(f"命名前缀: {name}")
    print(f"最大时长: {max_duration}秒\n")

    result = process_video(video_url, name=name, max_duration=max_duration)

    print(f"\n📊 结果:")
    print(f"   状态: {result['status']}")
    print(f"   总片段: {result['total']}")

    if result['status'] == 'success':
        print(f"\n⏱️  耗时统计:")
        ts = result['time_stats']
        print(f"   下载: {ts['download']}s")
        print(f"   检测: {ts['detect']}s")
        print(f"   切割上传: {ts['cut_upload']}s")
        print(f"   总计: {ts['total']}s")

        print(f"\n📦 片段列表:")
        for seg in result['segments']:
            print(f"   [{seg['index']}] {seg['task_id']}: {seg['start']}s-{seg['end']}s")
            print(f"       → {seg['oss_url']}")
    else:
        print(f"   失败原因: {result.get('reason', '未知')}")

    return result


def test_short_video():
    """测试3: 短视频（无需切割）"""
    print("\n" + "=" * 50)
    print("🎞️  测试3: 短视频处理")
    print("=" * 50)

    from utils.shotcutter import process_video

    # 使用一个短视频URL（如果有的话）
    video_url = "https://kinores.tvjoy.cn/background/1762412811986_动画_美人首.mp4"
    name = "short_test"
    max_duration = 60  # 60秒，可能只有1-2个片段

    print(f"视频: {video_url}")
    print(f"最大时长: {max_duration}秒\n")

    result = process_video(video_url, name=name, max_duration=max_duration)

    print(f"\n📊 结果: {result['status']}, {result['total']}个片段")

    return result


def main():
    """主测试入口"""
    print("🚀 shotcutter 完整测试")
    print("功能: 基于镜头识别的智能视频切割工具\n")

    import argparse
    parser = argparse.ArgumentParser(description='shotcutter测试')
    parser.add_argument('--test', type=int, default=0,
                        help='测试编号: 1=只分段, 2=完整流程, 3=短视频, 0=全部')
    parser.add_argument('--url', type=str, default=None,
                        help='自定义视频URL')
    parser.add_argument('--name', type=str, default='test',
                        help='命名前缀')
    parser.add_argument('--duration', type=int, default=30,
                        help='最大片段时长')
    args = parser.parse_args()

    try:
        if args.url:
            # 自定义测试
            print("🎯 自定义测试")
            from utils.shotcutter import process_video
            result = process_video(args.url, name=args.name, max_duration=args.duration)
            print(f"\n结果: {result}")
        elif args.test == 1:
            test_segment_only()
        elif args.test == 2:
            test_process_full()
        elif args.test == 3:
            test_short_video()
        else:
            # 运行所有测试
            # test_segment_only()
            test_process_full()

        print("\n" + "=" * 50)
        print("✅ 测试完成")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
