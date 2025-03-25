from os import listdir as os_listdir
from os.path import dirname as os_path_dirname
from importlib import import_module

# Dynamically import all Python files in the current directory and expose them in the __all__ array for easy import
__all__ = []
current_dir = os_path_dirname(__file__)
for file in os_listdir(current_dir):
    if file.endswith('.py') and file != '__init__.py':
        module_name = file[:-3]
        module = import_module(f'.{module_name}', package=__name__)
        globals()[f"{module_name}_bp"] = getattr(module, f"{module_name}_bp")
        __all__.append(module_name)