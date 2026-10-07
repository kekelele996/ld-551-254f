<template>
  <section class="page">
    <div class="page-title">
      <h1>学习仪表盘</h1>
    </div>
    <div class="stats">
      <el-statistic title="已注册课程" :value="enrollments.length" />
      <el-statistic title="总学习进度" :value="averageProgress" suffix="%" />
      <el-statistic title="已结业课程" :value="completedCount" />
    </div>
    <h2>我的课程</h2>
    <div class="grid">
      <div v-for="item in enrollments" :key="item.id" class="enroll-item">
        <el-tag v-if="item.is_completed" class="graduated-tag" type="success" effect="dark">已结业</el-tag>
        <CourseCard :course="item.course!" :progress="item.progress" />
      </div>
    </div>
    <el-empty v-if="!enrollments.length" description="还没有注册课程" />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import CourseCard from '@/components/CourseCard.vue'
import { useEnrollmentStore } from '@/stores/enrollmentStore'

const store = useEnrollmentStore()
const enrollments = computed(() => store.enrollments)
const averageProgress = computed(() => {
  if (!enrollments.value.length) return 0
  return Math.round(enrollments.value.reduce((sum, item) => sum + item.progress, 0) / enrollments.value.length)
})
// 结业以服务端 is_completed 为准：所有课时达标（测验须 60 分及格）
const completedCount = computed(() => enrollments.value.filter((item) => item.is_completed).length)

onMounted(store.fetchEnrollments)
</script>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stats :deep(.el-statistic) {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 18px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.enroll-item {
  position: relative;
}

.graduated-tag {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 2;
}
</style>
