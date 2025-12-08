<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>创建日常任务</h3>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label for="task-title">任务标题</label>
          <input type="text" id="task-title" v-model="formData.title" placeholder="请输入任务标题" class="form-input" required>
        </div>
        
        <div class="form-group">
          <label for="task-type">重复类型</label>
          <select id="task-type" v-model="formData.taskType" class="form-input">
            <option value="daily">每天</option>
            <option value="weekly">指定星期几</option>
          </select>
        </div>
        
        <div class="form-group" v-if="formData.taskType === 'weekly'">
          <label>选择重复的星期几</label>
          <div class="weekday-selector">
            <label v-for="day in weekdays" :key="day.value" class="weekday-option">
              <input type="checkbox" v-model="formData.selectedDays" :value="day.value">
              <span>{{ day.label }}</span>
            </label>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="start-date">开始日期</label>
            <input type="date" id="start-date" v-model="formData.startDate" class="form-input" required>
          </div>
          <div class="form-group">
            <label for="end-date">结束日期</label>
            <input type="date" id="end-date" v-model="formData.endDate" class="form-input" required>
          </div>
        </div>
        <div class="form-hint">
          任务将在指定日期范围内，按照选择的重复规则自动创建。
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="start-time">开始时间</label>
            <input type="time" id="start-time" v-model="formData.startTime" class="form-input" required>
          </div>
          <div class="form-group">
            <label for="end-time">结束时间</label>
            <input type="time" id="end-time" v-model="formData.endTime" class="form-input" required>
          </div>
        </div>
        
        <div class="form-group">
          <label for="entry-type">日程类型</label>
          <select id="entry-type" v-model="formData.entryType" class="form-input">
            <option value="course">课程</option>
            <option value="lecture">讲座</option>
            <option value="meeting">会议</option>
            <option value="individual_homework">个人作业</option>
            <option value="group_report">小组汇报</option>
            <option value="exam_prep">考试备考</option>
            <option value="work_delivery">工作交付</option>
            <option value="sports">运动</option>
            <option value="study">学习</option>
            <option value="other">其他</option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="description">描述</label>
          <textarea id="description" v-model="formData.description" placeholder="请输入任务描述" class="form-input" rows="3"></textarea>
        </div>
      </div>
      <div class="form-actions">
        <button class="cancel-btn" @click="$emit('close')">取消</button>
        <button class="save-btn" @click="handleBatchAdd" :disabled="isSubmitting">
          {{ isSubmitting ? '创建中...' : '创建日常任务' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { entriesAPI } from '../services/api'

const emit = defineEmits(['close', 'success'])

// 表单数据
const formData = reactive({
  title: '',
  taskType: 'daily', // 'daily' 或 'weekly'
  selectedDays: [1, 2, 3, 4, 5], // 默认选择周一至周五
  startDate: new Date().toISOString().split('T')[0],
  endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 默认7天后
  startTime: '09:00',
  endTime: '10:00',
  entryType: 'other',
  description: ''
})

const isSubmitting = ref(false)

// 星期选项
const weekdays = [
  { value: 0, label: '周日' },
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' }
]

// 创建日常任务
const handleBatchAdd = async () => {
  if (!formData.title) return
  
  isSubmitting.value = true
  
  try {
    const startDate = new Date(formData.startDate)
    const endDate = new Date(formData.endDate)
    
    // 生成所有需要添加的日期
    const datesToAdd = []
    let currentDate = new Date(startDate)
    
    while (currentDate <= endDate) {
      if (formData.taskType === 'daily' || formData.selectedDays.includes(currentDate.getDay())) {
        datesToAdd.push(new Date(currentDate))
      }
      currentDate.setDate(currentDate.getDate() + 1)
    }
    
    if (datesToAdd.length === 0) {
      alert('请选择有效的日期范围和重复规则')
      isSubmitting.value = false
      return
    }
    
    // 批量创建日常任务
    const promises = datesToAdd.map(date => {
      // 构建本地时间格式的datetime字符串，避免时区转换问题
      // 格式：YYYY-MM-DDTHH:mm:ss
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      
      const startDateTimeStr = `${year}-${month}-${day}T${formData.startTime}:00`
      const endDateTimeStr = `${year}-${month}-${day}T${formData.endTime}:00`
      
      return entriesAPI.addEntry({
        title: formData.title,
        description: formData.description,
        entry_type: formData.entryType,
        start_time: startDateTimeStr,
        end_time: endDateTimeStr
      })
    })
    
    await Promise.all(promises)
    
    // 发送成功事件
    emit('success', datesToAdd.length)
    // 关闭模态框
    emit('close')
  } catch (error) {
    console.error('创建日常任务失败:', error)
    alert('创建日常任务失败，请稍后重试')
  } finally {
    isSubmitting.value = false
  }
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

.form-hint {
  color: #666;
  font-size: 0.9rem;
  margin-top: -0.5rem;
  margin-bottom: 1rem;
  font-style: italic;
}

.weekday-selector {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.weekday-option {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e0e0e0;
  background-color: #f9f9f9;
}

.cancel-btn {
  padding: 0.75rem 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background-color: #f5f5f5;
}

.save-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  background-color: #4a90e2;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.save-btn:hover {
  background-color: #357abd;
}

.save-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>