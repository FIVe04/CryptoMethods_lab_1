class AppError(Exception):
    pass


class ValidationError(AppError):
    pass


class CryptoError(AppError):
    pass


class FormatError(AppError):
    pass


class StorageError(AppError):
    pass
