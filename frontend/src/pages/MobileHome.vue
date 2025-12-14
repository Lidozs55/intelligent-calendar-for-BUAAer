<template>
  <div class="mobile-home">
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 日程标签页 -->
      <div v-if="activeTab === 'calendar'" class="tab-content">
        <MobileCalendar />
      </div>
      
      <!-- 任务标签页 -->
      <div v-if="activeTab === 'tasks'" class="tab-content">
        <MobileTasks />
      </div>
      
      <!-- 智能输入标签页 -->
      <div v-if="activeTab === 'smart-input'" class="tab-content">
        <MobileSmartInput />
      </div>
      
      <!-- 设置标签页 -->
      <div v-if="activeTab === 'settings'" class="tab-content">
        <MobileSettings />
      </div>
    </div>
    
    <!-- 底部标签栏 -->
    <div class="bottom-tab-bar">
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'calendar' }"
        @click="activeTab = 'calendar'"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="16" y1="2" x2="16" y2="6"></line>
          <line x1="8" y1="2" x2="8" y2="6"></line>
          <line x1="3" y1="10" x2="21" y2="10"></line>
        </svg>
        <span>日程</span>
      </div>
      
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'tasks' }"
        @click="activeTab = 'tasks'"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="16" y1="3" x2="16" y2="7"></line>
          <line x1="8" y1="3" x2="8" y2="7"></line>
          <line x1="3" y1="11" x2="21" y2="11"></line>
          <line x1="3" y1="16" x2="21" y2="16"></line>
        </svg>
        <span>任务</span>
      </div>
      
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'smart-input' }"
        @click="activeTab = 'smart-input'"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
          <line x1="9" y1="9" x2="9.01" y2="9"></line>
          <line x1="15" y1="9" x2="15.01" y2="9"></line>
        </svg>
        <span>智能输入</span>
      </div>
      
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'settings' }"
        @click="activeTab = 'settings'"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
        <span>设置</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MobileCalendar from '../components/mobile/MobileCalendar.vue'
import MobileTasks from '../components/mobile/MobileTasks.vue'
import MobileSmartInput from '../components/mobile/MobileSmartInput.vue'
import MobileSettings from '../components/mobile/MobileSettings.vue'

// 当前激活的标签页
const activeTab = ref('calendar')
</script>

<style scoped>
/* 基础样式 */
.mobile-home {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 600px;
  margin: 0 auto;
  background-color: #f5f5f5;
  position: relative;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: white;
  position: relative;
}

/* 标签内容 */
.tab-content {
  padding: 8px 0;
}

/* 底部标签栏 */
.bottom-tab-bar {
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 60px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 600px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
}

/* 标签项 */
.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  cursor: pointer;
  color: #666;
  transition: all 0.3s ease;
}

/* 激活的标签项 */
.tab-item.active {
  color: var(--primary-color);
}

/* 标签项文字 */
.tab-item span {
  font-size: 12px;
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .mobile-home {
    height: 100vh;
  }
  
  .main-content {
    padding: 12px;
  }
  
  .bottom-tab-bar {
    height: 56px;
  }
}

/* 安全区域适配 */
@supports (padding: env(safe-area-inset-bottom)) {
  .bottom-tab-bar {
    padding-bottom: env(safe-area-inset-bottom);
    height: calc(60px + env(safe-area-inset-bottom));
  }
}
</style>