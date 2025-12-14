<template>
  <div class="mobile-tasks">
    <!-- 列表视图 -->
    <div class="list-view">
      <div class="section">
        <h3 class="section-title">待办任务</h3>
        <div v-if="pendingTasks.length === 0" class="empty-state">
          <p>没有待办任务</p>
        </div>
        <div v-else class="task-list">
          <div v-for="task in pendingTasks" :key="task.id" class="task-item">
            <input 
              type="checkbox" 
              :checked="task.completed" 
              @change="toggleTaskCompletion(task)"
              @click.stop
            />
            <div class="task-content" @click="showTaskDetail(task)">
              <h4 class="task-title">{{ task.title }}</h4>
              <p class="task-deadline" v-if="task.deadline">
                截止：{{ formatDateTime(task.deadline) }}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="section" v-if="completedTasks.length > 0">
        <h3 class="section-title">已完成任务</h3>
        <div class="task-list">
          <div v-for="task in completedTasks" :key="task.id" class="task-item completed">
            <input 
              type="checkbox" 
              :checked="task.completed" 
              @change="toggleTaskCompletion(task)"
              @click.stop
            />
            <div class="task-content" @click="showTaskDetail(task)">
              <h4 class="task-title">{{ task.title }}</h4>
              <p class="task-deadline" v-if="task.deadline">
                截止：{{ formatDateTime(task.deadline) }}
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
        <div v-if="currentDetail">
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
          <div class="detail-item">
            <span class="detail-label">重要性：</span>
            <span class="detail-value">{{ currentDetail.importance ? '重要' : '不重要' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">紧急性：</span>
            <span class="detail-value">{{ currentDetail.urgency ? '紧急' : '不紧急' }}</span>
          </div>
        </div>
        <button class="close-btn" @click="closeDetail">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTaskStore } from '../../store'
import { tasksAPI } from '../../services/api'

// 状态管理
const taskStore = useTaskStore()

// 详情弹窗状态
const showDetail = ref(false)
const currentDetail = ref(null)

// 格式化时间
const formatTime = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 待办任务
const pendingTasks = computed(() => {
  return taskStore.tasks.filter(task => !task.completed).sort((a, b) => {
    return new Date(a.deadline) - new Date(b.deadline)
  })
})

// 已完成任务
const completedTasks = computed(() => {
  return taskStore.tasks.filter(task => task.completed).sort((a, b) => {
    return new Date(b.updated_at || b.deadline) - new Date(a.updated_at || a.deadline)
  })
})

// 显示任务详情
const showTaskDetail = (task) => {
  currentDetail.value = task
  showDetail.value = true
}

// 关闭详情
const closeDetail = () => {
  showDetail.value = false
  currentDetail.value = null
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
  return currentDetail.value?.title || '任务详情'
})

// 加载数据
const loadData = async () => {
  try {
    // 加载任务数据
    const tasksResponse = await tasksAPI.getTasks(null)
    taskStore.setTasks(tasksResponse.tasks)
  } catch (err) {
    console.error('加载数据失败:', err)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* 基础样式 */
.mobile-tasks {
  padding: 0;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  min-height: calc(100vh - 60px);
}

/* 视图切换 */
.view-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
}

/* 列表视图 */
.list-view {
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
  transition: all 0.2s ease;
}

.task-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
}

.task-item.completed {
  opacity: 0.7;
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

.task-item:not(.completed) .task-title {
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
  min-width: 70px;
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

/* 响应式设计 */
@media (max-width: 480px) {
  .mobile-tasks {
    padding: 12px;
  }
  
  .section {
    padding: 12px;
  }
}
</style>