# 北航智能日历系统 - 详细安装指南

本指南将帮助用户完成北航智能日历系统的安装和配置，从环境搭建到应用启动，包含所有必要的步骤和常见问题解决方案。

## 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
   - [1. 安装Node.js](#1-安装nodejs)
   - [2. 安装Python](#2-安装python)
   - [3. 克隆项目代码](#3-克隆项目代码)
   - [4. 配置后端环境](#4-配置后端环境)
   - [5. 配置前端环境](#5-配置前端环境)
   - [6. 启动应用](#6-启动应用)
3. [EasyOCR 安装指南](#easyocr-安装指南)
   - [自动安装](#自动安装)
   - [手动安装（推荐）](#手动安装推荐)
   - [跳过OCR功能](#跳过ocr功能)
   - [替代方案](#替代方案)
4. [常见问题与解决方案](#常见问题与解决方案)
5. [测试应用](#测试应用)

## 系统要求

| 组件      | 版本要求                                  | 用途          |
| ------- | ------------------------------------- | ----------- |
| Node.js | 16.x 或更高                              | 前端开发环境      |
| Python  | 3.8 或更高                               | 后端开发环境      |
| npm     | 8.x 或更高                               | Node.js 包管理 |
| pip     | 20.x 或更高                              | Python 包管理  |
| 浏览器     | Chrome 90+ / Firefox 88+ / Safari 14+ | 运行前端应用      |

## 安装步骤

### 1. 安装Node.js

#### Windows系统

1. 访问 [Node.js 官方网站](https://nodejs.org/zh-cn/)
2. 下载 LTS 版本（长期支持版）的 Node.js 安装包
3. 双击安装包，按照默认选项完成安装
4. 验证安装：
   - 打开命令提示符（Win + R → 输入 `cmd` → 回车）
   - 输入 `node -v`，显示版本号则安装成功
   - 输入 `npm -v`，显示版本号则安装成功

#### macOS系统

1. 访问 [Node.js 官方网站](https://nodejs.org/zh-cn/)
2. 下载 LTS 版本的 Node.js 安装包
3. 双击安装包，按照默认选项完成安装
4. 验证安装：
   - 打开终端（Launchpad → 其他 → 终端）
   - 输入 `node -v` 和 `npm -v`，显示版本号则安装成功

#### Linux系统（Ubuntu/Debian）

```bash
# 使用NodeSource安装（推荐）
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证安装
node -v
npm -v
```

### 2. 安装Python

#### Windows系统

1. 访问 [Python 官方网站](https://www.python.org/downloads/windows/)
2. 下载 **最新稳定版** Python 安装包
3. 双击安装包，**务必勾选** "Add Python to PATH" 选项
4. 点击 "Install Now"，等待安装完成
5. 验证安装：
   - 打开命令提示符
   - 输入 `python --version`，显示版本号则安装成功
   - 输入 `pip --version`，显示版本号则安装成功

#### macOS系统

1. 访问 [Python 官方网站](https://www.python.org/downloads/macos/)
2. 下载 macOS 安装包
3. 双击安装包，按照默认选项完成安装
4. 验证安装：
   - 打开终端
   - 输入 `python3 --version` 和 `pip3 --version`

#### Linux系统（Ubuntu/Debian）

```bash
# 安装Python 3.10
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# 验证安装
python3 --version
pip3 --version
```

### 3. 克隆项目代码

#### 使用Git克隆（推荐）

1. 安装Git（如果未安装）：
   
   - Windows：访问 [Git官网](https://git-scm.com/downloads) 下载安装
   - macOS：`brew install git` 或从官网下载
   - Linux：`sudo apt install git`

2. 克隆项目：

```bash
git clone https://github.com/your-username/intelligent-calendar-for-BUAAer.git
cd intelligent-calendar-for-BUAAer
```

#### 直接下载ZIP文件

1. 访问项目GitHub页面
2. 点击 "Code" 按钮，选择 "Download ZIP"
3. 解压下载的ZIP文件
4. 进入解压后的目录

### 4. 配置后端环境

#### 创建虚拟环境（推荐）

```bash
# 在项目根目录下创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
env\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 配置环境变量

1. 在 `backend` 目录下创建 `.env` 文件：

```bash
# 进入backend目录
cd backend

# 创建.env文件（Windows）
type nul > .env

# 或使用文本编辑器创建
notepad .env
```

2. 添加以下内容到 `.env` 文件：

```
# 数据库配置（默认使用SQLite，无需修改）
DATABASE_URL=sqlite:///instance/app.db

# 应用密钥（用于加密会话数据）
SECRET_KEY=your-secret-key-here

# 大语言模型API配置（可选，可后续在前端设置）
LLM_API_KEY=your-api-key-here
LLM_API_URL=https://api.qwen.com/v1/chat/completions
```

### 5. 配置前端环境

```bash
cd frontend
npm install
```

### 6. 启动应用

#### 启动后端服务

```bash
# 在backend目录下
cd backend
python app.py
```

后端服务将在 `http://localhost:5000` 启动。

#### 启动前端服务

```bash
# 在frontend目录下
cd frontend
npm run dev
```

前端应用将在 `http://localhost:3000` 启动。

## EasyOCR 安装指南

### 自动安装

EasyOCR 会在应用首次启动时自动下载模型，但由于网络原因，可能会失败。

### 手动安装（推荐）

如果自动安装失败，推荐手动安装 EasyOCR 模型：

#### Windows系统

1. 下载模型文件：
   
   - [detector.tar.gz](https://www.jaided.ai/easyocr/model/detector.tar.gz)
   - [zh_sim_g2.zip](https://www.jaided.ai/easyocr/model/zh_sim_g2.zip)
   - [en_g2.zip](https://www.jaided.ai/easyocr/model/en_g2.zip)

2. 解压模型文件：
   
   - 创建目录：`C:\Users\你的用户名\.EasyOCR\model\`
   - 将下载的模型文件解压到该目录

#### macOS/Linux系统

1. 下载模型文件：

```bash
mkdir -p ~/.EasyOCR/model
cd ~/.EasyOCR/model

curl -O https://www.jaided.ai/easyocr/model/detector.tar.gz
curl -O https://www.jaided.ai/easyocr/model/zh_sim_g2.zip
curl -O https://www.jaided.ai/easyocr/model/en_g2.zip
```

2. 解压模型文件：

```bash
tar -xzf detector.tar.gz
unzip zh_sim_g2.zip
unzip en_g2.zip
```

### 跳过OCR功能

如果不需要图片识别功能，可以跳过 EasyOCR 安装：

1. 打开 `backend/routes/llm.py` 文件
2. 注释掉以下代码：

```python
# reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
```

### 替代方案

如果 EasyOCR 安装失败，可以考虑使用以下替代方案：

#### 1. 使用PaddleOCR

```bash
# 安装PaddleOCR
pip install paddlepaddle paddleocr
```

然后修改 `backend/routes/llm.py` 中的OCR相关代码，替换为PaddleOCR实现。

#### 2. 使用在线OCR服务

考虑使用百度OCR API、腾讯OCR API等在线服务，这些服务无需本地模型，直接通过API调用。

## 常见问题与解决方案

### 1. Node.js 安装失败

**问题**：安装Node.js时出现权限错误或版本不兼容

**解决方案**：

- 确保以管理员身份运行安装程序
- 尝试安装旧版本Node.js（如16.x）
- 检查系统是否满足最低要求

### 2. Python 依赖安装失败

**问题**：`pip install -r requirements.txt` 失败

**解决方案**：

- 升级pip：`pip install --upgrade pip`
- 使用国内镜像源：
  
  ```bash
  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
  ```
- 单独安装失败的包：
  
  ```bash
  pip install problematic-package
  ```

### 3. EasyOCR 模型下载超时

**解决方案**：

- 使用手动安装方法（推荐）
- 检查网络连接
- 尝试使用VPN或代理

### 4. 端口被占用

**问题**：启动服务时提示端口已被占用

**解决方案**：

- 查找占用端口的进程并关闭
  
  ```bash
  # Windows
  netstat -ano | findstr :5000
  taskkill /PID <进程ID> /F
  
  # macOS/Linux
  lsof -i :5000
  kill -9 <进程ID>
  ```

- 修改服务端口：
  
  - 后端：修改 `backend/app.py` 中的端口号
  - 前端：修改 `frontend/vite.config.js` 中的端口号

## 测试应用

1. 确保后端服务运行在 `http://localhost:5000`
2. 确保前端服务运行在 `http://localhost:3000`
3. 打开浏览器访问 `http://localhost:3000`
4. 应用应该正常加载，显示登录/注册页面
5. 尝试添加一个简单的事件，验证功能是否正常

## 下一步

恭喜！你已经成功安装了北航智能日历系统。现在你可以：

1. 在设置中配置大语言模型API密钥
2. 导入你的北航课程表
3. 开始使用智能日历管理你的时间和任务
4. 点击右上角"在手机打开"按钮，获取手机访问地址和二维码，在手机上使用日历功能

---

**祝你使用愉快！** 