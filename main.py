import requests
import datetime
import streamlit as st

# 腾讯问卷提交链接（替换为你的问卷链接）
TENCENT_DOCS_FORM_URL = "https://docs.qq.com/form/page/DQ3pwaVdsY21Pc3BQ"

# 记录访问
def log_visit():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 获取访问者 IP（使用第三方 API）
    try:
        ip = requests.get("https://api64.ipify.org?format=json").json().get("ip", "未知")
    except:
        ip = "未知"

    # 让用户选择设备类型
    device = st.selectbox("请选择你的设备", ["Windows", "Mac", "iPhone", "Android", "其他"])

    # 发送数据到腾讯问卷（需要 POST 请求）
    data = {
        "Q1": timestamp,  # 问卷中的第一个问题（时间戳）
        "Q2": ip,         # 问卷中的第二个问题（IP 地址）
        "Q3": device      # 问卷中的第三个问题（设备信息）
    }

    response = requests.post(TENCENT_DOCS_FORM_URL, data=data)

    if response.status_code == 200:
        st.success("✅ 访问已记录到腾讯文档！")
    else:
        st.warning("⚠️ 记录失败，请稍后重试")

# 显示 Streamlit 页面
st.title("📊 AI 经济实验平台")
st.write("本平台用于经济学实验数据分析")
st.markdown("---")

# 记录访问数据
log_visit()
