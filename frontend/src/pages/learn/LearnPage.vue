<template>
  <section class="page learn-page">
    <div class="learn-main">
      <el-alert type="info" :closable="false" :title="QUIZ_SCORE_RULE_TEXT" />
      <el-alert v-if="progress?.is_completed" type="success" :closable="false" title="恭喜，全部课时已完成，本课程已结业！" />
      <LessonPlayer :lesson="selectedLesson" :state="currentLessonState" @complete="complete" />
    </div>
    <aside class="learn-side">
      <ProgressIndicator :percentage="progress?.progress || 0" type="circle" label="学习进度" />
      <p class="progress-detail">
        已完成 {{ progress?.completed_lessons || 0 }} / {{ progress?.total_lessons || 0 }} 课时
        <el-tag v-if="progress?.is_completed" type="success" size="small">已结业</el-tag>
      </p>
      <ChapterTree :chapters="chapters" :lesson-states="lessonStates" @select-lesson="selectedLesson = $event" />
      <el-input v-model="note" type="textarea" :rows="6" placeholder="学习笔记" />
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import ChapterTree from '@/components/ChapterTree.vue'
import LessonPlayer from '@/components/LessonPlayer.vue'
import ProgressIndicator from '@/components/ProgressIndicator.vue'
import { QUIZ_SCORE_RULE_TEXT } from '@/constants/rules'
import { LessonType } from '@/constants/enums'
import { useCourseStore } from '@/stores/courseStore'
import { useEnrollmentStore } from '@/stores/enrollmentStore'
import type { LessonProgressState } from '@/types/enrollment'
import type { Lesson } from '@/types/lesson'

const route = useRoute()
const courseStore = useCourseStore()
const enrollmentStore = useEnrollmentStore()
const selectedLesson = ref<Lesson | null>(null)
const note = ref('')
const chapters = computed(() => courseStore.chapters)
const progress = computed(() => enrollmentStore.progress)

const lessonStates = computed<Record<number, LessonProgressState>>(() =>
  Object.fromEntries((progress.value?.lessons || []).map((item) => [item.lesson_id, item]))
)
const currentLessonState = computed(() => (selectedLesson.value ? lessonStates.value[selectedLesson.value.id] || null : null))

async function complete(score?: number) {
  if (!selectedLesson.value) return
  const lessonType = selectedLesson.value.type
  const result = await enrollmentStore.completeLesson(selectedLesson.value.id, score)
  if (lessonType === LessonType.QUIZ) {
    if (result.passed) {
      ElMessage.success(`测验得分 ${result.score} 分，已及格（历史最高 ${result.best_score} 分），课时计入完成`)
    } else {
      ElMessage.warning(`测验得分 ${result.score} 分，未达到 ${result.passing_score} 分及格线，不计入完成，可重做`)
    }
  } else {
    ElMessage.success('课时已完成')
  }
  if (result.is_completed) ElMessage.success('全部课时已完成，本课程已结业！')
}

onMounted(async () => {
  const courseId = Number(route.params.courseId)
  await courseStore.fetchCourse(courseId)
  selectedLesson.value = courseStore.chapters[0]?.lessons[0] || null
  await enrollmentStore.fetchProgress(courseId)
})
</script>

<style scoped>
.learn-page {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(300px, 3fr);
  gap: 20px;
}

.learn-main {
  display: grid;
  gap: 16px;
  align-content: start;
}

.learn-side {
  display: grid;
  gap: 16px;
  align-content: start;
}

.progress-detail {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #4b5563;
  font-size: 13px;
}
</style>
