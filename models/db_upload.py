
# deactive registration of new users
auth.settings.actions_disabled.append('register')

# add field for all users to store whether they want to be informed via email for every update
auth.settings.extra_fields['auth_user']= [
    Field('SendMessages', 'boolean', requires=IS_NOT_EMPTY()),
]

# change appearance of users in all auto generated forms
db.auth_user._format = '%(last_name)s'

auth.define_tables(username=True)

# create administrator group if not already there
#try:
#    auth.user_group('administrator')
#except KeyError:
#    auth.add_group('administrator')


### Do ondelete=’CASCADE’ has to be set on the auth_user table?
### Source: https://web2py.wordpress.com/tag/is_in_db/


db.define_table(
    'task',
    Field('Name', required=True),
    Field('Teacher', db.auth_user, required=True, label=T('Teacher')),
    Field('StartDate', 'date', required=True, label=T('StartDate')),
    Field('DueDate', 'date', required=True, label=T('DueDate')),
    Field('OpenForSubmission','boolean', label=T('OpenForSubmission')),
    Field('Token', 'string'),
    auth.signature,
    format='%(Name)s'
)

# display only last name of user instead of his/her id
db.task.DueDate.requires = IS_DATE(format=('%d.%m.%Y'))


db.define_table(
    'upload',
    Field('LastName', required=True, label=T('Last Name')),
    Field('FirstName', required=True, label=T('First Name')),
    Field('EMail', required=True, label=T('E-mail')),
    Field('AttendingClass', required=True, label=T('Class')),
    Field('Teacher', db.auth_user, required=True, label=T('Teacher')),
    Field('Task', db.task, required=True, label=T('Task')),
    Field('Token', 'string', label=T('Token')),
    Field('UploadedFile', 'upload', label=T('File to be uploaded')),
    auth.signature,
)

db.upload.LastName.requires = IS_NOT_EMPTY()
db.upload.FirstName.requires = IS_NOT_EMPTY()
db.upload.AttendingClass.requires = IS_NOT_EMPTY()
db.upload.EMail.requires = IS_EMAIL()

# define upload limits
db.upload.UploadedFile.requires = [IS_LENGTH(5242880, 0),IS_NOT_EMPTY()]

