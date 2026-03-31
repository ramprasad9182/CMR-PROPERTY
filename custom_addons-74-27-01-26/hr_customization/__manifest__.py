{
    'name': 'Attendance',
    'version': '1.0',
    'summary': 'Upload attendance data from Excel in HRMS',
    'description': """
Upload Attendance Excel directly from list view.
Adds an Upload Excel button beside New in HRMS.
""",
    'author': 'CMR',
    'category': 'Human Resources',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/attendance_excel_import_wizard.xml',
        'views/hr_upload.xml',
        'views/hr_attendance_views.xml',
        'views/overtime_master.xml',

    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
