# 北航智能日历系统

一个专为北航学生设计的智能日历系统，集成了课程管理、任务安排、智能输入和LLM辅助功能，帮助学生高效管理时间和任务。

## 项目简介

北航智能日历系统是一个全栈Web应用，旨在为北航学生提供一个集成化的时间管理平台。系统结合了传统日历功能与AI智能助手，能够自动解析任务描述、生成日程安排，并提供个性化的时间管理建议。

## 技术栈

### 后端

- **框架**: Flask 2.0+
- **数据库**: SQLAlchemy (SQLite)
- **认证**: JWT
- **LLM集成**: 支持多种大语言模型API
- **API设计**: RESTful

### 前端

- **框架**: Vue 3
- **构建工具**: Vite
- **状态管理**: Pinia
- **UI组件**: 
  - FullCalendar (日历视图)
  - Chart.js (数据可视化)
- **HTTP客户端**: Axios

## 功能特性

### 核心功能

- **课程管理**: 自动导入北航课程表，支持手动调整
- **任务管理**: 创建、编辑、删除任务，支持优先级和截止日期
- **日历视图**: 日/周/月视图切换，直观展示日程安排
- **智能输入**: 支持自然语言输入任务，自动解析时间和内容
- **LLM辅助**: 利用大语言模型生成智能日程建议
- **提醒服务**: 重要任务和事件提醒

### 高级功能

- **剪贴板队列**: 批量处理复制的任务内容
- **事件编辑**: 拖拽调整事件时间，快速编辑
- **设置面板**: 个性化配置系统参数
- **数据统计**: 任务完成情况统计和可视化

## 项目结构

```
intelligent-calendar-for-BUAAer/
├── backend/                 # 后端代码
│   ├── models/             # 数据模型
│   │   ├── course.py       # 课程模型
│   │   ├── entry.py        # 日历条目模型
│   │   ├── task.py         # 任务模型
│   │   └── user.py         # 用户模型
│   ├── routes/             # API路由
│   │   ├── auth.py         # 认证相关
│   │   ├── courses.py      # 课程管理
│   │   ├── entries.py      # 日历条目
│   │   ├── llm.py          # LLM集成
│   │   ├── schedule.py     # 日程管理
│   │   └── tasks.py        # 任务管理
│   ├── services/           # 业务逻辑
│   │   ├── buaa_api.py     # 北航API对接
│   │   ├── llm_parser.py   # LLM解析服务
│   │   ├── reminder.py     # 提醒服务
│   │   └── schedule_manager.py # 日程管理器
│   ├── utils/              # 工具函数
│   ├── app.py              # 应用入口
│   ├── config.py           # 配置文件
│   └── requirements.txt    # 依赖列表
├── frontend/               # 前端代码
│   ├── src/               # 源代码
│   │   ├── components/    # Vue组件
│   │   ├── services/      # 服务层
│   │   ├── store/         # 状态管理
│   │   ├── views/         # 页面视图
│   │   ├── App.vue        # 根组件
│   │   └── main.js        # 入口文件
│   ├── index.html         # HTML模板
│   ├── package.json       # 依赖配置
│   └── vite.config.js     # Vite配置
└── 环境配置指南.md        # 环境配置文档
```

## 环境配置

### 后端环境

1. **安装依赖**:
   
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **配置文件**:
   修改 `config.py` 文件，配置数据库连接和API密钥。
   
   **配置API_KEY**:
   
   - 阿里云百炼API_KEY获取方法：[开通服务后创建获取APIKey用于鉴权](https://help.aliyun.com/zh/model-studio/get-api-key)
   - 在 `config.py` 文件中找到 `LLM_API_KEY` 配置项，填入获取到的API_KEY
   - 确保API_KEY的归属业务空间有调用相应模型的权限

3. **初始化数据库**:
   
   ```bash
   python app.py
   ```
   
   应用启动时会自动创建数据库表。

### 前端环境

1. **安装依赖**:
   
   ```bash
   cd frontend
   npm install
   ```

2. **开发模式**:
   
   ```bash
   npm run dev
   ```
   
   前端应用将在 http://localhost:3000 启动。

3. **构建生产版本**:
   
   ```bash
   npm run build
   ```
   
   构建产物将生成在 `dist` 目录。

## 运行说明

### 开发环境

1. **启动后端服务**:
   
   ```bash
   cd backend
   python app.py
   ```
   
   后端服务将在 http://localhost:5000 启动。

2. **启动前端服务**:
   
   ```bash
   cd frontend
   npm run dev
   ```
   
   前端应用将在 http://localhost:3000 启动。

3. **访问应用**:
   在浏览器中访问 http://localhost:3000 即可使用应用。

### 生产环境

1. **构建前端**:
   
   ```bash
   cd frontend
   npm run build
   ```

2. **部署后端**:
   使用 Gunicorn 或 uWSGI 部署 Flask 应用。

3. **配置反向代理**:
   使用 Nginx 或 Apache 配置反向代理，将前端和后端服务整合。

## API文档

### 认证相关

- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/logout` - 用户登出

### 课程管理

- `GET /api/courses` - 获取课程列表
- `POST /api/courses` - 添加课程
- `PUT /api/courses/<id>` - 更新课程
- `DELETE /api/courses/<id>` - 删除课程

### 任务管理

- `GET /api/tasks` - 获取任务列表
- `POST /api/tasks` - 创建任务
- `PUT /api/tasks/<id>` - 更新任务
- `DELETE /api/tasks/<id>` - 删除任务

### 日历条目

- `GET /api/entries` - 获取日历条目
- `POST /api/entries` - 创建日历条目
- `PUT /api/entries/<id>` - 更新日历条目
- `DELETE /api/entries/<id>` - 删除日历条目

### LLM服务

- `POST /api/llm/parse` - 解析自然语言任务
- `POST /api/llm/schedule` - 生成智能日程

### 日程管理

- `GET /api/schedule` - 获取日程安排
- `POST /api/schedule/generate` - 生成日程

## 功能模块详细说明

### 1. 课程管理

- 支持从北航教务系统自动导入课程表
- 提供手动添加、编辑、删除课程的功能
- 课程自动显示在日历视图中
- 支持课程冲突检测

### 2. 任务管理

- 支持创建不同类型的任务（作业、考试、项目等）
- 任务优先级设置（高、中、低）
- 截止日期提醒
- 任务完成状态跟踪
- 任务分类和标签

### 3. 智能输入

- 支持自然语言输入任务描述
- 自动解析时间、地点、优先级等信息
- 批量处理剪贴板内容
- 智能补全和建议

### 4. LLM辅助

- 利用大语言模型生成日程安排建议
- 自动优化时间分配
- 提供个性化的学习计划
- 支持多轮对话式交互

### 5. 日历视图

- 拖拽调整事件时间
- 事件详情查看和编辑
- 支持不同类型事件的颜色区分

## 开发指南

### 代码规范

- 后端：遵循 PEP 8 规范
- 前端：遵循 Vue 3 最佳实践
- 提交信息：使用语义化提交信息

### 测试

- 后端：使用 pytest 进行单元测试
- 前端：使用 Vitest 进行组件测试
- 集成测试：使用 Postman 或 curl 进行API测试

### 开发流程

1. 创建分支：`git checkout -b feature/xxx`
2. 开发功能
3. 提交代码：`git commit -m "feat: add xxx feature"`
4. 推送分支：`git push origin feature/xxx`
5. 创建 Pull Request
6. 代码审查
7. 合并分支

## 贡献说明

欢迎各位开发者贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支
3. 提交代码
4. 运行测试
5. 创建 Pull Request

## 待完成功能

### 1. 专注模式

- 提供无干扰的专注工作环境
- 支持番茄工作法和自定义专注时长
- 专注期间屏蔽通知和干扰

### 2. 更完整的优先级系统

- 支持多维度优先级设置（紧急程度、重要程度）
- 优先级可视化展示
- 基于优先级的智能排序和提醒

### 3. 学习偏好配置

- 允许用户设置学习偏好（如最佳学习时间、科目偏好）
- 根据偏好智能推荐学习计划
- 个性化学习路径生成

### 4. 任务完成数据统计与分析

- 可视化展示任务完成情况
- 分析学习效率和时间分配
- 生成学习报告和建议

### 5. 任务智能拆解功能

- 将复杂任务自动拆解为子任务
- 基于历史数据推荐合理的拆解方式
- 子任务进度跟踪和管理

### 6. 多方案冲突解决

- 当日程安排冲突时，自动生成多种解决方案
- 支持手动调整和优化
- 考虑用户偏好和优先级的冲突解决

### 7. 北航邮件集成

- 自动从北航邮件中提取任务和日程
- 支持邮件提醒和日历同步
- 邮件附件自动关联到相关任务

### 8. 基于历史数据预测任务耗时/识别拖延模式

- 分析历史任务完成时间，预测新任务耗时
- 识别用户的拖延模式和习惯
- 提供个性化的时间管理建议

### 9. 健康管理功能

- 集成健康数据（如睡眠、运动）
- 基于健康状态调整学习计划
- 提醒用户保持健康的工作-休息平衡

## 致谢

感谢所有为本项目做出贡献的开发者和测试人员！

---

**北航智能日历系统** - 让时间管理更智能，让学习生活更高效！