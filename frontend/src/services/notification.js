// 通知服务

class NotificationService {
  constructor() {
    this.isSupported = 'Notification' in window
    this.permission = this.isSupported ? Notification.permission : 'denied'
  }

  // 请求通知权限
  async requestPermission() {
    if (!this.isSupported) {
      console.error('浏览器不支持通知功能')
      return false
    }

    if (this.permission === 'granted') {
      return true
    }

    if (this.permission !== 'denied') {
      const permission = await Notification.requestPermission()
      this.permission = permission
      return permission === 'granted'
    }

    return false
  }

  // 创建通知
  createNotification(title, options = {}) {
    if (!this.isSupported || this.permission !== 'granted') {
      console.error('无法发送通知：浏览器不支持或未获得权限')
      return null
    }

    try {
      const notification = new Notification(title, {
        body: options.body || '',
        icon: options.icon || '/favicon.ico',
        badge: options.badge || '',
        tag: options.tag || '',
        data: options.data || {},
        ...options
      })

      // 设置通知点击事件
      if (options.onclick) {
        notification.onclick = options.onclick
      }

      // 设置通知关闭事件
      if (options.onclose) {
        notification.onclose = options.onclose
      }

      // 设置通知错误事件
      if (options.onerror) {
        notification.onerror = options.onerror
      }

      // 设置通知显示事件
      if (options.onshow) {
        notification.onshow = options.onshow
      }

      return notification
    } catch (error) {
      console.error('创建通知失败：', error)
      return null
    }
  }

  // 检查是否需要发送通知
  checkNotifications(tasks, courses, reminderSettings) {
    if (!this.isSupported || this.permission !== 'granted') {
      return
    }

    const now = new Date()

    // 检查任务提醒
    tasks.forEach(task => {
      if (task.deadline && !task.completed) {
        const deadline = new Date(task.deadline)
        const timeDiff = deadline - now

        // 根据任务类型和设置检查是否需要发送提醒
        let reminderTime = 0
        switch (task.task_type) {
          case 'homework':
            reminderTime = reminderSettings.homework * 60 * 1000 // 转换为毫秒
            break
          case 'exam':
            // 考试支持多级提醒
            reminderSettings.exam.forEach(reminderMinutes => {
              const reminderMs = reminderMinutes * 60 * 1000
              if (Math.abs(timeDiff - reminderMs) < 60000) { // 误差1分钟内
                this.createNotification(
                  `考试提醒：${task.title}`,
                  {
                    body: `考试时间：${deadline.toLocaleString('zh-CN')}`,
                    tag: `exam-${task.id}`,
                    data: { taskId: task.id, type: 'exam' }
                  }
                )
              }
            })
            return // 跳过后续处理
          case 'lecture':
            reminderTime = reminderSettings.lecture * 60 * 1000 || 60 * 60 * 1000 // 默认1小时
            break
          case 'meeting':
            reminderTime = reminderSettings.meeting * 60 * 1000 || 30 * 60 * 1000 // 默认30分钟
            break
          default:
            reminderTime = reminderSettings.default * 60 * 1000 || 60 * 60 * 1000 // 默认1小时
        }

        // 检查是否需要发送提醒
        if (Math.abs(timeDiff - reminderTime) < 60000) { // 误差1分钟内
          this.createNotification(
            `任务提醒：${task.title}`,
            {
              body: `截止时间：${deadline.toLocaleString('zh-CN')}`,
              tag: `task-${task.id}`,
              data: { taskId: task.id, type: 'task' }
            }
          )
        }
      }
    })

    // 检查课程提醒
    courses.forEach(course => {
      // 计算课程在当前周的时间
      const courseTime = this._calculateCourseTime(course)
      if (courseTime) {
        const timeDiff = courseTime - now
        const reminderTime = reminderSettings.course * 60 * 1000 // 转换为毫秒

        // 检查是否需要发送提醒
        if (Math.abs(timeDiff - reminderTime) < 60000) { // 误差1分钟内
          this.createNotification(
            `课程提醒：${course.course_name}`,
            {
              body: `上课时间：${courseTime.toLocaleString('zh-CN')}\n地点：${course.classroom}`,
              tag: `course-${course.id}`,
              data: { courseId: course.id, type: 'course' }
            }
          )
        }
      }
    })
  }

  // 计算课程在当前周的时间
  _calculateCourseTime(course) {
    try {
      const now = new Date()
      const currentDayOfWeek = now.getDay() || 7 // 将周日转换为7
      const daysDiff = course.day_of_week - currentDayOfWeek
      const courseDate = new Date(now)
      courseDate.setDate(now.getDate() + daysDiff)

      // 解析课程时间
      const [hours, minutes] = course.start_time.split(':').map(Number)
      courseDate.setHours(hours, minutes, 0, 0)

      return courseDate
    } catch (error) {
      console.error('计算课程时间失败：', error)
      return null
    }
  }

  // 启动定时检查
  startCheckInterval(tasks, courses, reminderSettings, interval = 60000) { // 默认1分钟检查一次
    if (!this.isSupported || this.permission !== 'granted') {
      console.error('无法启动通知检查：浏览器不支持或未获得权限')
      return null
    }

    // 立即检查一次
    this.checkNotifications(tasks, courses, reminderSettings)

    // 设置定时检查
    const intervalId = setInterval(() => {
      this.checkNotifications(tasks, courses, reminderSettings)
    }, interval)

    return intervalId
  }

  // 停止定时检查
  stopCheckInterval(intervalId) {
    if (intervalId) {
      clearInterval(intervalId)
    }
  }
}

// 创建单例实例
const notificationService = new NotificationService()

export default notificationService
