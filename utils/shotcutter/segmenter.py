"""
智能分段器

基于镜头检测结果，按照最大时长约束进行智能分段。

核心策略（v1.1 无缝拼接优化）：
1. 顺序累加镜头，尽量接近max_duration
2. 单个镜头超长 → 硬截断
3. 片段之间无缝拼接，不丢失任何内容
4. 最后一段即使很短也保留

特点：
- 最大化时长利用率
- 保证镜头完整性（优先）
- 支持硬截断超长镜头
- 无缝拼接，保证时长连续
"""

from typing import List, Tuple
from .detector import Shot


class SmartSegmenter:
    """智能分段器"""

    def __init__(self, max_duration: int = 30):
        """
        初始化分段器

        Args:
            max_duration: 最大片段时长(30/60)
        """
        self.max_duration = max_duration

    def segment(self, shots: List[Shot]) -> List[Tuple[float, float]]:
        """
        将镜头列表智能分段（无缝拼接版本）

        Args:
            shots: 镜头列表

        Returns:
            List[Tuple[float, float]]: [(start_time, end_time), ...]

        优化说明：
        - 片段之间无缝拼接，不丢失任何内容
        - 从视频开头（0.0s）开始，到视频结尾
        - 在镜头边界处优先切分，但保证时长连续

        Examples:
            >>> shots = [Shot(0, 750, 0.0, 30.0, 30.0)]
            >>> segmenter = SmartSegmenter(max_duration=30)
            >>> segments = segmenter.segment(shots)
            >>> print(segments)
            [(0.0, 30.0)]
        """
        if not shots:
            return []

        segments = []
        current_start = 0.0  # 当前片段起始时间
        accumulated_duration = 0.0  # 当前片段累计时长

        for i, shot in enumerate(shots):
            # 情况1: 可以加入当前段
            if accumulated_duration + shot.duration <= self.max_duration:
                accumulated_duration += shot.duration

            # 情况2: 单个镜头超长 → 硬截断
            elif shot.duration > self.max_duration:
                # 保存当前段（如果有内容）
                if accumulated_duration > 0:
                    current_end = current_start + accumulated_duration
                    segments.append((current_start, current_end))
                    current_start = current_end  # 无缝拼接
                    accumulated_duration = 0.0

                # 硬截断超长镜头（从current_start开始）
                shot_start = current_start
                remaining = shot.duration

                while remaining > self.max_duration:
                    segments.append((shot_start, shot_start + self.max_duration))
                    shot_start += self.max_duration
                    remaining -= self.max_duration

                # 剩余部分
                if remaining > 0:
                    segments.append((shot_start, shot_start + remaining))
                    current_start = shot_start + remaining
                else:
                    current_start = shot_start

                accumulated_duration = 0.0

            # 情况3: 超出max_duration → 开始新段
            else:
                # 保存当前段
                if accumulated_duration > 0:
                    current_end = current_start + accumulated_duration
                    segments.append((current_start, current_end))
                    current_start = current_end  # 无缝拼接

                # 开始新段，包含这个镜头
                accumulated_duration = shot.duration

        # 处理最后一段
        if accumulated_duration > 0:
            current_end = current_start + accumulated_duration
            segments.append((current_start, current_end))

        # 输出分段结果
        print(f"📋 智能分段完成: {len(shots)}个镜头 → {len(segments)}个片段 (无缝拼接)")
        for i, (start, end) in enumerate(segments):
            print(f"   片段{i+1:2d}: {start:6.1f}s - {end:6.1f}s (时长: {end-start:5.1f}s)")

        # 验证连续性
        if len(segments) > 1:
            gaps = []
            for i in range(len(segments) - 1):
                gap = segments[i+1][0] - segments[i][1]
                if abs(gap) > 0.01:  # 允许0.01s的浮点误差
                    gaps.append((i+1, gap))

            if gaps:
                print(f"⚠️  警告: 检测到 {len(gaps)} 个间隔")
                for seg_idx, gap in gaps[:3]:  # 最多显示3个
                    print(f"   片段{seg_idx}和{seg_idx+1}之间: {gap:.2f}s")
            else:
                print(f"✅ 验证通过: 所有片段无缝拼接")

        return segments

    def _truncate_shot(self, shot: Shot) -> List[Tuple[float, float]]:
        """
        硬截断超长镜头

        Args:
            shot: 超长的镜头

        Returns:
            List[Tuple[float, float]]: 截断后的时间段列表
        """
        segments = []
        start_time = shot.start_time
        remaining_time = shot.duration

        # 按max_duration截断
        while remaining_time > self.max_duration:
            end_time = start_time + self.max_duration
            segments.append((start_time, end_time))
            start_time = end_time
            remaining_time -= self.max_duration

        # 处理剩余部分
        if remaining_time > 0:
            segments.append((start_time, shot.end_time))

        return segments

    def get_segment_stats(self, segments: List[Tuple[float, float]]) -> dict:
        """
        获取分段统计信息

        Args:
            segments: 分段结果

        Returns:
            dict: 统计信息
        """
        if not segments:
            return {
                'segment_count': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0,
                'min_duration': 0.0,
                'max_duration': 0.0,
                'utilization_rate': 0.0
            }

        durations = [end - start for start, end in segments]
        total_duration = sum(durations)

        stats = {
            'segment_count': len(segments),
            'total_duration': total_duration,
            'avg_duration': total_duration / len(segments),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'utilization_rate': (total_duration / (len(segments) * self.max_duration)) * 100
        }

        return stats