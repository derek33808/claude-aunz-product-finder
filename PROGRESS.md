# AU/NZ 选品工具 - 开发进度

## 当前状态: ✅ MVP 基础架构完成

## 已完成
- [x] 设计文档 (DESIGN.md)
- [x] 进度文档创建
- [x] Phase 1: MVP 基础架构

## Phase 1: MVP 基础架构 ✅

### 1.1 项目初始化
| 任务 | 状态 | 备注 |
|------|------|------|
| 后端项目结构 | ✅ 完成 | FastAPI + Supabase |
| 前端项目结构 | ✅ 完成 | React + TypeScript + Vite |
| 数据库表创建 | ✅ 完成 | Supabase SQL 迁移脚本 |

### 1.2 数据采集模块
| 模块 | 状态 | 备注 |
|------|------|------|
| eBay API | ✅ 完成 | Browse API 集成 |
| Google Trends | ✅ 完成 | pytrends 封装 |
| TradeMe 爬虫 | ✅ 完成 | Playwright 爬虫 |

### 1.3 核心功能
| 功能 | 状态 | 备注 |
|------|------|------|
| 产品搜索 | ✅ 完成 | 多平台搜索 API |
| 数据分析 | ✅ 完成 | 竞争分析、利润估算 |
| 报告生成 | ✅ 完成 | 后台任务生成 |

### 1.4 前端页面
| 页面 | 状态 | 备注 |
|------|------|------|
| Dashboard | ✅ 完成 | 数据概览 |
| Products | ✅ 完成 | 产品搜索 |
| Trends | ✅ 完成 | Google Trends 分析 |
| Reports | ✅ 完成 | 报告管理 |

---

## 技术栈确认
- **后端**: Python 3.11+ / FastAPI
- **前端**: React 18 / TypeScript / Vite
- **数据库**: Supabase (PostgreSQL)
- **存储**: Supabase Storage
- **爬虫**: Playwright

## 环境变量 (需要配置)
```
SUPABASE_URL=
SUPABASE_KEY=
EBAY_APP_ID=
EBAY_CERT_ID=
```

## 下一步 (Phase 2)
- [ ] 配置 Supabase 项目
- [ ] 部署后端到服务器
- [ ] 完善报告 PDF 生成
- [ ] 添加用户认证
- [ ] 实现定时数据采集

## 启动说明

### 后端
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 编辑配置
uvicorn app.main:app --reload
```

### 前端
```bash
cd frontend
npm install
cp .env.example .env  # 编辑配置
npm run dev
```

### 数据库
1. 创建 Supabase 项目
2. 运行 `supabase/migrations/001_initial_schema.sql`
3. (可选) 运行 `supabase/seed.sql` 添加测试数据

## 线上环境

| 服务 | URL |
|------|-----|
| **Frontend** | https://claude-aunz-product-finder.netlify.app |
| **Backend API** | https://claude-aunz-product-finder.onrender.com |
| **GitHub 仓库** | https://github.com/derek33808/claude-aunz-product-finder |
| **Supabase** | https://dfeeyhrjneuilmhsiwww.supabase.co |

## 更新日志

### 2026-01-21 13:48 (测试框架建设)
**准备执行**: 根据 QA 报告添加测试策略和测试框架
**状态**: ✅ 完成

**完成内容**:
- [x] DESIGN.md 添加测试策略章节
  - 测试范围定义（核心模块优先级）
  - 测试类型规划（单元测试、集成测试）
  - 测试覆盖率目标（MVP 50% -> Phase 2 70% -> Phase 3+ 80%）
  - 测试目录结构规范
- [x] DESIGN.md 添加验收标准章节
  - 功能验收标准（可测量条件）
  - 性能验收标准（响应时间目标）
  - 质量验收标准（覆盖率、Bug密度）
  - 部署验收标准（checklist）
- [x] 后端测试框架搭建
  - 创建 `backend/tests/` 目录结构
  - 添加 pytest 配置 (`pytest.ini`)
  - 创建 `conftest.py` 通用 fixtures
  - 创建 `test_main.py` 应用入口测试
  - 创建 `api/test_products.py` 产品 API 测试（15+ 测试用例）
  - 更新 `requirements.txt` 添加测试依赖
- [x] 前端测试框架搭建
  - 创建 `frontend/src/__tests__/` 目录结构
  - 添加 Vitest 配置 (`vitest.config.ts`)
  - 创建测试 setup 文件（mock 配置）
  - 创建 `App.test.tsx` 应用组件测试
  - 创建 `pages/Dashboard.test.tsx` Dashboard 页面测试
  - 更新 `package.json` 添加测试脚本和依赖

**关键文件**:
- `DESIGN.md` - 添加测试策略和验收标准
- `backend/tests/conftest.py` - pytest fixtures
- `backend/tests/test_main.py` - 入口测试
- `backend/tests/api/test_products.py` - API 测试
- `backend/pytest.ini` - pytest 配置
- `frontend/vitest.config.ts` - Vitest 配置
- `frontend/src/__tests__/setup.ts` - 测试 setup
- `frontend/src/__tests__/App.test.tsx` - App 组件测试
- `frontend/src/__tests__/pages/Dashboard.test.tsx` - Dashboard 测试

**下一步**:
- [ ] 安装测试依赖并运行测试
- [ ] 持续添加更多测试用例
- [ ] 配置 CI/CD 自动测试

---

### 2026-01-21 (新功能)
**准备执行**: 添加中英文切换、一键选爆品、使用手册
**状态**: ✅ 完成

**完成内容**:
- [x] 中英文切换功能 (react-i18next)
  - Header 添加语言切换按钮
  - 支持 English / 中文
  - 语言偏好保存到 localStorage
- [x] 一键选爆品按钮 (Dashboard)
  - 后端 API: `/api/products/hot`
  - 热度评分算法: 评论数(40%) + 评分(30%) + 价格合理性(30%)
  - 前端显示 Top 10 热门产品
- [x] 使用手册文档 (USER_GUIDE.md)

**关键文件**:
- `frontend/src/i18n/` - i18n 配置和语言文件
- `frontend/src/App.tsx` - 语言切换按钮
- `frontend/src/pages/Dashboard.tsx` - 一键选爆品功能
- `backend/app/api/routes/products.py` - 热门产品 API
- `USER_GUIDE.md` - 使用手册

**下一步**:
- [ ] 验证 Netlify 部署
- [ ] 测试线上功能

---

### 2026-01-21 11:17
**准备执行**: 排查 Netlify 域名无法访问问题
**状态**: ✅ 完成

**问题原因**: Netlify 构建配置未设置 `base` 目录，导致从仓库根目录构建而非 `frontend/` 子目录

**解决方案**:
1. 通过 Netlify API 更新 build_settings:
   - `base: "frontend"`
   - `cmd: "npm run build"`
   - `dir: "dist"`
2. 触发重新部署 `netlify deploy --build --prod`

**验证结果**: HTTP 200，网站正常访问 ✅

**关键文件**:
- `frontend/netlify.toml` - 重定向配置（已有）
- Netlify build_settings - 已修复

---

---

### 2026-01-21
- ✅ 部署到线上环境
  - Frontend: Netlify (自动部署)
  - Backend: Render (Python 免费层)
- ✅ 配置环境变量
- ✅ 修复 TypeScript 编译问题
- ✅ 修复 Google Trends API 超时问题 (添加模拟数据备用)
- ✅ 修复产品价格显示问题 (string to number)
- ✅ 修复 API 路径问题 (trailing slash)

### 2026-01-20
- 创建设计文档
- 添加一键生成报告功能设计
- 集成 Supabase 方案
- 完成 MVP 基础架构
  - 后端: FastAPI + Supabase
  - 前端: React + TypeScript + Ant Design
  - 数据采集: eBay API, Google Trends, TradeMe 爬虫
  - 报告生成: 后台任务处理
