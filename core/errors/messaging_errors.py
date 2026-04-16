from hyperlocal_platform.core.errors.messaging_errors import CommonMessagingError,ErrorTypeSEnum,SagaStateErrorTypDict


class BussinessError(CommonMessagingError):
    ...

class FatalError(CommonMessagingError):
    ...

class RetryableError(CommonMessagingError):
    ...