# -*- coding: utf-8 -*-
"""
访问控制工具
用于检测和限制页面访问权限
"""

import streamlit as st
import socket


def get_client_ip():
    """
    尝试获取客户端IP地址

    Returns:
        str: 客户端IP地址，无法获取时返回"unknown"
    """
    try:
        # 方法1: 从Streamlit的session state获取
        if hasattr(st, 'session_state') and '_client_ip' in st.session_state:
            return st.session_state._client_ip

        # 方法2: 使用新的 st.context.headers API
        try:
            headers = st.context.headers
            if headers:
                # 按优先级检查IP头
                ip = (
                    headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                    headers.get("X-Real-IP", "") or
                    headers.get("X-Real-Ip", "") or
                    headers.get("Remote-Addr", "") or
                    headers.get("Host", "").split(":")[0]
                )
                if ip and ip != "unknown":
                    return ip
        except Exception:
            pass

        # 方法3: 检查是否在本地运行（通过hostname）
        hostname = socket.gethostname()
        if hostname in ["localhost", "127.0.0.1"]:
            return "127.0.0.1"

        return "unknown"

    except Exception:
        return "unknown"


def is_local_access():
    """
    检测是否为本地访问

    本地访问定义：
    - 127.0.0.1 / localhost / ::1
    - 192.168.x.x（内网）
    - 10.x.x.x（内网）
    - 172.16.x.x - 172.31.x.x（内网）
    - 无法获取IP时（开发环境）

    Returns:
        bool: True表示本地/内网访问，False表示外网访问
    """
    client_ip = get_client_ip()

    # 无法获取IP，默认允许（开发环境）
    if client_ip == "unknown" or not client_ip:
        return True

    # 本地IP
    local_ips = ["127.0.0.1", "localhost", "::1", "0.0.0.0"]
    if client_ip in local_ips:
        return True

    # # 内网IP段
    # if (client_ip.startswith("192.168.") or
    #     client_ip.startswith("10.") or
    #     client_ip.startswith("172.16.") or
    #     client_ip.startswith("172.17.") or
    #     client_ip.startswith("172.18.") or
    #     client_ip.startswith("172.19.") or
    #     client_ip.startswith("172.2") or
    #     client_ip.startswith("172.30.") or
    #     client_ip.startswith("172.31.")):
    #     return True

    # 检查是否为IPv6本地地址
    if client_ip.startswith("fe80:") or client_ip.startswith("::1"):
        return True

    # 其他情况视为远程访问
    return False


def check_admin_access(page_name="此页面"):
    """
    检查管理员访问权限（仅本地访问）
    如果不是本地访问，显示错误信息并停止执行

    Args:
        page_name: 页面名称，用于错误提示
    """
    client_ip = get_client_ip()

    if not is_local_access():
        st.error("🚫 访问被拒绝")
        st.warning(f"""
        ### 权限说明
        
        **{page_name}** 仅限本地访问，远程访问已被禁止。
        
        **您的IP地址**: `{client_ip}`
        
        **原因**：
        - 此功能可能包含敏感的系统信息
        - 这是管理员专用功能
        - 保护用户隐私和系统安全
        
        **如需访问**：
        - 请在服务器本地打开浏览器访问（http://localhost:8501）
        - 或通过SSH隧道连接后访问
        
        """)
        st.stop()

    # 本地访问，显示提示
    st.success(f"✅ 本地访问已验证 (IP: {client_ip})")

