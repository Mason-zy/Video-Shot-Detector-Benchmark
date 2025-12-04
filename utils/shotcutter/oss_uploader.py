"""
OSS 上传模块

将视频文件上传到阿里云 OSS

作者: zhouzhiyong
"""

import os
import oss2
import requests
from io import BytesIO


# OSS 配置 (从环境变量读取敏感信息)
OSS_CONFIG = {
    "bucket_name": os.getenv("OSS_BUCKET_NAME", "ali-saving-data"),
    "endpoint": os.getenv("OSS_ENDPOINT", "https://oss-cn-hangzhou.aliyuncs.com"),
    "access_key_id": os.getenv("OSS_ACCESS_KEY_ID", ""),
    "access_key_secret": os.getenv("OSS_ACCESS_KEY_SECRET", ""),
}

# 初始化 OSS 客户端
_auth = oss2.Auth(OSS_CONFIG["access_key_id"], OSS_CONFIG["access_key_secret"])
_bucket = oss2.Bucket(auth=_auth, endpoint=OSS_CONFIG["endpoint"], bucket_name=OSS_CONFIG["bucket_name"])


def upload_to_oss_from_local(video_path: str, task_id: str) -> str:
    """
    从本地文件上传到OSS

    Args:
        video_path: 本地视频文件路径
        task_id: 任务ID，用于生成OSS文件名

    Returns:
        str: OSS文件URL，失败返回状态码字符串
    """
    with open(video_path, 'rb') as f:
        video_content = f.read()

    file_extension = os.path.splitext(video_path)[-1] or '.mp4'
    object_key = f"{task_id}{file_extension}"

    result = _bucket.put_object(object_key, video_content)

    if result.status == 200:
        oss_file_url = f"https://{OSS_CONFIG['bucket_name']}.oss-cn-hangzhou.aliyuncs.com/{object_key}"
        return oss_file_url
    else:
        return str(result.status)


def upload_to_oss_from_url(video_url: str, task_id: str) -> str:
    """
    从URL下载并上传到OSS

    Args:
        video_url: 视频URL
        task_id: 任务ID

    Returns:
        str: OSS文件URL
    """
    response = requests.get(video_url, stream=True)
    video_content = BytesIO(response.content)

    file_extension = os.path.splitext(video_url.split('?')[0])[-1] or '.mp4'
    object_key = f"{task_id}{file_extension}"

    result = _bucket.put_object(object_key, video_content)

    if result.status == 200:
        oss_file_url = f"https://{OSS_CONFIG['bucket_name']}.oss-cn-hangzhou.aliyuncs.com/{object_key}"
        return oss_file_url
    else:
        return str(result.status)
