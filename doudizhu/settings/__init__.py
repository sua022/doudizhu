import importlib
import os

TORNADO_SETTINGS_MODULE = os.getenv('TORNADO_SETTINGS_MODULE', 'settings.dev')
config = importlib.import_module(TORNADO_SETTINGS_MODULE)
