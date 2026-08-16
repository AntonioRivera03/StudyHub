class ApplicationError(Exception):
    def __init__(self, message: str, *, code: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class NotFoundError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_found", status_code=404)


class ConflictError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="conflict", status_code=409)


class ValidationError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error", status_code=422)
