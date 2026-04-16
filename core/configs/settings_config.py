from ..settings import CustomerSettings
from hyperlocal_platform.core.utils.settings_initializer import init_settings
from ..constants import ENV_PREFIX,SERVICE_NAME

SETTINGS:CustomerSettings=init_settings(settings=CustomerSettings,service_name=SERVICE_NAME,env_prefix=ENV_PREFIX)