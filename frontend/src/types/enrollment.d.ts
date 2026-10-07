import type { Course } from '@/types/course'

export interface Enrollment {
  id: number
  user_id: number
  course_id: number
  enrolled_at: string
  progress: number
  is_completed: boolean
  completed_at: string | null
  last_access_at: string
  course?: Course
}

export interface LessonProgressItem {
  lesson_id: number
  completed: boolean
  passed: boolean
  score: number | null
  best_score: number | null
  latest_score: number | null
  attempts: number
  completed_at: string | null
}

export interface ProgressSummary {
  enrollment_id: number
  course_id: number
  progress: number
  is_completed: boolean
  completed_lessons: number
  total_lessons: number
  passed_lessons: number
  failed_quiz_count: number
  quiz_pass_score: number
  quiz_score_policy: 'HIGHEST' | 'LATEST'
  lesson_progress: LessonProgressItem[]
}
