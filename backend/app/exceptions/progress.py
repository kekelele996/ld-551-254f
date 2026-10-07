class InvalidQuizSubmissionException(Exception):
    def __init__(self, message: str = "测验课时必须提交 0-100 的分数"):
        self.message = message
        super().__init__(message)
