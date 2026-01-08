# 环境与 Docker 配置

## 📋 目录

- [环境准备](#环境准备)
- [环境变量配置](#环境变量配置)
- [Docker Compose 文件说明](#docker-compose-文件说明)
- [启动服务](#启动服务)
- [开发模式](#开发模式)
- [生产环境部署](#生产环境部署)
- [常见问题](#常见问题)

---

## 环境准备

### 必需软件

1. **Docker** 和 **Docker Compose**
   - Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
   - 确保 Docker Compose 版本 >= 2.0

2. **Python 3.11+**（本地开发需要）
   - 用于生成密钥和运行脚本

3. **Node.js 18+**（前端开发需要）
   - 用于本地前端开发

### 验证安装

```bash
# 检查 Docker
docker --version
docker compose version

# 检查 Python
python --version

# 检查 Node.js
node --version
```

---

## 环境变量配置

### 1. 创建 .env 文件

在项目根目录 `biz-platform/` 下创建 `.env` 文件：

```bash
cd biz-platform
cp .env.example .env
```

### 2. 必需配置项

#### ⚠️ 安全配置（必须修改）

```env
# 生成 SECRET_KEY
# 命令：python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_generated_secret_key_here

# 设置管理员邮箱和密码
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=your_strong_password_here

# 设置数据库密码
POSTGRES_PASSWORD=your_db_password_here
```

**重要**：所有密码和密钥不能使用默认值 `changethis`，否则应用无法启动。

#### 项目配置

```env
PROJECT_NAME=biz-platform
STACK_NAME=biz-platform
ENVIRONMENT=local
```

#### 数据库配置

```env
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_db_password_here
```

#### CORS 配置

```env
BACKEND_CORS_ORIGINS="http://localhost,http://localhost:5173,https://localhost,https://localhost:5173"
FRONTEND_HOST=http://localhost:5173
```

### 3. 可选配置项

#### 邮件配置（可选）

如果不需要邮件功能，可以留空：

```env
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=info@example.com
SMTP_TLS=True
SMTP_SSL=False
SMTP_PORT=587
```

#### 微信小程序配置（可选）

```env
WECHAT_APPID=your_appid
WECHAT_SECRET=your_secret
```

#### 项目路径配置（必需）

```env
PROJECT_DIR=C:\Users\GALAX\Projects\biz-platform  # 项目根目录路径
```

#### 文件上传配置

```env
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=["pdf","doc","docx","jpg","jpeg","png","xls","xlsx"]
```

**注意**：上传目录路径会自动基于 `PROJECT_DIR` 推导，格式为 `{PROJECT_DIR}/data/uploads`

---

## Docker Compose 文件说明

项目包含三个 Docker Compose 配置文件，它们有不同的用途和使用场景：

### 1. `docker-compose.yml`（主配置文件）

**作用**：定义所有服务的标准配置，适用于所有环境（开发、测试、生产）。

**包含的服务**：
- **db**: PostgreSQL 数据库
- **adminer**: 数据库管理工具
- **prestart**: 数据库迁移和初始化
- **backend**: FastAPI 后端服务
- **frontend**: React 前端服务

**特点**：
- 使用 Traefik 作为反向代理（通过标签配置）
- 支持 HTTPS（生产环境）
- 服务通过子域名访问（如 `api.${DOMAIN}`）
- 假设 Traefik 已经存在（external network）

**使用场景**：
- 生产环境部署
- 需要独立 Traefik 的环境

### 2. `docker-compose.override.yml`（开发覆盖配置）

**作用**：**自动应用**的开发环境覆盖配置。Docker Compose 会自动读取此文件并覆盖主配置。

**关键特性**：
- **自动加载**：运行 `docker compose` 命令时会自动合并此文件
- **仅用于开发**：不应提交到生产环境
- **覆盖主配置**：可以覆盖 `docker-compose.yml` 中的任何配置

**主要覆盖内容**：

1. **添加本地 Traefik 代理（proxy）**：
   - 端口映射：80 → 80, 8090 → 8080（Dashboard）
   - 启用不安全模式（`--api.insecure=true`）用于本地开发
   - 创建内部 `traefik-public` 网络（`external: false`）

2. **端口映射到 localhost**：
   - `db`: 5432 → 5432（可直接连接）
   - `backend`: 8000 → 8000（可直接访问）
   - `adminer`: 8081 → 8080（可直接访问，使用 8081 避免与 EDB PEM 冲突）
   - ⚠️ **前端配置已注释**：前端服务配置已被注释，推荐使用本地开发服务器（`npm run dev`）而不是 Docker 容器

3. **开发模式配置**：
   - `restart: "no"`：开发时不需要自动重启
   - `command: fastapi run --reload`：启用代码热重载
   - `develop.watch`：文件变化自动同步到容器
   - 挂载代码目录实现实时更新

4. **添加开发工具**：
   - **mailcatcher**：邮件测试工具（端口 1080, 1025）
   - **playwright**：E2E 测试容器

5. **命名卷配置**：
   - **backend-venv**：后端虚拟环境命名卷（替代匿名卷）
     - 挂载到 `/app/.venv`，用于隔离容器内的 Python 虚拟环境
     - 避免本地 `.venv` 目录覆盖容器内的虚拟环境
     - 使用命名卷便于管理和清理

6. **开发环境变量**：
   - `SMTP_HOST: "mailcatcher"`：使用本地邮件测试工具
   - `VITE_API_URL=http://localhost:8000`：前端连接本地后端（前端通过本地开发服务器运行时使用）

7. **前端开发说明**：
   - ⚠️ **前端配置已注释**：`frontend` 服务配置在 `docker-compose.override.yml` 中已被注释
   - **推荐方式**：使用本地开发服务器（`npm run dev`）进行前端开发，获得更好的热更新体验
   - **启动方式**：运行 `scripts/dev-start-frontend.bat` 或手动在 `frontend` 目录执行 `npm run dev`
   - **优势**：更快的启动速度、更好的热更新支持、更接近生产环境的开发体验

**使用场景**：
- 本地开发环境（默认）
- 代码热重载和调试
- 不需要手动指定，Docker Compose 会自动使用

**如何禁用**：
```bash
# 使用 -f 参数只加载主配置文件
docker compose -f docker-compose.yml up -d
```

### 3. `docker-compose.traefik.yml`（独立 Traefik 配置）

**作用**：用于**生产环境**的独立 Traefik 反向代理配置。

**关键特性**：
- **独立运行**：Traefik 作为独立的服务运行
- **生产就绪**：包含 HTTPS、证书管理、访问控制
- **需要手动指定**：不会自动加载

**主要功能**：

1. **Let's Encrypt 自动证书**：
   - 自动获取和续期 SSL 证书
   - 使用 TLS Challenge 验证域名
   - 证书存储在 Docker Volume 中

2. **HTTPS 重定向**：
   - 自动将 HTTP 请求重定向到 HTTPS
   - 确保所有流量加密

3. **Dashboard 访问控制**：
   - HTTP Basic Auth 保护 Traefik Dashboard
   - 需要设置 `USERNAME` 和 `HASHED_PASSWORD` 环境变量

4. **网络配置**：
   - 使用外部网络 `traefik-public`（需要预先创建）
   - 与其他服务共享网络

**使用场景**：
- 生产环境部署
- 需要独立 Traefik 实例
- 需要自动 HTTPS 证书

**如何使用**：

```bash
# 1. 创建 Traefik 网络（如果不存在）
docker network create traefik-public

# 2. 启动 Traefik（需要设置环境变量）
export DOMAIN=your-domain.com
export EMAIL=your-email@example.com
export USERNAME=admin
export HASHED_PASSWORD=$(echo $(htpasswd -nb admin password) | sed -e s/\\$/\\$\\$/g)

docker compose -f docker-compose.traefik.yml up -d

# 3. 然后启动应用服务
docker compose up -d
```

**环境变量要求**：
- `DOMAIN`：你的域名
- `EMAIL`：Let's Encrypt 证书邮箱
- `USERNAME`：Dashboard 用户名
- `HASHED_PASSWORD`：Dashboard 密码哈希

---

## Docker Compose 文件使用场景对比

### 场景一：本地开发（默认）

**使用的文件**：
- `docker-compose.yml`（主配置）
- `docker-compose.override.yml`（自动应用）

**命令**：
```bash
docker compose watch
# 或
docker compose up -d
```

**特点**：
- ✅ 自动加载覆盖配置
- ✅ 端口映射到 localhost（可直接访问）
- ✅ 代码热重载（后端）
- ✅ 包含开发工具（mailcatcher、playwright）
- ✅ 本地 Traefik 代理（可选，用于测试子域名）
- ⚠️ **前端不在 Docker 中运行**：前端配置已被注释，需要使用本地开发服务器

**访问地址**：
- 前端：http://localhost:5173（通过本地 `npm run dev` 启动）
- 后端：http://localhost:8000
- Adminer：http://localhost:8081（端口已改为 8081，避免与 EDB PEM 冲突）
- Traefik Dashboard：http://localhost:8090
- MailCatcher：http://localhost:1080

### 场景二：仅使用主配置（不使用覆盖配置）

**使用的文件**：
- `docker-compose.yml`（仅主配置）

**命令**：
```bash
docker compose -f docker-compose.yml up -d
```

**特点**：
- ⚠️ 需要外部 Traefik 网络
- ⚠️ 服务通过子域名访问（需要配置 DNS）
- ⚠️ 无端口映射到 localhost
- ⚠️ 无代码热重载

**适用场景**：
- 测试生产环境配置
- 已有 Traefik 实例

### 场景三：生产环境（使用独立 Traefik）

**使用的文件**：
- `docker-compose.traefik.yml`（先启动 Traefik）
- `docker-compose.yml`（然后启动应用）

**步骤**：

1. **创建网络**：
```bash
docker network create traefik-public
```

2. **配置环境变量**：
```bash
export DOMAIN=your-domain.com
export EMAIL=your-email@example.com
export USERNAME=admin
# 生成密码哈希（Linux/Mac）
export HASHED_PASSWORD=$(echo $(htpasswd -nb admin your-password) | sed -e s/\\$/\\$\\$/g)
# Windows PowerShell
$password = "your-password"
$hashed = docker run --rm httpd:2.4-alpine htpasswd -nb admin $password
$env:HASHED_PASSWORD = $hashed.Replace('$', '$$')
```

3. **启动 Traefik**：
```bash
docker compose -f docker-compose.traefik.yml up -d
```

4. **启动应用**：
```bash
docker compose up -d
```

**特点**：
- ✅ 自动 HTTPS 证书（Let's Encrypt）
- ✅ HTTP 自动重定向到 HTTPS
- ✅ Traefik Dashboard 受密码保护
- ✅ 生产就绪配置

**访问地址**：
- 前端：https://dashboard.your-domain.com
- 后端：https://api.your-domain.com
- Adminer：https://adminer.your-domain.com
- Traefik Dashboard：https://traefik.your-domain.com

### 文件加载顺序

Docker Compose 按以下顺序加载配置文件：

1. `docker-compose.yml`（基础配置）
2. `docker-compose.override.yml`（自动应用，覆盖基础配置）

**注意**：
- `docker-compose.override.yml` 会被**自动**加载，无需指定
- `docker-compose.traefik.yml` 需要**手动**指定 `-f` 参数

### 为什么 override 会自动合并，而 traefik 不会？

这是 **Docker Compose 的设计约定**，不是配置文件决定的：

#### 1. `docker-compose.override.yml` 的特殊地位

**原因**：这是 Docker Compose 的**约定文件名**（Convention over Configuration）

- Docker Compose 会自动查找并加载 `docker-compose.override.yml`
- 这是 Docker Compose 的**内置行为**，无需配置
- 设计目的：方便开发环境覆盖生产配置

**工作原理**：
```bash
# 当你运行
docker compose up -d

# Docker Compose 内部实际执行（概念上）
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

**官方文档说明**：
> Docker Compose automatically uses two compose files: `docker-compose.yml` and `docker-compose.override.yml`. The `override` file is automatically applied if it exists.

#### 2. `docker-compose.traefik.yml` 需要手动指定

**原因**：这不是约定文件名，只是普通的自定义文件名

- Docker Compose 不会自动加载它
- 必须使用 `-f` 参数显式指定
- 设计目的：提供灵活性，让用户控制何时加载哪些配置

**工作原理**：
```bash
# 必须显式指定
docker compose -f docker-compose.traefik.yml up -d

# 如果不指定，Docker Compose 不会加载它
docker compose up -d  # ❌ 不会加载 traefik.yml
```

#### 3. 使用 `-f` 参数时的行为变化

**重要**：当你使用 `-f` 参数时，Docker Compose 的自动行为会改变！

```bash
# 情况 1：不使用 -f（默认行为）
docker compose up -d
# ✅ 自动加载：docker-compose.yml + docker-compose.override.yml

# 情况 2：使用 -f 指定主文件
docker compose -f docker-compose.yml up -d
# ⚠️ 只加载：docker-compose.yml（不会自动加载 override！）

# 情况 3：使用 -f 指定其他文件
docker compose -f docker-compose.traefik.yml up -d
# ⚠️ 只加载：docker-compose.traefik.yml（不会自动加载其他文件！）

# 情况 4：显式指定多个文件
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
# ✅ 加载：docker-compose.yml + docker-compose.override.yml（手动指定）
```

**规则总结**：
- ✅ **不使用 `-f`**：自动加载 `docker-compose.yml` + `docker-compose.override.yml`
- ⚠️ **使用 `-f`**：只加载指定的文件，**不会**自动加载 `override` 文件
- ✅ **需要多个文件**：使用多个 `-f` 参数显式指定

#### 4. 实际应用示例

**示例 1：本地开发（使用自动加载）**
```bash
# 自动加载 override，获得开发配置
docker compose up -d
```

**示例 2：测试生产配置（禁用 override）**
```bash
# 只加载主配置，忽略 override
docker compose -f docker-compose.yml up -d
```

**示例 3：启动 Traefik（独立服务）**
```bash
# 只加载 Traefik 配置
docker compose -f docker-compose.traefik.yml up -d
```

**示例 4：同时使用多个文件**
```bash
# 手动指定多个文件
docker compose -f docker-compose.yml -f docker-compose.traefik.yml up -d
```

#### 5. 为什么这样设计？

**设计理念**：
1. **约定优于配置**：`override` 文件遵循约定，自动加载，简化开发
2. **灵活性**：其他文件需要手动指定，给用户完全控制权
3. **明确性**：使用 `-f` 时，行为明确，不会有意外的自动加载

**好处**：
- 开发环境：自动获得开发配置（端口映射、热重载等）
- 生产环境：可以精确控制加载哪些配置
- 测试环境：可以禁用开发配置，测试生产行为

---

## Docker 镜像名称说明

### 构建的镜像

项目会构建以下自定义镜像：

| 镜像名称 | 标签 | 说明 | 构建来源 |
|---------|------|------|---------|
| `biz-platform-backend` | `latest` | FastAPI 后端镜像 | `backend/Dockerfile` |
| `biz-platform-frontend` | `latest` | React 前端镜像 | `frontend/Dockerfile` |
| `biz-platform-playwright` | `latest` | Playwright 测试镜像 | `frontend/Dockerfile.playwright` |

### 镜像命名规则

镜像名称由以下环境变量控制（在 `.env` 文件中）：

```env
# Docker 镜像配置
DOCKER_IMAGE_BACKEND=biz-platform-backend
DOCKER_IMAGE_FRONTEND=biz-platform-frontend
```

**实际镜像名称**：
- 后端：`${DOCKER_IMAGE_BACKEND}:${TAG-latest}` → `biz-platform-backend:latest`
- 前端：`${DOCKER_IMAGE_FRONTEND}:${TAG-latest}` → `biz-platform-frontend:latest`
- Playwright：`${项目目录名}-playwright:latest` → `biz-platform-playwright:latest`

**统一命名规则**：
所有自定义镜像都使用 `biz-platform-` 前缀，保持命名一致性。

### 为什么 Playwright 有 `biz-platform` 前缀？

**原因**：Docker Compose 的镜像命名规则不同

#### Backend 和 Frontend 的命名

在 `docker-compose.yml` 中，backend 和 frontend **明确指定了镜像名称**：

```yaml
backend:
  image: '${DOCKER_IMAGE_BACKEND}:${TAG-latest}'  # 明确指定
  # ...

frontend:
  image: '${DOCKER_IMAGE_FRONTEND}:${TAG-latest}'  # 明确指定
  # ...
```

镜像名称由环境变量 `DOCKER_IMAGE_BACKEND` 和 `DOCKER_IMAGE_FRONTEND` 控制，默认值为 `biz-platform-backend` 和 `biz-platform-frontend`，与 Playwright 保持一致的命名风格。

#### Playwright 的命名

在 `docker-compose.override.yml` 中，playwright 服务**没有指定 `image`**，只有 `build`：

```yaml
playwright:
  build:
    context: ./frontend
    dockerfile: Dockerfile.playwright
  # 没有 image: 字段
```

**Docker Compose 规则**：
- 当服务**没有指定 `image`** 时，Docker Compose 会自动生成镜像名
- 命名格式：`${项目目录名}-${服务名}:latest`
- 项目目录名是 `biz-platform`，服务名是 `playwright`
- 所以镜像名是：`biz-platform-playwright:latest`

**如何自定义 Playwright 镜像名**：

如果想自定义，可以在 `docker-compose.override.yml` 中添加：

```yaml
playwright:
  image: 'biz-platform-playwright:latest'  # 添加这行，保持命名一致性
  build:
    context: ./frontend
    dockerfile: Dockerfile.playwright
```

**注意**：建议保持 `biz-platform-` 前缀，以保持所有镜像命名的一致性。

### 什么是 Playwright？

**Playwright** 是一个现代化的**端到端（E2E）测试框架**，用于自动化浏览器测试。

#### 主要功能

1. **自动化浏览器操作**：
   - 模拟用户点击、输入、导航等操作
   - 支持 Chrome、Firefox、Safari 等浏览器
   - 支持移动端浏览器测试

2. **端到端测试**：
   - 测试完整的用户流程（登录、注册、操作等）
   - 验证前端功能是否正常工作
   - 测试前后端集成

3. **测试报告**：
   - 生成 HTML 测试报告
   - 截图和视频录制
   - 详细的错误信息

#### 项目中的使用

**测试文件位置**：`frontend/tests/`

- `login.spec.ts` - 登录功能测试
- `sign-up.spec.ts` - 注册功能测试
- `reset-password.spec.ts` - 密码重置测试
- `user-settings.spec.ts` - 用户设置测试
- `auth.setup.ts` - 认证设置

**运行测试**：

```bash
# 本地运行（需要先启动服务）
cd frontend
npx playwright test

# 在 Docker 中运行
docker compose run playwright npx playwright test

# 查看测试报告
npx playwright show-report
```

**为什么需要单独的 Docker 镜像？**

1. **包含浏览器**：Playwright 需要安装浏览器（Chromium、Firefox 等），镜像大小约 4.5GB
2. **独立环境**：测试环境与开发/生产环境隔离
3. **CI/CD 集成**：可以在 CI/CD 流水线中自动运行测试

**镜像特点**：
- 基于 `mcr.microsoft.com/playwright:v1.55.0-noble`
- 包含所有浏览器和测试工具
- 配置了测试环境变量
- 挂载测试结果目录

**标签（TAG）**：
- 默认：`latest`
- 可通过环境变量 `TAG` 设置，例如：`TAG=v1.0.0`

### 使用的官方镜像

项目还使用以下官方镜像（不构建）：

| 镜像名称 | 标签 | 用途 |
|---------|------|------|
| `postgres` | `17` | PostgreSQL 数据库 |
| `adminer` | `latest` | 数据库管理工具 |
| `traefik` | `3.0` | 反向代理（开发/生产） |
| `schickling/mailcatcher` | `latest` | 邮件测试工具（仅开发） |

### 查看镜像

```bash
# 查看所有镜像
docker images

# 查看项目相关镜像
docker images | grep -E "biz-platform"

# 查看特定镜像
docker images biz-platform-backend
docker images biz-platform-frontend
docker images biz-platform-playwright
```

### 镜像构建

镜像在以下情况会自动构建：

1. **首次启动**：
   ```bash
   docker compose up -d
   # 会自动构建 backend 和 frontend 镜像
   ```

2. **强制重新构建**：
   ```bash
   docker compose build
   # 或指定服务
   docker compose build backend
   docker compose build frontend
   ```

3. **不缓存构建**：
   ```bash
   docker compose build --no-cache
   ```

### 自定义镜像名称

如果需要使用自定义镜像名称（例如推送到 Docker Registry）：

1. **修改 `.env` 文件**：
   ```env
   DOCKER_IMAGE_BACKEND=your-registry/biz-platform-backend
   DOCKER_IMAGE_FRONTEND=your-registry/biz-platform-frontend
   TAG=v1.0.0
   ```

2. **构建并标记**：
   ```bash
   docker compose build
   docker tag biz-platform-backend:latest your-registry/biz-platform-backend:v1.0.0
   docker tag biz-platform-frontend:latest your-registry/biz-platform-frontend:v1.0.0
   ```

3. **推送到 Registry**：
   ```bash
   docker push your-registry/biz-platform-backend:v1.0.0
   docker push your-registry/biz-platform-frontend:v1.0.0
   ```

### 镜像大小参考

根据实际构建，镜像大小约为：

- `biz-platform-backend:latest`：约 2GB（包含 Python 环境和所有依赖）
- `biz-platform-frontend:latest`：约 226MB（基于 Nginx，包含编译后的前端）
- `biz-platform-playwright:latest`：约 4.5GB（包含浏览器和测试工具）

---

## 启动服务

### 方式一：使用 Docker Compose Watch（推荐）

```bash
cd biz-platform
docker compose watch
```

**特点**：
- 自动检测代码变化并重新加载
- 适合开发环境
- 自动启动所有服务

### 方式二：使用 Docker Compose Up

```bash
cd biz-platform
docker compose up -d
```

**查看日志**：
```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs backend
docker compose logs frontend

# 实时跟踪日志
docker compose logs -f backend
```

### 方式三：仅启动特定服务

```bash
# 只启动数据库和后端
docker compose up -d db backend

# 只启动数据库
docker compose up -d db
```

---

## 开发模式

### 本地开发工作流

Docker Compose 配置允许混合使用 Docker 和本地开发服务器：

#### 1. 后端本地开发

停止 Docker 中的后端服务：
```bash
docker compose stop backend
```

启动本地后端开发服务器：
```bash
cd backend
# 使用 uv（推荐）
uv sync
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows
fastapi dev app/main.py

# 或使用 uvicorn
uvicorn app.main:app --reload
```

后端将在 `http://localhost:8000` 运行。

#### 2. 前端本地开发（推荐方式）

⚠️ **注意**：`docker-compose.override.yml` 中的前端配置已被注释，前端不再通过 Docker 运行。

**推荐使用本地开发服务器**：

**方式一：使用启动脚本（推荐）**
```bash
# 从项目根目录运行
scripts\dev-start-frontend.bat
```

**方式二：手动启动**
```bash
cd frontend
npm install  # 首次运行需要安装依赖
npm run dev
```

前端将在 `http://localhost:5173` 运行，支持热更新。

**优势**：
- ✅ 更快的启动速度
- ✅ 更好的热更新体验（Vite HMR）
- ✅ 更接近生产环境的开发体验
- ✅ 无需重新构建 Docker 镜像

**如果需要使用 Docker 运行前端**：
如果需要测试 Docker 中的前端，可以取消注释 `docker-compose.override.yml` 中的前端配置，然后运行：
```bash
docker compose up -d frontend
```

### 访问地址

启动后，可以通过以下地址访问服务：

| 服务 | 地址 | 说明 |
| --- | --- | --- |
| 前端 | <http://localhost:5173> | Web 管理后台（通过本地 `npm run dev` 启动） |
| 后端 API | <http://localhost:8000> | FastAPI 后端 |
| API 文档 | <http://localhost:8000/docs> | Swagger UI |
| API 文档（ReDoc） | <http://localhost:8000/redoc> | ReDoc |
| Adminer | <http://localhost:8081> | 数据库管理（端口已改为 8081） |
| Traefik Dashboard | <http://localhost:8090> | Traefik 管理界面 |
| MailCatcher | <http://localhost:1080> | 邮件测试工具 |

### 使用 localhost.tiangolo.com 域名

如果想测试子域名路由（模拟生产环境）：

1. 修改 `.env` 文件：

   ```env
   DOMAIN=localhost.tiangolo.com
   ```

2. 重启服务：

   ```bash
   docker compose watch
   ```

3. 访问地址：

   - 前端：<http://localhost:5173>（通过本地 `npm run dev` 启动，不支持子域名）
   - 后端：<http://api.localhost.tiangolo.com>
   - Adminer：<http://adminer.localhost.tiangolo.com>

**注意**：
- `localhost.tiangolo.com` 是一个特殊域名，所有子域名都指向 `127.0.0.1`
- ⚠️ 前端不在 Docker 中运行，因此不支持通过 Traefik 子域名访问，只能通过 `http://localhost:5173` 访问

---

## 生产环境部署

### 1. 配置环境变量

修改 `.env` 文件中的生产环境配置：

```env
ENVIRONMENT=production
DOMAIN=your-domain.com
FRONTEND_HOST=https://dashboard.your-domain.com

# 生成新的密钥
SECRET_KEY=your_production_secret_key

# 配置数据库
POSTGRES_SERVER=db
POSTGRES_PASSWORD=strong_production_password

# 配置邮件
SMTP_HOST=smtp.your-domain.com
SMTP_USER=noreply@your-domain.com
SMTP_PASSWORD=your_smtp_password
EMAILS_FROM_EMAIL=noreply@your-domain.com

# 配置 Traefik（可选）
USERNAME=admin
HASHED_PASSWORD=$2y$10$...  # 使用 htpasswd 生成
EMAIL=your-email@example.com
```

### 2. 创建 Traefik 网络

```bash
docker network create traefik-public
```

### 3. 启动 Traefik（如果使用独立 Traefik）

```bash
docker compose -f docker-compose.traefik.yml up -d
```

### 4. 启动应用服务

```bash
docker compose up -d
```

### 5. 构建和推送镜像（可选）

```bash
# 构建镜像
docker compose build

# 标记镜像
docker tag biz-platform-backend:latest your-registry/biz-platform-backend:latest
docker tag biz-platform-frontend:latest your-registry/biz-platform-frontend:latest

# 推送镜像
docker push your-registry/biz-platform-backend:latest
docker push your-registry/biz-platform-frontend:latest
```

---

## 常见问题

### 1. 端口被占用

**问题**：端口 8000、5173、5432 等已被占用

**解决**：

- 修改 `docker-compose.override.yml` 中的端口映射
- 或停止占用端口的服务

### 2. 数据库连接失败

**问题**：后端无法连接到数据库

**解决**：

1. 检查数据库服务是否启动：`docker compose ps`
2. 检查 `.env` 中的数据库配置
3. 检查数据库日志：`docker compose logs db`
4. 确保 `POSTGRES_SERVER=db`（Docker 内部）或 `POSTGRES_SERVER=localhost`（本地开发）

### 3. 环境变量未生效

**问题**：修改 `.env` 后配置未生效

**解决**：

1. 重启服务：`docker compose restart`
2. 或完全重启：`docker compose down && docker compose up -d`
3. 检查 `.env` 文件格式（无多余空格，正确引号）

### 4. 权限问题（Linux）

**问题**：Docker 权限错误

**解决**：

```bash
# 将用户添加到 docker 组
sudo usermod -aG docker $USER
# 重新登录或执行
newgrp docker
```

### 5. 数据库迁移失败

**问题**：prestart 服务失败

**解决**：

1. 检查数据库是否就绪：`docker compose logs db`
2. 手动运行迁移：

   ```bash
   docker compose exec backend alembic upgrade head
   ```

### 6. 前端相关问题

**问题一**：前端 Docker 镜像构建失败

**解决**：

1. 检查 Node.js 版本兼容性
2. 清理构建缓存：`docker compose build --no-cache frontend`
3. 检查 `frontend/package.json` 依赖

**问题二**：前端服务未运行

**说明**：`docker-compose.override.yml` 中的前端配置已被注释，前端不再通过 Docker 运行。

**推荐解决方式**：
1. 使用本地开发服务器：运行 `scripts/dev-start-frontend.bat` 或在 `frontend` 目录执行 `npm run dev`
2. 如果需要使用 Docker 运行前端，可以取消注释 `docker-compose.override.yml` 中的前端配置

**问题三**：前端无法访问

**检查步骤**：
1. 确认前端开发服务器已启动：`npm run dev`
2. 检查端口 5173 是否被占用
3. 检查浏览器控制台是否有错误
4. 确认后端服务正在运行（前端需要连接后端 API）

### 7. Traefik 路由不工作

**问题**：无法通过子域名访问服务

**解决**：

1. 检查 Traefik 网络：`docker network ls | grep traefik-public`
2. 检查服务标签配置
3. 查看 Traefik 日志：`docker compose logs proxy` 或 `docker compose logs traefik`

### 8. 邮件功能不工作

**问题**：邮件发送失败

**解决**：

1. 开发环境使用 MailCatcher：<http://localhost:1080>
2. 检查 SMTP 配置是否正确
3. 检查防火墙和网络设置

### 9. Docker 卷相关问题

**问题一**：出现匿名卷（哈希名称的卷）

**说明**：项目已使用命名卷替代匿名卷，如果看到类似 `5fa54c6b5d3fb6f0a5df0f3910316bc513e588109cf467cd4e58711963f0fc5b` 的匿名卷，可能是旧配置遗留的。

**解决**：
1. 停止所有服务：`docker compose down`
2. 删除未使用的匿名卷：`docker volume prune`
3. 重新启动服务：`docker compose up -d`

**问题二**：数据库卷大小为 0

**说明**：新创建的数据库卷大小为 0 是正常的，数据库初始化后会有数据。

**检查**：
```bash
# 查看数据库日志，确认初始化完成
docker compose logs db
docker compose logs prestart

# 检查数据库是否正常运行
docker compose exec db psql -U postgres -d app -c "\dt"
```

**问题三**：卷占用空间过大

**解决**：
```bash
# 查看卷大小
docker system df -v

# 清理未使用的卷（⚠️ 会删除数据）
docker volume prune

# 清理特定卷（⚠️ 会删除数据）
docker volume rm biz-platform_backend-venv
```

---

## 服务管理命令

### 启动/停止/重启

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 停止并删除卷（⚠️ 会删除数据库数据）
docker compose down -v

# 重启特定服务
docker compose restart backend

# 重启所有服务
docker compose restart
```

### 查看状态

```bash
# 查看服务状态
docker compose ps

# 查看资源使用
docker stats

# 查看服务日志
docker compose logs -f [service_name]
```

### 进入容器

```bash
# 进入后端容器
docker compose exec backend bash

# 进入数据库容器
docker compose exec db psql -U postgres -d app

# 进入前端容器（如果前端在 Docker 中运行）
# ⚠️ 注意：前端配置已被注释，通常前端不在 Docker 中运行
# 如果需要进入前端容器，需要先取消注释 docker-compose.override.yml 中的前端配置
docker compose exec frontend sh
```

### 清理

```bash
# 停止并删除容器、网络
docker compose down

# 删除未使用的镜像
docker image prune

# 删除未使用的卷（⚠️ 谨慎使用）
docker volume prune

# 完全清理（⚠️ 会删除所有未使用的资源）
docker system prune -a
```

### 卷管理

项目使用以下命名卷：

| 卷名称 | 用途 | 挂载位置 | 说明 |
|--------|------|----------|------|
| `biz-platform_app-db-data` | 数据库数据 | `/var/lib/postgresql/data` | PostgreSQL 数据持久化 |
| `biz-platform_backend-venv` | 后端虚拟环境 | `/app/.venv` | Python 虚拟环境隔离（开发环境） |

**查看卷**：
```bash
# 查看所有卷
docker volume ls

# 查看项目相关卷
docker volume ls | grep biz-platform

# 查看卷详细信息
docker volume inspect biz-platform_app-db-data
docker volume inspect biz-platform_backend-venv
```

**删除卷**（⚠️ 谨慎操作）：
```bash
# 删除特定卷（会删除数据）
docker volume rm biz-platform_app-db-data
docker volume rm biz-platform_backend-venv

# 停止服务并删除所有卷
docker compose down -v
```

**卷命名规则**：
- Docker Compose 会自动为卷添加项目前缀
- 格式：`${项目目录名}_${卷名}`
- 例如：`biz-platform_app-db-data`、`biz-platform_backend-venv`

**为什么使用命名卷而不是匿名卷？**
- ✅ **易于识别**：命名卷名称清晰，便于管理
- ✅ **便于清理**：可以精确删除特定卷
- ✅ **避免混乱**：不会产生难以识别的匿名卷（如哈希名称）
- ✅ **持久化**：数据会保留在命名卷中，容器删除后数据不丢失

---

## 环境变量参考

详细的环境变量说明请参考：
- [环境变量配置说明](../biz-platform/docs/环境变量配置说明.md)
- [.env.example](../biz-platform/.env.example)

---

## 相关文档

- [开发文档](../biz-platform/development.md)
- [部署文档](../biz-platform/deployment.md)
- [架构设计](./架构设计.md)
- [业务需求](./业务需求.md)

---

---

## Docker 卷配置说明

### 命名卷 vs 匿名卷

项目使用**命名卷**而不是匿名卷，原因如下：

#### 命名卷的优势

1. **易于识别**：
   - 命名卷：`biz-platform_app-db-data`、`biz-platform_backend-venv`
   - 匿名卷：`5fa54c6b5d3fb6f0a5df0f3910316bc513e588109cf467cd4e58711963f0fc5b`

2. **便于管理**：
   - 可以精确删除特定卷
   - 可以备份和恢复特定卷
   - 不会产生难以识别的卷

3. **避免混乱**：
   - 所有卷都有清晰的命名
   - 不会在卷列表中看到大量匿名卷

#### 项目中的卷配置

**数据库卷**（`app-db-data`）：
```yaml
# docker-compose.yml
volumes:
  app-db-data:  # 命名卷定义

services:
  db:
    volumes:
      - app-db-data:/var/lib/postgresql/data  # 使用命名卷
```

**后端虚拟环境卷**（`backend-venv`）：
```yaml
# docker-compose.override.yml
volumes:
  backend-venv:  # 命名卷定义

services:
  backend:
    volumes:
      - backend-venv:/app/.venv  # 使用命名卷，替代匿名卷 /app/.venv
```

#### 从匿名卷迁移到命名卷

如果之前使用了匿名卷，迁移步骤：

1. **停止服务**：
   ```bash
   docker compose down
   ```

2. **清理旧卷**（可选）：
   ```bash
   # 查看所有卷
   docker volume ls
   
   # 删除未使用的匿名卷
   docker volume prune
   ```

3. **重新启动**：
   ```bash
   docker compose up -d
   ```

4. **验证**：
   ```bash
   # 应该看到命名卷，而不是匿名卷
   docker volume ls | grep biz-platform
   ```

---

**最后更新**：2026-01-01  
**版本**：1.1.0
