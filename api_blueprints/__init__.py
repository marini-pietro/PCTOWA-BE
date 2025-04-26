"""
This script dynamically exposes all Python modules in the current directory as part of the package.
It imports the modules containing API blueprints and adds them to the `__all__` variable,
allowing for easy import and usage in the main application.
"""

from os.path import dirname as os_path_dirname
from os import listdir as os_listdir

__all__ = []
current_dir = os_path_dirname(__file__)
for file in os_listdir(current_dir):
    # Check if the file is a Python file and not an init file or blueprints_utils.py
    if file.endswith(".py") and file != "__init__.py" and file != "blueprints_utils.py":
        module_name = file[:-3]
        if module_name + "_bp" not in __all__:
            __all__.append(module_name)
