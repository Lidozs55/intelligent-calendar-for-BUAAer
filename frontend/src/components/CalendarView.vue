<template>
  <div class="calendar-container">
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

// 事件类型到默认颜色的映射（使用深色系，确保白色字体清晰可见）
const typeToColor = {
  course: '#2c3e50',       // 深蓝灰色
  lecture: '#34495e',      // 深灰色
  exam: '#c0392b',         // 深红色
  meeting: '#27ae60',      // 深绿色
  homework: '#8e44ad',     // 深紫色
  exercise: '#16a085',     // 深青色
  sports: '#f39c12',       // 深橙色
  study: '#2980b9',        // 深蓝色
  other: '#7f8c8d'         // 深灰色
}

// 临时事件引用
let tempEvent = null

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
        // 每天显示到28:00（即第二天的4:00）
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
      
      // 添加定时器定期检查并修复日历标题
      setTimeout(() => {
        fixCalendarTitle()
      }, 100)
    },
    
    // 视图切换事件
    viewDidChange: () => {
      setTimeout(() => {
        fixCalendarTitle()
      }, 100)
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
      
      // 修复日历标题
      setTimeout(() => {
        fixCalendarTitle()
      }, 50)
      
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
const fetchDataAndUpdateCalendar = async () => {
  // 从API获取所有条目数据
  try {
    const response = await entriesAPI.getEntries()
    // 处理API返回的数据结构，确保获取到正确的条目数组
    const entries = Array.isArray(response) ? response : (response.entries || [])
    // 更新entryStore.entries数组
    entryStore.setEntries(entries)
    
    // 更新日历事件
    updateCalendarEvents(entries)
  } catch (error) {
    console.error('加载条目失败:', error)
    
    // 清空日历事件
    if (calendarRef.value) {
      const calendarApi = calendarRef.value.getApi()
      calendarApi.removeAllEvents()
    }
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
  let calendarEvents = entries.map(entry => {
    return {
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
    }
  })
  
  console.log('最终的日历事件:', calendarEvents.map(event => ({
    id: event.id,
    title: event.title,
    entry_type: event.extendedProps.type,
    editable: event.editable
  })))
  
  // 更新日历事件
  if (calendarRef.value) {
    const calendarApi = calendarRef.value.getApi()
    calendarApi.removeAllEvents()
    calendarApi.addEventSource(calendarEvents)
    console.log('日历事件已更新')
  } else {
    console.error('calendarRef.value为null，无法更新日历事件')
    // 如果calendarRef不可用，使用setTimeout重试
    setTimeout(() => {
      if (calendarRef.value) {
        const calendarApi = calendarRef.value.getApi()
        calendarApi.removeAllEvents()
        calendarApi.addEventSource(calendarEvents)
        console.log('延迟更新日历事件成功')
      }
    }, 500)
  }
}

// 处理事件更新
const handleEventUpdate = async (eventData) => {
  console.log('更新事件:', eventData)
  
  // 重新从API获取数据并更新日历
  await fetchDataAndUpdateCalendar()
  
  // 确保临时事件被销毁
  destroyTempEvent()
}

// 处理事件删除
const handleEventDelete = async (eventId) => {
  console.log('删除事件:', eventId)
  // 重新从API获取数据并更新日历
  await fetchDataAndUpdateCalendar()
}

// 修复日历标题，将结束日期减1天
const fixCalendarTitle = () => {
  const titleEl = document.querySelector('.fc-toolbar-title')
  if (titleEl) {
    const titleText = titleEl.textContent
    // 匹配日期范围格式：YYYY年MM月DD日 – YYYY年MM月DD日
    const dateRangeRegex = /(\d{4})年(\d{1,2})月(\d{1,2})日 – (\d{4})年(\d{1,2})月(\d{1,2})日/;
    const match = titleText.match(dateRangeRegex)
    console.log("fix calendar title")
    if (match) {
      console.log("fixing calendar title")
      // 解析日期
      const endYear = parseInt(match[4])
      const endMonth = parseInt(match[5]) - 1 // 月份转为0-11
      const endDay = parseInt(match[6])
      
      // 创建结束日期对象并减1天
      const endDate = new Date(endYear, endMonth, endDay)
      endDate.setDate(endDate.getDate() - 1)
      
      // 格式化新的结束日期
      const newEndYear = endDate.getFullYear()
      const newEndMonth = endDate.getMonth() + 1 // 月份转为1-12
      const newEndDay = endDate.getDate()
      
      // 构建新的标题文本
      const newTitle = `${match[1]}年${match[2]}月${match[3]}日 – ${newEndYear}年${newEndMonth}月${newEndDay}日`
      titleEl.textContent = newTitle
    }
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
  
  // 添加事件监听器
  document.addEventListener('click', handleGlobalClick);
  
  // 组件卸载时移除事件监听器
  onUnmounted(() => {
    document.removeEventListener('click', handleGlobalClick);
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

/* 快速跳转功能样式 */
.quick-jump-container {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
}

.quick-jump-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 0.5rem;
}

.weekday {
  text-align: center;
  font-size: 0.8rem;
  font-weight: 500;
  color: #666;
  padding: 0.5rem 0;
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

/* 在23:00和0:00的分界位置添加加粗的黑线 */
:deep(.fc-timegrid-view .fc-timegrid-slot[data-time="23:00:00"]) {
  border-bottom: 3px solid #000000 !important;
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
}

/* 确保网格线的z-index低于分隔线 */
:deep(.fc-timegrid-divider) {
  z-index: 0 !important;
}

/* 确保时间轴的z-index低于分隔线 */
:deep(.fc-timegrid-axis) {
  z-index: 0 !important;
}

/* 确保时间段显示完整并保留滚动条 */
:deep(.fc-scroller) {
  overflow-y: auto !important;
  overflow-x: hidden !important;
  max-height: calc(100vh - 220px) !important;
  position: relative;
}

/* 调整日程块样式：字体适当缩小，增加内边距 */
:deep(.fc-event) {
  font-size: 0.75rem !important;
  padding: 0px 4px !important;
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
