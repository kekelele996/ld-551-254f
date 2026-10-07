import type { Course } from '@/types/course'

export interface Enrollment {
  id: number
  user_id: number
  course_id: number
  enrolled_at: string
  progress: number
  last_access_at: string
  completed_at: string | null
  course?: Course
}

export type LessonStatus = 'completed' | 'failed' | 'pending'

export interface LessonProgressState {
  lesson_id: number
  status: LessonStatus
  best_score: number | null
  attempts: number
  completed_at: string | null
}

export interface ProgressSummary {
  enrollment_id: number
  course_id: number
  progress: number
  completed_lessons: number
  total_lessons: number
  is_completed: boolean
  passing_score: number
  lessons: LessonProgressState[]
}

export interface LessonCompleteResult {
  enrollment_id: number
  course_id: number
  lesson_id: number
  status: LessonStatus
  score: number | null
  best_score: number | null
  passed: boolean
  progress: number
  is_completed: boolean
  passing_score: number
}
