# -*- coding: utf-8 -*-
"""
日志管理工具模块
支持自动轮转（单文件最大5MB）
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json

# 日志目录
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件最大大小：5MB
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB in bytes

# 全局logger字典
_loggers = {}


def get_logger(name="app"):
    """
    获取logger实例
    支持文件自动轮转（单文件5MB）

    Args:
        name: logger名称

    Returns:
        logger实例
    """
    if name in _loggers:
        return _loggers[name]

    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加handler
    if logger.handlers:
        _loggers[name] = logger
        return logger

    # 日志文件路径：logs/YYYYMMDD_app.log
    log_filename = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}_{name}.log")

    # 创建RotatingFileHandler（自动轮转）
    file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=MAX_LOG_SIZE,
        backupCount=10,  # 保留最多10个备份文件
        encoding='utf-8'
    )

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # 添加handler到logger
    logger.addHandler(file_handler)

    # 缓存logger
    _loggers[name] = logger

    return logger


def log_pdf_generation(logger_name, generator_type, params):
    """
    记录PDF生成日志

    Args:
        logger_name: logger名称
        generator_type: 生成器类型（"默写纸" 或 "成绩小分条"）
        params: 参数字典，包含所有生成参数
    """
    logger = get_logger(logger_name)

    # 构建日志信息
    log_message = f"[{generator_type}生成器] "

    # 添加参数信息
    param_str = json.dumps(params, ensure_ascii=False, indent=2)
    log_message += f"参数: {param_str}"

    logger.info(log_message)


def log_dictation_generation(
    date_str,
    scope,
    items_count,
    col_num,
    row_num,
    font_size,
    padding,
    client_ip="unknown"
):
    """
    记录默写纸生成日志

    Args:
        date_str: 日期字符串
        scope: 标题/范围
        items_count: 项目数量
        col_num: 列数
        row_num: 行数
        font_size: 字号
        padding: 边距
        client_ip: 客户端IP地址
    """
    params = {
        "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "客户端IP": client_ip,
        "日期": date_str,
        "标题": scope,
        "项目数量": items_count,
        "列数": col_num,
        "行数": row_num,
        "字号": font_size,
        "边距(mm)": padding,
        "每页区域数": col_num * row_num
    }

    log_pdf_generation("dictation", "默写纸", params)


def log_grades_generation(
    excel_filename,
    title,
    card_title,
    orientation,
    cols,
    rows,
    card_h,
    margin,
    gutter,
    title_font_size,
    card_title_font_size,
    body_font_size,
    detail_cols,
    total_records,
    has_custom_font,
    client_ip="unknown"
):
    """
    记录成绩小分条生成日志

    Args:
        excel_filename: Excel文件名
        title: 文档标题
        card_title: 卡片标题
        orientation: 页面方向
        cols: 每行卡片数
        rows: 每页行数
        card_h: 卡片高度
        margin: 页面边距
        gutter: 卡片间距
        title_font_size: 人名/学号字号
        card_title_font_size: 卡片标题字号
        body_font_size: 正文字号
        detail_cols: 选择的列
        total_records: 总记录数
        has_custom_font: 是否使用自定义字体
        client_ip: 客户端IP地址
    """
    params = {
        "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "客户端IP": client_ip,
        "Excel文件": excel_filename,
        "文档标题": title,
        "卡片标题": card_title,
        "页面方向": orientation,
        "每行卡片数": cols,
        "每页行数": rows,
        "卡片高度": card_h,
        "页面边距": margin,
        "卡片间距": gutter,
        "人名/学号字号": title_font_size,
        "卡片标题字号": card_title_font_size,
        "正文字号": body_font_size,
        "选择的列": detail_cols,
        "总记录数": total_records,
        "使用自定义字体": has_custom_font,
        "每页卡片数": cols * rows
    }

    log_pdf_generation("grades", "成绩小分条", params)


def get_log_info():
    """
    获取日志文件信息

    Returns:
        日志文件信息列表
    """
    log_files = []

    if not os.path.exists(LOG_DIR):
        return log_files

    for filename in os.listdir(LOG_DIR):
        if filename.endswith('.log'):
            filepath = os.path.join(LOG_DIR, filename)
            file_size = os.path.getsize(filepath)
            file_mtime = os.path.getmtime(filepath)

            log_files.append({
                "文件名": filename,
                "文件路径": filepath,
                "大小(MB)": round(file_size / (1024 * 1024), 2),
                "修改时间": datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })

    # 按修改时间降序排序
    log_files.sort(key=lambda x: x["修改时间"], reverse=True)

    return log_files

