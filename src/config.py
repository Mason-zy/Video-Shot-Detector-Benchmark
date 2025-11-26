#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
Configuration File for Shot Detection Tool

包含默认参数和配置选项
"""

# 默认配置
DEFAULT_CONFIG = {
    # PySceneDetect 默认参数
    'pyscene': {
        'threshold': 27.0,          # 内容变化阈值
        'min_scene_len': 15,        # 最小镜头长度(帧)
        'description': '基于 OpenCV 的传统场景检测算法'
    },

    # FFmpeg 默认参数
    'ffmpeg': {
        'threshold': 0.3,           # 场景变化阈值 (0.0-1.0)
        'min_scene_len': 1.0,       # 最小镜头长度(秒)
        'description': '基于 FFmpeg select 滤镜的场景检测'
    },

    # TransNet V2 默认参数
    'transnet': {
        'model_dir': './models/transnetv2',
        'input_size': [100, 56],    # 模型输入尺寸
        'description': '基于深度学习的 SOTA 镜头分割模型'
    },

    # 输出配置
    'output': {
        'base_dir': 'output',
        'create_timestamp_dirs': True,
        'generate_reports': True,
        'video_format': 'mp4',
        'encoding': 'copy'          # 使用 copy 避免重新编码
    },

    # 通用配置
    'general': {
        'supported_formats': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'],
        'max_video_size_gb': 10,    # 最大视频文件大小限制
        'temp_dir': './temp',
        'cleanup_temp': True
    }
}

# 预设配置组合
PRESETS = {
    'fast': {
        'pyscene': {'threshold': 30.0, 'min_scene_len': 20},
        'ffmpeg': {'threshold': 0.4, 'min_scene_len': 1.5},
        'transnet': {'enabled': False}
    },
    'sensitive': {
        'pyscene': {'threshold': 20.0, 'min_scene_len': 10},
        'ffmpeg': {'threshold': 0.2, 'min_scene_len': 0.5},
        'transnet': {'enabled': True}
    },
    'balanced': {
        'pyscene': {'threshold': 27.0, 'min_scene_len': 15},
        'ffmpeg': {'threshold': 0.3, 'min_scene_len': 1.0},
        'transnet': {'enabled': True}
    }
}


def get_config(preset: str = 'balanced', custom_overrides: dict = None) -> dict:
    """
    获取配置，支持预设和自定义覆盖

    Args:
        preset: 预设名称 ('fast', 'sensitive', 'balanced')
        custom_overrides: 自定义配置覆盖

    Returns:
        dict: 合并后的配置
    """
    # 从默认配置开始
    config = DEFAULT_CONFIG.copy()

    # 应用预设
    if preset in PRESETS:
        for algo, params in PRESETS[preset].items():
            if algo in config:
                config[algo].update(params)

    # 应用自定义覆盖
    if custom_overrides:
        for section, values in custom_overrides.items():
            if section in config:
                config[section].update(values)
            else:
                config[section] = values

    return config