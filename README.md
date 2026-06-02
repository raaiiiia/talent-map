# 人才地图 MVP

一个本地优先的人才地图工具原型，面向企业 HR 和业务负责人。当前版本聚焦长三角视频创作人才，辅助覆盖 AI 算法人才，支持公开网页检索、手动链接、CSV/Excel/简历 PDF 导入、AI 辅助评分、人才地图和业务洞察报告。

## 线上访问

平台访问地址：https://talent-map.vercel.app

## 启动

```powershell
python app.py --port 8787
```

打开：

```text
http://127.0.0.1:8787
```

默认账号：

```text
TALENT_MAP_ADMIN_EMAIL
TALENT_MAP_ADMIN_PASSWORD
TALENT_MAP_ADMIN_NAME
```

## 使用流程

1. 登录后在「AI 创建」里通过问答式流程创建项目。
2. 在「设置」中填入自己的 DeepSeek API Key 和 Tavily API Key。
3. 在「检索」里生成搜索计划，并用 Tavily + DeepSeek 从公开网页提取候选人。
4. 在「导入」里补充手动链接、CSV、Excel 或 PDF 简历。
5. 在「候选人」里维护状态、评分和备注。
6. 在「人才地图」查看技能、平台、城市、公司网络和流动路径。
7. 在「报告」中导出 CSV、Excel，并打开可打印为 PDF 的业务人才洞察报告。

## 数据与合规边界

- 仅检索公开可读网页和企业已授权的数据源。
- 不抓取登录后、付费墙、验证码或明确禁止自动访问的数据。
- 不内置 LinkedIn、BOSS 直聘等账号爬取能力。
- AI 评分是辅助判断，不等同于录用结论。
- AI 推断出的年限、技能、项目、公司经历等信息应标记为待确认，并由用户复核。

## API Key

当前支持：

- DeepSeek：用于候选人抽取、归一化、评分、推荐理由和风险说明。
- Tavily：用于公开网页搜索。

API Key 默认只保存在本机 SQLite 数据库中，不会上传到第三方服务，除非你主动调用对应 API。

## 当前技术栈

- Python 标准库 HTTP Server
- SQLite 本地数据库
- 原生 HTML/CSS/JavaScript
- 无第三方 Python 依赖

后续可以平滑升级为 FastAPI + SQLAlchemy + 前端框架版本，并增加团队权限、任务队列、浏览器自动化采集和更强的报告模板。
