<template>
  <div class="mobile-calendar">
    <!-- 日期导航 -->
    <div class="date-nav">
      <button class="nav-btn" @click="prevDay">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
      </button>
      <div class="current-date" @click="toggleQuickJump">
        {{ formatDate(currentDate) }}
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="arrow-icon" :class="{ 'rotated': showQuickJump }">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
      <button class="nav-btn" @click="nextDay">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      </button>
    </div>
    
    <!-- 快速跳转小日历 -->
    <div v-show="showQuickJump" class="quick-jump-calendar" :class="{ expanded: showQuickJump }">
      <div class="calendar-header">
        <button @click="changeMonth(-1)" class="month-nav-btn">&lt;</button>
        <span class="current-month">{{ currentYear }}年{{ currentMonth + 1 }}月</span>
        <button @click="changeMonth(1)" class="month-nav-btn">&gt;</button>
      </div>
      <div class="calendar-grid">
        <div class="weekdays">
          <div class="weekday" v-for="day in weekdays" :key="day">{{ day }}</div>
        </div>
        <div class="days">
          <div 
            class="day empty" 
            v-for="emptyDay in emptyDaysBefore" 
            :key="'empty-' + emptyDay"
          ></div>
          <div 
            class="day" 
            v-for="day in daysInMonth" 
            :key="day"
            :class="{ 'today': isToday(day), 'selected': currentDate.getDate() === day && currentDate.getMonth() === currentMonth && currentDate.getFullYear() === currentYear }"
            @click="selectDate(day)"
          >
            {{ day }}
            <span class="importance-dot" v-if="getDayImportance(day)" :style="{ backgroundColor: getDayImportance(day) }"></span>
          </div>
          <div 
            class="day empty" 
            v-for="emptyDay in emptyDaysAfter" 
            :key="'empty-after-' + emptyDay"
          ></div>
        </div>
      </div>
    </div>
    
    <!-- 日程内容 -->
    <div class="calendar-content">
      <!-- 日程条目列表 -->
      <div class="section">
        <h3 class="section-title">今日日程</h3>
        <div v-if="entries.length === 0" class="empty-state">
          <p>今天没有日程</p>
        </div>
        <div v-else class="course-list">
          <div v-for="entry in entries" :key="entry.id" class="course-item" @click="showEventDetail(entry)">
            <div class="course-time">{{ formatTime(entry.start_time) }} - {{ formatTime(entry.end_time) }}</div>
            <div class="course-info">
              <h4 class="course-title">{{ entry.title }}</h4>
              <p class="course-location" v-if="entry.location">{{ entry.location }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 任务列表 -->
      <div class="section">
        <h3 class="section-title">今日任务</h3>
        <div v-if="tasks.length === 0" class="empty-state">
          <p>今天没有任务</p>
        </div>
        <div v-else class="task-list">
          <div v-for="task in tasks" :key="task.id" class="task-item">
            <input 
              type="checkbox" 
              :checked="task.completed" 
              @change="toggleTaskCompletion(task)"
              @click.stop
            />
            <div class="task-content" @click="showTaskDetail(task)">
              <h4 class="task-title">{{ task.title }}</h4>
              <p class="task-deadline" v-if="task.deadline">
                截止：{{ formatTime(task.deadline) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 详情弹窗 -->
    <div v-if="showDetail" class="detail-overlay" @click="closeDetail">
      <div class="detail-content" @click.stop>
        <h3>{{ detailTitle }}</h3>
        <div v-if="currentDetailType === 'course'">
          <div class="detail-item">
            <span class="detail-label">时间：</span>
            <span class="detail-value">{{ formatDateTime(currentDetail.start_time) }}</span>
          </div>
          <div class="detail-item" v-if="currentDetail.location">
            <span class="detail-label">地点：</span>
            <span class="detail-value">{{ currentDetail.location }}</span>
          </div>
          <div class="detail-item" v-if="currentDetail.description">
            <span class="detail-label">描述：</span>
            <span class="detail-value">{{ currentDetail.description }}</span>
          </div>
        </div>
        <div v-else-if="currentDetailType === 'task'">
          <div class="detail-item" v-if="currentDetail.description">
            <span class="detail-label">描述：</span>
            <span class="detail-value">{{ currentDetail.description }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">截止时间：</span>
            <span class="detail-value">{{ formatDateTime(currentDetail.deadline) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">状态：</span>
            <span class="detail-value">{{ currentDetail.completed ? '已完成' : '未完成' }}</span>
          </div>
        </div>
        <button class="close-btn" @click="closeDetail">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onActivated } from 'vue'
import { useTaskStore, useEntryStore, useCourseStore } from '../../store'
import { entriesAPI, tasksAPI, coursesAPI } from '../../services/api'

// 状态管理
const taskStore = useTaskStore()
const entryStore = useEntryStore()
const courseStore = useCourseStore()

// 组件内部状态，避免影响全局状态
const localEntries = ref([])

// 当前日期，确保初始值是有效日期
const currentDate = ref(new Date())

// 详情弹窗状态
const showDetail = ref(false)
const currentDetail = ref(null)
const currentDetailType = ref('')

// 快速跳转小日历显示状态
const showQuickJump = ref(false)

// 切换快速跳转小日历显示
const toggleQuickJump = () => {
  showQuickJump.value = !showQuickJump.value
}

// 格式化日期
const formatDate = (date) => {
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'long' })
}

// 格式化时间
const formatTime = (dateString) => {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch (error) {
    console.error('格式化时间失败:', error)
    return ''
  }
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } catch (error) {
    console.error('格式化日期时间失败:', error)
    return ''
  }
}

// 前一天
const prevDay = () => {
  currentDate.value = new Date(currentDate.value.getTime() - 24 * 60 * 60 * 1000)
}

// 后一天
const nextDay = () => {
  currentDate.value = new Date(currentDate.value.getTime() + 24 * 60 * 60 * 1000)
}

// 快速跳转小日历相关
const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const currentYear = computed(() => currentDate.value.getFullYear())
const currentMonth = computed(() => currentDate.value.getMonth())

// 计算当月天数
const daysInMonth = computed(() => {
  return new Date(currentYear.value, currentMonth.value + 1, 0).getDate()
})

// 计算当月第一天是星期几
const firstDayOfMonth = computed(() => {
  return new Date(currentYear.value, currentMonth.value, 1).getDay()
})

// 计算月初空白天数
const emptyDaysBefore = computed(() => {
  return firstDayOfMonth.value
})

// 计算月末空白天数
const emptyDaysAfter = computed(() => {
  const totalDays = emptyDaysBefore.value + daysInMonth.value
  const weeks = Math.ceil(totalDays / 7)
  return weeks * 7 - totalDays
})

// 获取当前月份的所有日程数据
const currentMonthEntries = computed(() => {
  // 从entryStore中获取所有日程
  const allEntries = [...entryStore.entries, ...courseStore.courses]
  return allEntries.filter(entry => {
    const entryDate = new Date(entry.start_time)
    return entryDate.getFullYear() === currentYear.value && entryDate.getMonth() === currentMonth.value
  })
})

// 获取特定日期的日程重要性
const getDayImportance = (day) => {
  const targetDate = new Date(currentYear.value, currentMonth.value, day)
  const dayEntries = currentMonthEntries.value.filter(entry => {
    const entryDate = new Date(entry.start_time)
    return entryDate.getDate() === day
  })
  
  if (dayEntries.length === 0) return null
  
  // 根据日程重要性返回对应的颜色
  const importanceMap = {
    'high': 'red',
    'medium': 'orange',
    'low': 'green'
  }
  
  // 优先返回高优先级的颜色
  for (const entry of dayEntries) {
    if (entry.importance === 'high') return importanceMap.high
  }
  for (const entry of dayEntries) {
    if (entry.importance === 'medium') return importanceMap.medium
  }
  return importanceMap.low
}

// 切换月份
const changeMonth = (delta) => {
  currentDate.value = new Date(currentYear.value, currentMonth.value + delta, currentDate.value.getDate())
}

// 检查是否为今天
const isToday = (day) => {
  const today = new Date()
  return today.getDate() === day && today.getMonth() === currentMonth.value && today.getFullYear() === currentYear.value
}

// 选择日期
const selectDate = (day) => {
  currentDate.value = new Date(currentYear.value, currentMonth.value, day)
}

// 获取当天日程条目
const entries = computed(() => {
  const dateStr = currentDate.value.toISOString().split('T')[0]
  return localEntries.value.filter(entry => {
    try {
      // 检查start_time是否有效
      if (!entry.start_time) return false
      
      const entryDate = new Date(entry.start_time).toISOString().split('T')[0]
      return entryDate === dateStr
    } catch (error) {
      // 处理无效日期
      return false
    }
  })
})

// 获取当天任务
const tasks = computed(() => {
  const dateStr = currentDate.value.toISOString().split('T')[0]
  return taskStore.tasks.filter(task => {
    try {
      // 检查deadline是否有效
      if (!task.deadline) return false
      
      const taskDate = new Date(task.deadline).toISOString().split('T')[0]
      return taskDate === dateStr
    } catch (error) {
      // 处理无效日期
      return false
    }
  })
})

// 显示事件详情
const showEventDetail = (entry) => {
  currentDetail.value = entry
  currentDetailType.value = 'course'
  showDetail.value = true
}

// 显示任务详情
const showTaskDetail = (task) => {
  currentDetail.value = task
  currentDetailType.value = 'task'
  showDetail.value = true
}

// 关闭详情
const closeDetail = () => {
  showDetail.value = false
  currentDetail.value = null
  currentDetailType.value = ''
}

// 切换任务完成状态
const toggleTaskCompletion = async (task) => {
  try {
    if (task.completed) {
      await tasksAPI.uncompleteTask(task.id)
    } else {
      await tasksAPI.completeTask(task.id)
    }
    // 重新加载任务数据
    const response = await tasksAPI.getTasks(null)
    taskStore.setTasks(response.tasks)
  } catch (err) {
    console.error('更新任务状态失败:', err)
  }
}

// 详情标题
const detailTitle = computed(() => {
  if (currentDetailType.value === 'course') {
    return currentDetail.value?.title || '课程详情'
  } else if (currentDetailType.value === 'task') {
    return currentDetail.value?.title || '任务详情'
  }
  return '详情'
})

// 加载数据
const loadData = async () => {
  try {
    // 获取当前日期
    const date = new Date(currentDate.value)
    date.setDate(date.getDate() - 1)
    const dateStr = date.toISOString().split('T')[0]
    
    // 加载当天的条目数据
    const entriesResponse = await entriesAPI.getEntriesByDate(dateStr)
    localEntries.value = entriesResponse.entries || []
    
    // 加载任务数据
    const tasksResponse = await tasksAPI.getTasks(null)
    taskStore.setTasks(tasksResponse.tasks)
    
    // 加载当前月份的所有条目数据，用于快速跳转日历的重要性显示
    const monthStart = new Date(currentYear.value, currentMonth.value, 1).toISOString().split('T')[0]
    const monthEnd = new Date(currentYear.value, currentMonth.value + 1, 0).toISOString().split('T')[0]
    const monthEntriesResponse = await entriesAPI.getEntriesByDateRange(monthStart, monthEnd)
    entryStore.setEntries(monthEntriesResponse.entries || [])
    
    // 加载课程数据
    const coursesResponse = await coursesAPI.getCourses()
    courseStore.setCourses(coursesResponse.courses || [])
  } catch (err) {
    console.error('加载数据失败:', err)
    localEntries.value = [] // 出错时清空数据
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadData()
})

// 组件激活时重新加载数据（解决标签页切换时的刷新问题）
onActivated(() => {
  loadData()
})

// 监听日期变化，重新加载数据
watch(currentDate, () => {
  loadData()
})
</script>

<style scoped>
/* 基础样式 */
.mobile-calendar {
  padding: 16px;
  background-color: white;
  min-height: calc(100vh - 60px);
}

/* 日期导航 */
.date-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
}

.nav-btn {
  background: none;
  border: none;
  color: var(--primary-color);
  font-size: 18px;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.nav-btn:hover {
  background-color: rgba(74, 144, 226, 0.1);
}

.current-date {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.arrow-icon {
  transition: transform 0.3s ease;
  margin-left: 4px;
}

.arrow-icon.rotated {
  transform: rotate(180deg);
}

/* 日历内容 */
.calendar-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 章节 */
.section {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

/* 空状态 */
.empty-state {
  text-align: center;
  color: var(--text-secondary);
  padding: 16px 0;
  font-size: 14px;
}

/* 课程列表 */
.course-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.course-item {
  background-color: white;
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.course-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
}

.course-time {
  font-size: 14px;
  color: var(--primary-color);
  font-weight: 500;
  margin-bottom: 4px;
}

.course-info {
  display: flex;
  flex-direction: column;
}

.course-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--text-primary);
}

.course-location {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

/* 任务列表 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  background-color: white;
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--primary-color);
  cursor: pointer;
}

.task-content {
  flex: 1;
  cursor: pointer;
}

.task-title {
  font-size: 15px;
  font-weight: 500;
  margin: 0 0 4px 0;
  color: var(--text-primary);
  text-decoration: line-through;
  text-decoration-color: var(--primary-color);
  text-decoration-thickness: 2px;
}

.task-item input[type="checkbox"]:not(:checked) + .task-content .task-title {
  text-decoration: none;
}

.task-deadline {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

/* 详情弹窗 */
.detail-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.detail-content {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  max-width: 400px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.detail-content h3 {
  margin-top: 0;
  margin-bottom: 16px;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
}

.detail-item {
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.detail-label {
  font-weight: 600;
  color: var(--text-primary);
  min-width: 60px;
  font-size: 14px;
}

.detail-value {
  flex: 1;
  color: var(--text-secondary);
  font-size: 14px;
  word-break: break-word;
}

.close-btn {
  margin-top: 20px;
  width: 100%;
  padding: 10px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.3s ease;
}

.close-btn:hover {
  background-color: var(--primary-dark);
}

/* 快速跳转小日历 */
.quick-jump-calendar {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px var(--shadow-color);
  /* 初始状态 - 折叠 */
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transform: translateY(-10px);
  /* 过渡效果 - 优化为更平滑的动画 */
  transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.3s ease-in-out,
              transform 0.3s ease-in-out;
}

.quick-jump-calendar.expanded {
  /* 展开状态 */
  max-height: 450px;
  opacity: 1;
  transform: translateY(0);
}

/* 箭头图标动画 */
.arrow-icon {
  transition: transform 0.3s ease;
  margin-left: 8px;
}

.arrow-icon.rotated {
  transform: rotate(180deg);
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.month-nav-btn {
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.month-nav-btn:hover {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.current-month {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.calendar-grid {
  width: 100%;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 8px;
}

.weekday {
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 4px 0;
}

.days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.day {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 8px 4px;
  text-align: center;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

/* 重要性颜色小点 */
.importance-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: block;
  margin-top: 2px;
}

.day:hover {
  background-color: rgba(var(--primary-color-rgb), 0.1);
  border-color: var(--primary-color);
}

.day.today {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  font-weight: 600;
}

.day.selected {
  background-color: rgba(74, 144, 226, 0.2);
  border-color: var(--primary-color);
  font-weight: 600;
}

.day.empty {
  background-color: transparent;
  border: none;
  cursor: default;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .mobile-calendar {
    padding: 12px;
  }
  
  .section {
    padding: 12px;
  }
  
  .course-item,
  .task-item {
    padding: 10px;
  }
  
  .quick-jump-calendar {
    padding: 12px;
  }
  
  .day {
    min-height: 32px;
    padding: 6px 2px;
    font-size: 13px;
  }
}
</style>