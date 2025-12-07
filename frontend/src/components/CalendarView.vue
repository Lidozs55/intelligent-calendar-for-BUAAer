<template>
  <div class="calendar-container">
    <!-- 顶部日期展示 -->
    <div class="top-date-display">
      <span class="current-date">{{ new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'long' }) }}</span>
    </div>
    
    <!-- 快速跳转功能 -->
    <div class="quick-jump-container">
      <button 
        class="quick-jump-btn"
        @click="toggleQuickJump"
      >
        快速跳转
      </button>
      
      <!-- 快速跳转小日历 -->
      <div v-if="showQuickJump" class="quick-jump-calendar">
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
              :class="{ 'today': isToday(day), 'selected': selectedDate && selectedDate.getDate() === day && selectedDate.getMonth() === currentMonth && selectedDate.getFullYear() === currentYear }"
              @click="selectDateAndJump(day)"
            >
              {{ day }}
            </div>
            <div 
              class="day empty" 
              v-for="emptyDay in emptyDaysAfter" 
              :key="'empty-after-' + emptyDay"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 加载状态提示 - 角落小提示 -->
    <div v-if="isLoading" class="loading-corner">
      <div class="loading-spinner"></div>
      <div class="loading-text">{{ loadingStatus }}</div>
    </div>
    
    <FullCalendar
      :options="calendarOptions"
      ref="calendarRef"
    />
    
    <!-- 事件编辑模态框 -->
    <EventEditModal
      :visible="showEditModal"
      :event="editingEvent"
      @close="showEditModal = false"
      @update="handleEventUpdate"
      @delete="handleEventDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { useCourseStore, useUserStore, useTaskStore, useEntryStore } from '../store'
import { coursesAPI, tasksAPI, entriesAPI, authAPI } from '../services/api'
import EventEditModal from './EventEditModal.vue'
import axios from 'axios'

const calendarRef = ref(null)
const courseStore = useCourseStore()
const userStore = useUserStore()
const taskStore = useTaskStore()
const entryStore = useEntryStore()

// 编辑模态框状态
const showEditModal = ref(false)
const editingEvent = ref(null)

// 加载状态
const loadingStatus = ref('')
const isLoading = ref(false)

// 取消令牌，用于取消正在进行的请求
let cancelTokenSource = null

// 事件类型到默认颜色的映射（使用与BUAA_API同步的颜色）
const typeToColor = {
  course: '#4a90e2',       // 北航蓝
  lecture: '#34495e',      // 深灰色
  exam: '#ff4444',         // 红色
  meeting: '#27ae60',      // 深绿色
  individual_homework: '#8e44ad',     // 深紫色 - 个人作业
  group_report: '#9b59b6',     // 紫色 - 小组汇报
  exam_prep: '#e74c3c',     // 红色 - 考试备考
  work_delivery: '#3498db',     // 蓝色 - 工作交付
  sports: '#f39c12',       // 深橙色
  study: '#2980b9',        // 深蓝色
  other: '#7f8c8d'         // 深灰色
}

// 临时事件引用
let tempEvent = null

// 撤销栈和重做栈，用于存储最近5次的事件修改记录
const undoStack = ref([])
const redoStack = ref([])
const MAX_UNDO_STEPS = 5

// 当前页面显示的中心日期，用于API请求
const currentViewDate = ref(new Date())

// 快速跳转功能状态
const showQuickJump = ref(false)
const currentDate = ref(new Date())
const currentYear = computed(() => currentDate.value.getFullYear())
const currentMonth = computed(() => currentDate.value.getMonth())
const selectedDate = ref(null)
const weekdays = ['日', '一', '二', '三', '四', '五', '六']

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

// 切换快速跳转日历显示
const toggleQuickJump = () => {
  showQuickJump.value = !showQuickJump.value
}

// 切换月份
const changeMonth = (delta) => {
  currentDate.value = new Date(currentYear.value, currentMonth.value + delta, 1)
}

// 检查是否为今天
const isToday = (day) => {
  const today = new Date()
  return today.getDate() === day && today.getMonth() === currentMonth.value && today.getFullYear() === currentYear.value
}

// 选择日期并跳转
const selectDateAndJump = (day) => {
  selectedDate.value = new Date(currentYear.value, currentMonth.value, day)
  
  // 跳转到选中日期
  if (calendarRef.value) {
    const calendarApi = calendarRef.value.getApi()
    calendarApi.gotoDate(selectedDate.value)
  }
  
  // 关闭快速跳转日历
  showQuickJump.value = false
  
  // 重新加载数据
  fetchDataAndUpdateCalendar(selectedDate.value)
}

// 点击外部关闭快速跳转日历
document.addEventListener('click', (e) => {
  const quickJumpContainer = document.querySelector('.quick-jump-container')
  if (quickJumpContainer && !quickJumpContainer.contains(e.target)) {
    showQuickJump.value = false
  }
})

// 销毁临时事件的函数
const destroyTempEvent = () => {
  if (tempEvent) {
    tempEvent.remove()
    tempEvent = null
  }
}

// 监听showEditModal变化，当模态框打开时销毁临时事件
watch(showEditModal, (newVal) => {
  if (newVal) {
    // 当打开编辑模态框时，销毁临时事件
    destroyTempEvent()
  }
})

// 检查日期是否是周末
const isWeekend = (date) => {
  const day = date.getDay()
  return day === 0 || day === 6 // 0是周日，6是周六
}

// 检查日期是否是法定节假日（示例数据，实际项目中可以从API获取）
const isHoliday = (date) => {
  const holidays = [
    // 示例节假日，格式：YYYY-MM-DD
    '2025-01-01', // 元旦
    '2025-02-01', // 春节
    '2025-02-02',
    '2025-02-03',
    '2025-02-04',
    '2025-02-05',
    '2025-02-06',
    '2025-04-03', // 清明节
    '2025-04-04',
    '2025-04-05',
    '2025-05-01', // 劳动节
    '2025-05-02',
    '2025-05-03',
    '2025-05-04',
    '2025-05-05',
    '2025-06-01', // 儿童节
    '2025-06-02',
    '2025-06-03',
    '2025-09-13', // 中秋节
    '2025-09-14',
    '2025-09-15',
    '2025-10-01', // 国庆节
    '2025-10-02',
    '2025-10-03',
    '2025-10-04',
    '2025-10-05',
    '2025-10-06',
    '2025-10-07'
  ]
  
  const dateStr = date.toISOString().split('T')[0]
  return holidays.includes(dateStr)
}

// 日历选项
const calendarOptions = {
    plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
    initialView: 'timeGridWeek',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: ''
    },
    editable: true, // 全局设置为可编辑，使用eventAllow回调函数控制具体事件是否可拖动
    selectable: true,
    selectMirror: true,
    dayMaxEvents: true,
    events: [],
    
    // 设置中文语言
    locale: 'zh-cn',
    
    // 自定义按钮文本
    buttonText: {
      today: '跳转到今天',
      month: '月',
      week: '周',
      list: '列表'
    },
    
    // 隐藏all-day项目
    allDaySlot: false,
    
    // 自定义时间格式，使用24小时制
    slotLabelFormat: {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    },
    
    // 自定义时间视图
    views: {
      timeGridWeek: {
        // 显示7天，从今天开始
        duration: { days: 7 },
        // 每天从4:00开始显示
        slotMinTime: '04:00:00',
        // 每天显示到第二天凌晨4:00，确保完整显示所有可能的日程
        slotMaxTime: '28:00:00',
        // 每小时一个时间段
        slotDuration: '01:00:00',
        // 显示当前时间线
        nowIndicator: true,
        // 调整列宽
        dayHeaderFormat: {
          weekday: 'short',
          month: 'numeric',
          day: 'numeric'
        }
      }
    },
    
    // 控制哪些事件可以被拖动
    eventAllow: function(dropInfo, draggedEvent) {
      // 拖动黑名单：这些类型的事件不允许拖动
      const dragBlacklist = ['course', 'lecture', 'exam'] // 不允许拖动的事件类型
      const eventType = draggedEvent.extendedProps.type || ''
      return !dragBlacklist.includes(eventType)
    },
    
    // 允许选择任意时长的时间段
    selectConstraint: {
      start: '04:00',
      end: '28:00'
    },
    
    // 日历加载完成事件
    viewDidMount: () => {
      console.log('日历已加载完成，开始加载数据')
      // 日历加载完成后再加载数据，确保calendarRef可用
      const initialDate = adjustInitialDate()
      fetchDataAndUpdateCalendar(initialDate)
    },
    
    // 视图切换事件
    viewDidChange: () => {
      // 视图切换时不需要额外操作
    },
    
    // 日期渲染事件，用于自定义表头样式和日期导航
    datesSet: (info) => {
      console.log('日期范围已设置:', info)
      // 确保始终显示7天
      if (info.view.type === 'timeGridWeek') {
        info.view.calendar.setOption('duration', { days: 7 })
      }
      
      // 当日期范围变化时，获取当前视图的中心日期并重新加载数据
      const centerDate = info.view.currentStart
      fetchDataAndUpdateCalendar(centerDate)
      
      // 仅为周末添加浅蓝背景（节假日功能暂时禁用）
      setTimeout(() => {
        // 获取所有日期单元格
        const dayCells = document.querySelectorAll('.fc-daygrid-day, .fc-timegrid-day')
        dayCells.forEach(cell => {
          const dateStr = cell.getAttribute('data-date')
          if (dateStr) {
            const date = new Date(dateStr)
            const day = date.getDay()
            // 0是周日，6是周六
            if (day === 0 || day === 6) {
              // 为整个单元格添加背景色
              cell.style.backgroundColor = '#e3f2fd'
              // 为日期文本添加颜色
              const dayText = cell.querySelector('.fc-daygrid-day-number, .fc-timegrid-day-number')
              if (dayText) {
                dayText.style.color = '#1976d2'
              }
            }
          }
        })
      }, 100)
    },
    
    // 选择日期范围事件
    select: (selectInfo) => {
      console.log('选择了日期范围:', selectInfo)
      
      // 如果已有临时事件，先移除
      if (tempEvent) {
        tempEvent.remove()
        tempEvent = null
      }
      
      // 创建临时事件
      const eventType = 'other' // 默认类型改为other
      const color = typeToColor[eventType] || '#7f8c8d'
      tempEvent = selectInfo.view.calendar.addEvent({
        title: '新建事件',
        start: selectInfo.start,
        end: selectInfo.end,
        backgroundColor: `${color}80`, // 添加透明度
        borderColor: color,
        allDay: false,
        extendedProps: {
          type: eventType,
          isTemp: true,
          fullTitle: '新建事件' // 存储完整标题，用于编辑时显示
        },
        className: 'temp-event', // 添加临时事件类名
        // 添加data属性以便识别
        display: 'auto',
        // 使用eventDidMount回调来添加data属性
        eventDidMount: function(info) {
          info.el.setAttribute('data-is-temp', 'true');
        }
      })
      
      // 清除选择，避免干扰
      selectInfo.view.calendar.unselect()
    },
    
    // 点击事件（打开编辑界面）
eventClick: (clickInfo) => {
  console.log('点击了事件:', clickInfo)
  
  // 检查是否是临时事件
  if (clickInfo.event.extendedProps.isTemp) {
    // 打开编辑模态框
    editingEvent.value = clickInfo.event
    showEditModal.value = true
    
    // 保存临时事件引用，以便在编辑后处理
    tempEvent = clickInfo.event
  } else {
    // 销毁现有临时事件
    destroyTempEvent()
    
    // 打开编辑模态框
    editingEvent.value = clickInfo.event
    showEditModal.value = true
  }
},
    
    // 拖拽结束事件
    eventDrop: async (dropInfo) => {
      console.log('拖拽了事件:', dropInfo)
      console.log('事件ID:', dropInfo.event.id)
      console.log('事件类型:', dropInfo.event.extendedProps.type)
      console.log('事件editable属性:', dropInfo.event.editable)
      
      // 获取事件类型
      const eventType = dropInfo.event.extendedProps.type || ''
      
      // 检查是否允许拖动（与updateCalendarEvents函数使用相同的黑名单）
      const dragBlacklist = ['course', 'lecture', 'exam'] // 不允许拖动的事件类型
      console.log('黑名单:', dragBlacklist)
      console.log('是否在黑名单中:', dragBlacklist.includes(eventType))
      
      if (dragBlacklist.includes(eventType)) {
        // 不允许拖动，恢复原状
        dropInfo.revert()
        return
      } else {
        // 保存原事件状态到撤销栈
        const originalEvent = {
          id: dropInfo.event.id,
          start: dropInfo.oldEvent.start,
          end: dropInfo.oldEvent.end,
          title: dropInfo.event.title,
          backgroundColor: dropInfo.event.backgroundColor,
          borderColor: dropInfo.event.borderColor,
          extendedProps: { ...dropInfo.event.extendedProps }
        }
        
        // 清空重做栈
        redoStack.value = []
        
        // 将原事件状态存入撤销栈
        undoStack.value.push(originalEvent)
        
        // 确保撤销栈不超过最大步数
        if (undoStack.value.length > MAX_UNDO_STEPS) {
          undoStack.value.shift()
        }
        
        // 允许拖动，保存数据到数据库
        console.log('保存拖动后的事件到数据库:', dropInfo.event)
        
        try {
          // 构建条目数据
          // 格式化日期时间为datetime-local格式（本地时间），不包含时区信息
          const formatDateTime = (date) => {
            const year = date.getFullYear()
            const month = String(date.getMonth() + 1).padStart(2, '0')
            const day = String(date.getDate()).padStart(2, '0')
            const hours = String(date.getHours()).padStart(2, '0')
            const minutes = String(date.getMinutes()).padStart(2, '0')
            return `${year}-${month}-${day}T${hours}:${minutes}`
          }
          
          const entryData = {
            title: dropInfo.event.title,
            description: '',
            entry_type: eventType,
            start_time: formatDateTime(dropInfo.event.start),
            end_time: formatDateTime(dropInfo.event.end),
            color: dropInfo.event.backgroundColor
          }
          
          // 调用API更新条目
          await entriesAPI.updateEntry(dropInfo.event.id, entryData)
          console.log('事件已保存到数据库:', dropInfo.event)
        } catch (error) {
          console.error('保存事件到数据库失败:', error)
          dropInfo.revert()
          alert('保存失败，请重试')
        }
      }
    },
    
    // 调整事件大小结束事件
    eventResize: async (resizeInfo) => {
      console.log('调整了事件大小:', resizeInfo)
      console.log('事件ID:', resizeInfo.event.id)
      console.log('事件类型:', resizeInfo.event.extendedProps.type)
      
      // 获取事件类型
      const eventType = resizeInfo.event.extendedProps.type || ''
      
      // 检查是否允许调整大小（与eventAllow逻辑相同）
      const resizeBlacklist = ['course', 'lecture', 'exam'] // 不允许调整大小的事件类型
      
      if (resizeBlacklist.includes(eventType)) {
        // 不允许调整大小，恢复原状
        resizeInfo.revert()
        return
      } else {
        // 保存原事件状态到撤销栈
        const originalEvent = {
          id: resizeInfo.event.id,
          start: resizeInfo.oldEvent.start,
          end: resizeInfo.oldEvent.end,
          title: resizeInfo.event.title,
          backgroundColor: resizeInfo.event.backgroundColor,
          borderColor: resizeInfo.event.borderColor,
          extendedProps: { ...resizeInfo.event.extendedProps }
        }
        
        // 清空重做栈
        redoStack.value = []
        
        // 将原事件状态存入撤销栈
        undoStack.value.push(originalEvent)
        
        // 确保撤销栈不超过最大步数
        if (undoStack.value.length > MAX_UNDO_STEPS) {
          undoStack.value.shift()
        }
        
        // 允许调整大小，保存数据到数据库
        console.log('保存调整大小后的事件到数据库:', resizeInfo.event)
        
        try {
          // 构建条目数据
          // 格式化日期时间为datetime-local格式（本地时间），不包含时区信息
          const formatDateTime = (date) => {
            const year = date.getFullYear()
            const month = String(date.getMonth() + 1).padStart(2, '0')
            const day = String(date.getDate()).padStart(2, '0')
            const hours = String(date.getHours()).padStart(2, '0')
            const minutes = String(date.getMinutes()).padStart(2, '0')
            return `${year}-${month}-${day}T${hours}:${minutes}`
          }
          
          const entryData = {
            title: resizeInfo.event.title,
            description: '',
            entry_type: eventType,
            start_time: formatDateTime(resizeInfo.event.start),
            end_time: formatDateTime(resizeInfo.event.end),
            color: resizeInfo.event.backgroundColor
          }
          
          // 调用API更新条目
          await entriesAPI.updateEntry(resizeInfo.event.id, entryData)
          console.log('事件已保存到数据库:', resizeInfo.event)
        } catch (error) {
          console.error('保存事件到数据库失败:', error)
          resizeInfo.revert()
          alert('保存失败，请重试')
        }
      }
    },
    
    // 修复today按钮逻辑，使用dateClick事件来处理
    dateClick: function(info) {
      console.log('点击了日期:', info)
      
      // 如果已有临时事件，先移除
      if (tempEvent) {
        tempEvent.remove()
        tempEvent = null
      }
      
      // 创建临时事件，默认时长1小时
      const endTime = new Date(info.date)
      endTime.setHours(endTime.getHours() + 1)
      
      const eventType = 'other' // 默认类型改为other
      const color = typeToColor[eventType] || '#7f8c8d'
      tempEvent = info.view.calendar.addEvent({
        title: '新建事件',
        start: info.date,
        end: endTime,
        backgroundColor: `${color}80`, // 添加透明度
        borderColor: color,
        allDay: false,
        extendedProps: {
          type: eventType,
          isTemp: true,
          fullTitle: '新建事件' // 存储完整标题，用于编辑时显示
        },
        className: 'temp-event', // 添加临时事件类名
        // 使用eventDidMount回调来添加data属性
        eventDidMount: function(info) {
          info.el.setAttribute('data-is-temp', 'true');
        }
      })
    }
}

// 修复日期显示逻辑：如果当前时间不到4:00，显示前一天的日期
const adjustInitialDate = () => {
  const now = new Date()
  const currentHour = now.getHours()
  
  // 如果当前时间不到4:00，设置初始日期为前一天
  if (currentHour < 4) {
    const yesterday = new Date(now)
    yesterday.setDate(now.getDate() - 1)
    return yesterday
  }
  
  return now
}

// 从API获取数据并更新日历
const fetchDataAndUpdateCalendar = async (date = adjustInitialDate()) => {
  // 设置加载状态
  isLoading.value = true
  loadingStatus.value = '正在获取日历数据...'
  
  try {
    // 保存当前视图日期
    currentViewDate.value = date
    
    // 格式化日期为YYYY-MM-DD格式
    const formattedDate = date.toISOString().split('T')[0]
    
    // 1. 获取指定日期范围内的entries
    const response = await entriesAPI.getEntriesByDate(formattedDate)
    // 处理API返回的数据结构，确保获取到正确的条目数组
    const entries = Array.isArray(response) ? response : (response.entries || [])
    // 更新entryStore.entries数组
    entryStore.setEntries(entries)
    
    // 更新日历事件
    updateCalendarEvents(entries)
    
    // 2. 同步北航课程表（复用SettingsPanel.vue的实现，使用新的按日期同步API）
    try {
      loadingStatus.value = '正在同步课程表...'
      
      // 获取北航学号
      const buaaIdResponse = await authAPI.getBuaaId()
      if (buaaIdResponse.buaa_id) {
        // 调用新的按日期同步课程表API
        await coursesAPI.syncBuaaCoursesByDate(formattedDate, {
          buaa_id: buaaIdResponse.buaa_id,
          password: '' // 密码由后端存储，前端不需要传递
        })
        
        // 3. 同步成功后，再次获取entries刷新前端
        loadingStatus.value = '课程表同步成功，正在刷新日历...'
        const refreshedResponse = await entriesAPI.getEntriesByDate(formattedDate)
        const refreshedEntries = Array.isArray(refreshedResponse) ? refreshedResponse : (refreshedResponse.entries || [])
        entryStore.setEntries(refreshedEntries)
        updateCalendarEvents(refreshedEntries)
      }
    } catch (syncError) {
      console.error('同步课程表失败:', syncError)
      // 同步失败不影响日历显示，继续执行
    }
  } catch (error) {
    console.error('加载条目失败:', error)
    
    // 清空日历事件
    if (calendarRef.value) {
      const calendarApi = calendarRef.value.getApi()
      calendarApi.removeAllEvents()
    }
  } finally {
    // 关闭加载状态
    isLoading.value = false
    loadingStatus.value = ''
  }
}

// 计算字符串的显示长度（中文字符算2个单位，英文字符算1个单位）
const getStringDisplayLength = (str) => {
  let length = 0
  for (let char of str) {
    // 中文字符范围：一-龥
    if (char.match(/[\u4e00-\u9fa5]/)) {
      length += 2
    } else {
      length += 1
    }
  }
  return length
}

// 截断字符串，超过指定显示长度则添加省略号
// 最大显示长度：19个单位（9个中文字符或19个英文字符）
const truncateString = (str, maxDisplayLength = 19) => {
  if (!str) return ''
  
  const displayLength = getStringDisplayLength(str)
  if (displayLength <= maxDisplayLength) return str
  
  let truncatedLength = 0
  let truncatedStr = ''
  
  for (let char of str) {
    const charLength = char.match(/[\u4e00-\u9fa5]/) ? 2 : 1
    
    // 检查添加当前字符和省略号后是否超过最大长度
    if (truncatedLength + charLength + 2 > maxDisplayLength) {
      break
    }
    
    truncatedStr += char
    truncatedLength += charLength
  }
  
  return truncatedStr + '...'
}

// 更新日历事件
const updateCalendarEvents = (entries) => {
  // 拖动黑名单：这些类型的事件不允许拖动
  const dragBlacklist = ['course', 'lecture', 'exam'] // 不允许拖动的事件类型
  
  // 将条目数据转换为FullCalendar所需的格式
  const calendarEventsMap = new Map()
  entries.forEach(entry => {
    calendarEventsMap.set(entry.id, {
      id: entry.id,
      title: truncateString(entry.title),
      start: entry.start_time,
      end: entry.end_time,
      backgroundColor: entry.color || '#000000',
      borderColor: entry.color || '#000000',
      allDay: false,
      editable: !dragBlacklist.includes(entry.entry_type), // 根据黑名单决定是否可编辑（拖动）
      extendedProps: {
        type: entry.entry_type, // 添加类型标识
        fullTitle: entry.title // 存储完整标题，用于编辑时显示
      }
    })
  })
  
  // 更新日历事件
  if (calendarRef.value) {
    const calendarApi = calendarRef.value.getApi()
    
    // 获取当前所有事件
    const currentEvents = calendarApi.getEvents()
    
    // 遍历当前所有事件
    currentEvents.forEach(event => {
      // 如果是临时事件，保留它
      if (event.extendedProps.isTemp) {
        return
      }
      
      // 如果是普通事件，检查是否在新的事件列表中
      const eventId = event.id
      if (calendarEventsMap.has(eventId)) {
        // 如果在，更新事件
        const updatedEvent = calendarEventsMap.get(eventId)
        event.setStart(updatedEvent.start)
        event.setEnd(updatedEvent.end)
        event.setProp('title', updatedEvent.title)
        event.setProp('backgroundColor', updatedEvent.backgroundColor)
        event.setProp('borderColor', updatedEvent.borderColor)
        // 由于FullCalendar没有setExtendedProp方法，我们需要重新创建事件
        event.remove()
        calendarApi.addEvent(updatedEvent)
        
        // 从map中移除，剩下的就是需要新增的事件
        calendarEventsMap.delete(eventId)
      } else {
        // 如果不在，移除事件
        event.remove()
      }
    })
    
    // 添加所有新的事件
    calendarEventsMap.forEach(event => {
      calendarApi.addEvent(event)
    })
    
    console.log('日历事件已更新，新增了', calendarEventsMap.size, '个事件')
  } else {
    console.error('calendarRef.value为null，无法更新日历事件')
    // 如果calendarRef不可用，使用setTimeout重试
    setTimeout(() => {
      if (calendarRef.value) {
        updateCalendarEvents(entries)
      }
    }, 500)
  }
}

// 处理事件更新
const handleEventUpdate = async (eventData) => {
  console.log('更新事件:', eventData)
  
  // 获取当前视图的中心日期
  if (calendarRef.value) {
    const calendarApi = calendarRef.value.getApi()
    
    // 如果是更新现有事件，保存原事件状态到撤销栈
    if (eventData.id) {
      const currentEvent = calendarApi.getEventById(eventData.id)
      if (currentEvent) {
        const originalEvent = {
          id: currentEvent.id,
          start: currentEvent.start,
          end: currentEvent.end,
          title: currentEvent.title,
          backgroundColor: currentEvent.backgroundColor,
          borderColor: currentEvent.borderColor,
          extendedProps: { ...currentEvent.extendedProps }
        }
        
        // 清空重做栈
        redoStack.value = []
        
        // 将原事件状态存入撤销栈
        undoStack.value.push(originalEvent)
        
        // 确保撤销栈不超过最大步数
        if (undoStack.value.length > MAX_UNDO_STEPS) {
          undoStack.value.shift()
        }
      }
    }
  }
  
  // 直接通过API更新服务器
  try {
    // 调用API更新条目
    if (eventData.id) {
      // 只处理已经存在的事件，新事件已经在EventEditModal.vue的saveEvent函数中处理过了
      await entriesAPI.updateEntry(eventData.id, {
        title: eventData.title,
        description: eventData.description || '',
        entry_type: eventData.extendedProps.type,
        start_time: eventData.start,
        end_time: eventData.end,
        color: eventData.backgroundColor
      })
      console.log('事件已更新到数据库:', eventData)
    }
    
    // 添加GET api/entries的逻辑，确保新建日程会立马显示
    // 使用当前视图的中心日期
    const formattedDate = currentViewDate.value.toISOString().split('T')[0]
    // 调用API获取所有条目，刷新前端
    const refreshedResponse = await entriesAPI.getEntriesByDate(formattedDate)
    const refreshedEntries = Array.isArray(refreshedResponse) ? refreshedResponse : (refreshedResponse.entries || [])
    // 更新entryStore.entries数组
    entryStore.setEntries(refreshedEntries)
    // 更新日历事件
    updateCalendarEvents(refreshedEntries)
    console.log('已刷新日历，新建日程已显示')
  } catch (error) {
    console.error('保存事件到数据库失败:', error)
    // 移除不必要的alert，只在控制台打印错误信息
  }
  
  // 确保临时事件被销毁
  destroyTempEvent()
}

// 处理事件删除
const handleEventDelete = async (eventId) => {
  console.log('删除事件:', eventId)
  
  // 保存被删除的事件状态到撤销栈
  if (calendarRef.value) {
    const calendarApi = calendarRef.value.getApi()
    const deletedEvent = calendarApi.getEventById(eventId)
    
    if (deletedEvent) {
      const originalEvent = {
        id: deletedEvent.id,
        start: deletedEvent.start,
        end: deletedEvent.end,
        title: deletedEvent.title,
        backgroundColor: deletedEvent.backgroundColor,
        borderColor: deletedEvent.borderColor,
        extendedProps: { ...deletedEvent.extendedProps }
      }
      
      // 清空重做栈
      redoStack.value = []
      
      // 将原事件状态存入撤销栈
      undoStack.value.push(originalEvent)
      
      // 确保撤销栈不超过最大步数
      if (undoStack.value.length > MAX_UNDO_STEPS) {
        undoStack.value.shift()
      }
    }
  }
  
  // 直接通过API删除服务器上的事件
  try {
    await entriesAPI.deleteEntry(eventId)
    console.log('事件已从数据库删除:', eventId)
  } catch (error) {
    console.error('删除事件到数据库失败:', error)
    // 移除不必要的alert，只在控制台打印错误信息
  }
  
  // 从日历视图中移除事件
  if (calendarRef.value) {
    const calendarApi = calendarRef.value.getApi()
    const eventToRemove = calendarApi.getEventById(eventId)
    if (eventToRemove) {
      eventToRemove.remove()
    }
  }
  
  // 添加GET api/entries的逻辑，确保删除后日历数据准确
  try {
    // 使用当前视图的中心日期
    const formattedDate = currentViewDate.value.toISOString().split('T')[0]
    // 调用API获取所有条目，刷新前端
    const refreshedResponse = await entriesAPI.getEntriesByDate(formattedDate)
    const refreshedEntries = Array.isArray(refreshedResponse) ? refreshedResponse : (refreshedResponse.entries || [])
    // 更新entryStore.entries数组
    entryStore.setEntries(refreshedEntries)
    // 更新日历事件
    updateCalendarEvents(refreshedEntries)
    console.log('已刷新日历，删除的日程已更新')
  } catch (error) {
    console.error('刷新日历失败:', error)
  }
}

// 撤销函数，处理Ctrl+Z操作
const handleUndo = async () => {
  if (undoStack.value.length === 0) {
    console.log('撤销栈为空，无法撤销')
    return
  }
  
  // 从撤销栈中取出最近的操作
  const lastOperation = undoStack.value.pop()
  
  try {
    if (calendarRef.value) {
      const calendarApi = calendarRef.value.getApi()
      
      // 查找当前事件
      const currentEvent = calendarApi.getEventById(lastOperation.id)
      if (currentEvent) {
        // 情况1：事件存在，恢复到之前的状态（拖动或修改）
        // 将当前事件状态存入重做栈
        const currentState = {
          id: currentEvent.id,
          start: currentEvent.start,
          end: currentEvent.end,
          title: currentEvent.title,
          backgroundColor: currentEvent.backgroundColor,
          borderColor: currentEvent.borderColor,
          extendedProps: { ...currentEvent.extendedProps }
        }
        redoStack.value.push(currentState)
        
        // 确保重做栈不超过最大步数
        if (redoStack.value.length > MAX_UNDO_STEPS) {
          redoStack.value.shift()
        }
        
        // 恢复事件到之前的状态
        currentEvent.setStart(lastOperation.start)
        currentEvent.setEnd(lastOperation.end)
        currentEvent.setProp('title', lastOperation.title)
        currentEvent.setProp('backgroundColor', lastOperation.backgroundColor)
        currentEvent.setProp('borderColor', lastOperation.borderColor)
        
        // 调用API更新服务器
        const formatDateTime = (date) => {
          const year = date.getFullYear()
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          const hours = String(date.getHours()).padStart(2, '0')
          const minutes = String(date.getMinutes()).padStart(2, '0')
          return `${year}-${month}-${day}T${hours}:${minutes}`
        }
        
        const entryData = {
          title: lastOperation.title,
          description: '',
          entry_type: lastOperation.extendedProps.type,
          start_time: formatDateTime(lastOperation.start),
          end_time: formatDateTime(lastOperation.end),
          color: lastOperation.backgroundColor
        }
        
        await entriesAPI.updateEntry(lastOperation.id, entryData)
        console.log('撤销操作成功')
      } else {
        // 情况2：事件不存在，可能是被删除的事件，需要重新创建
        // 将创建事件的操作存入重做栈
        redoStack.value.push(lastOperation)
        
        // 确保重做栈不超过最大步数
        if (redoStack.value.length > MAX_UNDO_STEPS) {
          redoStack.value.shift()
        }
        
        // 重新创建被删除的事件
        const newEvent = calendarApi.addEvent({
          id: lastOperation.id,
          title: lastOperation.title,
          start: lastOperation.start,
          end: lastOperation.end,
          backgroundColor: lastOperation.backgroundColor,
          borderColor: lastOperation.borderColor,
          allDay: false,
          editable: !['course', 'lecture', 'exam'].includes(lastOperation.extendedProps.type),
          extendedProps: { ...lastOperation.extendedProps }
        })
        
        // 调用API重新创建事件
        const formatDateTime = (date) => {
          const year = date.getFullYear()
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          const hours = String(date.getHours()).padStart(2, '0')
          const minutes = String(date.getMinutes()).padStart(2, '0')
          return `${year}-${month}-${day}T${hours}:${minutes}`
        }
        
        const entryData = {
          title: lastOperation.title,
          description: '',
          entry_type: lastOperation.extendedProps.type,
          start_time: formatDateTime(lastOperation.start),
          end_time: formatDateTime(lastOperation.end),
          color: lastOperation.backgroundColor
        }
        
        // 检查事件是否已经存在于数据库中
        try {
          // 尝试更新事件
          await entriesAPI.updateEntry(lastOperation.id, entryData)
          console.log('撤销删除操作成功，更新了事件')
        } catch (updateError) {
          // 如果更新失败，可能是因为事件不存在，尝试重新创建
          await entriesAPI.addEntry({
            ...entryData,
            id: lastOperation.id
          })
          console.log('撤销删除操作成功，重新创建了事件')
        }
      }
    }
  } catch (error) {
    console.error('撤销操作失败:', error)
    // 撤销失败时，将操作放回撤销栈
    undoStack.value.push(lastOperation)
  }
}

// 重做函数，处理Ctrl+Shift+Z和Ctrl+Y操作
const handleRedo = async () => {
  if (redoStack.value.length === 0) {
    console.log('重做栈为空，无法重做')
    return
  }
  
  // 从重做栈中取出最近的操作
  const lastOperation = redoStack.value.pop()
  
  try {
    if (calendarRef.value) {
      const calendarApi = calendarRef.value.getApi()
      
      // 查找当前事件
      const currentEvent = calendarApi.getEventById(lastOperation.id)
      
      // 将当前状态存入撤销栈，以便可以再次撤销
      if (currentEvent) {
        const currentState = {
          id: currentEvent.id,
          start: currentEvent.start,
          end: currentEvent.end,
          title: currentEvent.title,
          backgroundColor: currentEvent.backgroundColor,
          borderColor: currentEvent.borderColor,
          extendedProps: { ...currentEvent.extendedProps }
        }
        undoStack.value.push(currentState)
        
        // 确保撤销栈不超过最大步数
        if (undoStack.value.length > MAX_UNDO_STEPS) {
          undoStack.value.shift()
        }
        
        // 移除当前事件，准备重做
        currentEvent.remove()
      }
      
      // 无论事件是否存在，都重新创建事件并应用修改
      const newEvent = calendarApi.addEvent({
        id: lastOperation.id,
        title: lastOperation.title,
        start: lastOperation.start,
        end: lastOperation.end,
        backgroundColor: lastOperation.backgroundColor,
        borderColor: lastOperation.borderColor,
        allDay: false,
        editable: !['course', 'lecture', 'exam'].includes(lastOperation.extendedProps.type),
        extendedProps: { ...lastOperation.extendedProps }
      })
      
      // 调用API更新服务器
      const formatDateTime = (date) => {
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hours = String(date.getHours()).padStart(2, '0')
        const minutes = String(date.getMinutes()).padStart(2, '0')
        return `${year}-${month}-${day}T${hours}:${minutes}`
      }
      
      const entryData = {
        title: lastOperation.title,
        description: '',
        entry_type: lastOperation.extendedProps.type,
        start_time: formatDateTime(lastOperation.start),
        end_time: formatDateTime(lastOperation.end),
        color: lastOperation.backgroundColor
      }
      
      // 检查事件是否已经存在于数据库中
      try {
        // 尝试更新事件
        await entriesAPI.updateEntry(lastOperation.id, entryData)
        console.log('重做修改操作成功')
      } catch (updateError) {
        // 如果更新失败，可能是因为事件不存在，尝试重新创建
        await entriesAPI.addEntry({
          ...entryData,
          id: lastOperation.id
        })
        console.log('重做添加操作成功')
      }
    }
  } catch (error) {
    console.error('重做操作失败:', error)
    // 重做失败时，将操作放回重做栈
    redoStack.value.push(lastOperation)
  }
}

onMounted(() => {
  // 设置初始日期
  if (calendarRef.value) {
    const calendarApi = calendarRef.value.getApi()
    calendarApi.gotoDate(adjustInitialDate())
    
    // 修复today按钮点击事件
    setTimeout(() => {
      const todayBtn = document.querySelector('.fc-today-button');
      if (todayBtn) {
        todayBtn.addEventListener('click', function(e) {
          e.preventDefault();
          const now = new Date();
          const currentHour = now.getHours();
          
          // 如果当前时间不到4:00，跳转到前一天
          if (currentHour < 4) {
            const yesterday = new Date(now);
            yesterday.setDate(now.getDate() - 1);
            calendarApi.gotoDate(yesterday);
          } else {
            calendarApi.gotoDate(now);
          }
        });
      }
    }, 100);
  }
  
  // 添加全局点击事件监听器，点击非临时日程区域销毁临时事件
  const handleGlobalClick = (event) => {
    // 检查点击目标是否是临时日程
    const isClickOnTempEvent = event.target.closest('.fc-event[data-is-temp="true"]');
    
    // 如果有临时事件且点击位置不是临时日程本身，销毁临时事件
    if (tempEvent && !isClickOnTempEvent) {
      // 检查点击目标是否是临时日程的内部元素
      let isTempEventDescendant = false;
      const tempEventElement = document.querySelector('.fc-event[data-is-temp="true"]');
      if (tempEventElement && tempEventElement.contains(event.target)) {
        isTempEventDescendant = true;
      }
      
      if (!isTempEventDescendant) {
        destroyTempEvent();
      }
    }
  };
  
  // 添加键盘事件监听器，处理撤销和重做
  const handleKeyDown = (event) => {
    // Ctrl+Z: 撤销
    if (event.ctrlKey && event.key === 'z' && !event.shiftKey) {
      event.preventDefault();
      handleUndo();
    }
    // Ctrl+Shift+Z: 重做
    else if (event.ctrlKey && event.shiftKey && event.key === 'Z') {
      event.preventDefault();
      handleRedo();
    }
    // Ctrl+Y: 重做
    else if (event.ctrlKey && event.key === 'y') {
      event.preventDefault();
      handleRedo();
    }
  };
  
  // 添加事件监听器
  document.addEventListener('click', handleGlobalClick);
  document.addEventListener('keydown', handleKeyDown);
  
  // 组件卸载时移除事件监听器
  onUnmounted(() => {
    document.removeEventListener('click', handleGlobalClick);
    document.removeEventListener('keydown', handleKeyDown);
    // 组件卸载时确保销毁临时事件
    destroyTempEvent();
  });
  
  // 初始加载数据已移至viewDidMount事件处理
})

// 监听entryStore.entries的变化，当它变化时只更新日历事件，不重新请求API
watch(() => entryStore.entries, (newEntries) => {
  // 只更新日历事件，不重新请求API
  updateCalendarEvents(newEntries)
}, { deep: true })
</script>

<style scoped>
.calendar-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  overflow: hidden;
  position: relative;
  display: block;
}

/* 快速跳转功能样式 - 增强可见性 */
.quick-jump-container {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  background-color: rgba(255, 255, 255, 0.95);
  padding: 0.75rem;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.quick-jump-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-weight: 500;
}

.quick-jump-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(74, 144, 226, 0.3);
}

.quick-jump-btn:hover {
  background-color: var(--primary-dark);
}

.quick-jump-calendar {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 5px;
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 1rem;
  width: 300px;
  z-index: 1001;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.month-nav-btn {
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  width: 30px;
  height: 30px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.month-nav-btn:hover {
  background-color: #e0e0e0;
}

.current-month {
  font-weight: 500;
  font-size: 1rem;
}

.calendar-grid {
  width: 100%;
  background-color: rgba(255, 255, 255, 0.95);
  padding: 0.75rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 0.5rem;
  gap: 2px;
}

.weekday {
  text-align: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  padding: 0.5rem 0;
  background-color: rgba(245, 245, 245, 0.8);
  border-radius: 4px;
}

.days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.day {
  width: 100%;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  color: var(--text-primary);
  background-color: rgba(255, 255, 255, 0.8);
}

.day:hover {
  background-color: #e3f2fd;
  border-color: #4a90e2;
}

.day.today {
  background-color: #4a90e2;
  color: white;
  font-weight: 500;
}

.day.selected {
  background-color: #2196f3;
  color: white;
  font-weight: 500;
}

.day.empty {
  cursor: default;
}

.day.empty:hover {
  background-color: transparent;
  border-color: transparent;
}

/* 调整列宽，使用百分比大小 */
:deep(.fc-timegrid-view .fc-timegrid-col) {
  width: 14.28% !important; /* 7天，每天约14.28% */
}

/* 弱化表格线：浅灰色细虚线 */
:deep(.fc-timegrid-divider) {
  border-color: #e0e0e0 !important;
  border-style: dashed !important;
  z-index: 0 !important;
}

:deep(.fc-timegrid-col-bg .fc-timegrid-slot) {
  border-color: #e0e0e0 !important;
  border-style: dashed !important;
}

:deep(.fc-timegrid-axis) {
  border-right: 1px dashed #e0e0e0 !important;
  z-index: 0 !important;
  color: var(--text-primary) !important;
  font-weight: 500 !important;
  font-size: 0.8rem !important;
}

/* 增强列标题可见性 */
:deep(.fc-day-header) {
  color: var(--text-primary) !important;
  font-weight: 600 !important;
  background-color: rgba(255, 255, 255, 0.95) !important;
  border-bottom: 1px dashed #e0e0e0 !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 在23:00和0:00的分界位置添加加粗的黑线 */
:deep(.fc-timegrid-view .fc-timegrid-slot[data-time="23:00:00"]) {
  border-bottom: 2px solid #000000 !important;
  border-style: solid !important;
  position: relative;
  z-index: 1 !important;
}

/* 确保所有时间槽的z-index正确 */
:deep(.fc-timegrid-slot) {
  position: relative;
  z-index: 1 !important;
}

/* 确保事件的z-index高于分隔线 */
:deep(.fc-timegrid-view .fc-event) {
  position: relative;
  z-index: 2 !important;
  transition: all 0.2s ease !important;
}

/* 确保时间段显示完整并保留滚动条 */
:deep(.fc-scroller) {
  overflow-y: auto !important;
  overflow-x: hidden !important;
  max-height: calc(100vh - 300px) !important;
  position: relative;
  scrollbar-width: thin;
  scrollbar-color: var(--primary-color) transparent;
}

/* 确保23点格子完整显示，隐藏24点 */
:deep(.fc-timegrid-view .fc-timegrid-slot[data-time="23:00:00"]) {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
  height: auto !important;
}

/* 完全隐藏24点时间槽 */
:deep(.fc-timegrid-view .fc-timegrid-slot[data-time="24:00:00"]) {
  display: none !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* 优化日程块样式：圆角、阴影、字体 */
:deep(.fc-event) {
  font-size: 0.75rem !important;
  padding: 4px 6px !important;
  border-radius: 4px !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
  border: none !important;
  transition: all 0.2s ease !important;
}

/* 日程块hover效果 */
:deep(.fc-event:hover) {
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
}

/* 顶部日期展示样式 */
.top-date-display {
  text-align: center;
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 1rem;
  padding: 0.5rem;
  background-color: var(--bg-secondary);
  border-radius: 6px;
  box-shadow: 0 2px 4px var(--shadow-color);
}

/* 调整FullCalendar按钮样式 */
:deep(.fc-button) {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}

:deep(.fc-button:hover) {
  background-color: var(--primary-dark) !important;
  border-color: var(--primary-dark) !important;
}

:deep(.fc-button:focus) {
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
}

:deep(.fc-button:active) {
  background-color: var(--primary-dark) !important;
  border-color: var(--primary-dark) !important;
}

/* 加载状态样式 - 角落小提示 */
.loading-corner {
  position: fixed;
  bottom: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  min-width: 200px;
  max-width: 300px;
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.loading-spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4a90e2;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 0.9rem;
  color: #333;
  font-weight: 500;
  line-height: 1.4;
  word-break: break-word;
}

</style>
