from os import listdir as os_listdir
from os.path import dirname as os_path_dirname
from importlib import import_module

# Dynamically import all Python files in the current directory
current_dir = os_path_dirname(__file__)
for file in os_listdir(current_dir):
    if file.endswith('.py') and file != '__init__.py':
        module_name = file[:-3]
        module = import_module(f'.{module_name}', package=__name__)
        globals()[f"{module_name}_bp"] = getattr(module, f"{module_name}_bp")

# Expose all blueprints for easy import
__all__ = ['address_bp', 
           'class_bp', 
           'company_bp',
           'contact_bp',
           'sector_bp',
           'student_bp',
           'subject_bp',
           'turn_bp',
           'tutor_bp',
           'user_bp']