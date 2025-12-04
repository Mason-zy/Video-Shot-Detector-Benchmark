"""
智能分段器

基于镜头检测结果，按照最大时长约束进行智能分段。

核心策略：
1. 顺序累加镜头，尽量接近max_duration
2. 单个镜头超长 → 硬截断
3. 最后一段即使很短也保留

特点：
- 最大化时长利用率
- 保证镜头完整性（优先）
- 支持硬截断超长镜头
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
        print(f"🎯 分段器初始化: 最大时长 {max_duration}秒")

    def segment(self, shots: List[Shot]) -> List[Tuple[float, float]]:
        """
        将镜头列表智能分段

        Args:
            shots: 镜头列表

        Returns:
            List[Tuple[float, float]]: [(start_time, end_time), ...]

        Examples:
            >>> shots = [Shot(0, 750, 0.0, 30.0, 30.0)]
            >>> segmenter = SmartSegmenter(max_duration=30)
            >>> segments = segmenter.segment(shots)
            >>> print(segments)
            [(0.0, 30.0)]
        """
        if not shots:
            print("⚠️  警告: 没有镜头检测到")
            return []

        print(f"📋 开始智能分段: {len(shots)}个镜头, 最大时长{self.max_duration}秒")

        segments = []
        current_start = 0.0
        current_duration = 0.0
        total_utilization = 0.0
        truncated_count = 0

        for i, shot in enumerate(shots):
            print(f"  镜头{i+1}: {shot.start_time:.1f}s - {shot.end_time:.1f}s "
                  f"(时长: {shot.duration:.1f}s)")

            # 情况1: 可以加入当前段
            if current_duration + shot.duration <= self.max_duration:
                print(f"    ✅ 加入当前段 (累计: {current_duration + shot.duration:.1f}s)")
                current_duration += shot.duration

            # 情况2: 单个镜头超长 → 硬截断
            elif shot.duration > self.max_duration:
                print(f"    ⚠️  镜头超长({shot.duration:.1f}s > {self.max_duration}s), 需要截断")

                # 保存当前段（如果有内容）
                if current_duration > 0:
                    segment = (current_start, current_start + current_duration)
                    segments.append(segment)
                    utilization = (current_duration / self.max_duration) * 100
                    total_utilization += utilization
                    print(f"    💾 保存当前段: [{current_start:.1f}, {segment[1]:.1f}] "
                          f"(利用率: {utilization:.1f}%)")

                # 硬截断超长镜头
                truncated_segments = self._truncate_shot(shot)
                segments.extend(truncated_segments)
                truncated_count += len(truncated_segments)

                # 重置状态
                current_start = shot.end_time
                current_duration = 0.0

            # 情况3: 超出max_duration → 开始新段
            else:
                print(f"    🔄 开始新段 (当前段: {current_duration:.1f}s, "
                      f"新镜头: {shot.duration:.1f}s)")

                # 保存当前段
                if current_duration > 0:
                    segment = (current_start, current_start + current_duration)
                    segments.append(segment)
                    utilization = (current_duration / self.max_duration) * 100
                    total_utilization += utilization
                    print(f"    💾 保存当前段: [{current_start:.1f}, {segment[1]:.1f}] "
                          f"(利用率: {utilization:.1f}%)")

                # 开始新段
                current_start = shot.start_time
                current_duration = shot.duration

        # 处理最后一个段
        if current_duration > 0:
            segment = (current_start, current_start + current_duration)
            segments.append(segment)
            utilization = (current_duration / self.max_duration) * 100
            total_utilization += utilization
            print(f"    💾 保存最后段: [{current_start:.1f}, {segment[1]:.1f}] "
                  f"(利用率: {utilization:.1f}%)")

        # 统计信息
        avg_utilization = total_utilization / len(segments) if segments else 0
        print(f"✅ 分段完成:")
        print(f"   - 总片段数: {len(segments)}")
        print(f"   - 截断镜头数: {truncated_count}")
        print(f"   - 平均利用率: {avg_utilization:.1f}%")

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
        segment_count = 0

        print(f"    🔪 截断镜头 {shot.duration:.1f}s:")

        # 按max_duration截断
        while remaining_time > self.max_duration:
            end_time = start_time + self.max_duration
            segments.append((start_time, end_time))

            segment_count += 1
            print(f"      片段{segment_count}: [{start_time:.1f}, {end_time:.1f}] "
                  f"(时长: {self.max_duration}s)")

            start_time = end_time
            remaining_time -= self.max_duration

        # 处理剩余部分
        if remaining_time > 0:
            end_time = shot.end_time
            segments.append((start_time, end_time))

            segment_count += 1
            print(f"      片段{segment_count}: [{start_time:.1f}, {end_time:.1f}] "
                  f"(时长: {remaining_time:.1f}s)")

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