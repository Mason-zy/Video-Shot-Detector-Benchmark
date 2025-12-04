#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shotcutter 性能监控测试

测试各个处理阶段的耗时
"""

import time
import sys
import os

# 添加shotcutter到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def main():
    """测试带性能监控的版本"""
    print('🎬 shotcutter 性能监控测试')
    print('=' * 40)

    try:
        from shotcutter import segment_video

        # 测试真实视频
        video_url = 'https://kinores.tvjoy.cn/background/1762412811986_动画_美人首.mp4'
        max_duration = 30

        print(f'🎯 测试目标: 动画视频, 最大时长: {max_duration}秒')
        print(f'📹 视频地址: {video_url}')
        print()

        # 阶段1: 导入模块
        import_start = time.time()
        from shotcutter import segment_video  # 重新导入，记录时间
        import_end = time.time()
        print(f'✅ 导入模块: {(import_end - import_start):.2f}秒')

        # 阶段2: 创建检测器
        detector_start = time.time()
        from shotcutter import TransNetDetector
        detector = TransNetDetector()
        detector_end = time.time()
        print(f'✅ 检测器创建: {(detector_end - detector_start):.2f}秒')

        # 阶段3: 创建分段器
        segmenter_start = time.time()
        from shotcutter import SmartSegmenter
        segmenter = SmartSegmenter(max_duration=max_duration)
        segmenter_end = time.time()
        print(f'✅ 分段器创建: {(segmenter_end - segmenter_start):.2f}秒')

        # 阶段4: 处理视频路径
        path_start = time.time()
        from shotcutter import handle_video_path
        local_path = handle_video_path(video_url)
        path_end = time.time()
        print(f'✅ 视频路径处理: {(path_end - path_start):.2f}秒')

        # 阶段5: 镜头检测
        detect_start = time.time()
        shots = detector.detect_shots(local_path)
        detect_end = time.time()
        print(f'✅ 镜头检测完成: {len(shots)}个镜头, 耗时: {(detect_end - detect_start):.2f}秒')

        # 阶段6: 智能分段
        segment_start = time.time()
        segments = segmenter.segment(shots)
        segment_end = time.time()
        print(f'✅ 智能分段完成: {len(segments)}个片段, 耗时: {(segment_end - segment_start):.2f}秒')

        # 阶段7: 清理临时文件
        cleanup_start = time.time()
        from shotcutter import cleanup_temp_file
        cleanup_temp_file(local_path)
        cleanup_end = time.time()
        print(f'✅ 临时文件清理: {(cleanup_end - cleanup_start):.2f}秒')

        # 总计
        total_time = time.time() - import_start
        print(f'\n⏱️ 总处理时间: {total_time:.2f}秒')

        # 各阶段耗时
        stages = [
            ('模块导入', import_end - import_start),
            ('检测器创建', detector_end - detector_start),
            ('分段器创建', segmenter_end - segmenter_start),
            ('视频路径处理', path_end - path_start),
            ('镜头检测', detect_end - detect_start),
            ('智能分段', segment_end - segment_start),
            ('临时文件清理', cleanup_end - cleanup_start)
        ]

        print('\n⏱️ 各阶段耗时:')
        for stage, duration in stages:
            print(f'  {stage:12s} - 耗时: {duration:.2f}秒')

    except Exception as e:
        print(f'❌ 测试失败: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()