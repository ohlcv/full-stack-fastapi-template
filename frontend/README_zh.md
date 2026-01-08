# FastAPI 项目 - 前端

前端使用 [Vite](https://vitejs.dev/)、[React](https://reactjs.org/)、[TypeScript](https://www.typescriptlang.org/)、[TanStack Query](https://tanstack.com/query)、[TanStack Router](https://tanstack.com/router) 和 [Chakra UI](https://chakra-ui.com/) 构建。

## 前端开发

开始之前，请确保您的系统上安装了 Node Version Manager (nvm) 或 Fast Node Manager (fnm)。

* 要安装 fnm，请遵循[官方 fnm 指南](https://github.com/Schniz/fnm#installation)。如果您更喜欢 nvm，可以使用[官方 nvm 指南](https://github.com/nvm-sh/nvm#installing-and-updating)进行安装。

* 安装 nvm 或 fnm 后，进入 `frontend` 目录：

```bash
cd frontend
```
* 如果您的系统上未安装 `.nvmrc` 文件中指定的 Node.js 版本，您可以使用相应的命令进行安装：

```bash
# 如果使用 fnm
fnm install

# 如果使用 nvm
nvm install
```

* 安装完成后，切换到已安装的版本：

```bash
# 如果使用 fnm
fnm use

# 如果使用 nvm
nvm use
```

* 在 `frontend` 目录中，安装必要的 NPM 包：

```bash
npm install
```

* 使用以下 `npm` 脚本启动实时服务器：

```bash
npm run dev
```

* 然后在浏览器中打开 http://localhost:5173/。

请注意，此实时服务器不在 Docker 内运行，它是用于本地开发的，这是推荐的工作流程。当您对前端满意后，您可以构建前端 Docker 镜像并启动它，以在类似生产环境中进行测试。但每次更改都构建镜像不如运行带有实时重新加载的本地开发服务器那样高效。

查看 `package.json` 文件以了解其他可用选项。

### 移除前端

如果您正在开发仅 API 的应用程序并想要移除前端，可以轻松完成：

* 移除 `./frontend` 目录。

* 在 `docker-compose.yml` 文件中，移除整个 `frontend` 服务/部分。

* 在 `docker-compose.override.yml` 文件中，移除整个 `frontend` 和 `playwright` 服务/部分。

完成，您就有了一个无前端的（仅 API）应用程序。🤓

---

如果您愿意，您还可以从以下位置移除 `FRONTEND` 环境变量：

* `.env`
* `./scripts/*.sh`

但清理它们只是为了整洁，保留它们实际上不会有任何影响。

## 生成客户端

### 自动方式

* 激活后端虚拟环境。
* 从顶级项目目录运行脚本：

```bash
./scripts/generate-client.sh
```

* 提交更改。

### 手动方式

* 启动 Docker Compose 堆栈。

* 从 `http://localhost/api/v1/openapi.json` 下载 OpenAPI JSON 文件并将其复制到 `frontend` 目录根部的新文件 `openapi.json` 中。

* 要生成前端客户端，运行：

```bash
npm run generate-client
```

* 提交更改。

请注意，每次后端更改（更改 OpenAPI 模式）时，您都应该按照这些步骤再次更新前端客户端。

## 使用远程 API

如果您想要使用远程 API，您可以将环境变量 `VITE_API_URL` 设置为远程 API 的 URL。例如，您可以在 `frontend/.env` 文件中设置它：

```env
VITE_API_URL=https://api.my-domain.example.com
```

然后，当您运行前端时，它将使用该 URL 作为 API 的基础 URL。

## 代码结构

前端代码结构如下：

* `frontend/src` - 主要的前端代码。
* `frontend/src/assets` - 静态资源。
* `frontend/src/client` - 生成的 OpenAPI 客户端。
* `frontend/src/components` - 前端的不同组件。
* `frontend/src/hooks` - 自定义钩子。
* `frontend/src/routes` - 前端的不同路由，包括页面。
* `theme.tsx` - Chakra UI 自定义主题。

## 使用 Playwright 进行端到端测试

前端包含使用 Playwright 的初始端到端测试。要运行测试，您需要启动 Docker Compose 堆栈。使用以下命令启动堆栈：

```bash
docker compose up -d --wait backend
```

然后，您可以使用以下命令运行测试：

```bash
npx playwright test
```

您还可以在 UI 模式下运行测试以查看浏览器并与之交互：

```bash
npx playwright test --ui
```

要停止并移除 Docker Compose 堆栈并清理测试中创建的数据，请使用以下命令：

```bash
docker compose down -v
```

要更新测试，请导航到测试目录并根据需要修改现有测试文件或添加新文件。

有关编写和运行 Playwright 测试的更多信息，请参阅官方 [Playwright 文档](https://playwright.dev/docs/intro)。