# FastAPI Project - 开发

## Docker Compose

* 使用 Docker Compose 启动本地堆栈：

```bash
docker compose watch
```

* 现在你可以打开浏览器并访问以下 URL：

使用 Docker 构建的前端，根据路径处理路由：<http://localhost:5173>

后端，基于 OpenAPI 的 JSON Web API：<http://localhost:8000>

自动交互式文档，使用 Swagger UI（来自 OpenAPI 后端）：<http://localhost:8000/docs>

Adminer，数据库 Web 管理：<http://localhost:8080>

Traefik UI，查看代理如何处理路由：<http://localhost:8090>

**注意**：第一次启动堆栈时，可能需要一分钟才能准备就绪。后端会等待数据库准备就绪并配置所有内容。你可以查看日志以监控它。

要检查日志，请运行（在另一个终端中）：

```bash
docker compose logs
```

要检查特定服务的日志，请添加服务名称，例如：

```bash
docker compose logs backend
```

## Mailcatcher

Mailcatcher 是一个简单的 SMTP 服务器，它捕获后端在本地开发期间发送的所有电子邮件。它不会发送真实电子邮件，而是捕获并在 Web 界面中显示它们。

这对于以下情况很有用：

* 在开发期间测试电子邮件功能
* 验证电子邮件内容和格式
* 在不发送真实电子邮件的情况下调试与电子邮件相关的功能

当使用 Docker Compose 在本地运行时，后端会自动配置为使用 Mailcatcher（SMTP 在端口 1025 上）。所有捕获的电子邮件都可以在 <http://localhost:1080> 查看。

## 本地开发

Docker Compose 文件配置为每个服务在 `localhost` 上使用不同的端口。

对于后端和前端，它们使用与本地开发服务器相同的端口，因此后端在 `http://localhost:8000`，前端在 `http://localhost:5173`。

这样，你可以关闭 Docker Compose 服务并启动其本地开发服务，一切都会继续工作，因为它们都使用相同的端口。

例如，你可以在 Docker Compose 中停止 `frontend` 服务，在另一个终端中运行：

```bash
docker compose stop frontend
```

然后启动本地前端开发服务器：

```bash
cd frontend
npm run dev
```

或者你可以停止 `backend` Docker Compose 服务：

```bash
docker compose stop backend
```

然后你可以运行后端的本地开发服务器：

```bash
cd backend
fastapi dev app/main.py
```

## Docker Compose 在 `localhost.tiangolo.com`

当你启动 Docker Compose 堆栈时，默认情况下它使用 `localhost`，每个服务使用不同的端口（后端、前端、adminer 等）。

当你将其部署到生产环境（或暂存环境）时，它将在不同的子域上部署每个服务，例如 `api.example.com` 用于后端，`dashboard.example.com` 用于前端。

在关于[部署](deployment.md)的指南中，你可以阅读有关 Traefik（配置的代理）的信息。这是负责根据子域将流量传输到每个服务的组件。

如果你想测试所有内容在本地是否正常工作，可以编辑本地 `.env` 文件，并更改：

```dotenv
DOMAIN=localhost.tiangolo.com
```

这将被 Docker Compose 文件用于配置服务的基础域名。

Traefik 将使用它将在 `api.localhost.tiangolo.com` 的流量传输到后端，在 `dashboard.localhost.tiangolo.com` 的流量传输到前端。

域名 `localhost.tiangolo.com` 是一个特殊域名，配置为（及其所有子域）指向 `127.0.0.1`。这样你可以将其用于本地开发。

更新后，再次运行：

```bash
docker compose watch
```

部署时，例如在生产环境中，主要的 Traefik 在 Docker Compose 文件之外配置。对于本地开发，在 `docker-compose.override.yml` 中包含一个 Traefik，只是为了让你测试域名是否按预期工作，例如使用 `api.localhost.tiangolo.com` 和 `dashboard.localhost.tiangolo.com`。

## Docker Compose 文件和环境变量

有一个主要的 `docker-compose.yml` 文件，其中包含适用于整个堆栈的所有配置，它由 `docker compose` 自动使用。

还有一个 `docker-compose.override.yml`，其中包含开发的覆盖，例如将源代码挂载为卷。它由 `docker compose` 自动使用，以在 `docker-compose.yml` 之上应用覆盖。

这些 Docker Compose 文件使用包含配置的 `.env` 文件，这些配置将作为环境变量注入到容器中。

它们还使用一些从脚本中设置的环境变量中获取的额外配置，这些环境变量在调用 `docker compose` 命令之前设置。

更改变量后，请确保重启堆栈：

```bash
docker compose watch
```

## .env 文件

`.env` 文件包含所有配置、生成的密钥和密码等。

根据你的工作流程，你可能希望将其从 Git 中排除，例如，如果你的项目是公开的。在这种情况下，你必须确保为 CI 工具设置一种方式，以便在构建或部署项目时获取它。

一种方法可能是将每个环境变量添加到你的 CI/CD 系统，并更新 `docker-compose.yml` 文件以读取该特定环境变量，而不是读取 `.env` 文件。

## Pre-commits 和代码检查

我们使用一个名为 [pre-commit](https://pre-commit.com/) 的工具进行代码检查和格式化。

当你安装它时，它会在 git 提交之前运行。这样它确保代码在提交之前是一致的和格式化的。

你可以在项目根目录找到配置文件 `.pre-commit-config.yaml`。

#### 安装 pre-commit 以自动运行

`pre-commit` 已经是项目依赖项的一部分，但如果你愿意，也可以全局安装它，遵循[官方 pre-commit 文档](https://pre-commit.com/)。

在安装 `pre-commit` 工具并可用后，你需要在本地仓库中"安装"它，以便它在每次提交之前自动运行。

使用 `uv`，你可以这样做：

```bash
❯ uv run pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

现在每当你尝试提交时，例如使用：

```bash
git commit
```

...pre-commit 将运行并检查和格式化你即将提交的代码，并要求你再次使用 git 添加该代码（暂存它）然后再提交。

然后你可以再次 `git add` 修改/修复的文件，现在你可以提交了。

#### 手动运行 pre-commit hooks

你也可以在所有文件上手动运行 `pre-commit`，你可以使用 `uv` 这样做：

```bash
❯ uv run pre-commit run --all-files
check for added large files..............................................Passed
check toml...............................................................Passed
check yaml...............................................................Passed
ruff.....................................................................Passed
ruff-format..............................................................Passed
eslint...................................................................Passed
prettier.................................................................Passed
```

## URL

生产或暂存 URL 将使用这些相同的路径，但使用你自己的域名。

### 开发 URL

开发 URL，用于本地开发。

前端：<http://localhost:5173>

后端：<http://localhost:8000>

自动交互式文档（Swagger UI）：<http://localhost:8000/docs>

自动替代文档（ReDoc）：<http://localhost:8000/redoc>

Adminer：<http://localhost:8080>

Traefik UI：<http://localhost:8090>

MailCatcher：<http://localhost:1080>

### 配置了 `localhost.tiangolo.com` 的开发 URL

开发 URL，用于本地开发。

前端：<http://dashboard.localhost.tiangolo.com>

后端：<http://api.localhost.tiangolo.com>

自动交互式文档（Swagger UI）：<http://api.localhost.tiangolo.com/docs>

自动替代文档（ReDoc）：<http://api.localhost.tiangolo.com/redoc>

Adminer：<http://localhost.tiangolo.com:8080>

Traefik UI：<http://localhost.tiangolo.com:8090>

MailCatcher：<http://localhost.tiangolo.com:1080>
