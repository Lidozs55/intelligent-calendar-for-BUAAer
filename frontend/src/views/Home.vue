<template>
  <div class="home-container">
    <div class="calendar-section">
      <CalendarView ref="calendarViewRef" />
    </div>
  </div>
</template>

<script setup>
import { ref, defineExpose, watch } from 'vue'
import CalendarView from '../components/CalendarView.vue'

const calendarViewRef = ref(null)

// 定义组件暴露的方法，用于父组件调用
const addLLMEntries = (entries) => {
  if (calendarViewRef.value) {
    // 调用CalendarView组件的方法来添加新条目
    calendarViewRef.value.addLLMEntries(entries)
  }
}

defineExpose({
  addLLMEntries
})
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
  overflow: hidden;
}

.calendar-section {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0.75rem;
  flex: 1;
  min-height: 400px;
  height: 100%;
  overflow: hidden;
  position: relative;
  z-index: 5;
}

.calendar-section h2 {
  margin-bottom: 0.75rem;
  color: #333;
  font-size: 1.1rem;
}
</style>
