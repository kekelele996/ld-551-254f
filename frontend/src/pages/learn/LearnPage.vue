<template>
  <section class="page learn-page">
    <div class="learn-main">
      <el-alert
        v-if="progress?.is_completed"
        class="graduation-banner"
        type="success"
        :closable="false"
        show-icon
        title="🎉 恭喜！全部课时已达标，本门课程已结业"
      />
      <el-alert
        v-else-if="progress && progress.failed_quiz_count > 0"
        class="graduation-banner"
        type="warning"
        :closable="false"
        show-icon
        :title="`有 ${progress.failed_quiz_count} 个测验课时未达 ${progress.quiz_pass_score} 分，已在右侧大纲中标出，不计入已完成；及格后才能结业`"
      />
      <LessonPlayer
        :lesson="selectedLesson"
        :attempt="selectedAttempt"
        @complete="complete"
        @submit-quiz="submitQuiz"
      />
    </div>
    <aside class="learn-side">
      <ProgressIndicator :percentage="progress?.progress || 0" type="circle" :label="progress?.is_completed ? '已结业' : '学习进度'" />
      <el-tag v-if="progress?.is_completed" type="success" size="large">课程已结业</el-tag>
      <p class="progress-text">
        已完成 {{ progress?.completed_lessons ?? 0 }} / {{ progress?.total_lessons ?? 0 }} 课时
        <span v-if="progress && progress.failed_quiz_count > 0" class="failed-text">
          （{{ progress.failed_quiz_count }} 个测验未及格）
        </span>
      </p>
      <el-alert type="info" :closable="false">
        <template #title>
          测验需达 {{ progress?.quiz_pass_score ?? 60 }} 分才计入完成；重做成绩<strong>按历史最高分</strong>计入，考砸不掉进度。
        </template>
      </el-alert>
      <ChapterTree
        :chapters="chapters"
        :lesson-progress="progress?.lesson_progress ?? []"
        :draggable="false"
        @select-lesson="selectedLesson = $event"
      />
      <el-input v-model="note" type="textarea" :rows="6" placeholder="学习笔记" />
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import ChapterTree from '@/components/ChapterTree.vue'
import LessonPlayer from '@/components/LessonPlayer.vue'
import ProgressIndicator from '@/components/ProgressIndicator.vue'
import { useCourseStore } from '@/stores/courseStore'
import { useEnrollmentStore } from '@/stores/enrollmentStore'
import type { Lesson } from '@/types/lesson'

const route = useRoute()
const courseStore = useCourseStore()
const enrollmentStore = useEnrollmentStore()
const selectedLesson = ref<Lesson | null>(null)
const note = ref('')
const chapters = computed(() => courseStore.chapters)
const progress = computed(() => enrollmentStore.progress)
const selectedAttempt = computed(() =>
  selectedLesson.value ? enrollmentStore.lessonProgress(selectedLesson.value.id) : null
)

async function complete() {
  if (selectedLesson.value) await enrollmentStore.completeLesson(selectedLesson.value.id)
}

async function submitQuiz(score: number) {
  if (selectedLesson.value) await enrollmentStore.submitQuiz(selectedLesson.value.id, score)
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
  gap: 12px;
  align-content: start;
}

.graduation-banner {
  margin-bottom: 4px;
}

.learn-side {
  display: grid;
  gap: 16px;
  align-content: start;
  justify-items: start;
}

.progress-text {
  margin: 0;
  color: #4b5563;
  font-size: 14px;
}

.failed-text {
  color: #dc2626;
}
</style>
