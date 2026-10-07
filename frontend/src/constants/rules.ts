// 学习进度计分规则（与后端 backend/app/constants/rules.py 保持一致）

/** 测验课时及格分数：达到该分数课时才算完成 */
export const QUIZ_PASSING_SCORE = 60

/**
 * 多次提交测验按历史最高分计算课时完成状态与课程进度，
 * 即重做考砸不会拉低已完成进度
 */
export const QUIZ_SCORE_RULE_TEXT = `测验课时需达到 ${QUIZ_PASSING_SCORE} 分才算完成；多次提交按历史最高分计，重做考砸不影响已完成进度。全部课时完成后课程结业。`
