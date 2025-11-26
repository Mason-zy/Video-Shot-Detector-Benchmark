#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输出管理器
Output Manager for Shot Detection Results

管理镜头分割结果的输出、报告生成和文件组织
"""

import os
import csv
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from shot_detector import ShotBoundary


class OutputManager:
    """输出结果管理器"""

    def __init__(self, base_output_dir: str = "output"):
        """
        初始化输出管理器

        Args:
            base_output_dir: 基础输出目录
        """
        self.base_output_dir = base_output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.main_output_dir = None
        self.report_path = None
        self.detailed_report_path = None
        self._create_output_structure()

    def _create_output_structure(self):
        """创建输出目录结构"""
        # 创建主输出目录
        self.main_output_dir = os.path.join(
            self.base_output_dir,
            f"shot_comparison_{self.timestamp}"
        )
        os.makedirs(self.main_output_dir, exist_ok=True)

        # 创建各算法的子目录
        algorithm_dirs = ['pyscene', 'ffmpeg', 'transnet']
        for algo_dir in algorithm_dirs:
            os.makedirs(
                os.path.join(self.main_output_dir, algo_dir),
                exist_ok=True
            )

        # 设置报告文件路径
        self.report_path = os.path.join(self.main_output_dir, "report.csv")
        self.detailed_report_path = os.path.join(self.main_output_dir, "detailed_report.json")

        print(f"📁 输出目录已创建: {self.main_output_dir}")

    def get_algorithm_output_dir(self, algorithm_name: str) -> str:
        """
        获取指定算法的输出目录

        Args:
            algorithm_name: 算法名称 ('pyscene', 'ffmpeg', 'transnet')

        Returns:
            str: 算法输出目录路径
        """
        algo_dirs = {
            'pyscene': 'pyscene',
            'ffmpeg': 'ffmpeg',
            'transnet': 'transnet'
        }

        if algorithm_name.lower() not in algo_dirs:
            raise ValueError(f"不支持的算法: {algorithm_name}")

        return os.path.join(self.main_output_dir, algo_dirs[algorithm_name.lower()])

    def save_basic_report(self, results: Dict[str, Dict[str, Any]]):
        """
        保存基本对比报告 (CSV格式)

        Args:
            results: 各算法的结果数据
        """
        print("📊 生成基本对比报告...")

        with open(self.report_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                '算法',
                '检测到的镜头数量',
                '处理时间(秒)',
                '平均镜头时长(秒)',
                '最短镜头时长(秒)',
                '最长镜头时长(秒)',
                '提取文件数',
                '成功率(%)',
                '备注'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for algorithm, data in results.items():
                # 计算统计信息
                shot_count = data.get('shot_count', 0)
                processing_time = data.get('processing_time', 0)
                extracted_files = data.get('extracted_files', 0)

                # 计算平均、最短、最长镜头时长
                avg_duration = 0
                min_duration = 0
                max_duration = 0

                if 'shots' in data and len(data['shots']) > 0:
                    durations = [shot.duration for shot in data['shots']]
                    avg_duration = sum(durations) / len(durations)
                    min_duration = min(durations)
                    max_duration = max(durations)

                # 计算成功率
                success_rate = (extracted_files / shot_count * 100) if shot_count > 0 else 0

                writer.writerow({
                    '算法': algorithm,
                    '检测到的镜头数量': shot_count,
                    '处理时间(秒)': f"{processing_time:.2f}",
                    '平均镜头时长(秒)': f"{avg_duration:.2f}",
                    '最短镜头时长(秒)': f"{min_duration:.2f}",
                    '最长镜头时长(秒)': f"{max_duration:.2f}",
                    '提取文件数': extracted_files,
                    '成功率(%)': f"{success_rate:.1f}",
                    '备注': data.get('notes', '')
                })

        print(f"✅ 基本报告已保存: {self.report_path}")

    def save_detailed_report(self, results: Dict[str, Dict[str, Any]], video_info: Dict):
        """
        保存详细报告 (JSON格式)

        Args:
            results: 各算法的结果数据
            video_info: 视频信息
        """
        print("📋 生成详细报告...")

        detailed_data = {
            'metadata': {
                'timestamp': self.timestamp,
                'video_path': video_info.get('video_path', 'Unknown'),
                'video_info': {
                    'duration': video_info.get('duration', 0),
                    'fps': video_info.get('fps', 0),
                    'frame_count': video_info.get('frame_count', 0),
                    'resolution': f"{video_info.get('width', 0)}x{video_info.get('height', 0)}"
                },
                'total_processing_time': sum(
                    data.get('processing_time', 0) for data in results.values()
                )
            },
            'algorithms': {}
        }

        # 为每个算法添加详细信息
        for algorithm, data in results.items():
            algo_data = {
                'algorithm_info': data.get('algorithm_info', {}),
                'performance': {
                    'shot_count': data.get('shot_count', 0),
                    'processing_time': data.get('processing_time', 0),
                    'extracted_files': data.get('extracted_files', 0),
                    'success_rate': (data.get('extracted_files', 0) / max(data.get('shot_count', 1), 1) * 100)
                },
                'shots': []
            }

            # 添加每个镜头的详细信息
            if 'shots' in data:
                for i, shot in enumerate(data['shots']):
                    shot_info = {
                        'index': i + 1,
                        'start_frame': shot.start_frame,
                        'end_frame': shot.end_frame,
                        'start_time': shot.start_time,
                        'end_time': shot.end_time,
                        'duration': shot.duration,
                        'filename': f"shot_{i+1:02d}_{shot.to_time_string(shot.start_time)}_to_{shot.to_time_string(shot.end_time)}.mp4"
                    }
                    algo_data['shots'].append(shot_info)

            detailed_data['algorithms'][algorithm] = algo_data

        # 保存详细报告
        with open(self.detailed_report_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(detailed_data, jsonfile, indent=2, ensure_ascii=False)

        print(f"✅ 详细报告已保存: {self.detailed_report_path}")

    def generate_summary_analysis(self, results: Dict[str, Dict[str, Any]]) -> str:
        """
        生成对比分析摘要

        Args:
            results: 各算法的结果数据

        Returns:
            str: 分析摘要文本
        """
        print("🔍 生成对比分析摘要...")

        summary_lines = [
            "=" * 60,
            "镜头分割算法对比分析摘要",
            "=" * 60,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        # 统计基本信息
        total_shots = sum(data.get('shot_count', 0) for data in results.values())
        avg_processing_time = sum(data.get('processing_time', 0) for data in results.values()) / max(len(results), 1)

        summary_lines.extend([
            f"总体统计:",
            f"  - 总检测镜头数: {total_shots}",
            f"  - 平均处理时间: {avg_processing_time:.2f}秒",
            ""
        ])

        # 各算法详细对比
        summary_lines.append("各算法表现:")
        for algorithm, data in results.items():
            shot_count = data.get('shot_count', 0)
            processing_time = data.get('processing_time', 0)
            success_rate = (data.get('extracted_files', 0) / max(shot_count, 1) * 100)

            summary_lines.extend([
                f"  {algorithm}:",
                f"    - 检测镜头数: {shot_count}",
                f"    - 处理时间: {processing_time:.2f}秒",
                f"    - 提取成功率: {success_rate:.1f}%"
            ])

        summary_lines.extend([
            "",
            "文件位置:",
            f"  - 输出目录: {self.main_output_dir}",
            f"  - 基本报告: {self.report_path}",
            f"  - 详细报告: {self.detailed_report_path}",
            "=" * 60
        ])

        summary_text = "\n".join(summary_lines)

        # 保存摘要到文件
        summary_path = os.path.join(self.main_output_dir, "analysis_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)

        print(f"✅ 分析摘要已保存: {summary_path}")
        return summary_text

    def print_directory_structure(self):
        """打印输出目录结构"""
        print("\n📂 输出目录结构:")
        print(f"{self.main_output_dir}/")
        print("├── pyscene/          # PySceneDetect 结果")
        print("├── ffmpeg/           # FFmpeg 结果")
        print("├── transnet/         # TransNet V2 结果")
        print("├── report.csv        # 基本对比报告")
        print("├── detailed_report.json  # 详细报告")
        print("└── analysis_summary.txt   # 分析摘要")

    def get_output_info(self) -> Dict[str, str]:
        """
        获取输出信息

        Returns:
            Dict[str, str]: 输出路径信息
        """
        return {
            'main_output_dir': self.main_output_dir,
            'report_path': self.report_path,
            'detailed_report_path': self.detailed_report_path,
            'pyscene_dir': self.get_algorithm_output_dir('pyscene'),
            'ffmpeg_dir': self.get_algorithm_output_dir('ffmpeg'),
            'transnet_dir': self.get_algorithm_output_dir('transnet')
        }