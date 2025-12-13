import { defineStore } from 'pinia'

// 用户状态管理
export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,
    buaaId: null,
    buaaCookies: null
  }),
  
  actions: {
    // 设置用户信息
    setUserInfo(info) {
      this.userInfo = info
      this.buaaId = info.buaa_id
      if (info.buaa_cookies) {
        this.buaaCookies = info.buaa_cookies
      }
    },
    
    // 更新北航学号
    updateBuaaId(buaaId) {
      this.buaaId = buaaId
      if (this.userInfo) {
        this.userInfo.buaa_id = buaaId
      }
    },
    
    // 更新北航Cookie
    updateBuaaCookies(cookies) {
      this.buaaCookies = cookies
      if (this.userInfo) {
        this.userInfo.buaa_cookies = cookies
      }
    },
    
    // 清除用户信息
    clearUserInfo() {
      this.userInfo = null
      this.buaaId = null
      this.buaaCookies = null
    }
  }
})

// 条目状态管理 - 管理所有类型的条目（课程、会议、学习、运动等）
export const useEntryStore = defineStore('entry', {
  state: () => ({
    entries: [],
    loading: false,
    error: null
  }),
  
  actions: {
    // 设置条目列表
    setEntries(entries) {
      this.entries = entries
    },
    
    // 添加条目
    addEntry(entry) {
      this.entries.push(entry)
    },
    
    // 更新条目
    updateEntry(updatedEntry) {
      const index = this.entries.findIndex(entry => entry.id === updatedEntry.id)
      if (index !== -1) {
        this.entries[index] = updatedEntry
      }
    },
    
    // 删除条目
    deleteEntry(entryId) {
      this.entries = this.entries.filter(entry => entry.id !== entryId)
    },
    
    // 设置加载状态
    setLoading(loading) {
      this.loading = loading
    },
    
    // 设置错误信息
    setError(error) {
      this.error = error
    }
  }
})

// 课程状态管理（保留用于兼容旧代码）
export const useCourseStore = defineStore('course', {
  state: () => ({
    courses: [],
    loading: false,
    error: null
  }),
  
  actions: {
    // 设置课程列表
    setCourses(courses) {
      this.courses = courses
    },
    
    // 添加课程
    addCourse(course) {
      this.courses.push(course)
    },
    
    // 更新课程
    updateCourse(updatedCourse) {
      const index = this.courses.findIndex(course => course.id === updatedCourse.id)
      if (index !== -1) {
        this.courses[index] = updatedCourse
      }
    },
    
    // 删除课程
    deleteCourse(courseId) {
      this.courses = this.courses.filter(course => course.id !== courseId)
    },
    
    // 设置加载状态
    setLoading(loading) {
      this.loading = loading
    },
    
    // 设置错误信息
    setError(error) {
      this.error = error
    }
  }
})

// 任务状态管理 - 仅管理截止日期（events）类型的任务
export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [], // 待完成的任务
    completedTasks: [], // 已完成的任务
    loading: false,
    error: null
  }),
  
  actions: {
    // 设置任务列表
    setTasks(tasks) {
      // 过滤掉temp类型的任务，避免重复显示
      // 确保task_type存在且不为'temp'，处理undefined或null的情况
      const nonTempTasks = tasks.filter(task => {
        // 只有明确标记为'temp'的任务才会被过滤掉
        return task.task_type !== 'temp'
      })
      
      // 过滤掉已过期的未完成任务
      const now = new Date()
      const filteredTasks = nonTempTasks.filter(task => {
        // 已完成的任务全部保留
        if (task.completed) {
          return true
        }
        // 未完成的任务，只保留未过期的
        const deadline = new Date(task.deadline)
        return deadline >= now
      })
      
      // 区分待完成和已完成任务
      this.tasks = filteredTasks.filter(task => !task.completed)
      this.completedTasks = filteredTasks.filter(task => task.completed)
    },
    
    // 添加任务
    addTask(task) {
      this.tasks.push(task)
    },
    
    // 更新任务
    updateTask(updatedTask) {
      // 从原列表中移除
      this.tasks = this.tasks.filter(task => task.id !== updatedTask.id)
      this.completedTasks = this.completedTasks.filter(task => task.id !== updatedTask.id)
      
      // 根据完成状态添加到对应列表
      if (updatedTask.completed) {
        this.completedTasks.push(updatedTask)
      } else {
        this.tasks.push(updatedTask)
      }
    },
    
    // 删除任务
    deleteTask(taskId) {
      this.tasks = this.tasks.filter(task => task.id !== taskId)
      this.completedTasks = this.completedTasks.filter(task => task.id !== taskId)
    },
    
    // 设置加载状态
    setLoading(loading) {
      this.loading = loading
    },
    
    // 设置错误信息
    setError(error) {
      this.error = error
    }
  }
})

// 设置状态管理
export const useSettingsStore = defineStore('settings', {
  state: () => {
    // 从localStorage读取设置，但强制使用浅色主题
    const savedSettings = localStorage.getItem('appSettings')
    const parsedSettings = savedSettings ? JSON.parse(savedSettings) : {}
    
    return {
      reminderSettings: {
        course: parsedSettings.reminderSettings?.course || 30, // 课程/讲座/会议提前30分钟提醒
        exam: parsedSettings.reminderSettings?.exam || [14, 60] // 考试提前14天复习提醒，提前1小时前往考场提醒
      },
      theme: 'light', // 强制使用浅色主题
      energyCycle: {
        morning: parsedSettings.energyCycle?.morning || 'high',
        afternoon: parsedSettings.energyCycle?.afternoon || 'medium',
        evening: parsedSettings.energyCycle?.evening || 'low'
      },
      defaultColor: parsedSettings.defaultColor || '#4a90e2' // 默认主题色
    }
  },
  
  actions: {
    // 保存设置到localStorage
    saveSettingsToLocal() {
      const settingsToSave = {
        reminderSettings: this.reminderSettings,
        theme: this.theme,
        energyCycle: this.energyCycle,
        defaultColor: this.defaultColor
      }
      localStorage.setItem('appSettings', JSON.stringify(settingsToSave))
    },
    
    // 更新提醒设置
    updateReminderSettings(settings) {
      this.reminderSettings = { ...this.reminderSettings, ...settings }
      this.saveSettingsToLocal()
    },
    
    // 更新主题
    updateTheme(theme) {
      this.theme = theme
      this.saveSettingsToLocal()
    },
    
    // 更新精力周期
    updateEnergyCycle(cycle) {
      this.energyCycle = { ...this.energyCycle, ...cycle }
      this.saveSettingsToLocal()
    },
    
    // 更新默认颜色
    updateDefaultColor(color) {
      this.defaultColor = color
      this.saveSettingsToLocal()
    }
  }
})

// 剪切板内容队列管理
export const useClipboardStore = defineStore('clipboard', {
  state: () => ({
    clipboardQueue: [], // 存储最近10条剪切板内容
    maxQueueSize: 10 // 最大队列大小
  }),
  
  actions: {
    // 添加剪切板内容到队列
    addToQueue(text) {
      if (!text || text.trim() === '') {
        return
      }
      
      // 检查是否已存在相同内容
      const exists = this.clipboardQueue.some(item => item.text === text)
      if (exists) {
        return
      }
      
      // 创建剪切板内容对象
      const clipboardItem = {
        id: Date.now(),
        text: text,
        timestamp: new Date(),
        processed: false
      }
      
      // 添加到队列开头
      this.clipboardQueue.unshift(clipboardItem)
      
      // 限制队列大小
      if (this.clipboardQueue.length > this.maxQueueSize) {
        this.clipboardQueue = this.clipboardQueue.slice(0, this.maxQueueSize)
      }
    },
    
    // 标记剪切板内容为已处理
    markAsProcessed(id) {
      const index = this.clipboardQueue.findIndex(item => item.id === id)
      if (index !== -1) {
        this.clipboardQueue[index].processed = true
      }
    },
    
    // 移除剪切板内容
    removeFromQueue(id) {
      this.clipboardQueue = this.clipboardQueue.filter(item => item.id !== id)
    },
    
    // 清空队列
    clearQueue() {
      this.clipboardQueue = []
    },
    
    // 获取未处理的剪切板内容
    getUnprocessedItems() {
      return this.clipboardQueue.filter(item => !item.processed)
    }
  }
})
