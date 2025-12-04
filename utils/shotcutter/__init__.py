"""
shotcutter: 智能镜头切割工具

基于TransNetV2算法的视频智能分段工具。

核心功能：
- 基于TransNetV2的高精度镜头检测
- 智能分段策略，最大化30s/60s时长利用率
- 视频切割并上传OSS
- 支持本地文件和OSS URL

使用示例：
    from utils.shotcutter import process_video

    # 一站式处理：识别 → 切割 → 上传
    result = process_video("video.mp4", name="myproject", max_duration=30)
    print(result)
    # {
    #     "segments": [
    #         {"index": 1, "start": 0.0, "end": 28.5, "oss_url": "..."},
    #         {"index": 2, "start": 29.1, "end": 58.6, "oss_url": "..."},
    #     ],
    #     "total": 2,
    #     "time_stats": {"download": 2.3, "detect": 5.1, "cut_upload": 12.5, "total": 19.9}
    # }

作者: zhouzhiyong
版本: 1.0.0
"""

import os
import time

from .detector import TransNetDetector
from .segmenter import SmartSegmenter
from .cutter import cut_and_upload
from .utils import handle_video_path, cleanup_temp_file


def _find_model_directory():
    """自动查找TransNetV2模型目录"""
    possible_paths = [
        "./models/transnetv2",
        "../models/transnetv2",
        "../../models/transnetv2",
        "/home/yong/project/videoFen/models/transnetv2",
        os.path.expanduser("~/transnetv2_weights")
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return "./models/transnetv2"


def segment_video(video_path, max_duration=30, model_dir=None, device='auto'):
    """
    镜头分段接口（只返回时间点，不切割）

    Args:
        video_path: 视频文件路径或OSS URL
        max_duration: 最大片段时长(30/60)
        model_dir: TransNetV2模型目录(可选)
        device: 设备类型('auto'/'cuda'/'cpu')

    Returns:
        List[Tuple[float, float]]: [(start, end), ...]
    """
    if model_dir is None:
        model_dir = _find_model_directory()

    local_path = handle_video_path(video_path)
    is_temp_file = local_path != video_path

    try:
        detector = TransNetDetector(model_dir=model_dir, device=device)
        segmenter = SmartSegmenter(max_duration=max_duration)
        shots = detector.detect_shots(local_path)
        segments = segmenter.segment(shots)
        return segments
    finally:
        if is_temp_file:
            cleanup_temp_file(local_path)


def process_video(video_path: str, name: str, max_duration: int = 30,
                  model_dir: str = None, device: str = 'auto') -> dict:
    """
    一站式视频处理：识别镜头 → 切割 → 上传OSS

    Args:
        video_path: 视频文件路径或OSS URL
        name: 命名前缀，切割后命名为 name-1, name-2, ...
        max_duration: 最大片段时长(30/60秒)
        model_dir: TransNetV2模型目录(可选)
        device: 设备类型('auto'/'cuda'/'cpu')

    Returns:
        dict: {
            "status": "success",
            "segments": [...],
            "total": 18,
            "time_stats": {
                "download": 2.3,
                "detect": 5.1,
                "cut_upload": 12.5,
                "total": 19.9
            }
        }
    """
    if model_dir is None:
        model_dir = _find_model_directory()

    time_stats = {}
    total_start = time.time()

    # 1. 下载/处理视频路径
    t0 = time.time()
    local_path = handle_video_path(video_path)
    is_temp_file = local_path != video_path
    time_stats['download'] = round(time.time() - t0, 1)

    try:
        # 2. 镜头检测
        t0 = time.time()
        detector = TransNetDetector(model_dir=model_dir, device=device)
        shots = detector.detect_shots(local_path)
        time_stats['detect'] = round(time.time() - t0, 1)

        # 3. 智能分段
        segmenter = SmartSegmenter(max_duration=max_duration)
        segments = segmenter.segment(shots)

        if not segments:
            time_stats['total'] = round(time.time() - total_start, 1)
            return {
                "status": "failure",
                "reason": "未检测到有效片段",
                "segments": [],
                "total": 0,
                "time_stats": time_stats
            }

        # 4. 切割并上传
        t0 = time.time()
        results = cut_and_upload(local_path, segments, name)
        time_stats['cut_upload'] = round(time.time() - t0, 1)

        time_stats['total'] = round(time.time() - total_start, 1)

        # 打印时间统计
        print(f"⏱️  时间统计: 下载{time_stats['download']}s | 检测{time_stats['detect']}s | "
              f"切割上传{time_stats['cut_upload']}s | 总计{time_stats['total']}s")

        return {
            "status": "success",
            "segments": results,
            "total": len(results),
            "time_stats": time_stats
        }

    except Exception as e:
        time_stats['total'] = round(time.time() - total_start, 1)
        return {
            "status": "failure",
            "reason": str(e),
            "segments": [],
            "total": 0,
            "time_stats": time_stats
        }

    finally:
        if is_temp_file:
            cleanup_temp_file(local_path)


__version__ = "1.0.0"
__all__ = ['segment_video', 'process_video', 'cut_and_upload']