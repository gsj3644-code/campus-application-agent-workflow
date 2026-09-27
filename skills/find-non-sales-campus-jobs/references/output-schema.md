# 输出与质量门

## 表格

统一使用：使用说明、岗位总表、本轮新增与变更、官网监控池、不建议投与失效、搜索覆盖与日志。所有城市进入“岗位总表”，以“城市”筛选。

岗位总表基础字段：建议等级、信息粒度、公司、岗位全名、城市、招聘届别、核心职责、硬性要求、匹配原因、现实风险、当前状态、截止日期、核验日期、官方链接、站内搜索词、来源层级、发现方式、初始渠道、原始线索、漏检原因、学习规则ID。

新结果使用 `schema_version: 2`，并增加：发现入口类型、公众号身份、回源状态、回源链接。非公众号来源的“公众号身份”填“不适用”。“官方链接”用于最终投递或核验入口；“回源链接”记录从公众号或聚合线索追回的证据页，两者可相同。

“发现方式”使用 AI搜索、用户提供、历史复查或监控触发。AI 搜索岗位的反馈字段可留空；用户提供岗位必须保留初始渠道和原始线索，完成漏检分析，并关联学习规则或写“不适用”。链接依次选择职位详情、官方搜索结果、招聘首页；主投和可以投岗位提供有效链接或可复现路径。

## 状态文件

状态 JSON 存于候选人工作区，使用同一个 `岗位搜索状态.json`：

```json
{
  "schema_version": 2,
  "run_date": "YYYY-MM-DD",
  "search_mode": "quick|standard|deep",
  "scope_declared": true,
  "completion_claimed": false,
  "coverage": [{"city": "目标城市", "industry": "行业", "status": "completed|pending|failed"}],
  "discovery_passes": [{"channel": "发现渠道", "status": "completed|pending|failed"}],
  "company_pool": [{"entity_id": "ID", "company": "公司", "status": "checked|pending|failed", "entity_expansion_checked": false, "recruitment_channels_checked": true}],
  "old_positions_reviewed": true,
  "monitor_pool_checked": true,
  "dynamic_sites": [{"site": "官网", "pagination_checked": true, "filters_checked": true, "keywords_checked": true, "details_checked": true, "status": "completed|technical_review"}],
  "wechat_searches": [{"query": "2027届 秋招 校园招聘", "search_url": "https://weixin.sogou.com/weixin?type=2&query=...", "pages_checked": 1, "result_count": 10, "article_urls": [], "status": "completed|technical_review"}],
  "source_quality_metrics": {"wechat_discovered_leads": 10, "wechat_unique_leads": 6, "official_source_verified": 4, "official_account_complete": 1, "unverified_leads": 1, "stale_or_duplicate_leads": 4, "official_verification_rate": 0.6667},
  "residual_blind_spots": [],
  "learning_rules": [{"id": "LR-001", "reason": "role_keyword_gap", "trigger": "物流岗位搜索", "action": "增加履约/订单执行同义词", "scope": "当前候选人", "status": "active", "evidence_job_ids": ["J-001"], "created_at": "YYYY-MM-DD", "last_applied": null, "hit_count": 0}],
  "resume_from": "下一项",
  "jobs": []
}
```

`official_source_verified` 包含已回到职位详情、官方 ATS/招聘首页或信息完整的官方招聘公众号原文。`official_verification_rate = official_source_verified / wechat_unique_leads`；没有公众号独有线索时填 `null`，不伪造 100%。指标用于比较发现质量，不作为压低公众号召回的目标。

## 分档验收

- 快速档：声明范围；发现新岗位时执行至少一组搜狗微信综合查询；记录公众号身份和回源状态；核验岗位并保存待办和恢复位置；不要求完整公司池。
- 标准档：声明范围；完成或明确记录搜狗微信组合查询；至少一个其他公司发现渠道；有限公司池全部检查；旧岗位、监控池、岗位核验和去重完成；报告来源质量指标。技术待复核项可以保留，但必须列入盲区。
- 深度档：搜狗微信完成组合查询、公司及招聘公众号逐一查询和分页检查；至少两个独立发现渠道；公司池全部完成实体与招聘渠道扩展；旧岗位和监控池复查；动态网站检查完成；所有公众号独有线索均完成回源或给出明确人工复核任务；没有未处理盲区。

只有 `completion_claimed=true` 才按对应档位检查全部完成条件；阶段性结果可以保留待办，但必须准确报告。只有通过深度档验收才能声称“全量搜索完成”。

运行：

```powershell
python scripts/validate-job-results.py <结果.json|结果.csv|结果.xlsx>
```

用户调整冲刺比例时传入 `--max-sprint-ratio`。脚本检查结构、档位完成条件、用户补充岗位和学习规则关联；实时页面与人工渠道仍需浏览器或人工核验。
