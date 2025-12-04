"""
shotcutter: 智能镜头切割工具

基于TransNetV2算法的视频智能分段工具，支持流式处理。

核心功能：
- 基于TransNetV2的高精度镜头检测
- 智能分段策略，最大化30s/60s时长利用率
- 支持本地文件和OSS URL
- 提供批处理和流式两种模式

使用示例：
    from shotcutter import segment_video

    segments = segment_video("video.mp4", max_duration=30)
    print(segments)  # [(0.0, 29.8), (29.8, 58.3), ...]

作者: Assistant
版本: 1.0.0
"""

import os

from .detector import TransNetDetector
from .segmenter import SmartSegmenter
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
            print(f"✅ 找到模型目录: {path}")
            return path

    # 如果都找不到，返回默认路径，让用户自己配置
    default_path = "./models/transnetv2"
    print(f"⚠️  未找到模型目录，使用默认路径: {default_path}")
    return default_path


def segment_video(video_path, max_duration=30, streaming=False, model_dir=None, device='auto'):
    """
    统一的镜头分段接口

    Args:
        video_path: str - 视频文件路径或OSS URL
        max_duration: int - 最大片段时长(30/60)
        streaming: bool - 是否使用流式处理(默认False)
        model_dir: str - TransNetV2模型目录(可选，自动查找)
        device: str - 设备类型('auto'/'cuda'/'cpu'，默认'auto')

    Returns:
        List[Tuple[float, float]]: [(start_time, end_time), ...]

    Examples:
        >>> segments = segment_video("video.mp4", 30)
        >>> print(segments)
        [(0.0, 29.7), (29.7, 58.3), (58.3, 87.1)]

        >>> segments = segment_video("oss://bucket/video.mp4", 60, streaming=True)
        >>> print(f"共{len(segments)}个片段")

    Raises:
        FileNotFoundError: 视频文件不存在
        ValueError: 参数错误
        RuntimeError: 算法执行失败
    """
    # 参数检查
    if max_duration <= 0:
        raise ValueError("max_duration必须大于0")

    # 1. 自动查找模型目录
    if model_dir is None:
        model_dir = _find_model_directory()

    # 2. 处理视频路径（下载OSS文件等）
    local_path = handle_video_path(video_path)
    is_temp_file = local_path != video_path  # 是否是下载的临时文件

    try:
        # 3. 创建TransNetV2检测器
        detector = TransNetDetector(model_dir=model_dir, streaming=streaming, device=device)

        # 4. 创建智能分段器
        segmenter = SmartSegmenter(max_duration=max_duration)

        # 5. 检测镜头边界
        shots = detector.detect_shots(local_path)

        # 6. 智能分段
        segments = segmenter.segment(shots)

        return segments

    finally:
        # 7. 清理临时文件
        if is_temp_file:
            cleanup_temp_file(local_path)


__version__ = "1.0.0"
__all__ = ['segment_video']