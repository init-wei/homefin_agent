class ServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class PermissionDenied(ServiceError):
    pass


class NotFoundError(ServiceError):
    pass


class ValidationError(ServiceError):
    pass


class IntegrationError(ServiceError):
    pass
