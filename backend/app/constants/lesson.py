from enum import StrEnum


class QuizScorePolicy(StrEnum):
    """测验成绩计入进度与结业时采用的口径。"""

    HIGHEST = "HIGHEST"  # 历史最高分
    LATEST = "LATEST"  # 最近一次


# 测验及格分数线：达到 60 分才算通过，未通过不计入已完成课时
QUIZ_PASS_SCORE = 60

# 重做测验后的计分口径：按历史最高分，重做考砸进度不掉
QUIZ_SCORE_POLICY = QuizScorePolicy.HIGHEST
