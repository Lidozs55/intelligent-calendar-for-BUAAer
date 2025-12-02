<template>
  <div class="task-sidebar">
  <div class="sidebar-header">
    <h2>任务管理</h2>
  </div>
  
  <!-- 任务统计和进度条合并区域 -->
  <div class="stats-progress-section">
    <!-- 任务统计信息 -->
    <div class="task-stats">
      <div class="stat-item">
        <span class="stat-label">待完成</span>
        <span class="stat-value">{{ tasks.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已完成</span>
        <span class="stat-value">{{ completedTasks.length }}</span>
      </div>
      <div class="stat-item progress-stat">
        <span class="stat-label">完成率</span>
        <span class="stat-value">{{ progressPercentage }}%</span>
      </div>
    </div>
    
    <!-- 任务进度条 -->
    <div class="progress-bar-container">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${progressPercentage}%` }"></div>
      </div>
      <div class="progress-details">
        <span>已完成 {{ completedTasks.length }} / {{ totalTasks }} 个任务</span>
      </div>
    </div>
  </div>
    
    <div class="task-filter">
      <div class="filter-row">
        <div class="filter-item">
          <label for="status-filter">状态:</label>
          <select 
            id="status-filter"
            v-model="activeFilter"
            class="filter-select"
          >
            <option value="all">全部</option>
            <option value="pending">待完成</option>
            <option value="completed">已完成</option>
          </select>
        </div>
      </div>
    </div>
  
  <!-- 滚动内容区域：包含即将到期任务和任务列表 -->
  <div class="scrollable-content">
    <!-- 即将到期任务提醒 -->
    <div v-if="showUpcomingTasks && upcomingTasks.length > 0" class="upcoming-tasks-section">
      <div class="upcoming-header">
        <h3>即将到期任务</h3>
        <div class="upcoming-header-actions">
          <span class="upcoming-count">{{ upcomingTasks.length }}</span>
          <button class="close-upcoming-btn" @click="hideUpcomingTasks">×</button>
        </div>
      </div>
      <div class="upcoming-list">
        <div v-for="task in upcomingTasks" :key="task.id" class="upcoming-task">
          <div class="upcoming-task-content">
            <h4 class="upcoming-task-title">{{ task.title }}</h4>
            <p class="upcoming-task-deadline">
              截止时间：{{ formatDate(task.deadline) }}
            </p>
          </div>
          <button 
            :class="['mark-complete-btn', { 'undo-btn': task.completed }]" 
            @click="toggleTaskCompletion(task)"
          >
            {{ task.completed ? '还未完成' : '完成' }}
          </button>
        </div>
      </div>
    </div>
    
    <div class="task-list">
      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>
      
      <div v-else-if="error" class="error-state">
        <p>加载失败: {{ error }}</p>
      </div>
      
      <div v-else-if="displayTasks.length === 0" class="empty-state">
        <p>暂无任务</p>
        <button class="add-task-btn" @click="addNewTask">添加任务</button>
      </div>
      
      <div v-else>
        <div 
          v-for="task in displayTasks" 
          :key="task.id" 
          class="task-item"
          :class="{ completed: task.completed }"
        >
          <div class="task-checkbox">
            <input 
              type="checkbox" 
              :checked="task.completed" 
              @change="toggleTaskCompletion(task)"
            />
          </div>
          
          <div class="task-content">
            <h3 class="task-title">{{ task.title }}</h3>
            <p v-if="task.description" class="task-description">{{ task.description }}</p>
            <div class="task-meta">
              <span class="task-type">{{ getTaskTypeLabel(task.task_type) }}</span>
              <span v-if="task.deadline" class="task-deadline">
                {{ formatDate(task.deadline) }}
              </span>
              <span class="task-priority" :class="task.priority">
                {{ getPriorityLabel(task.priority) }}
              </span>
            </div>
          </div>
          
          <div class="task-actions">
            <button @click="editTask(task)">编辑</button>
            <button @click="deleteTask(task.id)">删除</button>
          </div>
        </div>
      </div>
    </div>
  </div>
    
    <div class="sidebar-footer">
      <button class="add-task-btn" @click="addNewTask">+ 添加任务</button>
    </div>
    
    <!-- 任务编辑弹窗 -->
    <div v-if="showTaskModal" class="modal-overlay" @click="closeTaskModal">
      <div class="modal-content" @click.stop>
        <h3>{{ editingTask ? '编辑任务' : '添加任务' }}</h3>
        <form @submit.prevent="saveTask">
          <div class="form-group">
            <label for="task-title">任务标题</label>
            <input 
              type="text" 
              id="task-title" 
              v-model="formData.title" 
              required
            />
          </div>
          
          <div class="form-group">
            <label for="task-description">任务描述</label>
            <textarea 
              id="task-description" 
              v-model="formData.description" 
              rows="3"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label for="task-type">任务类型</label>
            <select id="task-type" v-model="formData.task_type">
              <option value="homework">作业</option>
              <option value="exam">考试</option>
              <option value="lecture">讲座</option>
              <option value="meeting">会议</option>
              <option value="other">其他</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="task-deadline">截止日期</label>
            <input 
              type="datetime-local" 
              id="task-deadline" 
              v-model="formData.deadline"
            />
          </div>
          
          <div class="form-group">
            <label for="task-priority">优先级</label>
            <select id="task-priority" v-model="formData.priority">
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
              <option value="urgent">紧急</option>
            </select>
          </div>
          
          <div class="form-actions">
            <button type="button" class="cancel-btn" @click="closeTaskModal">取消</button>
            <button type="submit" class="save-btn">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTaskStore, useUserStore } from '../store'
import { tasksAPI } from '../services/api'

const taskStore = useTaskStore()
const userStore = useUserStore()
const activeFilter = ref('all')
const showTaskModal = ref(false)
const editingTask = ref(null)
const showUpcomingTasks = ref(true)
const formData = ref({
  title: '',
  description: '',
  task_type: 'homework',
  deadline: '',
  priority: 'medium',
  completed: false
})

// 计算属性：根据过滤条件显示任务
const displayTasks = computed(() => {
  let filteredTasks = []
  
  // 只根据状态筛选
  if (activeFilter.value === 'pending') {
    filteredTasks = taskStore.tasks
  } else if (activeFilter.value === 'completed') {
    filteredTasks = taskStore.completedTasks
  } else {
    filteredTasks = [...taskStore.tasks, ...taskStore.completedTasks]
  }
  
  // 按截止时间排序：时间靠前的排在前面，没有截止日期的排在最后
  return filteredTasks.sort((a, b) => {
    // 处理没有截止日期的情况
    if (!a.deadline && !b.deadline) return 0
    if (!a.deadline) return 1 // a没有截止日期，排在后面
    if (!b.deadline) return -1 // b没有截止日期，排在后面
    
    // 都有截止日期，按时间排序
    return new Date(a.deadline) - new Date(b.deadline)
  })
})

// 计算属性：总任务数
const totalTasks = computed(() => {
  return taskStore.tasks.length + taskStore.completedTasks.length
})

// 计算属性：任务完成百分比
const progressPercentage = computed(() => {
  if (totalTasks.value === 0) return 0
  return Math.round((taskStore.completedTasks.length / totalTasks.value) * 100)
})

// 计算属性：获取任务和已完成的任务
const loading = computed(() => taskStore.loading)
const error = computed(() => taskStore.error)
const tasks = computed(() => taskStore.tasks)
const completedTasks = computed(() => taskStore.completedTasks)

// 计算属性：即将到期的任务（24小时内）
const upcomingTasks = computed(() => {
  const now = new Date()
  const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000)
  
  // 获取所有任务，包括已完成和未完成
  const allTasks = [...taskStore.tasks, ...taskStore.completedTasks]
  
  return allTasks
    .filter(task => {
      if (!task.deadline) return false
      const deadline = new Date(task.deadline)
      return deadline >= now && deadline <= tomorrow
    })
    .sort((a, b) => {
      // 按截止时间排序，时间靠前的排在前面
      return new Date(a.deadline) - new Date(b.deadline)
    })
})

// 加载任务数据
const loadTasks = async () => {
  taskStore.setLoading(true)
  try {
    // 从API获取所有任务（包括已完成和未完成）
    const response = await tasksAPI.getTasks(null)
    console.log('API返回的任务数据:', response)
    
    // 确保response.tasks是数组
    const tasks = Array.isArray(response.tasks) ? response.tasks : []
    console.log('处理后的任务数据:', tasks)
    
    // 更新任务状态
    taskStore.setTasks(tasks)
    console.log('更新后的taskStore状态:', {
      tasks: taskStore.tasks,
      completedTasks: taskStore.completedTasks,
      totalTasks: taskStore.tasks.length + taskStore.completedTasks.length
    })
  } catch (err) {
    console.error('加载任务失败:', err)
    taskStore.setError(err.message || '加载任务失败')
  } finally {
    taskStore.setLoading(false)
  }
}

// 切换任务完成状态
const toggleTaskCompletion = async (task) => {
  // 直接切换任务的完成状态，不依赖v-model
  const newCompletedState = !task.completed
  
  try {
    // 调用API更新任务状态
    if (newCompletedState) {
      // 标记任务为完成
      await tasksAPI.completeTask(task.id)
    } else {
      // 标记任务为未完成
      await tasksAPI.uncompleteTask(task.id)
    }
    // 重新加载任务列表，确保数据最新
    await loadTasks()
  } catch (err) {
    console.error('更新任务状态失败:', err)
    // 重新加载任务列表，确保数据最新
    await loadTasks()
  }
}

// 添加新任务
const addNewTask = () => {
  editingTask.value = null
  formData.value = {
    title: '',
    description: '',
    task_type: 'homework',
    deadline: '',
    priority: 'medium',
    completed: false
  }
  showTaskModal.value = true
}

// 编辑任务
const editTask = (task) => {
  editingTask.value = task
  formData.value = {
    title: task.title,
    description: task.description,
    task_type: task.task_type,
    deadline: task.deadline ? formatDateTimeForInput(task.deadline) : '',
    priority: task.priority,
    completed: task.completed
  }
  showTaskModal.value = true
}

// 格式化日期时间为datetime-local输入框格式（处理UTC时间）
const formatDateTimeForInput = (dateString) => {
  const date = new Date(dateString)
  // 确保正确显示本地时间
  // 例如：后端返回的是UTC时间07:00Z，前端显示为本地时间15:00
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

// 保存任务
const saveTask = async () => {
  const taskData = {
    ...formData.value,
    deadline: formData.value.deadline ? formData.value.deadline : null,
    user_id: userStore.buaaId
  }
  
  try {
    if (editingTask.value) {
      // 更新任务
      await tasksAPI.updateTask(editingTask.value.id, taskData)
    } else {
      // 添加任务
      await tasksAPI.addTask(taskData)
    }
    
    // 重新加载任务列表，确保数据最新
    await loadTasks()
    
    closeTaskModal()
  } catch (err) {
    console.error('保存任务失败:', err)
    alert('保存任务失败，请重试')
  }
}

// 删除任务
const deleteTask = async (taskId) => {
  if (confirm('确定要删除这个任务吗？')) {
    try {
      // 调用API删除任务
      await tasksAPI.deleteTask(taskId)
      // 重新加载任务列表，确保数据最新
      await loadTasks()
    } catch (err) {
      console.error('删除任务失败:', err)
      alert('删除任务失败，请重试')
    }
  }
}

// 关闭任务弹窗
const closeTaskModal = () => {
  showTaskModal.value = false
  editingTask.value = null
  formData.value = {
    title: '',
    description: '',
    task_type: 'homework',
    deadline: '',
    priority: 'medium',
    completed: false
  }
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 获取任务类型标签
const getTaskTypeLabel = (type) => {
  const typeMap = {
    homework: '作业',
    exam: '考试',
    lecture: '讲座',
    meeting: '会议',
    other: '其他'
  }
  return typeMap[type] || type
}

// 获取优先级标签
const getPriorityLabel = (priority) => {
  const priorityMap = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return priorityMap[priority] || priority
}

// 隐藏即将到期任务窗口
const hideUpcomingTasks = () => {
  // 这里我们不直接修改upcomingTasks，而是通过计算属性的依赖来控制显示
  // 由于upcomingTasks是计算属性，我们需要通过其他方式来控制显示
  // 这里我们可以通过添加一个状态变量来控制
  showUpcomingTasks.value = false
}

// 初始化加载任务
onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.task-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1rem;
}

.sidebar-header {
  margin-bottom: 0.75rem;
}

.sidebar-header h2 {
  font-size: 1.25rem;
  margin: 0;
  color: #333;
}

.task-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.75rem;
  justify-content: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-label {
  font-size: 0.75rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: bold;
  color: #4a90e2;
}

.task-filter {
  margin-bottom: 1rem;
}

.filter-row {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.filter-item label {
  font-size: 0.8rem;
  color: #666;
  font-weight: 500;
  white-space: nowrap;
}

.filter-select {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.filter-select:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

.filter-select:hover {
  border-color: #4a90e2;
}

.task-list {
  margin-bottom: 0;
}

.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #666;
}

.error-state {
  color: #e74c3c;
}

.empty-state .add-task-btn {
  margin-top: 1rem;
}

.task-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 0.75rem;
  background-color: white;
  transition: all 0.3s ease;
}

.task-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.task-item.completed {
  opacity: 0.7;
}

.task-item.completed .task-title {
  text-decoration: line-through;
}

.task-checkbox {
  margin-top: 0.25rem;
}

.task-content {
  flex: 1;
}

.task-title {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: #333;
}

.task-description {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.task-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.task-type {
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
}

.task-deadline {
  color: #666;
}

.task-priority {
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-weight: 500;
}

.task-priority.low {
  background-color: #e8f5e8;
  color: #2e7d32;
}

.task-priority.medium {
  background-color: #fff3e0;
  color: #f57c00;
}

.task-priority.high {
  background-color: #ffebee;
  color: #c62828;
}

.task-priority.urgent {
  background-color: #ffcdd2;
  color: #b71c1c;
}

.task-actions {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.task-actions button {
  padding: 0.25rem 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.3s ease;
}

.task-actions button:hover {
  background-color: #f5f5f5;
}

.sidebar-footer {
  margin-top: auto;
}

.add-task-btn {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  background-color: #4a90e2;
  color: white;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.add-task-btn:hover {
  background-color: #357abd;
}

/* 滚动内容区域样式 */
.scrollable-content {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 1rem;
}

/* 任务统计和进度条合并样式 */
.stats-progress-section {
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.progress-bar-container {
  margin-top: 0.5rem;
}

.progress-bar {
  height: 6px;
  background-color: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background-color: #4a90e2;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-details {
  font-size: 0.75rem;
  color: #666;
  text-align: center;
}

/* 即将到期任务样式 */
.upcoming-tasks-section {
  background-color: #fff3e0;
  border-left: 4px solid #ff9800;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.upcoming-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.upcoming-header h3 {
  margin: 0;
  font-size: 0.9rem;
  color: #333;
  font-weight: 500;
}

.upcoming-header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.upcoming-count {
  background-color: #ff9800;
  color: white;
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: bold;
}

.close-upcoming-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.close-upcoming-btn:hover {
  background-color: #f5f5f5;
  color: #333;
}

/* 还未完成按钮样式 */
.mark-complete-btn.undo-btn {
  background-color: #f44336;
  color: white;
  border-color: #f44336;
}

.mark-complete-btn.undo-btn:hover {
  background-color: #d32f2f;
  border-color: #d32f2f;
}

.upcoming-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.upcoming-task {
  background-color: white;
  border-radius: 6px;
  padding: 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.upcoming-task-content {
  flex: 1;
  margin-right: 0.75rem;
}

.upcoming-task-title {
  margin: 0 0 0.25rem 0;
  font-size: 0.9rem;
  color: #333;
  font-weight: 500;
}

.upcoming-task-deadline {
  margin: 0;
  font-size: 0.8rem;
  color: #666;
}

.mark-complete-btn {
  padding: 0.25rem 0.75rem;
  border: 1px solid #4caf50;
  border-radius: 4px;
  background-color: white;
  color: #4caf50;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.3s ease;
  align-self: center;
}

.mark-complete-btn:hover {
  background-color: #4caf50;
  color: white;
}

/* 弹窗样式 */
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
  max-width: 500px;
  padding: 1.5rem;
}

.modal-content h3 {
  margin-bottom: 1rem;
  color: #333;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
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
</style>
