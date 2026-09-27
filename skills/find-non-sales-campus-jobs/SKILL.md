---
name: find-non-sales-campus-jobs
description: Use when searching, resuming, verifying, comparing, monitoring, ranking, importing, or exporting campus, graduate, entry-level, or internship opportunities for a candidate who prefers non-sales work. Uses WeChat and Sogou WeChat as a high-recall discovery layer, official job pages and ATS as the verification layer, and supports search tiers, missed-job learning, dynamic sites, realistic ranking, and quality-controlled outputs; also use when manually invoked as $find-non-sales-campus-jobs.
---

# 非销售校招岗位搜索

## 输入

以 `个人求职事实信息库.md` 为事实来源，先读“快速读取区”，再按需读取详细章节和证明材料。确认招聘类型与届别、毕业时间、教育与经历、技能、城市优先级、岗位方向、职责边界、工作条件、行业/公司/薪资偏好，以及实习和正式岗范围。影响搜索范围或分级的缺口集中询问，其余字段标记状态后继续。

## 选择搜索档位

- 快速：用户要当天清单、小批量结果或验证若干岗位。直接搜索岗位并核验，不建立完整公司池。
- 标准：默认档。围绕优先城市、行业和现实岗位建立有限公司池，兼顾速度与覆盖。
- 深度：仅在用户明确要求全量、查漏或覆盖审计时使用。执行完整公司发现、实体扩展和动态网站验收。

先声明档位和有限范围。只有深度档且全部验收通过时，才能表述“全量搜索完成”；其他档位按实际范围表述。

## 双层搜索架构

- 发现层：微信公众号、搜狗微信、学校就业号和聚合线索负责提高新岗位、地方岗位和短窗口岗位的召回率。
- 核验层：公司职位详情、官方 ATS、官方公告和政府/高校正式页面负责确认岗位、城市、届别、职责、截止和投递状态。

公众号线索不因无法回源而丢弃，但不得仅凭非官方转载直接进入“主投”或“可以投”。执行公众号身份判断、回源和晋级规则时读取 [wechat-discovery-and-verification.md](references/wechat-discovery-and-verification.md)。

## 执行

1. 读取上次状态、有效旧岗位、监控池及已生效学习规则。
2. 声明档位，以及城市、行业、公司层级、来源渠道和复查范围。
3. 搜索任务先按 [search-and-coverage.md](references/search-and-coverage.md) 执行公众号与其他渠道发现，再按 [wechat-discovery-and-verification.md](references/wechat-discovery-and-verification.md) 判断公众号身份并回到官方来源；指定岗位核验可跳过公众号发现。
4. 按 [company-discovery.md](references/company-discovery.md) 建立与档位匹配的公司池；快速档可直接从岗位开始，再按搜索与覆盖规则补充其他渠道。
5. 按 [verification-and-ranking.md](references/verification-and-ranking.md) 核验和分级。
6. 用户从任何渠道补充岗位时，按 [feedback-learning.md](references/feedback-learning.md) 收录、核验、分析漏检并生成下轮规则。
7. 每完成一个范围单元保存岗位、覆盖状态、学习记录和恢复位置；续搜只处理待办、失败项和状态变化。
8. 按 [output-schema.md](references/output-schema.md) 输出来源身份、回源状态和来源质量指标，并运行 `scripts/validate-job-results.py`。

## 联动

获得用户明确确认或可靠材料后，可直接更正 `个人求职事实信息库.md` 的当前值、快速摘要和更正记录。将主投、可以投及用户选择的冲刺岗位交给简历 Skill，再交给网申 Skill；交接岗位记录 JD、来源、投递路径、粒度、分级、匹配、风险和材料需求。

## 完成

报告已完成范围、未完成项、技术或渠道盲区、公众号独有线索数、官方回源率、未回源线索数、用户反馈产生的搜索规则和下次恢复位置。标准档完成不等于互联网全量；深度档也只代表预先声明范围内的全量。
