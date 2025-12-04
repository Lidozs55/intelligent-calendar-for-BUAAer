# 北航智能日历系统 - BUAA API调用指南

## 1. 系统概述

该智能日历系统是一个面向北航学生的课程表和考试信息管理系统，通过调用北航官方API实现课程表和考试信息的自动获取与同步。系统采用前后端分离架构，后端使用Flask框架，前端使用Vue.js框架。

## 2. 核心组件

### 2.1 BUAA API客户端 (`BUAAAPIClient`)

位于 `/backend/services/buaa_api.py`，是系统与北航教务系统交互的核心组件，负责：

- 处理北航SSO登录流程
- 获取课程表信息
- 获取考试信息
- 检查登录状态
- 处理API响应

### 2.2 会话管理器 (`SessionManager`)

位于 `/backend/services/session_manager.py`，用于管理用户与北航系统的会话，包括：

- 创建和管理用户会话
- 维护会话超时（默认30分钟）
- 更新和获取会话Cookie
- 销毁过期会话

### 2.3 SSO登录处理器 (`SSOLoginHandler`)

负责处理北航单点登录流程，包括：

- 从登录页面提取execution参数
- 执行完整的SSO登录流程
- 返回登录成功后的Cookie

## 3. API调用流程

### 3.1 获取课程表信息

**功能**：获取指定日期的课程表信息

**调用方法**：`BUAAAPIClient.fetch_course_schedule(user_key, date)`

**参数说明**：
- `user_key`：用户唯一标识，用于会话管理
- `date`：查询日期，格式为YYYY-MM-DD

**API端点**：`https://byxt.buaa.edu.cn/jwapp/sys/homeapp/api/home/teachingSchedule/detail.do?rq={date}&lxdm=student`

**返回格式**：
```json
{
  "need_login": false,
  "data": {
    "courses": [
      {
        "bizName": "课程名称",
        "time": "08:00-09:40",
        "place": "主M202"
      }
    ]
  }
}
```

### 3.2 获取考试信息

**功能**：获取指定学期的考试信息

**调用方法**：`BUAAAPIClient.fetch_exam_schedule(user_key, date)`

**参数说明**：
- `user_key`：用户唯一标识，用于会话管理
- `date`：查询日期，用于计算学期代码

**学期代码计算规则**：
- 8月至12月：`{year}-{year+1}-1`
- 1月至2月：`{year-1}-{year}-1`
- 3月至7月：`{year}-{year+1}-2`

**API端点**：`https://byxt.buaa.edu.cn/jwapp/sys/homeapp/api/home/student/exams.do?termCode={term_code}`

**返回格式**：
```json
{
  "need_login": false,
  "data": {
    "exams": [
      {
        "kcmc": "课程名称",
        "ksrq": "2025-01-10",
        "kssj": "09:00",
        "jssj": "11:00",
        "ksdd": "主M301",
        "ksxz": "期末考试"
      }
    ]
  }
}
```

### 3.3 检查登录状态

**功能**：检查用户与北航系统的会话是否有效

**调用方法**：`BUAAAPIClient.check_login_status(user_key)`

**参数说明**：
- `user_key`：用户唯一标识

**返回格式**：
- `(True, None)`：会话有效
- `(False, login_url)`：会话无效，需要重新登录

## 4. 认证流程

### 4.1 SSO登录流程

1. **初始化请求**：向目标API发送请求，触发302重定向到SSO登录页面
2. **获取登录页面**：访问SSO登录页面，提取`execution`参数
3. **提交登录表单**：使用用户名、密码和`execution`参数提交登录表单
4. **跟随重定向**：处理登录成功后的重定向，获取认证Cookie
5. **验证登录**：检查是否获得核心认证Cookie（`CASTGC`或`_WEU`）

### 4.2 会话管理

- 会话默认超时时间：30分钟
- 会话存储：使用内存存储，定期清理过期会话
- 会话更新：每次API调用时更新会话最后访问时间

## 5. 数据解析

### 5.1 课程数据解析

**函数**：`parse_course_data(course_data, date)`

**功能**：将北航API返回的原始课程数据解析为统一格式，支持多种数据格式

**解析后的数据格式**：
```python
{
  'kcmc': '课程名称',  # 课程名称
  'jsxm': '教师姓名',  # 教师姓名
  'jxlh': '教学楼',    # 教学楼
  'jash': '教室号',    # 教室号
  'kssj': '开始时间',  # 开始时间（HH:MM）
  'jssj': '结束时间',  # 结束时间（HH:MM）
  'xqj': 1,            # 星期几（1-7，周一到周日）
  'zcd': '1-16',       # 周次范围
  'original_date': '2025-12-01'  # 原始日期
}
```

### 5.2 考试数据解析

**函数**：`parse_exam_data(exam_data)`

**功能**：将原始考试数据解析为统一格式

**解析后的数据格式**：
```python
{
  'kcmc': '课程名称',      # 课程名称
  'ksrq': '2025-01-10',    # 考试日期
  'kssj': '09:00',         # 开始时间
  'jssj': '11:00',         # 结束时间
  'ksdd': '主M301',        # 考试地点
  'ksxz': '期末考试',      # 考试性质
  'kh': '1001',            # 课号
  'kch': 'CS101',          # 课程号
  'xf': '3.0',             # 学分
  'cj': '',                # 成绩
  'khfsmc': '闭卷考试'     # 考核方式名称
}
```

## 6. API调用示例

### 6.1 后端调用示例

```python
from services.buaa_api import buaa_api_client

# 初始化会话
session = requests.Session()
user_key = "unique_user_id"

# 获取课程表（2025年12月1日）
course_result = buaa_api_client.fetch_course_schedule(user_key, "2025-12-01")

if not course_result["need_login"]:
    courses = course_result["data"]["courses"]
    # 处理课程数据
    parsed_courses = parse_course_data(courses, "2025-12-01")
    print(f"获取到{len(parsed_courses)}门课程")
else:
    print("需要重新登录")
    # 处理登录流程

# 获取考试信息
exam_result = buaa_api_client.fetch_exam_schedule(user_key, "2025-12-01")

if not exam_result["need_login"]:
    exams = exam_result["data"]["exams"]
    # 处理考试数据
    parsed_exams = parse_exam_data(exams)
    print(f"获取到{len(parsed_exams)}场考试")
else:
    print("需要重新登录")
```

### 6.2 前端调用示例

前端通过HTTP请求调用后端API，后端再调用北航API：

**获取课程表**：
```javascript
fetch('/courses/fetch_course_schedule?date=2025-12-01', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => {
  if (!data.need_login) {
    console.log('课程表数据:', data.data.courses);
  } else {
    // 处理登录
  }
});
```

**同步北航课程和考试信息**：
```javascript
fetch('/courses/sync_buaa', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: '学号',
    password: '密码'
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('同步成功:', data.data);
  } else {
    console.error('同步失败:', data.message);
  }
});
```

## 7. 错误处理

### 7.1 常见错误类型

| 错误类型 | 描述 | 处理方式 |
|---------|------|----------|
| NetworkError | 网络请求失败 | 检查网络连接，重试请求 |
| AuthenticationError | 认证失败 | 重新执行登录流程 |
| DataError | 数据格式错误 | 检查API响应格式，更新解析逻辑 |
| 未知错误 | 其他错误 | 记录错误日志，返回友好提示 |

### 7.2 错误返回格式

```json
{
  "need_login": false,
  "error": "错误信息",
  "cookies": {}
}
```

## 8. 最佳实践

1. **会话管理**：定期检查会话状态，避免无效请求
2. **错误重试**：对网络错误实现自动重试机制
3. **请求限流**：合理设置请求间隔，避免请求过于频繁
4. **数据缓存**：对频繁访问的数据进行缓存，减少API调用
5. **日志记录**：记录API调用日志，便于调试和监控
6. **异常处理**：完善的异常处理机制，确保系统稳定运行

## 9. 注意事项

1. **API稳定性**：北航API可能会不定期更新，需要及时调整代码
2. **登录安全**：妥善处理用户密码，避免明文存储
3. **会话安全**：确保会话数据安全，防止会话劫持
4. **请求频率**：避免过于频繁的API调用，遵守北航系统的访问限制
5. **数据隐私**：妥善处理用户数据，遵守隐私保护法规

## 10. 系统架构图

```
前端应用 (Vue.js)
    ↓ HTTP请求
后端API (Flask)
    ↓ 会话管理
SessionManager
    ↓ API调用
BUAAAPIClient
    ↓ SSO认证
SSOLoginHandler
    ↓ 网络请求
北航教务系统API
    ↓ 数据解析
parse_course_data / parse_exam_data
    ↓ 数据存储
数据库
    ↓ 数据返回
前端应用
```

## 11. 代码结构

```
backend/
├── services/
│   ├── buaa_api.py         # 北航API客户端
│   └── session_manager.py  # 会话管理器
├── routes/
│   └── courses.py          # 课程相关路由
├── models/
│   ├── course.py           # 课程模型
│   └── entry.py            # 日历条目模型
└── app.py                  # 应用入口
```

## 12. 扩展建议

1. **添加数据缓存**：使用Redis或其他缓存系统，减少API调用
2. **实现异步同步**：使用Celery等异步任务队列，提高系统性能
3. **添加监控告警**：实现API调用监控，及时发现问题
4. **支持多种认证方式**：除了密码登录外，支持扫码登录等方式
5. **添加数据验证**：对API返回数据进行严格验证，确保数据准确性
6. **实现分布式会话**：使用Redis等分布式存储，支持多实例部署

通过以上指南，您可以了解北航智能日历系统如何调用BUAA_API获取课程表和考试信息，以及系统的核心架构和设计思路。如果需要进一步开发或扩展功能，可以参考相关代码实现。