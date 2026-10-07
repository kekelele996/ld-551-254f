<template>
  <section class="lesson-player">
    <template v-if="lesson">
      <header>
        <h2>{{ lesson.title }}</h2>
        <el-tag>{{ lessonTypeLabel[lesson.type] }}</el-tag>
      </header>
      <video v-if="lesson.type === LessonType.VIDEO" controls class="video" @ended="complete">
        <source :src="lesson.content" />
      </video>
      <article v-else-if="lesson.type === LessonType.TEXT" class="text-content" @scroll.passive="handleScroll">
        {{ lesson.content }}
      </article>
      <div v-else class="quiz">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            满分 100 分，{{ passScore }} 分及格，及格后本课时才计入课程进度与结业。
            可反复重做，成绩<strong>按历史最高分计入</strong>，重做考砸进度不会掉。
          </template>
        </el-alert>
        <p class="quiz-question">{{ quizQuestion }}</p>
        <el-form @submit.prevent>
          <el-form-item label="答案">
            <el-input v-model="answer" placeholder="请输入测验答案" @keyup.enter="submitQuiz" />
          </el-form-item>
          <el-button type="primary" @click="submitQuiz">提交测验</el-button>
        </el-form>
        <div v-if="attempt" class="quiz-result">
          <el-tag :type="passed ? 'success' : 'danger'">
            本次 {{ attempt.latest_score }} 分{{ passed ? '，已及格' : `，未达 ${passScore} 分` }}
          </el-tag>
          <span class="quiz-history">
            已作答 {{ attempt.attempts }} 次 · 历史最高 {{ attempt.best_score ?? 0 }} 分
            <template v-if="!passed">（不计入已完成，可继续重做）</template>
          </span>
        </div>
      </div>
      <el-button v-if="lesson.type !== LessonType.QUIZ" class="complete" type="success" plain @click="complete">
        标记完成
      </el-button>
      <p v-else-if="passed" class="complete-tip">✅ 该测验已及格，计入已完成课时</p>
    </template>
    <el-empty v-else description="请选择课时" />
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { LessonType } from '@/constants/enums'
import { QUIZ_PASS_SCORE } from '@/constants/lesson'
import type { Lesson } from '@/types/lesson'
import type { LessonProgressItem } from '@/types/enrollment'

const props = defineProps<{ lesson: Lesson | null; attempt: LessonProgressItem | null }>()
const emit = defineEmits<{ complete: []; submitQuiz: [score: number] }>()

const passScore = QUIZ_PASS_SCORE
const answer = ref('')

const passed = computed(() => props.attempt?.passed ?? false)

// Mock 评分：内容里的正确答案（JSON questions[].answer）与输入比对；答对 100，答错 50
const quizQuestion = computed(() => {
  if (!props.lesson) return ''
  try {
    const parsed = JSON.parse(props.lesson.content)
    return parsed?.questions?.[0]?.title ?? '请回答以下测验题'
  } catch {
    return '请回答以下测验题'
  }
})

function complete() {
  emit('complete')
}

function submitQuiz() {
  if (!props.lesson) return
  const value = answer.value.trim()
  if (!value) {
    ElMessage.warning('请先填写答案再提交')
    return
  }
  let score = 50
  try {
    const parsed = JSON.parse(props.lesson.content)
    const correct = String(parsed?.questions?.[0]?.answer ?? '').trim()
    score = correct && value === correct ? 100 : 50
  } catch {
    score = value ? 50 : 0
  }
  emit('submitQuiz', score)
}

function handleScroll(event: Event) {
  const el = event.target as HTMLElement
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 8) complete()
}

watch(
  () => props.lesson?.id,
  () => {
    answer.value = ''
  }
)

const lessonTypeLabel: Record<LessonType, string> = {
  [LessonType.VIDEO]: '视频',
  [LessonType.TEXT]: '文本',
  [LessonType.QUIZ]: '测验'
}
</script>

<style scoped>
.lesson-player {
  min-height: 520px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  background: #fff;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.video {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #111827;
  border-radius: 8px;
}

.text-content {
  height: 360px;
  overflow-y: auto;
  white-space: pre-wrap;
  line-height: 1.8;
  color: #374151;
}

.quiz {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.quiz-question {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.quiz-result {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.quiz-history {
  color: #6b7280;
  font-size: 13px;
}

.complete {
  margin-top: 16px;
}

.complete-tip {
  margin-top: 16px;
  color: #16a34a;
}
</style>
