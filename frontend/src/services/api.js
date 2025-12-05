import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 这里可以添加认证token
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    return Promise.reject(error)
  }
)

// 认证相关API
export const authAPI = {
  // 设置北航学号
  setBuaaId: (data) => api.post('/auth/buaa_id', data),
  // 获取北航学号
  getBuaaId: () => api.get('/auth/buaa_id')
}

// 大语言模型解析API
export const llmAPI = {
  // 解析文本内容
  parseText: (data) => api.post('/llm/parse/text', data),
  // 解析语音转文字内容
  parseVoice: (data) => api.post('/llm/parse/voice', data),
  // 解析图片OCR识别内容
  parseImage: (data) => api.post('/llm/parse/image', data),
  // 解析剪切板内容
  parseClipboard: (data) => api.post('/llm/parse/clipboard', data)
}

// 课程相关API
export const coursesAPI = {
  // 获取课程列表
  getCourses: () => api.get('/courses'),
  // 添加课程
  addCourse: (data) => api.post('/courses', data),
  // 更新课程
  updateCourse: (id, data) => api.put(`/courses/${id}`, data),
  // 删除课程
  deleteCourse: (id) => api.delete(`/courses/${id}`),
  // 同步北航课程表
  syncBuaaCourses: (data) => api.post('/courses/sync_buaa', data),
  // 验证北航登录凭证
  verifyBuaaCredentials: (data) => api.post('/courses/verify_buaa_credentials', data)
}

// 条目相关API - 用于处理所有类型的条目（课程、会议、学习、运动等）
export const entriesAPI = {
  // 获取所有条目
  getEntries: () => api.get('/entries'),
  // 按日期范围获取条目
  getEntriesByDate: (date) => api.get(`/entries/${date}`),
  // 添加新条目
  addEntry: (data) => api.post('/entries', data),
  // 更新条目
  updateEntry: (id, data) => api.put(`/entries/${id}`, data),
  // 删除条目
  deleteEntry: (id) => api.delete(`/entries/${id}`),
  // 获取课程类型的条目
  getCourseEntries: () => api.get('/entries/courses')
}

// 任务相关API
export const tasksAPI = {
  // 获取任务列表
  getTasks: (completed) => api.get('/tasks', { params: { completed } }),
  // 添加任务
  addTask: (data) => api.post('/tasks', data),
  // 更新任务
  updateTask: (id, data) => api.put(`/tasks/${id}`, data),
  // 删除任务
  deleteTask: (id) => api.delete(`/tasks/${id}`),
  // 标记任务为完成
  completeTask: (id) => api.put(`/tasks/${id}/complete`),
  // 标记任务为未完成
  uncompleteTask: (id) => api.put(`/tasks/${id}/uncomplete`)
}

// 日程管理相关API
export const scheduleAPI = {
  // 检查日程冲突
  checkConflict: (data) => api.post('/schedule/check_conflict', data),
  // 自动安排任务
  autoSchedule: (data) => api.post('/schedule/auto_schedule', data),
  // 查找可用时间段
  findAvailableSlots: (data) => api.post('/schedule/find_available_slots', data),
  // 保存专注记录
  saveFocusRecord: (data) => api.post('/schedule/save_focus_record', data),
  // 获取专注历史记录
  getFocusHistory: () => api.get('/schedule/get_focus_history')
}

// API_KEY相关API
export const settingsAPI = {
  // 保存API_KEY
  saveApiKey: (data) => api.post('/settings/api_key', data)
}

export default api
