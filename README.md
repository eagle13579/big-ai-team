# 超级AI团队

> 基于24个开源AI项目的结构模块深度分析与重组

## 项目背景

本项目通过对24个顶级AI项目（包括OpenClaw、MetaGPT、DeerFlow、OpenManus、GStack、claw-code等）的深度分析，提取出可复用的核心结构模块，重新组合成一套**超级AI团队最佳实践架构**。特别整合了claw-code项目的智能体装配（Agent Harness）机制，实现LLM与本地工具、文件系统和执行反馈循环的高效连接。

## 设计目标

- **模块化**: 每个组件可独立迁移、替换、升级
- **可扩展**: 支持从单Agent到多Agent协作的平滑扩展
- **生产级**: 包含完整的安全、监控、容错机制
- **成本优化**: 智能模型路由，降低60%+ API成本
- **执行闭环**: 实现"运行测试 -> 捕获错误 -> 反馈给AI -> 修改"的自动化循环

## 系统架构

项目采用五层架构模型：

1. **接入与意图层**: 多平台适配器、意图识别引擎、任务路由器
2. **角色与编排层**: 角色工厂、规划编排器、子Agent调度器、状态机管理
3. **技能与执行层**: 技能注册中心、工具执行器、MCP适配器、安全沙箱
4. **记忆与持久层**: 上下文管理器、记忆网格、向量数据库
5. **工作流与验证层**: 执行反馈循环、多语言一致性审计、团队协作模式

## 开发路径

项目开发分为四个阶段：

- **Phase 1 (Week 1-2)**: 基础设施 + L1层
- **Phase 2 (Week 3-4)**: L2层 + L3层核心
- **Phase 3 (Week 5-6)**: L3层增强 + L4层
- **Phase 4 (Week 7-8)**: L5层 + 完善

## 目录结构

```
big-ai-team/
├── src/            # 源代码目录
├── docs/           # 文档目录
│   └── prd.md      # 产品需求文档
├── tests/          # 测试目录
├── .gitignore      # Git忽略文件
└── README.md       # 项目说明
```

## 技术栈

- **接入层**: FastAPI + WebSocket
- **编排层**: Python + asyncio
- **执行层**: Python + subprocess
- **记忆层**: Redis + PostgreSQL
- **向量检索**: pgvector
- **消息队列**: Redis Pub/Sub
- **测试框架**: pytest + coverage
- **监控**: Prometheus + Grafana

## 参考项目

- OpenClaw: MCP适配器、记忆网格
- MetaGPT: 角色工厂、多Agent协作
- DeerFlow: 规划编排器、Harness
- OpenManus: 工具执行器、Skill系统
- claw-code: 智能体装配、执行循环、审计机制

## 许可证

MIT License

---

**版本**: 1.0.0  
**最后更新**: 2026-04-05  
**维护者**: AI架构团队
