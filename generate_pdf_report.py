#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux系统进程巡检报告生成器 - ReportLab版本
使用reportlab库生成PDF，无需外部依赖
"""

import json
import sys
import os
import subprocess
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, Image
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def register_chinese_fonts():
    """注册中文字体"""
    # 优先使用 font 文件夹中的字体
    font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font')
    font_paths = [
        os.path.join(font_dir, 'SimHei.ttf'),
        os.path.join(font_dir, 'SimSun.ttf'),
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Chinese', font_path))
                return 'Chinese'
            except Exception:
                continue
    
    # 尝试系统字体
    try:
        result = subprocess.run(
            ['fc-list', ':lang=zh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False
        )
        font_path = None
        if result.stdout:
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.rsplit(':', 1)
                if len(parts) != 2:
                    continue
                path = parts[1].strip()
                if os.path.exists(path):
                    font_path = path
                    break
        if font_path:
            pdfmetrics.registerFont(TTFont('Chinese', font_path))
            return 'Chinese'
    except Exception:
        pass

    # 系统默认字体路径
    system_font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    ]

    for font_path in system_font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Chinese', font_path))
                return 'Chinese'
            except Exception:
                continue

    return 'Helvetica'

# 全局字体设置
CHINESE_FONT = None

def get_font():
    """获取中文字体名称"""
    global CHINESE_FONT
    if CHINESE_FONT is None:
        CHINESE_FONT = register_chinese_fonts()
    return CHINESE_FONT

def create_styles():
    """创建样式"""
    font_name = get_font()
    styles = getSampleStyleSheet()
    
    # 标题样式
    styles.add(ParagraphStyle(
        name='CustomTitle',
        fontName=font_name,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50')
    ))
    
    # 副标题样式
    styles.add(ParagraphStyle(
        name='CustomSubtitle',
        fontName=font_name,
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#5a6c7d')
    ))
    
    # 章节标题
    styles.add(ParagraphStyle(
        name='ChapterTitle',
        fontName=font_name,
        fontSize=16,
        leading=20,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#2c3e50'),
        borderColor=colors.HexColor('#2c3e50'),
        borderWidth=2,
        borderPadding=5
    ))
    
    # 小节标题
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName=font_name,
        fontSize=13,
        leading=16,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#34495e')
    ))
    
    # 正文
    styles.add(ParagraphStyle(
        name='CustomBody',
        fontName=font_name,
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceBefore=5,
        spaceAfter=5
    ))
    
    # 表格单元格
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName=font_name,
        fontSize=8,
        leading=10,
        wordWrap=True
    ))
    
    # 表格标题
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName=font_name,
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER
    ))
    
    # 警告框
    styles.add(ParagraphStyle(
        name='AlertTitle',
        fontName=font_name,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#721c24'),
        spaceAfter=5
    ))
    
    styles.add(ParagraphStyle(
        name='AlertBody',
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#721c24')
    ))
    
    # 成功框
    styles.add(ParagraphStyle(
        name='SuccessTitle',
        fontName=font_name,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#155724'),
        spaceAfter=5
    ))
    
    styles.add(ParagraphStyle(
        name='SuccessBody',
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#155724')
    ))
    
    # 元信息
    styles.add(ParagraphStyle(
        name='MetaInfo',
        fontName=font_name,
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=5
    ))
    
    return styles

def load_audit_data(json_path):
    """加载审计数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_cover_page(data, styles):
    """创建封面"""
    elements = []
    
    info = data['audit_info']
    proc_summary = data['process_summary']
    port_summary = data['port_summary']
    
    # 计算风险等级
    overall_risk = '正常'
    risk_color = colors.HexColor('#28a745')
    if proc_summary.get('suspicious_processes', 0) > 0:
        overall_risk = '高风险'
        risk_color = colors.HexColor('#dc3545')
    elif port_summary.get('high_risk_ports', 0) > 0:
        overall_risk = '中高风险'
        risk_color = colors.HexColor('#fd7e14')
    elif port_summary.get('medium_risk_ports', 0) > 5:
        overall_risk = '中风险'
        risk_color = colors.HexColor('#ffc107')
    
    # 顶部装饰线
    elements.append(Spacer(1, 3*cm))
    
    # 主标题
    elements.append(Paragraph("Linux系统进程巡检报告", styles['CustomTitle']))
    elements.append(Spacer(1, 0.5*cm))
    
    # 副标题
    elements.append(Paragraph("System Process & Port Security Audit Report", styles['CustomSubtitle']))
    elements.append(Spacer(1, 3*cm))
    
    # 元信息表格
    meta_data = [
        ['主机:', info['hostname']],
        ['系统:', f"{info['os_name']} {info['os_version']}"],
        ['内核:', info['kernel']],
        ['时间:', info['audit_time']],
    ]
    
    meta_table = Table(meta_data, colWidths=[3*cm, 8*cm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), get_font()),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 2*cm))
    
    # 风险等级
    risk_data = [['整体风险等级:', overall_risk]]
    risk_table = Table(risk_data, colWidths=[4*cm, 4*cm])
    risk_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), get_font()),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#333')),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('BACKGROUND', (1, 0), (1, 0), risk_color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(risk_table)
    
    elements.append(PageBreak())
    return elements

def create_summary_section(data, styles):
    """创建执行摘要"""
    elements = []
    
    info = data['audit_info']
    proc_summary = data['process_summary']
    port_summary = data['port_summary']
    
    elements.append(Paragraph("一、执行摘要", styles['ChapterTitle']))
    
    # 巡检概况
    elements.append(Paragraph("巡检概况", styles['SectionTitle']))
    elements.append(Paragraph(
        f"本次巡检针对主机 <b>{info['hostname']}</b> 进行系统进程与端口安全分析。"
        f"巡检时间: {info['audit_time']}。系统运行时间: {info['uptime']}",
        styles['CustomBody']
    ))
    elements.append(Spacer(1, 0.3*cm))
    
    # 关键发现 - 统计卡片
    elements.append(Paragraph("关键发现", styles['SectionTitle']))
    
    stats_data = [
        ['总进程数', '监听端口', '可疑进程', '高风险端口'],
        [
            str(proc_summary['total_processes']),
            str(port_summary['total_listening']),
            str(proc_summary.get('suspicious_processes', 0)),
            str(port_summary.get('high_risk_ports', 0))
        ]
    ]
    
    stats_table = Table(stats_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), get_font()),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 20),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#666')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#2c3e50')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 15),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 15),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # 风险评估
    elements.append(Paragraph("风险评估", styles['SectionTitle']))
    
    if proc_summary.get('suspicious_processes', 0) > 0:
        elements.append(create_alert_box(
            "⚠ 发现可疑进程",
            f"系统检测到 <b>{proc_summary['suspicious_processes']}</b> 个可疑进程，建议立即进行详细审查。"
            "可疑进程可能指示系统已被入侵或存在恶意软件。",
            'danger',
            styles
        ))
    
    if port_summary.get('high_risk_ports', 0) > 0:
        elements.append(create_alert_box(
            "⚠ 发现高风险端口",
            f"系统检测到 <b>{port_summary['high_risk_ports']}</b> 个高风险端口处于开放状态。"
            "这些端口可能成为攻击者的目标，建议评估其必要性并采取适当的防护措施。",
            'warning',
            styles
        ))
    
    if proc_summary.get('suspicious_processes', 0) == 0 and port_summary.get('high_risk_ports', 0) == 0:
        elements.append(create_alert_box(
            "✓ 系统状态良好",
            "本次巡检未发现明显的安全威胁。系统进程和端口状态正常，建议继续保持良好的安全实践。",
            'success',
            styles
        ))
    
    elements.append(PageBreak())
    return elements

def create_alert_box(title, content, alert_type, styles):
    """创建警告框"""
    if alert_type == 'danger':
        bg_color = colors.HexColor('#f8d7da')
        border_color = colors.HexColor('#dc3545')
        title_style = styles['AlertTitle']
        body_style = styles['AlertBody']
    elif alert_type == 'warning':
        bg_color = colors.HexColor('#fff3cd')
        border_color = colors.HexColor('#ffc107')
        title_style = styles['AlertTitle']
        body_style = styles['AlertBody']
    else:  # success
        bg_color = colors.HexColor('#d4edda')
        border_color = colors.HexColor('#28a745')
        title_style = styles['SuccessTitle']
        body_style = styles['SuccessBody']
    
    data = [
        [Paragraph(title, title_style)],
        [Paragraph(content, body_style)]
    ]
    
    table = Table(data, colWidths=[14*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('BOX', (0, 0), (-1, -1), 2, border_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    return table

def create_system_info_section(data, styles):
    """创建系统基本信息"""
    elements = []
    info = data['audit_info']
    
    elements.append(Paragraph("二、系统基本信息", styles['ChapterTitle']))
    
    # 硬件信息
    elements.append(Paragraph("2.1 硬件信息", styles['SectionTitle']))
    
    hw_data = [
        ['CPU型号', info.get('cpu_info', 'N/A')],
        ['CPU核心数', f"{info.get('cpu_cores', 'N/A')} 核"],
        ['内存总量', info.get('memory_total', 'N/A')],
        ['内存使用', info.get('memory_used', 'N/A')],
    ]
    
    hw_table = Table(hw_data, colWidths=[3*cm, 11*cm])
    hw_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), get_font()),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#dee2e6')),
    ]))
    elements.append(hw_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # 系统状态
    elements.append(Paragraph("2.2 系统状态", styles['SectionTitle']))
    
    sys_data = [
        ['项目', '值'],
        ['主机名', info['hostname']],
        ['操作系统', f"{info['os_name']} {info['os_version']}"],
        ['内核版本', info['kernel']],
        ['系统架构', info['architecture']],
        ['运行时间', info['uptime']],
        ['磁盘使用', info.get('disk_usage', 'N/A')],
    ]
    
    sys_table = Table(sys_data, colWidths=[3*cm, 11*cm])
    sys_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), get_font()),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#dee2e6')),
    ]))
    elements.append(sys_table)
    
    elements.append(PageBreak())
    return elements

def create_user_analysis_section(data, styles):
    elements = []
    processes = data.get('processes', [])
    user_stats = {}
    for proc in processes:
        user = proc.get('user') or ''
        if not user:
            continue
        info = user_stats.setdefault(user, {'total': 0, 'system': 0, 'root_other': 0, 'suspicious': 0, 'user': 0})
        info['total'] += 1
        t = proc.get('type')
        if t == 'system':
            info['system'] += 1
        elif t == 'root_other':
            info['root_other'] += 1
        elif t == 'suspicious':
            info['suspicious'] += 1
        elif t == 'user':
            info['user'] += 1
    elements.append(Paragraph("三、用户分析", styles['ChapterTitle']))
    elements.append(Paragraph("3.1 用户进程概览", styles['SectionTitle']))
    total_users = len(user_stats)
    total_processes = len(processes)
    suspicious_users = sum(1 for v in user_stats.values() if v['suspicious'] > 0)
    elements.append(Paragraph(f"系统当前共有 <b>{total_users}</b> 个用户账户参与进程运行，共 <b>{total_processes}</b> 个进程。", styles['CustomBody']))
    if suspicious_users > 0:
        elements.append(Paragraph(f"其中 <b>{suspicious_users}</b> 个用户存在可疑进程，建议重点关注。", styles['CustomBody']))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph("3.2 用户进程统计表", styles['SectionTitle']))
    table_data = [['用户', '进程总数', '系统进程数', 'Root其他进程数', '可疑进程数', '普通用户进程数']]
    for user, info in sorted(user_stats.items(), key=lambda item: item[1]['total'], reverse=True):
        table_data.append([
            user[:16],
            str(info['total']),
            str(info['system']),
            str(info['root_other']),
            str(info['suspicious']),
            str(info['user'])
        ])
    user_table = Table(table_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 3*cm, 2.5*cm, 3*cm])
    user_table.setStyle(create_table_style())
    elements.append(user_table)
    elements.append(Spacer(1, 0.5*cm))
    suspicious_list = [(u, info) for u, info in user_stats.items() if info['suspicious'] > 0]
    if suspicious_list:
        elements.append(Paragraph("3.3 存在可疑进程的用户", styles['SectionTitle']))
        susp_data = [['用户', '可疑进程数', '进程总数']]
        for user, info in sorted(suspicious_list, key=lambda item: item[1]['suspicious'], reverse=True):
            susp_data.append([
                user[:16],
                str(info['suspicious']),
                str(info['total'])
            ])
        susp_table = Table(susp_data, colWidths=[4*cm, 4*cm, 4*cm])
        susp_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), get_font()),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#dee2e6')),
        ]))
        elements.append(susp_table)
    elements.append(PageBreak())
    return elements

def create_process_section(data, styles):
    """创建进程分析"""
    elements = []
    proc_summary = data['process_summary']
    processes = data.get('processes', [])
    user_stats = data.get('user_process_stats', [])
    
    elements.append(Paragraph("四、进程分析", styles['ChapterTitle']))
    
    # 进程概览
    elements.append(Paragraph("4.1 进程概览", styles['SectionTitle']))
    elements.append(Paragraph(
        f"系统当前共有 <b>{proc_summary['total_processes']}</b> 个进程在运行，分布如下：",
        styles['CustomBody']
    ))
    elements.append(Spacer(1, 0.3*cm))
    
    overview_data = [
        ['进程类型', '数量', '说明'],
        ['系统进程', str(proc_summary['system_processes']), '操作系统核心服务和守护进程'],
        ['用户进程', str(proc_summary['user_processes']), '普通用户运行的应用程序'],
        ['Root其他进程', str(proc_summary['root_other_processes']), 'Root用户运行的非系统进程'],
    ]
    
    if proc_summary.get('suspicious_processes', 0) > 0:
        overview_data.append([
            '可疑进程',
            str(proc_summary["suspicious_processes"]),
            '需要立即审查'
        ])
    
    overview_table = Table(overview_data, colWidths=[3*cm, 2*cm, 9*cm])
    overview_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), get_font()),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#dee2e6')),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # 用户进程分布
    elements.append(Paragraph("用户进程分布", styles['SectionTitle']))
    
    user_data = [['用户', '进程数']]
    for stat in user_stats[:10]:
        user_data.append([stat['user'], str(stat['count'])])
    
    user_table = Table(user_data, colWidths=[6*cm, 8*cm])
    user_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), get_font()),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#dee2e6')),
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # 系统进程详情
    elements.append(Paragraph("4.2 系统进程详情", styles['SectionTitle']))
    elements.append(Paragraph("以下为系统核心进程列表（前15个）：", styles['CustomBody']))
    elements.append(Spacer(1, 0.2*cm))
    
    system_procs = [p for p in processes if p.get('type') == 'system'][:15]
    if system_procs:
        proc_data = [['类型', '用户', 'PID', 'CPU%', '内存%', '进程名']]
        for proc in system_procs:
            proc_data.append([
                '系统',
                proc['user'][:10],
                str(proc['pid']),
                f"{proc['cpu']}%",
                f"{proc['mem']}%",
                proc['name'][:25]
            ])
        
        proc_table = Table(proc_data, colWidths=[1.5*cm, 1.8*cm, 1.2*cm, 1.2*cm, 1.2*cm, 6*cm])
        proc_table.setStyle(create_table_style())
        elements.append(proc_table)
    
    elements.append(PageBreak())
    
    # 用户进程详情
    elements.append(Paragraph("4.3 用户进程详情", styles['SectionTitle']))
    elements.append(Paragraph("以下为用户进程列表（前15个）：", styles['CustomBody']))
    elements.append(Spacer(1, 0.2*cm))
    
    user_procs = [p for p in processes if p.get('type') == 'user'][:15]
    if user_procs:
        proc_data = [['类型', '用户', 'PID', 'CPU%', '内存%', '进程名']]
        for proc in user_procs:
            proc_data.append([
                '用户',
                proc['user'][:10],
                str(proc['pid']),
                f"{proc['cpu']}%",
                f"{proc['mem']}%",
                proc['name'][:25]
            ])
        
        proc_table = Table(proc_data, colWidths=[1.5*cm, 1.8*cm, 1.2*cm, 1.2*cm, 1.2*cm, 6*cm])
        proc_table.setStyle(create_table_style())
        elements.append(proc_table)
    
    elements.append(Spacer(1, 0.5*cm))
    
    # CPU占用前十的进程
    elements.append(Paragraph("4.4 CPU占用前十的进程", styles['SectionTitle']))
    cpu_top_processes = data.get('cpu_top_processes', [])
    if cpu_top_processes:
        cpu_data = [['用户', 'PID', 'CPU%', '内存%', '进程名']]
        for proc in cpu_top_processes:
            cpu_data.append([
                proc['user'][:10],
                str(proc['pid']),
                f"{proc['cpu']}%",
                f"{proc['mem']}%",
                proc['name'][:25]
            ])
        
        cpu_table = Table(cpu_data, colWidths=[2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 7*cm])
        cpu_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), get_font()),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#dee2e6')),
        ]))
        elements.append(cpu_table)
    else:
        elements.append(Paragraph("暂无CPU占用数据", styles['CustomBody']))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # 内存占用前十的进程
    elements.append(Paragraph("4.5 内存占用前十的进程", styles['SectionTitle']))
    mem_top_processes = data.get('mem_top_processes', [])
    if mem_top_processes:
        mem_data = [['用户', 'PID', 'CPU%', '内存%', '进程名']]
        for proc in mem_top_processes:
            mem_data.append([
                proc['user'][:10],
                str(proc['pid']),
                f"{proc['cpu']}%",
                f"{proc['mem']}%",
                proc['name'][:25]
            ])
        
        mem_table = Table(mem_data, colWidths=[2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 7*cm])
        mem_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), get_font()),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#dee2e6')),
        ]))
        elements.append(mem_table)
    else:
        elements.append(Paragraph("暂无内存占用数据", styles['CustomBody']))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # 可疑进程分析
    elements.append(Paragraph("4.6 可疑进程分析", styles['SectionTitle']))
    
    suspicious_procs = [p for p in processes if p.get('type') == 'suspicious']
    if suspicious_procs:
        elements.append(create_alert_box(
            f"⚠ 发现 {len(suspicious_procs)} 个可疑进程",
            "以下进程被标记为可疑，可能包含恶意代码或异常行为，建议立即审查。",
            'danger',
            styles
        ))
        elements.append(Spacer(1, 0.3*cm))
        
        susp_data = [['PID', '用户', 'CPU%', '内存%', '命令']]
        for proc in suspicious_procs:
            susp_data.append([
                str(proc['pid']),
                proc['user'][:10],
                f"{proc['cpu']}%",
                f"{proc['mem']}%",
                proc.get('cmd', proc['name'])[:40]
            ])
        
        susp_table = Table(susp_data, colWidths=[1.5*cm, 2*cm, 1.2*cm, 1.2*cm, 8*cm])
        susp_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), get_font()),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8d7da')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(susp_table)
    else:
        elements.append(create_alert_box(
            "✓ 未发现可疑进程",
            "本次巡检未发现明显的可疑进程，系统进程状态正常。",
            'success',
            styles
        ))
    
    elements.append(PageBreak())
    return elements

def create_port_section(data, styles):
    """创建端口分析"""
    elements = []
    port_summary = data['port_summary']
    ports = data.get('ports', [])
    
    elements.append(Paragraph("五、端口分析", styles['ChapterTitle']))
    
    # 端口概览
    elements.append(Paragraph("5.1 端口概览", styles['SectionTitle']))
    elements.append(Paragraph(
        f"系统当前共有 <b>{port_summary['total_listening']}</b> 个端口处于监听状态。",
        styles['CustomBody']
    ))
    elements.append(Spacer(1, 0.3*cm))
    
    stats_data = [
        ['正常端口', '中风险端口', '高风险端口', '已建立连接'],
        [
            str(port_summary.get('normal_ports', 0)),
            str(port_summary.get('medium_risk_ports', 0)),
            str(port_summary.get('high_risk_ports', 0)),
            str(port_summary.get('established_connections', 0))
        ]
    ]
    
    stats_table = Table(stats_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), get_font()),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 18),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#666')),
        ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#ffc107')),
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor('#2c3e50')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 12),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # 监听端口详情
    elements.append(Paragraph("5.2 监听端口详情", styles['SectionTitle']))
    
    port_data = [['协议', '端口', '监听地址', '所属进程', '风险等级']]
    for port in ports[:30]:  # 限制显示数量
        risk_label = {
            'high': '高风险',
            'medium': '中风险',
            'low': '低风险',
            'normal': '正常',
            'dynamic': '动态'
        }.get(port['risk'], port['risk'])
        
        port_data.append([
            port['proto'],
            str(port['port']),
            port['address'][:20],
            port['process'][:15],
            risk_label
        ])
    
    port_table = Table(port_data, colWidths=[1.5*cm, 1.5*cm, 4*cm, 3*cm, 2*cm])
    port_table.setStyle(create_table_style())
    elements.append(port_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # 风险端口识别
    elements.append(Paragraph("5.3 风险端口识别", styles['SectionTitle']))
    
    high_risk_ports = [p for p in ports if p['risk'] == 'high']
    medium_risk_ports = [p for p in ports if p['risk'] == 'medium']
    
    if high_risk_ports:
        elements.append(create_alert_box(
            f"⚠ 高风险端口",
            f"发现 {len(high_risk_ports)} 个高风险端口处于开放状态",
            'danger',
            styles
        ))
        elements.append(Spacer(1, 0.3*cm))
        
        port_descriptions = {
            '135': 'MS RPC (Windows服务)',
            '139': 'NetBIOS (Windows文件共享)',
            '445': 'SMB (Windows文件共享)',
            '1433': 'MS SQL Server',
            '3389': 'RDP远程桌面',
            '5900': 'VNC远程桌面',
            '6666': 'IRC/恶意软件常用',
            '6667': 'IRC聊天服务器'
        }
        
        risk_data = [['端口', '协议', '所属进程', '常见用途']]
        for port in high_risk_ports:
            desc = port_descriptions.get(str(port['port']), '未知服务')
            risk_data.append([
                str(port['port']),
                port['proto'],
                port['process'][:15],
                desc
            ])
        
        risk_table = Table(risk_data, colWidths=[2*cm, 2*cm, 4*cm, 6*cm])
        risk_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), get_font()),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8d7da')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(risk_table)
    
    if medium_risk_ports:
        elements.append(Spacer(1, 0.3*cm))
        elements.append(create_alert_box(
            f"⚠ 中风险端口",
            f"发现 {len(medium_risk_ports)} 个中风险端口处于开放状态，建议评估其必要性。",
            'warning',
            styles
        ))
    
    if not high_risk_ports and not medium_risk_ports:
        elements.append(create_alert_box(
            "✓ 端口状态良好",
            "未发现高风险或中风险端口，系统端口配置相对安全。",
            'success',
            styles
        ))
    
    elements.append(PageBreak())
    return elements

def create_recommendations_section(data, styles):
    """创建安全建议"""
    elements = []
    proc_summary = data['process_summary']
    port_summary = data['port_summary']
    
    elements.append(Paragraph("六、安全建议", styles['ChapterTitle']))
    
    # 进程安全建议
    elements.append(Paragraph("进程安全建议", styles['SectionTitle']))
    
    proc_items = [
        '<b>定期审查进程</b>：建议每周运行一次进程巡检脚本，及时发现异常进程。',
        '<b>最小权限原则</b>：确保服务以最小权限运行，避免使用root账户运行不必要的应用。',
        '<b>进程监控</b>：部署进程监控工具（如auditd），记录进程创建和异常行为。',
        '<b>及时更新</b>：保持系统和应用程序更新，修复已知漏洞。',
    ]
    
    if proc_summary.get('suspicious_processes', 0) > 0:
        proc_items.append(
            f'<font color="#dc3545"><b>立即行动</b></font>：对标记的可疑进程进行详细调查，必要时终止进程并进行系统扫描。'
        )
    
    for item in proc_items:
        elements.append(Paragraph(f"• {item}", styles['CustomBody']))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # 端口安全建议
    elements.append(Paragraph("端口安全建议", styles['SectionTitle']))
    
    port_items = [
        '<b>关闭不必要的端口</b>：仅开放业务必需的端口，关闭所有未使用的服务。',
        '<b>使用防火墙</b>：配置iptables或firewalld，限制端口访问来源。',
        '<b>端口访问控制</b>：对敏感端口（如数据库端口）配置IP白名单。',
        '<b>使用非标准端口</b>：对于SSH等服务，考虑使用非标准端口减少扫描攻击。',
        '<b>定期端口扫描</b>：使用nmap等工具定期扫描本机端口，发现异常开放端口。',
    ]
    
    if port_summary.get('high_risk_ports', 0) > 0:
        port_items.append(
            f'<font color="#dc3545"><b>高风险端口处理</b></font>：立即评估高风险端口的必要性，如非必需应立即关闭。'
        )
    
    for item in port_items:
        elements.append(Paragraph(f"• {item}", styles['CustomBody']))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # 系统加固建议
    elements.append(Paragraph("系统加固建议", styles['SectionTitle']))
    
    harden_items = [
        '<b>启用SELinux/AppArmor</b>：使用强制访问控制增强系统安全性。',
        '<b>配置日志审计</b>：启用并定期检查系统日志（/var/log/）。',
        '<b>文件完整性监控</b>：部署AIDE或Tripwire监控关键系统文件。',
        '<b>网络安全</b>：配置入侵检测系统（IDS）如Snort或Suricata。',
        '<b>定期备份</b>：建立定期备份机制，确保数据可恢复。',
    ]
    
    for item in harden_items:
        elements.append(Paragraph(f"• {item}", styles['CustomBody']))
    
    elements.append(PageBreak())
    return elements

def create_appendix_section(data, styles):
    """创建附录"""
    elements = []
    info = data['audit_info']
    
    elements.append(Paragraph("七、附录", styles['ChapterTitle']))
    
    # 常见端口参考
    elements.append(Paragraph("A. 常见端口参考", styles['SectionTitle']))
    
    port_ref = [
        ['端口', '服务', '说明'],
        ['22', 'SSH', '安全远程登录'],
        ['80', 'HTTP', 'Web服务'],
        ['443', 'HTTPS', '加密Web服务'],
        ['21', 'FTP', '文件传输（不安全）'],
        ['23', 'Telnet', '远程登录（不安全）'],
        ['25', 'SMTP', '邮件发送'],
        ['3306', 'MySQL', 'MySQL数据库'],
        ['5432', 'PostgreSQL', 'PostgreSQL数据库'],
        ['6379', 'Redis', 'Redis缓存服务'],
        ['8080', 'HTTP-Alt', '备用HTTP端口'],
    ]
    
    port_table = Table(port_ref, colWidths=[2*cm, 3*cm, 9*cm])
    port_table.setStyle(create_table_style())
    elements.append(port_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # 脚本使用说明
    elements.append(Paragraph("B. 脚本使用说明", styles['SectionTitle']))
    elements.append(Paragraph(
        "本报告由Linux系统进程自动分析脚本生成，使用方法：",
        styles['CustomBody']
    ))
    elements.append(Spacer(1, 0.2*cm))
    
    code_text = '''# 1. 运行数据收集脚本
sudo bash linux_process_audit.sh

# 2. 生成PDF报告
python3 generate_pdf_report.py /tmp/linux_audit_*/audit_data.json

# 3. 查看报告
ls -la linux_process_audit_report_*.pdf'''
    
    code_data = [[code_text]]
    code_table = Table(code_data, colWidths=[14*cm])
    code_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(code_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # 报告信息
    elements.append(Paragraph("C. 报告信息", styles['SectionTitle']))
    
    report_data = [
        ['项目', '值'],
        ['报告生成时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['巡检主机', info['hostname']],
        ['操作系统', info['os_name']],
    ]
    
    report_table = Table(report_data, colWidths=[3*cm, 11*cm])
    report_table.setStyle(create_table_style())
    elements.append(report_table)
    
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph(
        "--- 报告结束 ---",
        ParagraphStyle(
            name='EndText',
            fontName=get_font(),
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666')
        )
    ))
    elements.append(Paragraph(
        "本报告由Linux系统进程自动分析脚本自动生成",
        ParagraphStyle(
            name='EndText2',
            fontName=get_font(),
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#999')
        )
    ))
    
    return elements

def create_table_style():
    """创建表格样式"""
    return TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), get_font()),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#dee2e6')),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#333')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#333')),
    ])

def generate_pdf_report(json_path, output_path=None):
    """生成PDF报告"""
    # 加载数据
    print("正在加载审计数据...")
    data = load_audit_data(json_path)
    
    # 确定输出路径
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.dirname(json_path) or '/tmp'
        output_path = os.path.join(output_dir, f'linux_process_audit_report_{timestamp}.pdf')
    
    # 创建PDF文档
    print("正在生成PDF报告...")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 创建样式
    styles = create_styles()
    
    # 构建文档内容
    elements = []
    elements.extend(create_cover_page(data, styles))
    elements.extend(create_summary_section(data, styles))
    elements.extend(create_system_info_section(data, styles))
    elements.extend(create_user_analysis_section(data, styles))
    elements.extend(create_process_section(data, styles))
    elements.extend(create_port_section(data, styles))
    elements.extend(create_recommendations_section(data, styles))
    elements.extend(create_appendix_section(data, styles))
    
    # 生成PDF
    doc.build(elements)
    print(f"PDF报告已生成: {output_path}")
    
    # 复制到脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.dirname(output_path)
    if script_dir != output_dir:
        try:
            import shutil
            report_name = os.path.basename(output_path)
            copy_path = os.path.join(script_dir, report_name)
            shutil.copy2(output_path, copy_path)
            print(f"报告已复制到: {copy_path}")
        except Exception as e:
            pass
    
    return output_path

def main():
    if len(sys.argv) < 2:
        print("用法: python3 generate_pdf_report.py <audit_data.json>")
        print("示例: python3 generate_pdf_report.py /tmp/linux_audit_20240101_120000/audit_data.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if not os.path.exists(json_path):
        print(f"错误: 找不到文件 '{json_path}'")
        sys.exit(1)
    
    try:
        output_path = generate_pdf_report(json_path)
        print("\n完成!")
    except Exception as e:
        print(f"生成PDF时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
