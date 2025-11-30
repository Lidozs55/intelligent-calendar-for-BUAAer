<template>
  <div class="calendar-container">
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
import { ref, onMounted, onUnmounted, watch } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { useCourseStore, useUserStore, useTaskStore, useEntryStore } from '../store'
import { coursesAPI, tasksAPI, entriesAPI } from '../services/api'
import EventEditModal from './EventEditModal.vue'

const calendarRef = ref(null)
const courseStore = useCourseStore()
const userStore = useUserStore()
const taskStore = useTaskStore()
const entryStore = useEntryStore()

// 编辑模态框状态
const showEditModal = ref(false)
const editingEvent = ref(null)

// 临时事件引用
let tempEvent = null

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
      day: '日',
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
      fetchDataAndUpdateCalendar()
    },
    
    // 日期渲染事件，用于自定义表头样式和日期导航
    datesSet: (info) => {
      console.log('日期范围已设置:', info)
      // 确保始终显示7天
      if (info.view.type === 'timeGridWeek') {
        info.view.calendar.setOption('duration', { days: 7 })
      }
      
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
      tempEvent = selectInfo.view.calendar.addEvent({
        title: '新建事件',
        start: selectInfo.start,
        end: selectInfo.end,
        backgroundColor: 'rgba(74, 144, 226, 0.5)',
        borderColor: '#4a90e2',
        allDay: false,
        extendedProps: {
          type: 'temp', // 标记为临时事件
          isTemp: true
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
      
      tempEvent = info.view.calendar.addEvent({
        title: '新建事件',
        start: info.date,
        end: endTime,
        backgroundColor: 'rgba(74, 144, 226, 0.5)',
        borderColor: '#4a90e2',
        allDay: false,
        extendedProps: {
          type: 'meeting', // 默认类型
          isTemp: true
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
// 最大显示长度：18个单位（9个中文字符或18个英文字符）
const truncateString = (str, maxDisplayLength = 17) => {
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
        type: entry.entry_type // 添加类型标识
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

/* 调整列宽，使用百分比大小 */
:deep(.fc-timegrid-view .fc-timegrid-col) {
  width: 14.28% !important; /* 7天，每天约14.28% */
}

/* 在23:00和0:00的分界位置添加加粗的黑线 */
:deep(.fc-timegrid-view .fc-timegrid-slot[data-time="23:00:00"]) {
  border-bottom: 3px solid #000000 !important;
  z-index: 1 !important;
}

/* 确保分隔线显示在表格上方但在日程下方 */
:deep(.fc-timegrid-slot) {
  position: relative;
  z-index: 1 !important;
}

:deep(.fc-timegrid-view .fc-event) {
  position: relative;
  z-index: 2 !important;
}

/* 确保时间段显示完整并保留滚动条 */
:deep(.fc-scroller) {
  overflow-y: auto !important;
  overflow-x: hidden !important;
  max-height: calc(100vh - 220px) !important;
  position: relative;
}

</style>
