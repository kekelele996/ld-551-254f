class LessonValidationException(Exception):
    def __init__(self, message: str = "课时数据不合法"):
        self.message = message
        super().__init__(message)
