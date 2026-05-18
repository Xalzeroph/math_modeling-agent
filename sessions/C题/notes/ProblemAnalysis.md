# 数学建模分析文档 — C题 我国碳排放数据分析与研究

## 阅读清单（Stage 1 门禁）

| # | 类型 | 标题/文献 | 来源 | 阅读完成 |
|---|------|----------|------|---------|
| 1 | 算法文档 | 评价类算法说明（熵权法、TOPSIS、灰色关联分析） | algorithms/03-评价类算法说明.md | ✅ |
| 2 | 算法文档 | 预测类算法说明（灰色预测、ARIMA、回归分析） | algorithms/02-预测类算法说明.md | ✅ |
| 3 | 外部文献 | Will China achieve its 2060 carbon neutral commitment from the provincial perspective? (Sun et al., 2022) | OpenAlex/ACCRE | ✅ |
| 4 | 外部文献 | Can China achieve its carbon emission peaking? A scenario analysis based on STIRPAT and system dynamics model (Liu & Xiao, 2018) | OpenAlex/Ecological Indicators | ✅ |
| 5 | 外部文献 | Will China peak its energy-related carbon emissions by 2030? Lessons from 30 Chinese provinces (Fang et al., 2019) | OpenAlex/Applied Energy | ✅ |
| 6 | 外部文献 | A review of the global climate change impacts, adaptation, and sustainable mitigation measures (Abbass et al., 2022) | OpenAlex | ✅ |
| 7 | 外部文献 | China's transportation sector carbon dioxide emissions efficiency and its influencing factors based on the EBM DEA model (Zhao et al., 2021) | OpenAlex/Energy | ✅ |
| 8 | 外部文献 | Environmental consequences of population, affluence and technological progress for European countries (Pham et al., 2020) | OpenAlex/JEMA | ✅ |

## 一、问题分析

### 1.1 问题背景

碳排放中的"碳"主要指以二氧化碳（CO₂）为主的温室气体。过量排放导致温室效应加剧、气候异常、生态系统退化等全球性问题，严重威胁可持续发展。

我国高度重视碳排工作：
- **2020年**：明确2030年前碳达峰、2060年前碳中和目标
- **2021年**：全国碳排放权交易市场启动上线交易
- **2025年**：政府工作报告再次强调"积极稳妥推进碳达峰碳中和"

准确掌握碳排放时空特征、识别关键影响因素、科学预测碳排趋势并制定对应策略，是支撑"双碳"目标实现的重要基础。

### 1.2 问题重述

**问题1（省域碳排放综合评价）**：
基于附件1（2019-2025全国碳排放数据）和附件2（2022年30省排放清单），分析各省碳排放指标是否存在显著空间差异；构建涵盖碳排放规模、效率、经济贡献等维度的评价指标体系，对省份进行分类排序。

**问题2（影响因素识别与预测模型）**：
利用中国统计年鉴中的能源结构数据，识别影响碳排放的基础因素，建立碳排放预测模型。

**问题3（情景预测）**：
利用问题2的预测模型，设定基准情景、碳减排情景、加强碳减排情景三种发展模式，预测2026-2045年我国碳排放量和碳排放强度的变化趋势，判断碳达峰时间及峰值水平。

**问题4（政策建议）**：
结合分析结果，针对我国碳达峰碳中和目标，提出政策建议。

### 1.3 问题类型

**混合型**：
- **评价类**（问题1）：构建指标体系 → 赋权 → 排序/分类
- **预测类**（问题2-3）：因素识别 → 模型建立 → 情景预测
- **政策分析**（问题4）：基于实证结果提出建议

## 二、模型选择

### 2.1 问题1：省域碳排放综合评价

#### 候选方案

| 方案 | 赋权方法 | 排序方法 | 分类方法 | 优势 | 劣势 |
|------|---------|---------|---------|------|------|
| **A: 熵权法+TOPSIS+K-Means** | 熵权法（客观） | TOPSIS | K-Means聚类 | 客观无偏、信息量驱动、可解释性强 | 忽略指标冲突性 |
| B: CRITIC+灰色关联+层次聚类 | CRITIC（客观） | 灰色关联分析 | 层次聚类 | 考虑指标冲突性 | 计算复杂度较高 |
| C: AHP+TOPSIS+系统聚类 | AHP（主观） | TOPSIS | 系统聚类 | 可融入专家经验 | 主观性过强 |

**选择方案A**：熵权法+TOPSIS+K-Means

理由：
1. 碳排放数据是客观面板数据，适合客观赋权方法
2. 熵权法基于数据离散程度赋权，信息量越大权重越大，符合评价目标
3. TOPSIS是经典的多指标排序方法，贴近度在[0,1]区间，结果直观
4. K-Means聚类可根据综合得分将30省分为若干梯队
5. 方案A完全使用数据驱动，避免主观偏差

#### 指标体系设计

**碳排放规模维度**：
- C1: 碳排放总量 (Mt CO₂) — 区域碳排放绝对规模
- C2: 人均碳排放量 (t CO₂/人) — 碳排放人均水平

**碳排放效率维度**：
- C3: 碳排放强度 (t CO₂/万元GDP) — 单位GDP碳排放
- C4: 碳生产率 (万元GDP/t CO₂) — 碳排放的经济产出效率

**经济贡献维度**：
- C5: 经济贡献协调度 $R_i = \frac{g_i / \sum g_k}{c_i / \sum c_k}$ — 其中 $g_i$ 为省份 i 的 GDP，$c_i$ 为省份 i 的碳排放量；$R_i > 1$ 表示经济贡献大于碳排放贡献（协调度好），$R_i < 1$ 表示碳排放贡献相对过高

#### 算法流程

1. 数据收集与预处理
   - 从附件2提取30省2022年碳排放数据
   - 匹配各省GDP、人口数据
   - 计算各指标值
2. 熵权法计算权重
   - 极差标准化（区分正负向指标）
   - 计算信息熵 → 信息效用值 → 权重
3. TOPSIS排序
   - 向量标准化 → 加权 → 正负理想解 → 贴近度
4. K-Means聚类分类
   - 基于综合得分和原始指标特征聚类
5. 可视化输出

### 2.2 问题2：碳排放影响因素识别与预测模型

#### 候选方案

| 方案 | 因素识别方法 | 预测模型 | 优势 | 劣势 |
|------|-------------|---------|------|------|
| **A: STIRPAT扩展模型** | 岭回归/OLS + 扩展STIRPAT | 多元回归情景预测 | 理论基础强、广泛应用、因素解释清晰 | 因素间可能有共线性 |
| B: LMDI分解+ARIMA | LMDI因素分解 | ARIMA时序预测 | 分解无残差、因素贡献明确 | 时序预测缺乏因素解释力 |
| C: Lasso回归特征选择+XGBoost | Lasso特征选择 | XGBoost集成学习 | 预测精度可能更高 | 可解释性差、不符合"简洁优先"原则 |

**选择方案A**：STIRPAT扩展模型

理由：
1. STIRPAT（Stochastic Impacts by Regression on Population, Affluence, and Technology）是环境压力评估的经典模型
2. 多篇顶级期刊论文验证其在中国碳达峰预测中的有效性（Sun et al., 2022; Liu & Xiao, 2018）
3. 模型结构清晰、可解释性强，适合数学建模竞赛
4. 可通过设置不同情景参数进行预测

#### STIRPAT模型

**基本形式**：
$$I = a P^b A^c T^d e$$

其中：
- $I$：环境压力（碳排放量）
- $P$：人口规模
- $A$：人均财富（GDP/人）
- $T$：技术水平（碳排放强度或能源强度）
- $a$：模型系数
- $b, c, d$：弹性系数
- $e$：误差项

**对数形式**：
$$\ln I = \ln a + b \ln P + c \ln A + d \ln T + \ln e$$

**扩展形式**（加入更多因素）：
$$\ln I = \ln a + b_1 \ln P + b_2 \ln A + b_3 \ln T + b_4 \ln U + b_5 \ln S + b_6 \ln E + \ln e$$

其中扩展因素：
- $U$：城镇化率（城市人口/总人口）
- $S$：产业结构（第二产业占比）
- $E$：能源结构（煤炭消费占比）

#### 影响因素假设

| 因素 | 符号 | 预期影响 | 理论依据 |
|------|------|---------|---------|
| 人口规模 | $P$ | + | 人口越多，能源消耗和碳排放越多 |
| 人均GDP | $A$ | + | 经济发展增加碳排放（EKC上升段） |
| 碳排放强度 | $T$ | + | 强度越高表示单位GDP碳排放越高 |
| 城镇化率 | $U$ | + | 城镇化进程增加能源需求 |
| 第二产业占比 | $S$ | + | 工业是主要碳排放源 |
| 煤炭占比 | $E$ | + | 煤炭是高碳能源 |

### 2.3 问题3：情景预测

基于问题2的STIRPAT扩展模型，设定三种情景：

**基准情景**：延续历史趋势，各因素按历史平均增长率发展
**碳减排情景**：适度的政策干预，2030年碳达峰目标约束
**加强碳减排情景**：强力的政策干预，提前碳达峰并加速下降

#### 情景参数设定

| 因素 | 基准情景 | 碳减排情景 | 加强碳减排情景 |
|------|---------|-----------|--------------|
| 人口增长率 | 历史平均 | 历史平均(因政策影响小) | 历史平均 |
| 人均GDP增速 | 历史平均 | 逐步放缓 | 明显放缓(结构转型) |
| 碳排放强度降速 | 历史平均 | 加速下降 | 快速下降 |
| 城镇化率增速 | 历史平均 | 适度增速 | 稳步推进 |
| 第二产业占比降速 | 历史平均 | 加速下降 | 快速下降 |
| 煤炭占比降速 | 历史平均 | 加速下降 | 快速下降(能源革命) |

### 2.4 参考文献信息

| 论文名称 | 作者 | 年份 | 来源 |
|---------|------|------|------|
| Will China achieve its 2060 carbon neutral commitment from the provincial perspective? | Sun, Cui & Ge | 2022 | Advances in Climate Change Research |
| Can China achieve its carbon emission peaking? A scenario analysis based on STIRPAT and system dynamics model | Liu & Xiao | 2018 | Ecological Indicators |
| Will China peak its energy-related carbon emissions by 2030? Lessons from 30 Chinese provinces | Fang et al. | 2019 | Applied Energy |
| China's transportation sector carbon dioxide emissions efficiency and its influencing factors based on the EBM DEA model | Zhao et al. | 2021 | Energy |
| Environmental consequences of population, affluence and technological progress | Pham et al. | 2020 | Journal of Environmental Management |
| 灰色系统理论教程 | 邓聚龙 | 1990 | 华中理工大学出版社 |
| Multiple Attribute Decision Making | Hwang & Yoon | 1981 | Springer |
| Information Theory and Entropy | Shannon | 1948 | Bell System Technical Journal |

### 2.5 模型适用性分析

**熵权法+TOPSIS**：
- 适用于省份综合评价问题（样本数=30，指标数=5），数据充分
- 熵权法客观无偏，避免人为干预
- TOPSIS排序结果直观，贴近度可直接比较

**STIRPAT扩展模型**：
- 碳排放预测的标准学术方法，理论基础扎实
- 可解释性强，影响因素明确
- 适合情景分析（通过调节各因素参数）

**局限性**：
- 影响因素的选择和数据可获得性可能受限
- 长期预测（至2045年）不确定性较大
- 模型假设各因素间独立，实际情况可能存在交互效应

## 三、算法设计

### 3.1 求解思路

**整体框架**：

```
问题1 → 指标体系构建 → 熵权法赋权 → TOPSIS排序 → K-Means聚类
问题2 → 数据收集(统计年鉴) → 因素分析 → STIRPAT建模 → 参数估计
问题3 → 情景设计 → STIRPAT预测 → 碳达峰判断
问题4 → 结果汇总 → 政策建议
```

### 3.2 问题1算法流程

```
Step 1: 数据准备
  - 从附件2提取30省碳排放总量、分行业排放数据
  - 匹配各省GDP、人口数据
  - 计算5个评价指标

Step 2: 熵权法赋权
  - 极差标准化（正向/负向指标区分）
  - 计算信息熵 e_j = -1/ln(m) * Σ(p_ij * ln(p_ij))
  - 计算权重 w_j = (1-e_j) / Σ(1-e_k)

Step 3: TOPSIS排序
  - 向量标准化 r_ij = x_ij / sqrt(Σx_ij²)
  - 加权 v_ij = w_j * r_ij
  - 正理想解 V⁺, 负理想解 V⁻
  - 贴近度 C_i = D⁻_i / (D⁺_i + D⁻_i)

Step 4: K-Means聚类（肘部法则+轮廓系数选k）
  - 基于贴近度和指标特征聚类
  - 枚举 k=2~8，计算各k的轮廓系数 $s(k)$ 和 SSE(肘部)
  - 选轮廓系数最大且肘部拐点对应的 k 值
  - 预期分 3-5 类（高排放/中排放/低排放等）

Step 5: 空间差异分析
  - 东中西部对比
  - 可视化输出（地图、柱状图、雷达图）
```

### 3.3 问题2算法流程

```
Step 1: 数据收集
  - 中国统计年鉴能源结构数据（煤炭占比、清洁能源占比）
  - 人口、GDP、城镇化率、产业结构数据

Step 2: STIRPAT模型构建
  - 对数线性化处理
  - 多重共线性检验（VIF > 10 判定共线性）
  - 岭回归参数估计（10折交叉验证选最优 alpha，alpha 搜索范围 [0.01, 100] 对数网格）

Step 3: 模型检验
  - R²、调整R²
  - F检验
  - 各变量t检验
  - 残差分析

Step 4: 影响因素分析
  - 弹性系数排序
  - 贡献度分解
```

### 3.4 问题3算法流程

```
Step 1: 情景参数设定
  - 基准情景：各因素按历史趋势外推
  - 碳减排情景：政策导向的适度减速
  - 加强碳减排情景：强力政策干预

Step 2: 各因素2026-2045年取值预测
  - 人口：logistic增长模型
  - 人均GDP：增长放缓模型
  - 碳排放强度：指数下降模型
  - 其他因素：线性/指数外推

Step 3: STIRPAT模型预测
  - 代入各情景参数
  - 计算2026-2045年碳排放量
  - 计算碳排放强度

Step 4: 碳达峰判断
  - 达峰时间
  - 峰值水平
  - 下降趋势
```

### 3.5 关键代码模块

| 模块 | 功能 | 使用算法 |
|------|------|---------|
| `solvers/problem1_evaluation.py` | 省域碳排放评价 | 熵权法+TOPSIS+K-Means |
| `solvers/problem2_stirpat.py` | 影响因素识别与STIRPAT建模 | 岭回归/STIRPAT |
| `solvers/problem3_scenario.py` | 情景预测 | STIRPAT扩展预测 |
| `verifications/verify_problem1.py` | 问题1验证 | 敏感性分析+聚类轮廓系数 |
| `verifications/verify_problem2.py` | 问题2验证 | 拟合优度+残差检验 |
| `verifications/verify_problem3.py` | 问题3验证 | 情景合理性+达峰判断 |

### 3.6 评价指标

| 指标 | 公式 | 用于 |
|------|------|------|
| 信息熵 | $e_j = -\frac{1}{\ln m}\sum p_{ij}\ln p_{ij}$ | 熵权法 |
| TOPSIS贴近度 | $C_i = D^-_i/(D^+_i+D^-_i)$ | 综合评价排序 |
| 轮廓系数 | $s(i) = (b(i)-a(i))/\max(a(i),b(i))$ | K-Means聚类评价 |
| R²决定系数 | $R^2 = 1 - RSS/TSS$ | 回归拟合优度 |
| RMSE | $\sqrt{\frac{1}{n}\sum(y_i-\hat{y}_i)^2}$ | 预测误差 |
| MAPE | $\frac{100\%}{n}\sum|(y_i-\hat{y}_i)/y_i|$ | 预测百分比误差 |
| VIF方差膨胀因子 | $VIF_j = 1/(1-R^2_j)$ | 多重共线性检验 |

## 四、数据要求

### 4.1 表格文件分析

| 文件 | 类型 | 结构 | 用途 |
|------|------|------|------|
| 附件1-中国2019年-2025年碳排放数据.csv | 输入 | 17255行×4列(Area,CO2,Sector,Date) | 全国时序碳排放 |
| 附件2-2022年30个省份排放清单.xlsx | 输入 | 30省Sheet，每省50行×23列(分能源类型、分行业) | 省级碳排放详细数据 |

### 4.2 外部数据需求

| 数据项 | 来源 | 用途 |
|--------|------|------|
| 各省GDP数据 | 中国统计年鉴 | 计算碳排放强度、经济贡献指标 |
| 各省人口数据 | 中国统计年鉴 | 计算人均碳排放 |
| 全国能源结构（煤炭占比等） | 中国统计年鉴 | STIRPAT模型扩展因素 |
| 城镇化率 | 中国统计年鉴 | STIRPAT模型扩展因素 |
| 产业结构（一/二/三产占比） | 中国统计年鉴 | STIRPAT模型扩展因素 |

### 4.3 数据预处理

1. **附件1处理**：
   - 提取全国总量（Sector='Total'）
   - 按时序聚合
   - 计算年/季度/月度碳排放

2. **附件2处理**：
   - 提取各省总排放（TotalEmissions行）
   - 提取分行业排放结构
   - 计算各能源类型占比

3. **外部数据匹配**：
   - 统一年份和省份名称
   - 缺失值处理（线性插值或邻近值填充）
   - 异常值检测和处理

## 五、实现要求

### 5.1 编程语言

Python 3.x

### 5.2 主要功能模块

| 文件 | 功能 |
|------|------|
| `solvers/problem1_evaluation.py` | 熵权法+TOPSIS+K-Means综合评价 |
| `solvers/problem2_stirpat.py` | STIRPAT因素建模 |
| `solvers/problem3_scenario.py` | 三情景预测 |
| `verifications/verify_problem1.py` | 问题1验证脚本 |
| `verifications/verify_problem2.py` | 问题2验证脚本 |
| `verifications/verify_problem3.py` | 问题3验证脚本 |

### 5.3 输出要求

- 所有图表保存为SVG格式（矢量图）
- 结果表格保存为CSV
- 数值精度保留4位小数

### 5.4 可视化需求

| 图表 | 对应问题 | 说明 |
|------|---------|------|
| 省域碳排放综合得分排名图 | 问题1 | TOPSIS贴近度排序 |
| 省域碳排放分类地图 | 问题1 | K-Means聚类结果展示 |
| 指标权重分布图 | 问题1 | 熵权法权重 |
| 各因素弹性系数图 | 问题2 | STIRPAT模型结果 |
| 碳排放历史趋势图 | 问题2 | 2019-2025碳排放时序 |
| 三情景碳排放预测图 | 问题3 | 2026-2045预测 |
| 碳排放强度预测图 | 问题3 | 三情景强度对比 |
| 碳达峰判断图 | 问题3 | 峰值标注 |

## 六、术语与符号

### 6.1 核心术语

| 中文 | 英文 | 缩写 | 定义 |
|------|------|------|------|
| 碳排放 | Carbon Emission | CE | CO₂排放量 |
| 碳达峰 | Carbon Peak | - | 碳排放量达到历史最高值 |
| 碳中和 | Carbon Neutral | - | 净零碳排放 |
| 碳排放强度 | Carbon Emission Intensity | CEI | 单位GDP碳排放 |
| 熵权法 | Entropy Weight Method | EWM | 基于信息熵的客观赋权法 |
| 贴近度 | Closeness Coefficient | C | TOPSIS综合评价得分 |
| 信息熵 | Information Entropy | e | 指标离散程度度量 |

### 6.2 数学符号

| 符号 | 含义 | 单位 |
|------|------|------|
| $I$ | 碳排放量（环境压力） | Mt CO₂ |
| $P$ | 人口规模 | 万人 |
| $A$ | 人均GDP | 元/人 |
| $T$ | 技术水平（碳排放强度） | t CO₂/万元 |
| $U$ | 城镇化率 | % |
| $S$ | 第二产业占比 | % |
| $E$ | 煤炭消费占比 | % |
| $w_j$ | 指标j的权重 | - |
| $C_i$ | 省份i的综合TOPSIS贴近度 | - |
| $e_j$ | 指标j的信息熵 | - |
| $p_{ij}$ | 省份i在指标j上的比重，$p_{ij} = r_{ij} / \sum_i r_{ij}$ | - |
| $r_{ij}$ | 标准化后的指标值 | - |
| $v_{ij}$ | 加权标准化值，$v_{ij} = w_j \cdot r_{ij}$ | - |
| $D_i^+$ | 省份i到正理想解的欧氏距离 | - |
| $D_i^-$ | 省份i到负理想解的欧氏距离 | - |
| $g_i$ | 省份i的GDP | 亿元 |
| $c_i$ | 省份i的碳排放量 | Mt CO₂ |
| $R_i$ | 经济贡献协调度，$R_i = (g_i/\sum g_k)/(c_i/\sum c_k)$ | - |
| $a$ | STIRPAT模型常数项 | - |
| $b, c, d$ | STIRPAT基本模型弹性系数（人口/富裕度/技术） | - |
| $b_1, b_2, b_3, b_4, b_5, b_6$ | 扩展STIRPAT各因素弹性系数 | - |
| $\varepsilon$ | 模型误差项（原式中的 $e$） | - |
