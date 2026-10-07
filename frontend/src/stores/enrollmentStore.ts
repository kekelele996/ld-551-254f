import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Enrollment, ProgressSummary } from '@/types/enrollment'
import request from '@/utils/request'

export const useEnrollmentStore = defineStore('enrollment', () => {
  const enrollments = ref<Enrollment[]>([])
  const progress = ref<ProgressSummary | null>(null)

  async function fetchEnrollments() {
    enrollments.value = await request.get<unknown, Enrollment[]>('/enrollments')
  }

  async function fetchProgress(courseId: number) {
    progress.value = await request.get<unknown, ProgressSummary>(`/enrollments/${courseId}/progress`)
    return progress.value
  }

  // 标记视频/文本课时完成（测验课时不能走这个接口）
  async function completeLesson(lessonId: number) {
    const enrollment = await request.post<unknown, Enrollment>('/enrollments/progress/complete', { lesson_id: lessonId })
    await fetchProgress(enrollment.course_id)
    return enrollment
  }

  // 提交测验；后端按历史最高分计入，重做考砸进度不掉
  async function submitQuiz(lessonId: number, score: number) {
    const enrollment = await request.post<unknown, Enrollment>('/enrollments/progress/quiz', { lesson_id: lessonId, score })
    await fetchProgress(enrollment.course_id)
    return enrollment
  }

  function lessonProgress(lessonId: number) {
    return progress.value?.lesson_progress.find((item) => item.lesson_id === lessonId) || null
  }

  return { enrollments, progress, fetchEnrollments, fetchProgress, completeLesson, submitQuiz, lessonProgress }
})
