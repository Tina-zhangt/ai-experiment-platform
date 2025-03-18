import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan
import pyreadstat
import tempfile
# 解决中文乱码
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 设置页面布局
st.set_page_config(page_title="AI 经济实验平台 - OLS 回归分析", layout="wide")

st.title("📊 AI 经济实验平台 - OLS 回归分析（教学版）")
st.markdown("---")

# 侧边栏
st.sidebar.header("📂 数据输入方式")

# 选择数据输入方式
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
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dta") as tmpfile:
                tmpfile.write(uploaded_file.getbuffer())
                tmpfile_path = tmpfile.name
            data, meta = pyreadstat.read_dta(tmpfile_path)

        st.sidebar.write("📊 数据预览:")
        st.sidebar.dataframe(data.head())
    else:
        st.warning("请上传有效的 Excel、Stata 或 CSV 文件！")
        st.stop()

# 选择因变量和自变量
st.sidebar.header("📌 选择回归变量")
y_col = st.sidebar.selectbox("📈 选择因变量（Y）:", data.columns)
x_cols = st.sidebar.multiselect("📉 选择自变量（X）:", [col for col in data.columns if col != y_col],
                                default=[col for col in data.columns if col != y_col][:1])

if not x_cols:
    st.warning("请至少选择一个自变量！")
    st.stop()

X = data[x_cols].values
Y = data[y_col].values
X_with_const = sm.add_constant(X)

# 运行OLS回归
st.subheader("📊 OLS 回归分析")
model = sm.OLS(Y, X_with_const).fit()
st.text(model.summary())

# 可视化回归结果
st.subheader("📈 数据可视化")
if len(x_cols) == 1:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(x=data[x_cols[0]], y=data[y_col], label="数据点")
    ax.plot(data[x_cols[0]], model.predict(X_with_const), color='red', label="回归线")
    ax.set_xlabel(x_cols[0])
    ax.set_ylabel(y_col)
    ax.legend()
    st.pyplot(fig)
else:
    st.warning("多元回归无法使用 2D 图像可视化")

# 模型诊断工具
st.subheader("📋 模型诊断")
if len(x_cols) > 1:  # 只有当自变量数量 > 1 时，才进行VIF分析
    vif_data = pd.DataFrame()
    vif_data["变量"] = x_cols
    vif_data["VIF 值"] = [variance_inflation_factor(X, i) for i in range(X.shape[1])]
    st.write("**📌 方差膨胀因子（VIF）**")
    st.dataframe(vif_data)
    if vif_data["VIF 值"].max() > 10:
        st.warning("⚠️ VIF 过高，可能存在多重共线性问题！建议删除高度相关变量。")

# 异方差检验
bp_test = het_breuschpagan(model.resid, X_with_const)
st.write("**📌 Breusch-Pagan 异方差检验**")
st.write(f"📊 检验统计量: {bp_test[0]}, p值: {bp_test[1]}")
if bp_test[1] < 0.05:
    st.warning("⚠️ 检验结果显著，模型可能存在异方差问题。建议使用稳健标准误。")

# AI 反馈
st.subheader("🤖 AI 智能反馈")
if model.rsquared < 0.5:
    st.warning("📉 模型拟合度较低，可能遗漏重要变量或数据噪声较大。")
if any(model.pvalues[1:] > 0.05):
    st.warning("⚠️ 部分回归系数不显著，可能需要增加样本量或调整自变量。")
else:
    st.success("✅ 回归系数显著，模型可用于经济预测！")