<template>
  <section class="lesson-player">
    <template v-if="lesson">
      <header>
        <h2>{{ lesson.title }}</h2>
        <div class="header-tags">
          <el-tag>{{ lesson.type }}</el-tag>
          <el-tag v-if="state?.status === 'completed'" type="success">已完成</el-tag>
          <el-tag v-else-if="state?.status === 'failed'" type="danger">未及格</el-tag>
        </div>
      </header>
      <video v-if="lesson.type === LessonType.VIDEO" controls class="video" @ended="complete()">
        <source :src="lesson.content" />
      </video>
      <article v-else-if="lesson.type === LessonType.TEXT" class="text-content" @scroll.passive="handleScroll">
        {{ lesson.content }}
      </article>
      <div v-else class="quiz">
        <el-alert type="info" :closable="false" :title="QUIZ_SCORE_RULE_TEXT" />
        <div v-if="state" class="quiz-meta">
          <span>历史最高分：{{ state.best_score ?? '—' }}</span>
          <span>已提交 {{ state.attempts }} 次</span>
          <span>及格线：{{ QUIZ_PASSING_SCORE }} 分</span>
        </div>
        <el-form v-if="questions.length" @submit.prevent>
          <el-form-item v-for="(question, index) in questions" :key="index" :label="`${index + 1}. ${question.title}`">
            <el-input v-model="answers[index]" placeholder="请输入答案" />
          </el-form-item>
        </el-form>
        <el-form v-else @submit.prevent>
          <el-form-item label="答案">
            <el-input v-model="answers[0]" placeholder="请输入测验答案" />
          </el-form-item>
        </el-form>
        <el-button type="primary" @click="submitQuiz">
          {{ state?.attempts ? '重新提交测验' : '提交测验' }}
        </el-button>
        <el-alert
          v-if="lastScore !== null"
          class="quiz-result"
          :type="lastScore >= QUIZ_PASSING_SCORE ? 'success' : 'error'"
          :closable="false"
          :title="
            lastScore >= QUIZ_PASSING_SCORE
              ? `本次得分 ${lastScore} 分，已及格，课时计入完成`
              : `本次得分 ${lastScore} 分，未达到 ${QUIZ_PASSING_SCORE} 分及格线，不计入完成，可重做`
          "
        />
      </div>
      <el-button v-if="lesson.type !== LessonType.QUIZ" class="complete" type="success" plain @click="complete()">标记完成</el-button>
    </template>
    <el-empty v-else description="请选择课时" />
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { LessonType } from '@/constants/enums'
import { QUIZ_PASSING_SCORE, QUIZ_SCORE_RULE_TEXT } from '@/constants/rules'
import type { LessonProgressState } from '@/types/enrollment'
import type { Lesson } from '@/types/lesson'

interface QuizQuestion {
  title: string
  answer: string
}

const props = defineProps<{ lesson: Lesson | null; state?: LessonProgressState | null }>()
const emit = defineEmits<{ complete: [score?: number] }>()
const answers = ref<string[]>([''])
const lastScore = ref<number | null>(null)

const questions = computed<QuizQuestion[]>(() => {
  if (props.lesson?.type !== LessonType.QUIZ) return []
  try {
    const parsed = JSON.parse(props.lesson.content) as { questions?: QuizQuestion[] }
    return Array.isArray(parsed.questions) ? parsed.questions.filter((item) => item?.title) : []
  } catch {
    return []
  }
})

watch(
  () => props.lesson?.id,
  () => {
    answers.value = questions.value.length ? questions.value.map(() => '') : ['']
    lastScore.value = null
  },
  { immediate: true }
)

function complete() {
  emit('complete')
}

function submitQuiz() {
  const score = gradeQuiz()
  lastScore.value = score
  emit('complete', score)
}

function gradeQuiz(): number {
  if (!questions.value.length) return answers.value[0]?.trim() ? 100 : 0
  const correct = questions.value.filter((question, index) => {
    const expected = question.answer.trim().toLowerCase()
    const actual = (answers.value[index] || '').trim().toLowerCase()
    return actual.length > 0 && (actual.includes(expected) || expected.includes(actual))
  }).length
  return Math.round((correct / questions.value.length) * 100)
}

function handleScroll(event: Event) {
  const el = event.target as HTMLElement
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 8) complete()
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

.header-tags {
  display: flex;
  gap: 8px;
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
  justify-items: start;
}

.quiz form {
  width: 100%;
}

.quiz-meta {
  display: flex;
  gap: 16px;
  color: #6b7280;
  font-size: 13px;
}

.quiz-result {
  width: 100%;
}

.complete {
  margin-top: 16px;
}
</style>
