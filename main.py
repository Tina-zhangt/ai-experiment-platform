import requests
import datetime
import streamlit as st

# 腾讯问卷提交链接（替换为你的实际问卷链接）
TENCENT_DOCS_FORM_URL = "https://docs.qq.com/form/page/DQ3pwaVdsY21Pc3BQ"

# **获取用户信息**
def get_user_info():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # **获取 IP 地址**
    try:
        ip = requests.get("https://api64.ipify.org?format=json").json().get("ip", "未知")
    except:
        ip = "未知"

    # **获取设备信息**
    try:
        user_agent = st.experimental_user_agent()
        device = user_agent if user_agent else "未知设备"
    except:
        device = "未知设备"

    return timestamp, ip, device

# **自动提交访问数据**
def log_visit():
    timestamp, ip, device = get_user_info()

    # **构造腾讯问卷提交的 URL**
    visit_url = f"{TENCENT_DOCS_FORM_URL}?Q1={timestamp}&Q2={ip}&Q3={device}"

    # **后台请求腾讯问卷**
    response = requests.get(visit_url)

    if response.status_code == 200:
        st.sidebar.success("✅ 访问数据已自动记录！")
    else:
        st.sidebar.warning("⚠️ 访问记录失败，请稍后重试")

# **📌 侧边栏 - 访问记录**
st.sidebar.header("📋 访问记录")
log_visit()

# **📌 主界面 - OLS 回归分析**
st.title("📊 AI 经济实验平台 - OLS 回归分析（教学版）")
st.markdown("---")

# **数据输入方式**
st.sidebar.header("📂 数据输入方式")
input_method = st.sidebar.radio("选择数据来源:", ["生成模拟数据", "上传文件（Excel / Stata / CSV）"])

if input_method == "生成模拟数据":
    num_samples = st.sidebar.slider("样本数量", min_value=10, max_value=500, value=100)
    noise_level = st.sidebar.slider("数据噪声", min_value=0.0, max_value=2.0, value=0.5)
    num_features = st.sidebar.slider("自变量数量", min_value=1, max_value=5, value=1)

    np.random.seed(42)
    X = np.random.rand(num_samples, num_features) * 10
    beta = np.random.uniform(1.5, 3.5, num_features)
    intercept = 5
    error = np.random.randn(num_samples) * noise_level
    Y = intercept + np.dot(X, beta) + error

    data = pd.DataFrame(X, columns=[f"X{i + 1}" for i in range(num_features)])
    data["Y"] = Y

elif input_method == "上传文件（Excel / Stata / CSV）":
    uploaded_file = st.sidebar.file_uploader("📂 上传数据文件", type=["csv", "xlsx", "dta"])
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1]

        if file_extension == "csv":
            data = pd.read_csv(uploaded_file)
        elif file_extension == "xlsx":
            data = pd.read_excel(uploaded_file, engine='openpyxl')
        elif file_extension == "dta":
            data = pd.read_stata(uploaded_file)

        st.sidebar.write("📊 数据预览:")
        st.sidebar.dataframe(data.head())
    else:
        st.warning("请上传有效的 Excel、Stata 或 CSV 文件！")
        st.stop()

# **选择因变量和自变量**
st.sidebar.header("📌 选择回归变量")
y_col = st.sidebar.selectbox("📈 选择因变量（Y）:", data.columns)
x_cols = st.sidebar.multiselect("📉 选择自变量（X）:", [col for col in data.columns if col != y_col], default=[col for col in data.columns if col != y_col][:1])

if not x_cols:
    st.warning("请至少选择一个自变量！")
    st.stop()

X = data[x_cols].values
Y = data[y_col].values
X_with_const = sm.add_constant(X)

# **运行 OLS 回归**
st.subheader("📊 OLS 回归分析")
model = sm.OLS(Y, X_with_const).fit()
st.text(model.summary())

# **数据可视化**
st.subheader("📈 数据可视化")
if len(x_cols) == 1:
    st.line_chart({"真实值": data[y_col], "预测值": model.predict(X_with_const)})

# **模型评价**
st.subheader("📋 模型评价")
st.write(f"R²: {model.rsquared:.4f}")
if model.rsquared < 0.5:
    st.warning("📉 模型拟合度较低，可能遗漏重要变量或数据噪声较大。")
