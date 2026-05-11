# 自进化数学建模引擎 (Self-Evolving Math Modeling Engine)

跟 Claude Code 对话就能完成数学建模竞赛的全栈系统。没有脚本流水线，对话推进，做完自动变强。

## 快速开始

1. 将此文件夹拖入 Claude Code
2. 说"帮我做这道数模题"（附题目 PDF 或文本）
3. 按对话自然推进 8 个阶段（问题分析→建模→验证→论文→进化）
4. 可随时打断、讨论、回溯——对话就是流水线

## 核心资产

| 资产 | 数量 | 说明 |
|------|------|------|
| 角色文档 | 2500+ 行 | 建模手/编程手/论文手完整工作流程 |
| 论文库 | **1489 篇 PDF** | 按6大类28子类组织，支持按需下载 |
| 算法库 | 74 方法 | 9 领域 27 子领域结构化索引 + MATLAB→Python 映射 |
| 反模式库 | 39 条 | 四大类，按严重度分级，进化时自动检测 |
| 评分基线 | 91 篇 CUMCM 论文 | 10 维度 p25/p50/p75 经验分布 |
| CLI 工具 | 13 个 | 搜索/验证/评分/编译/进化/论文学习 |

## 自进化能力

每次建模完成后，执行 7 种增强：

- **记录** — 经验写入角色文档，算法标记已验证
- **对比** — 跟历史最佳对比得分
- **强化** — 高分策略升权，低分降权
- **填补** — 检测未做题型和未验证算法
- **蒸馏** — 提取高频代码特征
- **论文学习** — 每次读一篇按模型类型匹配的范文提取写作规律
- **反模式检测** — 自动扫描 12 项规则

## 目录结构

```
├── CLAUDE.md              # 入口：定义身份+建模流程+工具
├── SOP.md                 # 8 阶段操作规范
├── roles/                 # 三个角色文档（会进化）
├── algorithms/            # 算法库 + 结构化索引 + MATLAB→Python映射
├── references/
│   └── papers/            # 1489篇论文，按6大类组织：优化类/评价类/预测类/统计类/图论网络类/仿真综合类
├── rules/                 # 39条反模式
├── templates/             # LaTeX 模板
├── tools/                 # 13 个 CLI 工具
├── models/cases/          # 案例沉淀
└── sessions/              # 每次建模的完整归档
```

## 论文库分类（部分）

| 大类 | 子类数 | 篇数 |
|------|--------|------|
| 优化类 | 3 | 142 |
| 评价类 | 3 | 112 |
| 预测类 | 3 | 70 |
| 统计类 | 9 | 609 |
| 图论网络类 | 3 | 91 |
| 仿真综合类 | 11 | 221 |
| **总计** | **28** | **1489** |

## 申明

- 本仓库中的算法说明文档、LaTeX 模板、角色文档等文字性内容采用 CC BY-NC-SA 4.0 许可。
- 代码工具（`tools/` 目录）采用 MIT 许可。
- 论文 PDF（`references/` 目录）版权归原作者所有，仅供学习参考。

## 致谢

本项目的设计灵感来源于以下开源项目：
- [LLM-MM-Agent](https://github.com/usail-hkust/LLM-MM-Agent) (NeurIPS 2025) — HMML 三级算法知识库
- [mathmodel-skill](https://github.com/handsomeZR-netizen/mathmodel-skill) — 91 篇论文评分基线与 32 反模式
- [MathModel-MutiAgentSystem](https://github.com/haitanghuaweimianTom/MathModel-MutiAgentSystem) — Memory Pool 与代码自修复
- [AutoMCM-Pro](https://github.com/RealSeaberry/AutoMCM-Pro) — 强制自验证协议与 GitOps 流水线
- [dick20/MCM-ICM](https://github.com/dick20/MCM-ICM) — 2004-2025 美赛 O 奖论文
- [personqianduixue/Math_Model](https://github.com/personqianduixue/Math_Model) — 数学建模资源库
- [HuangCongQing/Algorithms_MathModels](https://github.com/HuangCongQing/Algorithms_MathModels) — 算法 MATLAB 实现
- [hacheyz/PMMAA](https://github.com/hacheyz/PMMAA) — Python 数学建模算法与应用
- [Giyn/MathematicalModelingAlgorithm](https://github.com/Giyn/MathematicalModelingAlgorithm) — 独立可导入的 Python 算法模块
