<template>
  <div v-if="visible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ event ? '编辑日程' : '创建日程' }}</h3>
        <button @click="closeModal" class="close-btn">×</button>
      </div>
      
      <div class="modal-body">
        <form @submit.prevent="saveEvent">
          <div class="form-group">
            <label for="event-title">日程标题</label>
            <input 
              type="text" 
              id="event-title" 
              v-model="formData.title" 
              required 
              class="form-input"
            />
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label for="event-type">事件类型</label>
              <select 
                id="event-type" 
                v-model="formData.extendedProps.type" 
                class="form-input"
              >
                <option value="course">课程</option>
                <option value="lecture">讲座</option>
                <option value="exam">考试</option>
                <option value="meeting">会议</option>
                <option value="homework">作业</option>
                <option value="exercise">作业完成</option>
                <option value="sports">体育运动</option>
                <option value="study">学习</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="event-color">展示颜色</label>
              <input 
                type="color" 
                id="event-color" 
                v-model="formData.backgroundColor" 
                class="form-input color-input"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label for="event-start">开始时间</label>
              <input 
                type="datetime-local" 
                id="event-start" 
                v-model="formData.start" 
                required 
                class="form-input"
              />
            </div>
            
            <div class="form-group">
              <label for="event-end">结束时间</label>
              <input 
                type="datetime-local" 
                id="event-end" 
                v-model="formData.end" 
                required 
                class="form-input"
              />
            </div>
          </div>
          
          <div class="form-actions">
            <button type="button" @click="deleteEvent" class="delete-btn">删除日程</button>
            <div>
              <button type="button" @click="closeModal" class="cancel-btn">取消</button>
              <button type="submit" class="save-btn">保存</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { entriesAPI } from '../services/api'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  event: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['close', 'update', 'delete'])

// 表单数据
const formData = ref({
  id: null,
  title: '',
  start: '',
  end: '',
  backgroundColor: '#000000',
  borderColor: '#000000',
  allDay: false,
  extendedProps: {
    type: 'meeting'
  }
})

// 重置表单
const resetForm = () => {
  formData.value = {
    id: null,
    title: '',
    start: '',
    end: '',
    backgroundColor: '#000000',
    borderColor: '#000000',
    allDay: false,
    extendedProps: {
      type: 'meeting'
    }
  }
}

// 监听事件变化，更新表单数据
watch(() => props.event, (newEvent) => {
  if (newEvent) {
    // 格式化日期时间
    // 确保使用UTC时间创建Date对象，避免时区转换问题
    const start = new Date(newEvent.start)
    const end = new Date(newEvent.end)
    
    // 转换为datetime-local格式（本地时间）
    const formatDateTime = (date) => {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day}T${hours}:${minutes}`
    }
    
    // 更新表单数据
    formData.value = {
      id: newEvent.id,
      title: newEvent.title,
      start: formatDateTime(start),
      end: formatDateTime(end),
      backgroundColor: newEvent.extendedProps.isTemp ? '#000000' : newEvent.backgroundColor,
      borderColor: newEvent.extendedProps.isTemp ? '#000000' : newEvent.borderColor,
      allDay: newEvent.allDay,
      extendedProps: {
        type: newEvent.extendedProps.type || 'meeting'
      }
    }
  } else {
    // 重置表单
    resetForm()
  }
}, { immediate: true })

// 保存事件
const saveEvent = async () => {
  try {
    // 转换为后端API期望的格式
    // 直接使用formData.value.start和formData.value.end，它们是本地时间格式
    // 后端会将其解析为datetime对象，SQLite会存储为UTC时间
    const entryData = {
      title: formData.value.title,
      description: '', // 暂时为空，后续可以添加描述字段
      entry_type: formData.value.extendedProps.type,
      start_time: formData.value.start,
      end_time: formData.value.end,
      color: formData.value.backgroundColor
    }
    
    // 调用API保存事件
    if (formData.value.id) {
      // 更新现有事件
      await entriesAPI.updateEntry(formData.value.id, entryData)
    } else {
      // 创建新事件
      await entriesAPI.addEntry(entryData)
    }
    
    // 关闭模态框并通知父组件
    emit('update', formData.value)
    closeModal()
  } catch (error) {
    console.error('保存事件失败:', error)
    // 更详细的错误信息
    if (error.response) {
      console.error('错误响应:', error.response.data)
      alert(`保存事件失败: ${error.response.data.message || '未知错误'}`)
    } else if (error.request) {
      console.error('错误请求:', error.request)
      alert('保存事件失败: 网络错误，请检查网络连接')
    } else {
      console.error('错误信息:', error.message)
      alert(`保存事件失败: ${error.message}`)
    }
  }
}

// 删除事件
const deleteEvent = async () => {
  if (confirm('确定要删除这个日程吗？')) {
    try {
      if (formData.value.id) {
        // 调用API删除事件
      await entriesAPI.deleteEntry(formData.value.id)
        
        // 关闭模态框并通知父组件
        emit('delete', formData.value.id)
        closeModal()
      }
    } catch (error) {
      console.error('删除事件失败:', error)
      // 更详细的错误信息
      if (error.response) {
        console.error('错误响应:', error.response.data)
        alert(`删除事件失败: ${error.response.data.message || '未知错误'}`)
      } else if (error.request) {
        console.error('错误请求:', error.request)
        alert('删除事件失败: 网络错误，请检查网络连接')
      } else {
        console.error('错误信息:', error.message)
        alert(`删除事件失败: ${error.message}`)
      }
    }
  }
}

// 关闭模态框
const closeModal = () => {
  emit('close')
  resetForm()
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background-color: #f5f5f5;
  color: #333;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-row .form-group {
  flex: 1;
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

.color-input {
  padding: 0.25rem;
  height: 44px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.form-actions > div {
  display: flex;
  gap: 1rem;
}

.delete-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s ease;
}

.delete-btn:hover {
  background-color: #d32f2f;
}

.cancel-btn {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #e0e0e0;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background-color: #e0e0e0;
}

.save-btn {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s ease;
}

.save-btn:hover {
  background-color: #357abd;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
  }
  
  .form-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .form-actions > div {
    justify-content: space-between;
  }
}
</style>