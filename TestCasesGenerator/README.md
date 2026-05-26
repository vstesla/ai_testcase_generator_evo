# TuoGuan Group 1 Automation Tools

本项目是一个基于 FastAPI 构建的自动化工具集合，旨在为托管业务提供 AI 测试用例生成和清算领域事中规则的自动化校验能力。

本仓库采用了模块化的目录结构，各个工具集在 `app/teams/tuoguan_group1` 目录下独立维护，并通过统一的入口对外提供 API 接口。

---

## 1. 模块结构概览

目前系统集成了以下两大核心工具模块，您可以点击对应链接查看各个模块的详细设计与接口文档：

### 1.1 智能测试用例生成模块 (`ai_testcase_generator`)
- **路径**: [`app/teams/tuoguan_group1/ai_testcase_generator`](./app/teams/tuoguan_group1/ai_testcase_generator/)
- **功能简介**:
  该模块对接内部 AI Agent 服务，提供测试数据集的自动泛化、对抗样本生成能力。同时支持基于大模型的指令附件（如存款协议、缴款通知书）的动态生成与 PDF 排版渲染，并内置了与“解析小助”对接的比对评测能力。
- **文档链接**: [智能测试用例生成接口文档](./app/teams/tuoguan_group1/ai_testcase_generator/README.md)

### 1.2 事中规则自动化测试模块 (`in_flight_rules_automation_tools`)
- **路径**: [`app/teams/tuoguan_group1/in_flight_rules_automation_tools`](./app/teams/tuoguan_group1/in_flight_rules_automation_tools/)
- **功能简介**:
  该模块基于 Playwright 构建，用于对前端页面的清算业务事中规则进行自动化 UI 校验。支持动态修改底层数据库数据以构造一致/不一致场景，通过模拟指令录入验证前端页面的红色/绿色拦截提示信息。该模块采用了高度可扩展的“注册表模式”，可轻松接入数百个不同的事中规则。
- **文档链接**: [事中规则自动化测试接口文档](./app/teams/tuoguan_group1/in_flight_rules_automation_tools/README.md)

---

## 2. 环境依赖与运行

### 2.1 环境配置
本项目使用 Python 编写，主要依赖项包括 `FastAPI`, `Uvicorn`, `Playwright` 等。请确保您已配置相关的数据库 (MySQL) 与 COS 存储环境变量。

如果需要使用 `in_flight_rules_automation_tools` 进行 UI 自动化，请确保已安装 Playwright 驱动：
```bash
pip install playwright
playwright install chromium
```

### 2.2 启动服务
在项目根目录下，执行以下命令即可启动全局的 API 服务：
```bash
python app/main.py
```
服务将在 `http://127.0.0.1:8000` 启动，所有的子模块路由将挂载在主服务下。

---

## 3. 路由配置
所有的子模块路由都统一在 `app/teams/tuoguan_group1_router.py` 中进行注册：
- 测试用例生成相关的接口前缀通常为：`/ai_testcase_generator`
- 事中规则自动化测试的接口前缀通常为：`/in_flight_rules`

可以通过访问 `http://127.0.0.1:8000/docs` 查看由 FastAPI 自动生成的完整 Swagger UI 接口文档。
