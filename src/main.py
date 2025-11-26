#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
镜头分割算法对比工具主程序
Main Entry Point for Shot Boundary Detection Comparison Tool

作者: Assistant
日期: 2024-11-25
"""

import argparse
import sys
import os
import time
from typing import Dict, List, Any, Optional

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shot_detector import ShotBoundary
from pyscene_detector import PySceneDetector
from ffmpeg_detector import FFmpegDetector
from transnet_detector import TransNetV2Detector
from output_manager import OutputManager


class ShotComparisonApp:
    """镜头分割对比应用主类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化应用

        Args:
            config: 配置参数
        """
        self.config = config
        self.video_path = config['video_path']
        self.output_manager = OutputManager(config.get('output_dir', 'output'))
        self.enabled_algorithms = config.get('algorithms', ['pyscene', 'ffmpeg', 'transnet'])

        print("🎬 镜头分割算法对比工具")
        print("=" * 50)
        print(f"📹 输入视频: {self.video_path}")
        print(f"🔧 启用的算法: {', '.join(self.enabled_algorithms)}")
        print("=" * 50)

    def validate_video_file(self) -> bool:
        """
        验证视频文件是否存在且可读

        Returns:
            bool: 验证结果
        """
        if not os.path.exists(self.video_path):
            print(f"❌ 视频文件不存在: {self.video_path}")
            return False

        if not os.access(self.video_path, os.R_OK):
            print(f"❌ 无法读取视频文件: {self.video_path}")
            return False

        # 检查文件扩展名
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
        file_ext = os.path.splitext(self.video_path)[1].lower()
        if file_ext not in video_extensions:
            print(f"⚠️  警告: 不常见的视频格式 {file_ext}，可能无法正常处理")

        return True

    def run_algorithm(self, algorithm_name: str) -> Dict[str, Any]:
        """
        运行指定的镜头分割算法

        Args:
            algorithm_name: 算法名称

        Returns:
            Dict[str, Any]: 算法运行结果
        """
        print(f"\n🚀 开始运行 {algorithm_name.upper()} 算法...")
        print("-" * 40)

        start_time = time.time()
        result = {
            'algorithm': algorithm_name,
            'shot_count': 0,
            'processing_time': 0,
            'extracted_files': 0,
            'shots': [],
            'notes': ''
        }

        try:
            # 创建检测器实例
            detector = self._create_detector(algorithm_name)
            if detector is None:
                return result

            # 检测镜头边界
            shots = detector.detect_shots()
            result['shots'] = shots
            result['shot_count'] = len(shots)

            if not shots:
                result['notes'] = '未检测到任何镜头'
                return result

            # 提取镜头片段
            output_dir = self.output_manager.get_algorithm_output_dir(algorithm_name)
            extracted_files = detector.extract_shots(shots, output_dir)
            result['extracted_files'] = len(extracted_files)

            # 添加算法信息
            result['algorithm_info'] = detector.get_algorithm_info()

            # 计算总时长
            total_duration = sum(shot.duration for shot in shots)
            result['total_duration'] = total_duration

            processing_time = time.time() - start_time
            result['processing_time'] = processing_time

            print(f"✅ {algorithm_name.upper()} 完成!")
            print(f"   检测镜头数: {len(shots)}")
            print(f"   提取文件数: {len(extracted_files)}")
            print(f"   处理时间: {processing_time:.2f}秒")

        except Exception as e:
            result['notes'] = f'错误: {str(e)}'
            print(f"❌ {algorithm_name.upper()} 运行失败: {e}")

        return result

    def _create_detector(self, algorithm_name: str):
        """
        创建检测器实例

        Args:
            algorithm_name: 算法名称

        Returns:
            检测器实例或None
        """
        try:
            if algorithm_name.lower() == 'pyscene':
                return PySceneDetector(
                    self.video_path,
                    threshold=self.config.get('pyscene_threshold', 27.0),
                    min_scene_len=self.config.get('pyscene_min_scene_len', 15)
                )
            elif algorithm_name.lower() == 'ffmpeg':
                return FFmpegDetector(
                    self.video_path,
                    threshold=self.config.get('ffmpeg_threshold', 0.3),
                    min_scene_len=self.config.get('ffmpeg_min_scene_len', 1.0)
                )
            elif algorithm_name.lower() == 'transnet':
                return TransNetV2Detector(
                    self.video_path,
                    model_dir=self.config.get('transnet_model_dir', './models/transnetv2')
                )
            else:
                print(f"❌ 不支持的算法: {algorithm_name}")
                return None

        except ImportError as e:
            print(f"❌ {algorithm_name} 依赖库缺失: {e}")
            return None
        except Exception as e:
            print(f"❌ 创建 {algorithm_name} 检测器失败: {e}")
            return None

    def run_all_algorithms(self) -> Dict[str, Dict[str, Any]]:
        """
        运行所有启用的算法

        Returns:
            Dict[str, Dict[str, Any]]: 所有算法的结果
        """
        results = {}

        for algorithm in self.enabled_algorithms:
            result = self.run_algorithm(algorithm)
            results[algorithm] = result

            # 如果设置了只运行第一个成功的算法，则提前退出
            if self.config.get('run_first_only', False) and result['shot_count'] > 0:
                print(f"✨ 只运行第一个成功算法: {algorithm}")
                break

        return results

    def generate_reports(self, results: Dict[str, Dict[str, Any]]):
        """
        生成所有报告

        Args:
            results: 算法结果
        """
        print(f"\n📊 生成分析报告...")
        print("=" * 40)

        # 获取视频信息
        video_info = {
            'video_path': self.video_path,
            **self._get_video_info()
        }

        # 生成基本报告
        self.output_manager.save_basic_report(results)

        # 生成详细报告
        self.output_manager.save_detailed_report(results, video_info)

        # 生成分析摘要
        summary = self.output_manager.generate_summary_analysis(results)

        # 打印摘要
        print("\n" + summary)

    def _get_video_info(self) -> Dict[str, Any]:
        """
        获取视频基本信息

        Returns:
            Dict[str, Any]: 视频信息
        """
        try:
            # 使用第一个可用的检测器获取视频信息
            for algorithm in ['pyscene', 'ffmpeg', 'transnet']:
                if algorithm in self.enabled_algorithms:
                    detector = self._create_detector(algorithm)
                    if detector:
                        return detector.video_info
            return {}
        except Exception:
            return {}

    def run(self):
        """运行主程序"""
        try:
            # 验证视频文件
            if not self.validate_video_file():
                return 1

            # 显示输出目录结构
            self.output_manager.print_directory_structure()

            # 运行算法
            results = self.run_all_algorithms()

            if not results:
                print("❌ 没有算法成功运行")
                return 1

            # 生成报告
            self.generate_reports(results)

            print(f"\n🎉 任务完成! 结果保存在: {self.output_manager.main_output_dir}")
            return 0

        except KeyboardInterrupt:
            print("\n⏹️  用户中断操作")
            return 1
        except Exception as e:
            print(f"\n❌ 程序运行出错: {e}")
            return 1


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='镜头分割算法对比工具 - 对比 PySceneDetect, FFmpeg, TransNet V2 的效果',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py input_video.mp4                    # 运行所有算法
  python main.py input_video.mp4 -a pyscene ffmpeg  # 只运行指定算法
  python main.py input_video.mp4 --pyscene-threshold 30.0  # 调整参数
  python main.py input_video.mp4 --output-dir my_results  # 指定输出目录

算法说明:
  pyscene   - PySceneDetect (基于 OpenCV 的传统算法)
  ffmpeg    - FFmpeg (基于 select 滤镜的场景检测)
  transnet  - TransNet V2 (基于深度学习的 SOTA 模型)
        """
    )

    # 必需参数
    parser.add_argument('video_path', help='输入视频文件路径')

    # 可选参数
    parser.add_argument('-a', '--algorithms', nargs='+',
                        choices=['pyscene', 'ffmpeg', 'transnet'],
                        default=['pyscene', 'ffmpeg', 'transnet'],
                        help='选择要运行的算法 (默认: 全部)')

    parser.add_argument('-o', '--output-dir', default='output',
                        help='输出目录 (默认: output)')

    parser.add_argument('--first-only', action='store_true',
                        help='只运行第一个成功的算法')

    # PySceneDetect 参数
    parser.add_argument('--pyscene-threshold', type=float, default=27.0,
                        help='PySceneDetect 内容变化阈值 (默认: 27.0)')

    parser.add_argument('--pyscene-min-scene-len', type=int, default=15,
                        help='PySceneDetect 最小镜头长度(帧) (默认: 15)')

    # FFmpeg 参数
    parser.add_argument('--ffmpeg-threshold', type=float, default=0.3,
                        help='FFmpeg 场景变化阈值 (默认: 0.3)')

    parser.add_argument('--ffmpeg-min-scene-len', type=float, default=1.0,
                        help='FFmpeg 最小镜头长度(秒) (默认: 1.0)')

    # TransNet V2 参数
    parser.add_argument('--transnet-model-dir', default='./models/transnetv2',
                        help='TransNet V2 模型目录 (默认: ./models/transnetv2)')

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 构建配置
    config = {
        'video_path': args.video_path,
        'output_dir': args.output_dir,
        'algorithms': args.algorithms,
        'run_first_only': args.first_only,
        'pyscene_threshold': args.pyscene_threshold,
        'pyscene_min_scene_len': args.pyscene_min_scene_len,
        'ffmpeg_threshold': args.ffmpeg_threshold,
        'ffmpeg_min_scene_len': args.ffmpeg_min_scene_len,
        'transnet_model_dir': args.transnet_model_dir
    }

    # 创建并运行应用
    app = ShotComparisonApp(config)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())