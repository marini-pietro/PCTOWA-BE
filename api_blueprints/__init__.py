import os

# __all__ = ['address_bp', 
#            'class_bp',
#             'company_bp',
#             'contact_bp',
#             'sector_bp',
#             'student_bp',
#             'subject_bp',
#             'turn_bp',
#             'tutor_bp',
#             'user_bp'
#            ]

__all__ = []
current_dir = os.path.dirname(__file__)
for file in os.listdir(current_dir):
    if file.endswith('.py') and file != '__init__.py' and file != 'blueprints_utils.py':
        module_name = file[:-3]
        if module_name + '_bp' not in __all__:
            __all__.append(module_name)