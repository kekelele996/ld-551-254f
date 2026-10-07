// 测验及格分数线：60 分及格，未及格不计入已完成课时
export const QUIZ_PASS_SCORE = 60

// 重做测验的计分口径
export enum QuizScorePolicy {
  HIGHEST = 'HIGHEST',
  LATEST = 'LATEST'
}

// 本平台按【历史最高分】计入课程进度与结业：重做考砸进度不掉
export const QUIZ_SCORE_POLICY = QuizScorePolicy.HIGHEST

export const quizScorePolicyText: Record<QuizScorePolicy, string> = {
  [QuizScorePolicy.HIGHEST]: '按历史最高分计入',
  [QuizScorePolicy.LATEST]: '按最近一次成绩计入'
}
