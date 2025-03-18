import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.sandbox.regression.gmm import IV2SLS
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

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

# **📌 6. 结果分析**
st.subheader("📋 结果分析")

# **方差膨胀因子（VIF）**
if len(x_cols) > 1:
    vif_data = pd.DataFrame()
    vif_data["变量"] = x_cols
    vif_data["VIF 值"] = [variance_inflation_factor(X.values, i) for i in range(1, X.shape[1])]
    st.write("**📌 方差膨胀因子（VIF）**")
    st.dataframe(vif_data)
    if vif_data["VIF 值"].max() > 10:
        st.warning("⚠️ VIF 过高，可能存在多重共线性问题！建议删除高度相关变量。")

# **异方差检验**
bp_test = het_breuschpagan(model.resid, X)
st.write("**📌 Breusch-Pagan 异方差检验**")
st.write(f"📊 检验统计量: {bp_test[0]}, p值: {bp_test[1]}")
if bp_test[1] < 0.05:
    st.warning("⚠️ 检验结果显著，模型可能存在异方差问题。建议使用稳健标准误。")

# **📌 7. 可视化回归结果**
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
