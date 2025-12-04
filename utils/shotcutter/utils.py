"""
工具函数模块

包含文件处理、OSS下载、临时文件管理等工具功能。
"""

import os
import tempfile
import requests
import urllib.parse
from typing import Optional


def handle_video_path(video_path: str) -> str:
    """
    处理视频路径：
    - 本地文件直接返回
    - HTTP/HTTPS/OSS URL下载到临时文件

    Args:
        video_path: 视频路径或URL

    Returns:
        str: 本地视频文件路径

    Raises:
        FileNotFoundError: 本地文件不存在
        RuntimeError: 下载失败

    Examples:
        >>> # 本地文件
        >>> path = handle_video_path("local.mp4")
        >>> print(path)  # "local.mp4"

        >>> # 远程URL
        >>> path = handle_video_path("https://example.com/video.mp4")
        >>> print(path)  # "/tmp/video_123456.mp4"
    """
    if _is_remote_url(video_path):
        print(f"🌐 检测到远程URL: {video_path}")
        return download_video(video_path)
    else:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        print(f"📁 使用本地文件: {video_path}")
        return video_path


def _is_remote_url(url: str) -> bool:
    """
    判断是否为远程URL

    Args:
        url: URL字符串

    Returns:
        bool: 是否为远程URL
    """
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in ('http', 'https', 'oss')


def download_video(url: str, timeout: int = 300) -> str:
    """
    下载视频到临时文件

    Args:
        url: 视频URL
        timeout: 下载超时时间(秒)

    Returns:
        str: 临时文件路径

    Raises:
        RuntimeError: 下载失败
    """
    print(f"⬇️  开始下载视频: {url}")

    try:
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.mp4',
            prefix='shotcutter_',
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()

        # 下载文件
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        print(f"📊 文件大小: {total_size / (1024*1024):.1f}MB" if total_size else "📊 文件大小: 未知")

        # 流式下载
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # 显示下载进度
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        if downloaded_size % (10 * 1024 * 1024) == 0:  # 每10MB显示一次
                            print(f"⏳ 下载进度: {progress:.1f}% ({downloaded_size/(1024*1024):.1f}MB)")

        print(f"✅ 下载完成: {temp_path}")
        return temp_path

    except requests.exceptions.RequestException as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise RuntimeError(f"下载失败: {str(e)}")
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise RuntimeError(f"处理失败: {str(e)}")


def cleanup_temp_file(file_path: str) -> bool:
    """
    清理临时文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否成功删除
    """
    try:
        if os.path.exists(file_path):
            # 检查是否为临时文件
            if is_temp_file(file_path):
                os.remove(file_path)
                print(f"🗑️  已清理临时文件: {file_path}")
                return True
            else:
                print(f"⚠️  跳过非临时文件: {file_path}")
                return False
        else:
            print(f"⚠️  文件不存在: {file_path}")
            return False
    except Exception as e:
        print(f"❌ 清理文件失败: {str(e)}")
        return False


def is_temp_file(file_path: str) -> bool:
    """
    判断是否为临时文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否为临时文件
    """
    temp_dirs = ['/tmp', '/var/tmp', tempfile.gettempdir()]
    abs_path = os.path.abspath(file_path)
    return any(abs_path.startswith(temp_dir) for temp_dir in temp_dirs)


def get_video_info(video_path: str) -> dict:
    """
    获取视频基本信息

    Args:
        video_path: 视频文件路径

    Returns:
        dict: 视频信息
    """
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)

        info = {
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration': 0.0,
            'file_size': 0
        }

        # 计算时长
        if info['fps'] > 0:
            info['duration'] = info['frame_count'] / info['fps']

        # 文件大小
        if os.path.exists(video_path):
            info['file_size'] = os.path.getsize(video_path)

        cap.release()

        return info

    except Exception as e:
        print(f"⚠️  获取视频信息失败: {str(e)}")
        return {}


def format_duration(seconds: float) -> str:
    """
    格式化时长显示

    Args:
        seconds: 秒数

    Returns:
        str: 格式化时长字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.0f}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}小时{minutes}分{secs:.0f}秒"


def format_file_size(bytes_size: int) -> str:
    """
    格式化文件大小显示

    Args:
        bytes_size: 字节数

    Returns:
        str: 格式化大小字符串
    """
    if bytes_size < 1024:
        return f"{bytes_size}B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f}KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f}MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f}GB"