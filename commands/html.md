---
description: HTML Artifact——先判断价值，再构建可运行的单文件交付
argument-hint: [需求描述]
skills: html-artifact
---

判断以下需求是否值得产出 HTML Artifact；有实际价值就直接构建。

需求：$ARGUMENTS

**第一步·价值判断**：一句话回答——交互/可视化能否比 Text/Table/SVG 显著降低理解成本？不能就改用更轻的媒介并说明。

**第二步·构建**（若值得）：

1. 单文件；CSS/JS 全内联；零构建、零外部网络依赖。
2. 优先 SVG + CSS + 原生 JS；框架仅在复杂度确实需要时用。
3. 交互必须有实际意义（筛选/对比/参数模拟），禁用装饰性动效。
4. 深浅色可读；≤768px 不破版。
5. 构建后实际打开验证：渲染、每个交互点一遍、控制台无错误。

完整规范见 html-artifact skill。
