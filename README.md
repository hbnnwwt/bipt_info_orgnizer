# BIPTInfoOrganizer - 信息组织器

基于 FastAPI + Vue 3 的信息采集与文档管理工具。通过 REST API 与 bipthelper（智能检索系统）协同工作。

## 功能

- **爬虫配置** — 配置和管理多个站点的爬取规则
- **文档管理** — 查看、管理已推送到 bipthelper 的文档
- **审计日志** — 本地操作记录
- **AI 辅助分类** — 通过 bipthelper 接口进行文档分类

## 快速开始

### 前提

- Python 3.11+
- Node.js 18+
- bipthelper 已运行（端口 8000）

### 安装与运行

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖
cd ../frontend
npm install

# 启动前端开发服务器（端口 3001）
npm run dev

# 启动后端（端口 8001，另开终端）
cd ../backend
python main.py
```

访问 `http://localhost:3001`

### 配置

编辑 `backend/.env`：

```
BIPTHELPER_URL=http://localhost:8000
ORGANIZER_API_KEY=your-key-from-bipthelper
```

ORGANIZER_API_KEY 必须与 bipthelper 的 `.env` 中的 `ORGANIZER_API_KEY` 一致。

## 架构

```
bipt_info_organizer (8001)
  └── backend/          — FastAPI 后端
  └── frontend/         — Vue 3 SPA
         └── /api/*    → backend (8001)
  └── 调用 bipthelper API (8000) 操作文档
         └── POST /api/documents        — 推送文档
         └── PUT /api/documents/{id}    — 更新分类
         └── GET /api/documents         — 查询文档
         └── DELETE /api/documents/{id} — 删除文档

bipthelper (8000)
  └── backend/          — 文档存储 + 搜索索引
  └── Meilisearch (7700) — 全文检索
```

## 初始账号

与 bipthelper 共享：`admin` / `admin123`