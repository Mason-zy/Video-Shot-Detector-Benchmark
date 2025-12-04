"""
视频切割器（并发版本 - 全局池）

根据分段结果并发切割视频并上传OSS

特性：
- 并发切割：多进程并行处理多个片段
- 并发上传：多线程并行上传到OSS
- 自适应并发：根据CPU核心数动态调整
- 全局资源池：多个请求共享，防止系统过载

作者: zhouzhiyong
"""

import os
import time
import atexit
import tempfile
from typing import List, Tuple, Dict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

# 使用本地 OSS 上传模块（解耦）
from .oss_uploader import upload_to_oss_from_local


def get_max_workers() -> int:
    """
    动态计算最大并发数

    策略：
    - 基础：CPU核心数 × 0.6
    - 下限：2（保证基本并发）
    - 上限：48（防止过载）
    - 支持环境变量覆盖

    Returns:
        int: 最大并发数
    """
    cpu_count = os.cpu_count() or 4

    # 基础计算：60% 核心数
    workers = int(cpu_count * 0.6)

    # 兜底：最小 2，最大 48
    workers = max(2, min(48, workers))

    # 环境变量覆盖（方便调试）
    env_workers = os.environ.get('SHOTCUTTER_MAX_WORKERS')
    if env_workers:
        try:
            workers = int(env_workers)
        except ValueError:
            pass

    return workers


# ========== 全局配置 ==========
MAX_WORKERS = get_max_workers()

# ========== 全局进程池和线程池 ==========
# 所有请求共享，自动排队，防止资源过载
_GLOBAL_PROCESS_POOL: ProcessPoolExecutor = None
_GLOBAL_THREAD_POOL: ThreadPoolExecutor = None


def _get_process_pool() -> ProcessPoolExecutor:
    """获取全局进程池（懒加载）"""
    global _GLOBAL_PROCESS_POOL
    if _GLOBAL_PROCESS_POOL is None:
        _GLOBAL_PROCESS_POOL = ProcessPoolExecutor(max_workers=MAX_WORKERS)
        print(f"🔧 初始化全局进程池: max_workers={MAX_WORKERS}")
    return _GLOBAL_PROCESS_POOL


def _get_thread_pool() -> ThreadPoolExecutor:
    """获取全局线程池（懒加载）"""
    global _GLOBAL_THREAD_POOL
    if _GLOBAL_THREAD_POOL is None:
        _GLOBAL_THREAD_POOL = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        print(f"🔧 初始化全局线程池: max_workers={MAX_WORKERS}")
    return _GLOBAL_THREAD_POOL


def _cleanup_pools():
    """清理全局池（程序退出时调用）"""
    global _GLOBAL_PROCESS_POOL, _GLOBAL_THREAD_POOL
    if _GLOBAL_PROCESS_POOL is not None:
        _GLOBAL_PROCESS_POOL.shutdown(wait=False)
        _GLOBAL_PROCESS_POOL = None
    if _GLOBAL_THREAD_POOL is not None:
        _GLOBAL_THREAD_POOL.shutdown(wait=False)
        _GLOBAL_THREAD_POOL = None


# 注册清理函数
atexit.register(_cleanup_pools)


def _cut_single_segment(args: Tuple) -> Dict:
    """
    切割单个视频片段（进程池工作函数）

    使用 ffmpeg 直接切割，速度快，内存占用低
    -c copy: 直接复制流，不重新编码（快5-10倍）

    Args:
        args: (video_path, start, end, output_path, index)

    Returns:
        dict: {"index": 1, "path": "/tmp/xxx.mp4", "start": 0.0, "end": 28.5}
    """
    import subprocess

    video_path, start, end, output_path, index = args
    duration = end - start

    try:
        # 使用 ffmpeg 快速切割
        # -ss: 起始时间
        # -t: 持续时间
        # -i: 输入文件
        # -c copy: 直接复制流，不重新编码（关键优化）
        # -avoid_negative_ts make_zero: 避免时间戳问题
        cmd = [
            'ffmpeg',
            '-y',  # 覆盖输出文件
            '-ss', str(start),  # 起始时间
            '-t', str(duration),  # 持续时间
            '-i', video_path,  # 输入
            '-c', 'copy',  # 直接复制流（不重新编码）
            '-avoid_negative_ts', 'make_zero',
            output_path
        ]

        # 静默执行
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300  # 5分钟超时
        )

        if result.returncode == 0:
            return {
                "index": index,
                "path": output_path,
                "start": start,
                "end": end,
                "status": "success"
            }
        else:
            error_msg = result.stderr.decode('utf-8', errors='ignore')[-200:]
            return {
                "index": index,
                "path": None,
                "start": start,
                "end": end,
                "status": "failed",
                "error": f"ffmpeg错误: {error_msg}"
            }

    except subprocess.TimeoutExpired:
        return {
            "index": index,
            "path": None,
            "start": start,
            "end": end,
            "status": "failed",
            "error": "切割超时（5分钟）"
        }
    except Exception as e:
        return {
            "index": index,
            "path": None,
            "start": start,
            "end": end,
            "status": "failed",
            "error": str(e)
        }


def _upload_single_segment(args: Tuple) -> Dict:
    """
    上传单个视频片段（线程池工作函数）

    Args:
        args: (local_path, task_id, index, start, end)

    Returns:
        dict: 上传结果
    """
    local_path, task_id, index, start, end = args

    try:
        oss_url = upload_to_oss_from_local(local_path, task_id)
        return {
            "index": index,
            "start": round(start, 1),
            "end": round(end, 1),
            "duration": round(end - start, 1),
            "task_id": task_id,
            "oss_url": oss_url,
            "status": "success"
        }
    except Exception as e:
        return {
            "index": index,
            "start": round(start, 1),
            "end": round(end, 1),
            "duration": round(end - start, 1),
            "task_id": task_id,
            "oss_url": None,
            "status": "failed",
            "error": str(e)
        }


def cut_and_upload(video_path: str, segments: List[Tuple[float, float]],
                   name: str) -> List[dict]:
    """
    并发切割视频并上传到OSS（使用全局池）

    流程：
    1. 并发切割所有片段（多进程，全局池）
    2. 并发上传所有片段（多线程，全局池）

    多个请求会自动排队，共享全局池资源，防止系统过载。

    Args:
        video_path: 本地视频路径
        segments: [(start, end), ...] 分段时间点
        name: 命名前缀，最终命名为 name-1, name-2, ...

    Returns:
        List[dict]: [{
            "index": 1,
            "start": 0.0,
            "end": 28.5,
            "duration": 28.5,
            "task_id": "name-1",
            "oss_url": "https://..."
        }, ...]
    """
    total = len(segments)
    process_pool = _get_process_pool()
    thread_pool = _get_thread_pool()

    print(f"🔪 并发切割上传: {total}个片段 (全局池: max_workers={MAX_WORKERS})")

    with tempfile.TemporaryDirectory(prefix="shotcutter_") as temp_dir:
        # ========== 阶段1: 并发切割 ==========
        t0 = time.time()
        print(f"📹 阶段1: 并发切割中...")

        # 准备切割任务参数
        cut_tasks = []
        for idx, (start, end) in enumerate(segments):
            output_path = os.path.join(temp_dir, f"segment_{idx+1}.mp4")
            cut_tasks.append((video_path, start, end, output_path, idx + 1))

        # 提交到全局进程池
        futures = [process_pool.submit(_cut_single_segment, task) for task in cut_tasks]

        # 等待结果
        cut_results = []
        for future in as_completed(futures):
            result = future.result()
            cut_results.append(result)
            if result["status"] == "success":
                print(f"   ✅ 片段{result['index']}: {result['start']:.1f}s - {result['end']:.1f}s")
            else:
                print(f"   ❌ 片段{result['index']}: {result.get('error', '未知错误')}")

        cut_time = time.time() - t0
        success_cuts = [r for r in cut_results if r["status"] == "success"]
        print(f"📹 切割完成: {len(success_cuts)}/{total} 成功, 耗时 {cut_time:.1f}s")

        # ========== 阶段2: 并发上传 ==========
        t0 = time.time()
        print(f"📤 阶段2: 并发上传中...")

        # 准备上传任务参数（只上传成功切割的）
        upload_tasks = []
        for result in success_cuts:
            task_id = f"{name}-{result['index']}"
            upload_tasks.append((
                result["path"],
                task_id,
                result["index"],
                result["start"],
                result["end"]
            ))

        # 提交到全局线程池
        futures = [thread_pool.submit(_upload_single_segment, task) for task in upload_tasks]

        # 等待结果
        upload_results = []
        for future in as_completed(futures):
            result = future.result()
            upload_results.append(result)
            if result["status"] == "success":
                print(f"   ✅ [{result['index']}/{total}] {result['task_id']}")
            else:
                print(f"   ❌ [{result['index']}/{total}] {result.get('error', '未知错误')}")

        upload_time = time.time() - t0
        success_uploads = [r for r in upload_results if r["status"] == "success"]
        print(f"📤 上传完成: {len(success_uploads)}/{len(success_cuts)} 成功, 耗时 {upload_time:.1f}s")

    # 按 index 排序返回
    final_results = sorted(
        [r for r in upload_results if r["status"] == "success"],
        key=lambda x: x["index"]
    )

    # 移除 status 字段
    for r in final_results:
        r.pop("status", None)

    print(f"⏱️  总计: 切割{cut_time:.1f}s + 上传{upload_time:.1f}s = {cut_time + upload_time:.1f}s")

    return final_results


# ========== 兼容旧接口 ==========

def cut_video(video_path: str, segments: List[Tuple[float, float]],
              output_dir: str = None) -> List[str]:
    """
    根据分段结果切割视频到本地（并发版本，使用全局池）

    Args:
        video_path: 本地视频路径
        segments: [(start, end), ...] 分段时间点
        output_dir: 输出目录，None则使用临时目录

    Returns:
        List[str]: 切割后的视频路径列表
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="shotcutter_cut_")

    os.makedirs(output_dir, exist_ok=True)

    total = len(segments)
    process_pool = _get_process_pool()

    print(f"🎬 并发切割视频: {total}个片段 (全局池)")

    # 准备任务
    cut_tasks = []
    for idx, (start, end) in enumerate(segments):
        output_path = os.path.join(output_dir, f"segment_{idx+1}.mp4")
        cut_tasks.append((video_path, start, end, output_path, idx + 1))

    # 提交到全局进程池
    futures = [process_pool.submit(_cut_single_segment, task) for task in cut_tasks]

    # 等待结果
    cut_paths = [None] * total
    for future in as_completed(futures):
        result = future.result()
        if result["status"] == "success":
            cut_paths[result["index"] - 1] = result["path"]
            print(f"   ✅ 片段{result['index']}: {result['start']:.1f}s - {result['end']:.1f}s")
        else:
            print(f"   ❌ 片段{result['index']}: {result.get('error', '未知错误')}")

    # 过滤失败的
    cut_paths = [p for p in cut_paths if p is not None]
    print(f"🎬 切割完成: {output_dir}")

    return cut_paths


def upload_segments(segment_paths: List[str], name: str) -> List[dict]:
    """
    并发上传切割后的视频片段到OSS（使用全局池）

    Args:
        segment_paths: 本地视频路径列表
        name: 命名前缀，最终命名为 name-1, name-2, ...

    Returns:
        List[dict]: [{"index": 1, "oss_url": "..."}, ...]
    """
    total = len(segment_paths)
    thread_pool = _get_thread_pool()

    print(f"📤 并发上传: {total}个片段 (全局池)")

    # 准备任务
    upload_tasks = []
    for idx, path in enumerate(segment_paths):
        task_id = f"{name}-{idx+1}"
        upload_tasks.append((path, task_id, idx + 1, 0.0, 0.0))

    # 提交到全局线程池
    futures = [thread_pool.submit(_upload_single_segment, task) for task in upload_tasks]

    # 等待结果
    results = []
    for future in as_completed(futures):
        result = future.result()
        if result["status"] == "success":
            results.append({
                "index": result["index"],
                "task_id": result["task_id"],
                "oss_url": result["oss_url"]
            })
            print(f"   ✅ {result['task_id']} → {result['oss_url']}")
        else:
            print(f"   ❌ {result['task_id']}: {result.get('error', '未知错误')}")

    # 按 index 排序
    results.sort(key=lambda x: x["index"])
    print(f"📤 上传完成")

    return results


def get_pool_status() -> dict:
    """
    获取全局池状态（用于监控）

    Returns:
        dict: 池状态信息
    """
    return {
        "max_workers": MAX_WORKERS,
        "process_pool_initialized": _GLOBAL_PROCESS_POOL is not None,
        "thread_pool_initialized": _GLOBAL_THREAD_POOL is not None,
    }
