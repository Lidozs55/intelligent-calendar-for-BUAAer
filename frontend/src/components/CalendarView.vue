<template>
  <div class="calendar-container">
    <!-- 顶部日期展示已移至App.vue的header中 -->
    
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
            <div 
              class="schedule-indicator" 
              :style="{ backgroundColor: getIndicatorColor(calculateImportanceLevel(day)) }"
            ></div>
          </div>
          <div 
            class="day empty" 
            v-for="emptyDay in emptyDaysAfter" 
            :key="'empty-after-' + emptyDay"
          ></div>
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
    
    <!-- 批量添加模态框 -->
    <BatchAddModal
      v-if="showBatchAddModal"
      @close="showBatchAddModal = false"
      @success="handleBatchAddSuccess"
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
import BatchAddModal from './BatchAddModal.vue'
import axios from 'axios'

const calendarRef = ref(null)
const courseStore = useCourseStore()
const userStore = useUserStore()
const taskStore = useTaskStore()
const entryStore = useEntryStore()

// 编辑模态框状态
const showEditModal = ref(false)
const editingEvent = ref(null)

// 批量添加模态框状态
const showBatchAddModal = ref(false)

// 处理批量添加成功事件
const handleBatchAddSuccess = async () => {
  try {
    // 使用当前视图的中心日期
    const formattedDate = currentViewDate.value.toISOString().split('T')[0]
    
    // 创建新的AbortController用于此请求
    const batchAddAbortController = new AbortController()
    
    // 调用API获取所有条目，刷新前端
    const refreshedResponse = await entriesAPI.getEntriesByDate(formattedDate, batchAddAbortController.signal)
    const refreshedEntries = Array.isArray(refreshedResponse) ? refreshedResponse : (refreshedResponse.entries || [])
    // 更新entryStore.entries数组
    entryStore.setEntries(refreshedEntries)
    // 更新日历事件
    updateCalendarEvents(refreshedEntries)
    console.log('已刷新日历，批量创建的日常任务已更新')
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('批量添加成功后刷新日历请求已取消')
      return
    }
    console.error('刷新日历失败:', error)
  }
}

// 加载状态
const loadingStatus = ref('')
const isLoading = ref(false)

// 监听isLoading状态变化，动态更新日历的可编辑和可选择状态
watch(isLoading, (newValue) => {
  if (calendarRef.value) {
    const calendarApi = calendarRef.value.getApi()
    calendarApi.setOption('editable', !newValue)
    calendarApi.setOption('selectable', !newValue)
  }
})

// 取消控制器，用于取消正在进行的请求
let abortController = null

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

// 根据持续时间动态调整事件padding的函数
const updateEventPadding = (event) => {
  // 获取事件的开始和结束时间
  const start = event.start;
  const end = event.end;
  
  // 计算事件持续时间（毫秒）
  const durationMs = end - start;
  // 转换为小时
  const durationHours = durationMs / (1000 * 60 * 60);
  
  // 获取事件元素
  const eventEl = event.el;
  const contentEl = eventEl.querySelector('.fc-event-main');
  
  // 如果是临时事件，添加data属性以便识别
  if (event.extendedProps.isTemp) {
    eventEl.setAttribute('data-is-temp', 'true');
  }
  
  // 根据持续时间设置不同的padding
  if (durationHours >= 1.5) {
    // 如果事件持续时间达到或超过1.5小时，设置固定padding（已减半）
    eventEl.style.padding = '1.5px 2.5px !important';
    contentEl.style.padding = '1px 2px !important';
  } else {
    // 否则，设置百分比padding（增加!important以确保生效）
    eventEl.style.padding = '2% 4% !important';
    contentEl.style.padding = '1% 3% !important';
  }
}

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
  if (showQuickJump.value) {
    fetchMonthEntries()
  }
}

// 切换月份
const changeMonth = (delta) => {
  currentDate.value = new Date(currentYear.value, currentMonth.value + delta, 1)
  fetchMonthEntries()
}

// 检查是否为今天
const isToday = (day) => {
  const today = new Date()
  return today.getDate() === day && today.getMonth() === currentMonth.value && today.getFullYear() === currentYear.value
}

// 月视图日程数据，用于显示指示器
const monthEntries = ref({})

// 获取当月所有日期的日程信息
const fetchMonthEntries = async () => {
  try {
    const year = currentYear.value
    const month = currentMonth.value
    
    // 计算当月第一天和最后一天
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    
    // 格式化日期
    const startDate = firstDay.toISOString().split('T')[0]
    const endDate = lastDay.toISOString().split('T')[0]
    
    // 创建新的AbortController用于此请求
    const monthAbortController = new AbortController()
    
    // 获取当月所有日程
    const response = await entriesAPI.getEntriesByDateRange(startDate, endDate, monthAbortController.signal)
    const entries = Array.isArray(response) ? response : (response.entries || [])
    
    // 按日期分组并计算重要性
    const entriesByDate = {}
    entries.forEach(entry => {
      const date = entry.start_time.split('T')[0]
      if (!entriesByDate[date]) {
        entriesByDate[date] = []
      }
      entriesByDate[date].push(entry)
    })
    
    monthEntries.value = entriesByDate
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('获取当月日程请求已取消')
      return
    }
    console.error('获取当月日程失败:', error)
    monthEntries.value = {}
  }
}

// 计算日期的日程重要性等级（0-无日程，1-低，2-中，3-高）
const calculateImportanceLevel = (date) => {
  const dateStr = new Date(currentYear.value, currentMonth.value, date).toISOString().split('T')[0]
  const entries = monthEntries.value[dateStr] || []
  
  if (entries.length === 0) return 0
  
  // 根据日程类型和数量计算重要性
  let importance = 1
  
  entries.forEach(entry => {
    if (entry.entry_type === 'exam' || entry.entry_type === 'exam_prep') {
      importance = Math.max(importance, 3)
    } else if (entry.entry_type === 'individual_homework' || entry.entry_type === 'group_report' || entry.entry_type === 'work_delivery') {
      importance = Math.max(importance, 2)
    } else if (entry.entry_type === 'course' || entry.entry_type === 'meeting') {
      importance = Math.max(importance, 1)
    }
  })
  
  // 如果同一天有多个日程，提升重要性
  if (entries.length >= 3) {
    importance = Math.min(importance + 1, 3)
  }
  
  return importance
}

// 获取日程指示器颜色
const getIndicatorColor = (importanceLevel) => {
  switch (importanceLevel) {
    case 1: return '#4CAF50' // 绿色 - 低重要性
    case 2: return '#FFC107' // 黄色 - 中重要性
    case 3: return '#F44336' // 红色 - 高重要性
    default: return 'transparent' // 无日程
  }
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
  const quickJumpCalendar = document.querySelector('.quick-jump-calendar')
  const quickJumpBtn = document.querySelector('.fc-quickJump-button')
  if (showQuickJump.value && quickJumpCalendar && !quickJumpCalendar.contains(e.target) && quickJumpBtn && !quickJumpBtn.contains(e.target)) {
    showQuickJump.value = false
  }
})

// 防抖函数，用于限制函数调用频率
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

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
      left: 'prev,next today quickJump',
      center: 'title',
      right: 'batchAdd'
    },
    editable: !isLoading.value, // 全局设置为可编辑，使用eventAllow回调函数控制具体事件是否可拖动
    selectable: !isLoading.value,
    selectMirror: true,
    dayMaxEvents: true,
    events: [],
    
    // 设置中文语言
    locale: 'zh-cn',
    
    // 自定义按钮文本
    buttonText: {
      today: '回到今天',
      month: '月',
      week: '周',
      list: '列表'
    },
    
    // 自定义按钮
    customButtons: {
      quickJump: {
        text: '快速跳转',
        click: toggleQuickJump
      },
      batchAdd: {
        text: '+ 创建日常任务',
        click: () => { showBatchAddModal.value = true }
      },
      today: {
        text: '回到今天',
        click: function() {
          const calendar = this;
          const now = new Date();
          const currentHour = now.getHours();
          
          // 如果当前时间不到4:00，跳转到前一天
          if (currentHour < 4) {
            const yesterday = new Date(now);
            yesterday.setDate(now.getDate() - 1);
            calendar.gotoDate(yesterday);
          } else {
            // 强制跳转到今天，确保显示的是今天开始的7天视图
            const today = new Date();
            calendar.gotoDate(today);
            
            // 强制重新加载数据，确保日期范围正确
            const centerDate = today;
            fetchDataAndUpdateCalendar(centerDate);
          }
        }
      }
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
        },
        // 自定义标题格式
        titleFormat: {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        }
      }
    },
    
    // 自定义日期范围计算逻辑，确保标题显示正确的日期范围
    datesDidUpdate: (info) => {
      if (info.view.type === 'timeGridWeek') {
        // 获取开始和结束日期
        const startDate = new Date(info.start)
        const endDate = new Date(info.end)
        
        // 减去一天，因为FullCalendar的end日期是下一周的开始
        endDate.setDate(endDate.getDate() - 1)
        
        // 更新视图的内部日期范围
        info.view.currentStart = startDate
        info.view.currentEnd = endDate
      }
    },
    
    // 控制哪些事件可以被拖动
    eventAllow: function(dropInfo, draggedEvent) {
      // 拖动黑名单：这些类型的事件不允许拖动
      const dragBlacklist = ['course', 'lecture', 'exam'] // 不允许拖动的事件类型
      const eventType = draggedEvent.extendedProps.type || ''
      // 检查是否是临时日程或在黑名单中
      return !(dragBlacklist.includes(eventType) || draggedEvent.extendedProps.isTemp)
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
    datesSet: debounce((info) => {
      console.log('日期范围已设置:', info)
      // 确保始终显示7天
      if (info.view.type === 'timeGridWeek') {
        info.view.calendar.setOption('duration', { days: 7 })
      }
      
      // 当日期范围变化时，获取当前视图的实际开始日期并重新加载数据
      // 使用info.start而不是info.view.currentStart，因为后者可能被错误修改
      const centerDate = info.start
      fetchDataAndUpdateCalendar(centerDate)
      
      // 移除动态标题修改，使用FullCalendar的titleFormat选项直接控制标题格式
      
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
    }, 300),
    
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
        display: 'auto'
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
          // 移除alert提示，避免干扰用户
          // alert('保存失败，请重试')
          // 不再恢复事件位置，因为FullCalendar已经更新了事件的位置和大小
          // dropInfo.revert()
        }
        
        // 修复：无论API请求是否成功，都更新事件padding
        updateEventPadding(dropInfo.event)
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
          // 移除alert提示，避免干扰用户
          // alert('保存失败，请重试')
          // 不再恢复事件大小，因为FullCalendar已经更新了事件的位置和大小
          // resizeInfo.revert()
        }
        
        // 修复：无论API请求是否成功，都更新事件padding
        updateEventPadding(resizeInfo.event)
      }
    },
    
    // 日期点击事件处理
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
        className: 'temp-event' // 添加临时事件类名
      })
    },
    
    // 事件渲染完成后处理 - 根据持续时间动态调整padding
    eventDidMount: function(info) {
      // 获取事件的开始和结束时间
      const start = info.event.start;
      const end = info.event.end;
      
      // 计算事件持续时间（毫秒）
      const durationMs = end - start;
      // 转换为小时
      const durationHours = durationMs / (1000 * 60 * 60);
      
      // 获取事件元素
      const eventEl = info.el;
      const contentEl = eventEl.querySelector('.fc-event-main');
      
      // 如果是临时事件，添加data属性以便识别
      if (info.event.extendedProps.isTemp) {
        eventEl.setAttribute('data-is-temp', 'true');
      }
      
      // 根据持续时间设置不同的padding
      if (durationHours >= 1.5) {
        // 如果事件持续时间达到或超过1.5小时，设置固定padding（已减半）
        eventEl.style.padding = '1.5px 2.5px';
        contentEl.style.padding = '1px 2px';
      } else {
        // 否则，设置百分比padding（增加!important以确保生效）
        eventEl.style.padding = '2% 4% !important';
        contentEl.style.padding = '1% 3% !important';
      }
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
  
  // 取消之前正在进行的请求
  if (abortController) {
    abortController.abort()
    console.log('已取消之前的请求')
  }
  
  // 创建新的AbortController
  abortController = new AbortController()
  
  try {
    // 确保date是一个有效的JavaScript Date对象
    let validDate = date
    if (!(validDate instanceof Date)) {
      // 如果是FullCalendar的日期对象，将其转换为JavaScript Date对象
      validDate = new Date(validDate)
    }
    
    // 保存当前视图日期
    currentViewDate.value = validDate
    
    // 格式化日期为YYYY-MM-DD格式
    const formattedDate = validDate.toISOString().split('T')[0]
    
    // 1. 获取指定日期范围内的entries
    const response = await entriesAPI.getEntriesByDate(formattedDate, abortController.signal)
    // 处理API返回的数据结构，确保获取到正确的条目数组
    const entries = Array.isArray(response) ? response : (response.entries || [])
    // 更新entryStore.entries数组
    entryStore.setEntries(entries)
    
    // 更新日历事件
    updateCalendarEvents(entries)
    
    // 2. 同步北航课程表（使用新的按日期同步API）
    try {
      loadingStatus.value = '正在同步课程表...'
      
      // 获取北航学号
      const buaaIdResponse = await authAPI.getBuaaId(abortController.signal)
      if (buaaIdResponse.buaa_id) {
        // 调用新的按日期同步课程表API，并传递abort signal
          await coursesAPI.syncBuaaCoursesByDate(formattedDate, {
            buaa_id: buaaIdResponse.buaa_id,
            password: '' // 密码由后端存储，前端不需要传递
          }, abortController.signal)
        
        // 3. 同步成功后，再次获取entries刷新前端
        loadingStatus.value = '课程表同步成功，正在刷新日历...'
        const refreshedResponse = await entriesAPI.getEntriesByDate(formattedDate, abortController.signal)
        const refreshedEntries = Array.isArray(refreshedResponse) ? refreshedResponse : (refreshedResponse.entries || [])
        entryStore.setEntries(refreshedEntries)
        updateCalendarEvents(refreshedEntries)
      }
    } catch (syncError) {
      if (syncError.name === 'AbortError') {
        console.log('课程表同步请求已取消')
        return
      }
      console.error('同步课程表失败:', syncError)
      // 同步失败不影响日历显示，继续执行
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('获取日历数据请求已取消')
      return
    }
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
    // 清理abortController
    abortController = null
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
// 最大显示长度：20个单位（10个中文字符或20个英文字符）
const truncateString = (str, maxDisplayLength = 20) => {
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
    // 创建新的AbortController用于此请求
    const updateEventAbortController = new AbortController()
    
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
      }, updateEventAbortController.signal)
      console.log('事件已更新到数据库:', eventData)
    }
    
    // 添加GET api/entries的逻辑，确保新建日程会立马显示
    // 使用当前视图的中心日期
    const formattedDate = currentViewDate.value.toISOString().split('T')[0]
    // 调用API获取所有条目，刷新前端
    const refreshedResponse = await entriesAPI.getEntriesByDate(formattedDate, updateEventAbortController.signal)
    const refreshedEntries = Array.isArray(refreshedResponse) ? refreshedResponse : (refreshedResponse.entries || [])
    // 更新entryStore.entries数组
    entryStore.setEntries(refreshedEntries)
    // 更新日历事件
    updateCalendarEvents(refreshedEntries)
    console.log('已刷新日历，新建日程已显示')
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('更新事件请求已取消')
      return
    }
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
      
      // 从日历视图中移除事件
      deletedEvent.remove()
    }
  }
  
  // 刷新日历数据，确保删除后数据准确
  try {
    // 创建新的AbortController用于此请求
    const deleteEventAbortController = new AbortController()
    
    // 使用当前视图的中心日期
    const formattedDate = currentViewDate.value.toISOString().split('T')[0]
    // 调用API获取所有条目，刷新前端
    const refreshedResponse = await entriesAPI.getEntriesByDate(formattedDate, deleteEventAbortController.signal)
    const refreshedEntries = Array.isArray(refreshedResponse) ? refreshedResponse : (refreshedResponse.entries || [])
    // 更新entryStore.entries数组
    entryStore.setEntries(refreshedEntries)
    // 更新日历事件
    updateCalendarEvents(refreshedEntries)
    console.log('已刷新日历，删除的日程已更新')
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('刷新日历请求已取消')
      return
    }
    console.error('刷新日历失败:', error)
    // 移除不必要的alert，只在控制台打印错误信息
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
</script><style scoped>
/* ==============================================
   日历组件样式重构
   ==============================================
   1. 基础布局
   2. 日历容器和视图结构
   3. 滚动条样式
   4. 工具栏和按钮样式
   5. 日历视图网格和分隔线
   6. 事件样式
   7. 快速跳转日历
   8. 加载状态
   ============================================== */

/* 1. 基础布局 */
.calendar-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

/* 2. 日历容器和视图结构 */
.fc {
  margin: 0;
  padding: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.fc .fc-view {
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
}

.fc-timegrid {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.fc-timegrid .fc-timegrid-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.fc-timegrid-main {
  flex: 1;
  overflow: hidden;
  height: 100%;
}

.fc-timegrid-table {
  height: 100%;
  table-layout: fixed;
}

.fc-timegrid-body .fc-scroller {
  flex: 1;
  min-height: 0;
}

.fc .fc-daygrid-body,
.fc .fc-timegrid-body {
  overflow: hidden;
}

/* 3. 滚动条样式 */
.fc-scroller {
  overflow-y: auto;
  overflow-x: hidden;
  flex: 1;
  min-height: 0;
  height: auto;
  max-height: calc(100vh - 250px);
  position: relative;
  scrollbar-width: thin;
  scrollbar-color: var(--primary-color) transparent;
}

.fc-scroller::-webkit-scrollbar {
  width: 6px;
}

.fc-scroller::-webkit-scrollbar-track {
  background: transparent;
}

.fc-scroller::-webkit-scrollbar-thumb {
  background-color: var(--primary-color);
  border-radius: 3px;
  border: 2px solid transparent;
  background-clip: content-box;
}

/* 4. 工具栏和按钮样式 */
.fc-header-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.fc-toolbar-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  flex: 1;
  margin: 0 1rem;
}

/* 基础按钮样式 - 使用:deep()穿透组件封装，添加!important确保优先级 */
:deep(.fc-button) {
  background-color: var(--primary-color) !important;
  color: white !important;
  border: none !important;
  padding: 0.5rem 1rem !important;
  border-radius: 4px !important;
  cursor: pointer !important;
  font-size: 0.85rem !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
  font-weight: 500 !important;
  line-height: 1.5 !important;
  height: auto !important;
  min-height: 36px !important;
  text-transform: none !important;
}

:deep(.fc-button:hover) {
  background-color: var(--primary-dark) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(74, 144, 226, 0.3) !important;
}

:deep(.fc-button:active) {
  transform: translateY(-1px) scale(0.95) !important;
}

:deep(.fc-button:focus) {
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
  outline: none !important;
}

/* 自定义按钮样式 - 确保主题色正确应用 */
:deep(.fc-quickJump-button),
:deep(.fc-batchAdd-button),
:deep(.fc-today-button),
:deep(.fc-prev-button),
:deep(.fc-next-button) {
  background-color: var(--primary-color) !important;
  color: white !important;
}

:deep(.fc-today-button.fc-button-active) {
  background-color: var(--primary-dark) !important;
}

/* 5. 日历视图网格和分隔线 */
/* 时间轴样式 */
:deep(.fc-timegrid-axis) {
  border-right: 1px dashed #e0e0e0;
  z-index: 0;
  color: var(--text-primary);
  font-weight: 500;
  font-size: 0.75rem;
}

/* 日期列样式 */
:deep(.fc-timegrid-view .fc-timegrid-col) {
  width: 14.28%;
}

/* 列标题样式 */
:deep(.fc-day-header) {
  color: var(--text-primary);
  font-weight: 600;
  background-color: rgba(255, 255, 255, 0.95);
  border-bottom: 1px dashed #e0e0e0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 表格分隔线样式 */
:deep(.fc-timegrid-divider) {
  border-color: #e0e0e0;
  border-style: dashed;
  z-index: 0;
}

:deep(.fc-timegrid-col-bg .fc-timegrid-slot) {
  border-color: #e0e0e0;
  border-style: dashed;
}

/* 23:00特殊分隔线 */
:deep(.fc-timegrid-view .fc-timegrid-slot[data-time="23:00:00"]) {
  border-bottom: 2px solid #000000;
  position: relative;
  z-index: 1;
}

/* 隐藏24点时间槽 */
:deep(.fc-timegrid-view .fc-timegrid-slot[data-time="24:00:00"]) {
  display: none;
  height: 0;
  margin: 0;
  padding: 0;
}

/* 时间槽z-index管理 */
:deep(.fc-timegrid-slot) {
  position: relative;
  z-index: 1;
}

/* 6. 事件样式 */
/* 分开处理日程长度和字体大小：
   - 日程长度（事件高度）使用:root选择器
   - 字体大小使用:deep()选择器 */

/* ----------------------
   日程长度（事件高度）设置 - 使用:root选择器
   ---------------------- */
/* 确保事件块高度与实际时长正相关 */
:root .fc-event {
  /* 确保事件块高度由FullCalendar自动计算，不设置固定高度 */
  min-height: auto !important;
  height: auto !important;
  /* 其他基础样式 */
  padding: 3px 5px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: none;
  transition: all 0.2s ease;
  position: relative;
  z-index: 2;
}

:root .fc-event:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* 确保时间网格视图中的事件高度与时长正相关 */
:root .fc-timegrid-event {
  /* 移除所有可能影响高度计算的固定高度设置 */
  height: auto !important;
  min-height: auto !important;
  /* 使用FullCalendar的CSS变量控制事件高度，auto表示由时长自动计算 */
  --fc-timegrid-event-min-height: auto !important;
  /* 确保事件容器高度正确 */
  --fc-event-min-height: auto !important;
}

/* 确保事件容器正确计算高度 */
:root .fc-timegrid-event-harness {
  height: auto !important;
  min-height: auto !important;
}

/* 确保事件内容正确显示 */
:root .fc-timegrid-event-main {
  padding: 2px 4px;
  height: auto !important;
  min-height: auto !important;
}

/* 确保可拖动事件也保持正确的高度 */
:root .fc-timegrid-event.fc-event-draggable {
  height: auto !important;
  min-height: auto !important;
}

/* 确保事件内容区域正确计算高度 */
:root .fc-timegrid-event .fc-event-main-frame {
  height: auto !important;
  min-height: auto !important;
}

/* 确保事件标题区域正确计算高度 */
:root .fc-timegrid-event .fc-event-content {
  height: auto !important;
  min-height: auto !important;
  padding: 0;
  margin: 0;
}

/* 确保事件内容高度正确 */
:root .fc-event-main {
  height: auto !important;
  min-height: auto !important;
}

/* ----------------------
   字体大小设置 - 使用:deep()选择器
   ---------------------- */
/* 事件块整体字体大小 */
:deep(.fc-event) {
  font-size: 0.7rem !important;
}

/* 事件标题统一样式 - 直接定位到标题元素 */
:deep(.fc-event-title) {
  font-size: 0.7rem !important;
  line-height: 1.2 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* 事件时间字体大小 */
:deep(.fc-event-time) {
  font-size: inherit !important;
  margin-bottom: 0 !important;
}

/* 7. 快速跳转日历样式 */
.quick-jump-calendar {
  position: absolute;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 5px;
  background-color: white;
  border: 1px solid var(--border-color);
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
  background-color: var(--primary-color);
  border: 1px solid var(--primary-dark);
  width: 30px;
  height: 30px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  color: white;
}

.month-nav-btn:hover {
  background-color: var(--primary-dark);
  border-color: var(--primary-dark);
}

.current-month {
  font-weight: 500;
  font-size: 0.95rem;
  color: var(--text-primary);
}

/* 日历网格 */
.calendar-grid {
  display: flex;
  flex-direction: column;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0;
  margin-bottom: 0.5rem;
}

.weekday {
  text-align: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 0.25rem 0;
}

.days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.25rem;
}

.day {
  position: relative;
  padding: 0.5rem;
  text-align: center;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.day:hover {
  background-color: var(--bg-secondary);
}

.day.today {
  background-color: var(--primary-light);
  color: var(--primary-color);
  font-weight: 600;
}

.day.selected {
  background-color: var(--primary-color);
  color: white;
  font-weight: 600;
}

.day.empty {
  cursor: default;
}

.day.empty:hover {
  background-color: transparent;
}

/* 日程指示器 */
.schedule-indicator {
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
}

/* 8. 加载状态 */
.loading-corner {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  font-size: 0.8rem;
  color: var(--text-primary);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-left-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 0.8rem;
  color: var(--text-primary);
}
</style>
