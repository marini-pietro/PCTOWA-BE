from os.path import dirname as os_path_dirname
from os import listdir as os_listdir

__all__ = []
current_dir = os_path_dirname(__file__)
for file in os_listdir(current_dir):
    if file.endswith('.py') and file != '__init__.py' and file != 'blueprints_utils.py':
        module_name = file[:-3]
        if module_name + '_bp' not in __all__:
            __all__.append(module_name)