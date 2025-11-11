# -*- coding: utf-8 -*-
"""
教学工具集 - 主页
多功能PDF生成工具
"""

import streamlit as st

st.set_page_config(
    page_title="教学工具集",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 教学工具集")
st.caption("多功能PDF生成工具 - 提升教学效率")
st.markdown("---")

# Welcome section
st.header("欢迎使用教学工具集！")

st.markdown("""
这是一个集成了多种教学辅助工具的应用，帮助老师快速生成各类教学材料。

### 📑 可用功能

请使用左侧导航栏选择需要的功能：
""")

# Feature cards
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 重默生成器")
    st.markdown("""
    **功能**：生成表格形式的默写练习PDF
    
    **适用场景**：
    - 词汇默写练习
    - 短语听写测试
    - 单元复习材料
    
    **特点**：
    - 自动排版，整齐美观
    - 支持混合中英文
    - 一次生成多个练习区域
    - SimSun + Times-Roman 字体
    
    👉 点击左侧导航栏的 **"📝 默写纸生成器"** 开始使用
    """)

with col2:
    st.subheader("📄 成绩小分条")
    st.markdown("""
    **功能**：生成学生成绩小分条PDF
    
    **适用场景**：
    - 期中/期末成绩通知
    - 单元测验成绩单
    - 家长会材料
    
    **特点**：
    - Excel模板导入
    - 自定义列选择
    - 实时预览效果
    - 灵活的布局设置
    - 可配置字体字号
    
    👉 点击左侧导航栏的 **"📄 成绩小分条"** 开始使用
    """)

st.markdown("---")

# Quick start guide
with st.expander("🚀 快速开始", expanded=False):
    st.markdown("""
    ### 使用步骤
    
    1. **选择功能**
       - 在左侧导航栏点击需要的功能页面
    
    2. **准备材料**
       - 重默生成器：准备15个项目（10个单词 + 5个短语）
       - 成绩小分条：准备包含学生成绩的Excel文件
    
    3. **配置参数**
       - 根据页面提示输入或上传数据
       - 调整布局、字号等参数
    
    4. **生成PDF**
       - 点击生成按钮
       - 下载生成的PDF文件
    
    ### 💡 提示
    
    - 每个功能页面都有详细的使用说明
    - 成绩小分条功能提供实时预览
    - 可以下载Excel模板参考格式
    """)


# Footer
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>💡 如有问题或建议，请联系徐戈涵</p>
    <p style="font-size: 12px;">© 2025 教学工具集 · All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)


