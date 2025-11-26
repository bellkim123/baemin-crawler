class BaeminError(Exception):
    def __init__(self, message="baemin error", code=500, status="ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class LoginError(BaeminError):
    def __init__(self, message="login failed", status="LOGIN_FAILED", code=401):
        super().__init__(message, code, status)


class StructureChangedError(BaeminError):
    def __init__(self, message="structure changed", code=500, status="STRUCTURE_CHANGED"):
        super().__init__(message, code, status)


class RecaptchaError(BaeminError):
    def __init__(self, message="recaptcha required", code=401, status="NEED_RECAPTCHA"):
        super().__init__(message, code, status)
