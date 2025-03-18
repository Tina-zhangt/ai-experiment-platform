import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.sandbox.regression.gmm import IV2SLS
import datetime
import seaborn as sns
import matplotlib.pyplot as plt

# **📌 设置 Streamlit 页面**
st.set_page_config(page_title="AI 经济实验平台", layout="wide")

# **📌 侧边栏 - 选择数据输入方式**
st.sidebar.header("📂 数据输入方式")
input_method = st.sidebar.radio("选择数据来源:", ["生成模拟数据", "直接编辑数据", "上传文件（Excel / Stata / CSV）"])

# **📌 1. 数据输入**
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

elif input_method == "直接编辑数据":
    st.sidebar.write("📊 请直接编辑数据")
    data = st.experimental_data_editor(pd.DataFrame(columns=["Y"] + [f"X{i}" for i in range(1, 4)]))

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

# **📌 2. 选择回归变量**
st.sidebar.header("📌 选择回归变量")
y_col = st.sidebar.selectbox("📈 选择因变量（Y）:", data.columns)
x_cols = st.sidebar.multiselect("📉 选择自变量（X）:", [col for col in data.columns if col != y_col], default=[col for col in data.columns if col != y_col][:1])

if not x_cols:
    st.warning("请至少选择一个自变量！")
    st.stop()

# **📌 3. 选择估计方法**
st.sidebar.header("📊 选择估计方法")
model_type = st.sidebar.selectbox("选择回归方法:", ["OLS 估计", "OLS + 稳健标准误", "GLS 估计", "IV 估计"])

# **📌 4. 运行回归模型**
X = sm.add_constant(data[x_cols])
Y = data[y_col]

if model_type == "OLS 估计":
    model = sm.OLS(Y, X).fit()
elif model_type == "OLS + 稳健标准误":
    model = sm.OLS(Y, X).fit(cov_type="HC3")
elif model_type == "GLS 估计":
    model = sm.GLS(Y, X).fit()
elif model_type == "IV 估计":
    st.sidebar.subheader("⚙ 选择 IV 变量")
    endog_var = st.sidebar.selectbox("选择内生变量", x_cols)
    instrument_vars = st.sidebar.multiselect("选择工具变量", [col for col in x_cols if col != endog_var])

    if len(instrument_vars) == 0:
        st.warning("⚠ 请选择至少一个工具变量！")
        st.stop()

    model = IV2SLS(Y, X, data[instrument_vars]).fit()

# **📌 5. 显示回归结果**
st.subheader("📊 估计结果")
st.text(model.summary())

# **📌 6. 可视化回归结果**
st.subheader("📈 数据可视化")
plot_option = st.selectbox("选择可视化方式:", ["散点图", "散点图 + 回归线 + 公式", "真实值 vs 预测值"])

fig, ax = plt.subplots(figsize=(8, 5))
if plot_option == "散点图":
    sns.scatterplot(x=data[x_cols[0]], y=data[y_col], ax=ax)
elif plot_option == "散点图 + 回归线 + 公式":
    sns.regplot(x=data[x_cols[0]], y=data[y_col], ax=ax, line_kws={"color": "red"})
    equation = f"y = {model.params[0]:.2f} + {model.params[1]:.2f} * X"
    ax.text(0.05, 0.9, equation, transform=ax.transAxes, fontsize=12, verticalalignment='top')
elif plot_option == "真实值 vs 预测值":
    sns.lineplot(x=data.index, y=data[y_col], label="真实值", ax=ax)
    sns.lineplot(x=data.index, y=model.predict(X), label="预测值", ax=ax)
ax.set_xlabel(x_cols[0])
ax.set_ylabel(y_col)
st.pyplot(fig)

# **📌 7. 方法介绍**
st.sidebar.header("📘 方法介绍")
method_intro = {
    "OLS 估计": "普通最小二乘法（OLS），适用于无内生性问题的回归分析。",
    "OLS + 稳健标准误": "OLS 方法，但使用稳健标准误以减少异方差问题的影响。",
    "GLS 估计": "广义最小二乘法（GLS），适用于误差项存在自相关或异方差的问题。",
    "IV 估计": "工具变量回归（IV），用于解决内生性问题，并自动进行工具变量有效性检验。"
}
st.sidebar.info(method_intro[model_type])
