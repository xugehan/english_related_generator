# -*- coding: utf-8 -*-
"""
默写纸生成器页面
"""

import streamlit as st
import os
import tempfile
from generator import make_chongmo_pdf, generate_preview_image
st.set_page_config(
    page_title="默写纸生成器",
    page_icon="📝",
    layout="wide"
)
st.title("📝 默写纸生成器")
st.caption("生成灵活布局的默写PDF - 支持自定义行列数、字号和任意数量内容")
st.markdown("---")

# Main layout: Left side for inputs, Right side for preview
col_left, col_right = st.columns([1, 1])

with col_left:
    # 基本设置
    st.header("⚙️ 基本设置")

    date_str = st.text_input(
        "日期",
        value="1111",
        help="例如：1111 表示11月11日，格式自由"
    )

    scope = st.text_input(
        "标题",
        value="eager-effort",
        help="例如：eager-effort"
    )

    st.markdown("---")

    # 布局设置
    st.subheader("📐 布局设置")

    layout_col1, layout_col2, layout_col3, layout_col4 = st.columns(4)

    with layout_col1:
        col_num = st.number_input(
            "列数",
            min_value=1,
            max_value=4,
            value=2,
            help="每页的列数（1-4列）"
        )

    with layout_col2:
        row_num = st.number_input(
            "行数",
            min_value=1,
            max_value=5,
            value=3,
            help="每页的行数（1-5行）"
        )

    with layout_col3:
        font_size = st.number_input(
            "字号 (pt)",
            min_value=8,
            max_value=16,
            value=11,
            help="文字大小（8-16pt）"
        )

    with layout_col4:
        padding = st.number_input(
            "边距 (mm)",
            min_value=1,
            max_value=10,
            value=3,
            help="单元格内边距（1-10mm）"
        )

    st.info(f"📄 每页将包含 {col_num} × {row_num} = {col_num * row_num} 个练习区域")

    st.markdown("---")

    # 内容项目
    st.subheader("📝 内容项目")
    st.caption("**每行一个项目**（可以是单词或短语，支持任意数量），更改后请点击下框外以更新预览。")

    default_text = """n. 鹰
n. 耳朵
v. 赢得；挣得；搏得
n. 地震
adj. 东方的；东部的
n. 生态学
n. 经济
n. 边缘；刀刃；优势
n. 编辑；审校者；剪辑师
adj. 高效的
放心好了，别着急
赢得好名声
在地球上
紧张，不安
起作用，生效"""

    text_input = st.text_area(
        "批量输入",
        value=default_text,
        height=350,
        help="每行一个项目，支持任意数量",
        label_visibility="collapsed"
    )

    items = [line.strip() for line in text_input.strip().split('\n') if line.strip()]

with col_right:
    # 内容预览
    st.header("📋 内容预览")

    if len(items) == 0:
        st.error("❌ 至少需要输入1个项目")
        st.info("请在左侧文本框中输入内容，每行一个项目")
    else:
        st.success(f"✅ 已输入 {len(items)} 个项目")

        # 显示PDF预览图
        try:
            with st.spinner("生成预览中..."):
                preview_image = generate_preview_image(
                    date_str, scope, items,
                    cols=col_num, rows=row_num, font_size=font_size,
                    padding=padding, dpi=120
                )
                st.image(preview_image, caption="PDF预览（第一页）", use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ 无法生成预览: {str(e)}")
            # 降级到文本预览
            with st.expander("查看所有项目", expanded=False):
                for i, item in enumerate(items, 1):
                    st.text(f"{i}. {item}")

st.markdown("---")

# PDF生成按钮 - 全宽在底部
st.subheader("🎨 生成PDF")

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn2:
    if st.button("📄 生成PDF", type="primary", use_container_width=True, disabled=(len(items) == 0)):
        if len(items) == 0:
            st.error("❌ 至少需要1个项目才能生成PDF")
        else:
            with st.spinner("正在生成PDF..."):
                try:
                    # 创建临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                        output_path = tmp_pdf.name

                    # 生成PDF with custom parameters
                    make_chongmo_pdf(
                        date_str, scope, items, output_path,
                        cols=col_num, rows=row_num, font_size=font_size, padding=padding
                    )

                    # 读取PDF
                    with open(output_path, "rb") as pdf_file:
                        pdf_data = pdf_file.read()

                    st.success("✅ PDF生成成功！")

                    # 生成文件名
                    filename = f"{date_str}-{scope}.pdf"

                    st.download_button(
                        label="⬇️ 下载PDF",
                        data=pdf_data,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )

                    # 清理临时文件
                    if os.path.exists(output_path):
                        os.unlink(output_path)

                except Exception as e:
                    st.error(f"生成PDF时出错: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

st.markdown("---")

# Additional info
st.info("""
💡 **提示**：
- 生成的PDF包含多个相同的练习区域（根据行列设置），方便打印后裁剪分发
- 支持任意数量的内容项目。
- 标题行会自动调整下划线长度以适应页面宽度
- 可以自定义字号、行数和列数以适应不同的教学需求
- 使用SimSun字体（中文）和Times-Roman字体（英文）以获得最佳显示效果
""")

