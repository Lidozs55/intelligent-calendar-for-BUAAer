<template>
  <div class="quadrant-view-container">
    <!-- 四象限网格 -->
    <div class="quadrant-grid">
      <!-- 象限标签 -->
      <div class="quadrant-labels">
        <div class="top-label">重要</div>
        <div class="bottom-label">不重要</div>
        <div class="left-label">不紧急</div>
        <div class="right-label">紧急</div>
      </div>
      
      <!-- 视觉分隔线 -->
      <div class="visual-dividers">
        <div class="horizontal-divider"></div>
        <div class="vertical-divider"></div>
      </div>
      
      <!-- 单一任务容器 -->
      <div class="tasks-container">
        <!-- 所有任务 -->
        <div 
          v-for="task in allTasks" 
          :key="task.id" 
          class="task-item"
          :class="{ completed: task.completed }"
          draggable="true"
          @dragstart="onDragStart($event, task)"
          @click.stop="selectTask(task)"
          :style="getTaskStyle(task)"
          :data-task-id="task.id"
        >
          <div class="task-header">
            <div class="task-checkbox">
              <input 
                type="checkbox" 
                :checked="task.completed" 
                @change="toggleTaskCompletion(task)"
                @click.stop
              />
            </div>
            <h3 class="task-title">{{ task.title }}</h3>
            <div class="task-meta-right">
              <span class="task-type">{{ getTaskTypeLabel(task.task_type) }}</span>
              <span class="task-priority" :class="task.priority">
                {{ getPriorityLabel(task.priority) }}
              </span>
            </div>
          </div>
          <p v-if="task.description" class="task-description">{{ task.description }}</p>
          <div class="task-meta">
            <span v-if="task.deadline" class="task-deadline">
              截止: {{ formatDate(task.deadline) }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- 坐标轴 -->
      <div class="axes">
        <div class="x-axis"></div>
        <div class="y-axis"></div>
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="action-buttons">
      <button class="btn refresh-btn" @click="refreshTasks">刷新任务</button>
    </div>
    
    <!-- 任务详情弹窗 -->
    <div v-if="selectedTask" class="task-detail-modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>任务详情</h3>
          <button class="close-btn" @click="closeDetailModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="task-detail-item">
            <label>标题:</label>
            <span>{{ selectedTask.title }}</span>
          </div>
          <div class="task-detail-item">
            <label>描述:</label>
            <span>{{ selectedTask.description }}</span>
          </div>
          <div class="task-detail-item">
            <label>类型:</label>
            <span>{{ getTaskTypeLabel(selectedTask.task_type) }}</span>
          </div>
          <div class="task-detail-item">
            <label>截止日期:</label>
            <span>{{ formatDate(selectedTask.deadline) }}</span>
          </div>
          <div class="task-detail-item">
            <label>优先级:</label>
            <span :class="`priority-${selectedTask.priority}`">{{ getPriorityLabel(selectedTask.priority) }}</span>
          </div>
          <div class="task-detail-item">
            <label>状态:</label>
            <span>{{ selectedTask.completed ? '已完成' : '未完成' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTaskStore } from '../store'
import { tasksAPI } from '../services/api'

const taskStore = useTaskStore()
const selectedTask = ref(null)
const draggingTask = ref(null)

// 加载任务数据
const loadTasks = async () => {
  try {
    const response = await tasksAPI.getTasks(null)
    const tasks = Array.isArray(response.tasks) ? response.tasks : []
    taskStore.setTasks(tasks)
  } catch (err) {
    console.error('加载任务失败:', err)
  }
}

// 所有任务 - 过滤掉已过期的任务
const allTasks = computed(() => {
  const now = new Date()
  const tasks = [...taskStore.tasks, ...taskStore.completedTasks]
  // 只保留未过期或已完成的任务
  return tasks.filter(task => {
    const deadline = new Date(task.deadline)
    return deadline >= now || task.completed
  })
})

// 计算紧急度数值 (0-100)
const calculateUrgency = (task) => {
  const now = new Date()
  const deadline = new Date(task.deadline)
  const timeDiff = deadline - now
  const daysDiff = timeDiff / (1000 * 60 * 60 * 24)
  
  let urgency = 0
  // 紧急度计算：0-2天为100-50，2-7天为50-20，7-14天为20-0
  if (daysDiff <= 2) {
    // 0-2天：100-50
    urgency = Math.max(50, 100 - (daysDiff * 25))
  } else if (daysDiff <= 7) {
    // 2-7天：50-20
    urgency = Math.max(20, 50 - ((daysDiff - 2) * 6))
  } else if (daysDiff <= 14) {
    // 7-14天：20-0
    urgency = Math.max(0, 20 - ((daysDiff - 7) * (20/7)))
  } else {
    urgency = 0
  }
  
  return urgency
}

// 现在直接使用task.priority作为纵坐标，不再需要单独的位置存储

// 获取任务样式
const getTaskStyle = (task) => {
  // 计算横坐标：由紧急度决定，不允许拖动修改
  // 调整x范围，防止任务块卡出边界，使用10%-90%范围
  const urgency = calculateUrgency(task)
  // 将0-100的紧急度映射到10%-90%的x坐标范围
  const xPercent = 10 + (urgency / 100) * 80
  const x = `${xPercent}%`
  
  // 略微加长任务格宽度，从200px增加到240px
  const width = '240px'
  
  // 固定任务块高度，避免高度变化导致的偏移
  const height = 100
  
  // 纵坐标：直接使用整数priority作为纵坐标值
  let y = task.priority-10

  if(y<0){
    y=0
  }
  if(y>480){
    y=480
  }
  

  
  return {
    position: 'absolute',
    left: x,
    top: `${y}px`,
    width: width,
    height: `${height}px`,
    transform: 'translateX(-50%)', // 居中对齐
    zIndex: 10,
    cursor: 'move'
  }
}

// 拖动开始
const onDragStart = (event, task) => {
  draggingTask.value = task
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', task.id)
  

}

// 拖动结束
const onDragEnd = () => {
  draggingTask.value = null
}

// 选择任务
const selectTask = (task) => {
  selectedTask.value = task
}

// 关闭详情弹窗
const closeDetailModal = () => {
  selectedTask.value = null
}

// 切换任务完成状态
const toggleTaskCompletion = async (task) => {
  try {
    if (task.completed) {
      await tasksAPI.uncompleteTask(task.id)
    } else {
      await tasksAPI.completeTask(task.id)
    }
    await loadTasks()
  } catch (err) {
    console.error('更新任务状态失败:', err)
  }
}

// 刷新任务
const refreshTasks = async () => {
  await loadTasks()
}

// 键盘快捷键处理 - 仅保留必要的快捷键
const handleKeyDown = (event) => {
  // 可以添加其他快捷键，但移除了撤销重做
}

// 获取任务类型标签
const getTaskTypeLabel = (type) => {
  const typeMap = {
    individual_homework: '个人作业',
    group_report: '小组汇报',
    exam_prep: '考试备考',
    work_delivery: '工作交付'
  }
  return typeMap[type] || type
}

// 获取优先级标签
const getPriorityLabel = (priority) => {
  // 将整数优先级映射到文本标签
  if (typeof priority === 'number') {
    if (priority <= 80) {
      return '高'
    } else if (priority <= 240) {
      return '中'
    } else {
      return '低'
    }
  }
  // 兼容旧的字符串格式
  const priorityMap = {
    low: '低',
    medium: '中',
    high: '高'
  }
  return priorityMap[priority] || priority
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 组件挂载
onMounted(() => {
  loadTasks()
  document.addEventListener('keydown', handleKeyDown)
  
  // 添加拖放事件监听
  const quadrantGrid = document.querySelector('.quadrant-grid')
  if (quadrantGrid) {
    // 允许在整个网格上拖放
    quadrantGrid.addEventListener('dragover', (e) => {
      e.preventDefault()
      e.dataTransfer.dropEffect = 'move'
    })
    
    quadrantGrid.addEventListener('drop', async (e) => {
          e.preventDefault()
          if (draggingTask.value) {
            const taskId = e.dataTransfer.getData('text/plain')
            const gridRect = quadrantGrid.getBoundingClientRect()
            
            // 计算相对位置 - 只计算纵坐标用于优先级更新
            const y = Math.round(e.clientY - gridRect.top)
            
            // 根据位置更新任务优先级和紧急度
            const task = draggingTask.value
            
            // 计算任务框中间位置（加上任务高度的一半）
            // 使用固定的任务高度100px
            const taskHeight = 100
            const middleY = y + taskHeight / 2
            
            // 直接使用实际y坐标作为优先级值，不再计算中间位置
            // 这样可以确保任务块放置在拖动的准确位置
            let newPriority = Math.round(y)
            // 确保优先级为正数
            newPriority = Math.max(0, newPriority)
            
            // 紧急度：将y坐标映射到0-100的连续值
            // 顶部为重要，底部为不重要，所以紧急度与y坐标成反比
            // 使用相对位置计算紧急度，基于grid高度
            const urgency = Math.max(0, Math.min(100, 100 - (y / gridRect.height) * 100))
            
            // 更新任务重要性和紧急度到数据库
            try {
              const response = await tasksAPI.updateTask(task.id, { 
                priority: newPriority, 
                urgency: urgency 
              })
              await loadTasks()
            } catch (err) {
              console.error('更新任务失败:', err)
            }
            
            draggingTask.value = null
          }
        })
  }
})

// 组件卸载
onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.quadrant-view-container {
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: 100%;
  overflow: hidden;
}

.view-title {
  font-size: 24px;
  margin-bottom: 20px;
  color: #333;
  text-align: center;
}

.quadrant-grid {
  position: relative;
  width: 100%;
  height: calc(100% - 60px); /* 减去操作按钮的高度 */
  margin: 0;
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: auto;
}

.quadrant-labels {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}

.top-label, .bottom-label {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-weight: bold;
  background-color: white;
  padding: 5px 10px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.top-label {
  top: -20px;
}

.bottom-label {
  bottom: -20px;
}

.left-label, .right-label {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  font-weight: bold;
  background-color: white;
  padding: 5px 10px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.left-label {
  left: -60px;
}

.right-label {
  right: -40px;
}

/* 视觉分隔线 */
.visual-dividers {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.horizontal-divider {
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: rgba(221, 221, 221, 0.8);
  transform: translateY(-1px);
}

.vertical-divider {
  position: absolute;
  left: 50%;
  top: 0;
  width: 2px;
  height: 100%;
  background-color: rgba(221, 221, 221, 0.8);
  transform: translateX(-1px);
}

/* 单一任务容器 */
.tasks-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.task-item {
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 80px;
  overflow: hidden;
}

.task-item:hover {
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.task-item.completed {
  opacity: 0.7;
  background-color: #f0f0f0;
  text-decoration: line-through;
}

.task-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.task-checkbox {
  margin-right: 10px;
}

.task-title {
  flex: 1;
  margin: 0;
  font-size: 16px;
  color: #333;
}

.task-meta-right {
  display: flex;
  gap: 8px;
}

.task-type, .task-priority {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.task-type {
  background-color: #e0e0e0;
  color: #333;
}

.task-priority.low {
  background-color: #4caf50;
  color: white;
}

.task-priority.medium {
  background-color: #ff9800;
  color: white;
}

.task-priority.high {
  background-color: #f44336;
  color: white;
}

.task-priority.urgent {
  background-color: #9c27b0;
  color: white;
}

.task-description {
  margin: 8px 0;
  color: #666;
  font-size: 14px;
}

.task-meta {
  display: flex;
  justify-content: flex-end;
  font-size: 12px;
  color: #888;
}

.task-deadline {
  background-color: #fff3cd;
  color: #856404;
  padding: 2px 6px;
  border-radius: 4px;
}

.axes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.x-axis, .y-axis {
  background-color: #333;
  position: absolute;
}

.x-axis {
  width: 100%;
  height: 2px;
  top: 50%;
  left: 0;
  transform: translateY(-1px); /* 微调，确保线宽居中 */
  z-index: 2;
}

.y-axis {
  width: 2px;
  height: 100%;
  left: 50%;
  top: 0;
  transform: translateX(-1px); /* 微调，确保线宽居中 */
  z-index: 2;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  justify-content: center;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: all 0.3s ease;
}

.refresh-btn {
  background-color: var(--primary-color);
  color: white;
}

.refresh-btn:hover {
  background-color: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px var(--shadow-color);
}

.task-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #ddd;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #888;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 15px;
}

.task-detail-item {
  display: flex;
  margin-bottom: 15px;
  align-items: flex-start;
}

.task-detail-item label {
  font-weight: bold;
  width: 80px;
  margin-right: 10px;
  flex-shrink: 0;
}

.task-detail-item span {
  flex: 1;
  word-break: break-word;
}

.priority-low {
  color: #4caf50;
  font-weight: bold;
}

.priority-medium {
  color: #ff9800;
  font-weight: bold;
}

.priority-high {
  color: #f44336;
  font-weight: bold;
}

.priority-urgent {
  color: #9c27b0;
  font-weight: bold;
}
</style>
