# Vercel 部署说明

## ✅ 已完成的修改

1. **创建了 `api/index.py`** - Vercel 的入口文件
2. **使用内存数据库** - 替代文件系统的 SQLite（Vercel serverless 不支持持久化文件）
3. **更新了 `vercel.json`** - 指向新的入口点
4. **添加了错误处理** - 处理缺失的环境变量

## 🚀 部署步骤

### 1. 在 Vercel 设置环境变量

访问你的 Vercel 项目：
- Dashboard → 你的项目 → Settings → Environment Variables
- 添加：`GITHUB_TOKEN` = 你的 GitHub token

### 2. 重新部署

Vercel 会自动检测到 GitHub 推送并重新部署，或者：
- 在 Vercel Dashboard → Deployments → 点击 "Redeploy"

## 📝 重要说明

### 数据持久化问题

**当前配置使用内存数据库**，这意味着：
- ⚠️ 每次函数重启，数据会丢失
- ⚠️ 不同的请求可能使用不同的实例，数据不共享

### 解决方案：使用外部数据库

#### 选项 1: Vercel Postgres（推荐）

1. Vercel Dashboard → Storage → Create Database
2. 选择 Postgres
3. 连接后自动添加 `POSTGRES_URL` 环境变量
4. 修改 `api/index.py`：

```python
# 替换这行：
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

# 改为：
import os
database_url = os.environ.get('POSTGRES_URL', 'sqlite:///:memory:')
# Vercel Postgres URL 可能需要调整
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
```

5. 添加依赖到 `requirements.txt`：
```
psycopg2-binary==2.9.9
```

#### 选项 2: Supabase（免费）

1. 访问 https://supabase.com 并创建项目
2. 获取数据库连接 URL
3. 在 Vercel 添加环境变量 `DATABASE_URL`
4. 使用上面相同的代码修改

## 🧪 测试 API

```bash
# 测试首页
curl https://your-app.vercel.app/

# 获取所有笔记
curl https://your-app.vercel.app/api/notes

# 创建笔记
curl -X POST https://your-app.vercel.app/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"测试","content":"这是一个测试笔记"}'
```

## 📚 API 端点

- `GET /` - 主页和 API 信息
- `GET /health` - 健康检查
- `GET /api/notes` - 获取所有笔记
- `POST /api/notes` - 创建笔记
- `GET /api/notes/<id>` - 获取单个笔记
- `PUT /api/notes/<id>` - 更新笔记
- `DELETE /api/notes/<id>` - 删除笔记
- `POST /api/notes/<id>/translate` - 翻译笔记
- `POST /api/notes/generate` - AI 生成结构化笔记

## 🔧 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用（使用原始的 src/main.py）
python src/main.py

# 访问
http://localhost:5000
```

## ⚠️ 注意事项

1. **GITHUB_TOKEN 必须设置** - AI 功能才能工作
2. **内存数据库** - 当前数据不持久化，仅用于测试
3. **生产环境** - 建议配置 PostgreSQL 或其他外部数据库
