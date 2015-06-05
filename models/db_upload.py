
# deactive registration of new users
auth.settings.actions_disabled.append('register')

## after auth = Auth(db)
auth.settings.extra_fields['auth_user']= [
    Field('SendMessages','boolean',requires = IS_NOT_EMPTY()),
]
#db.auth_user.id.represent = db.auth_user._format % db.auth_user['last_name']
## before auth.define_tables(username=True)
auth.define_tables(username=True)

### Do ondelete=’CASCADE’ has to be set on the auth_user table???
### Source: https://web2py.wordpress.com/tag/is_in_db/

db.define_table(
    'task',
    Field('Name', required=True),
    Field('Teacher', db.auth_user, required=True),
    Field('DueDate', 'date', required=True),
    Field('Token', 'string'),
    auth.signature,
    format='%(Name)s'
)

# display only last name of user instead of his/her id
#db.task.Teacher.requires = IS_IN_DB(db, 'auth_user.id', '%(last_name)s', zero=T('choose one'))
db.task.DueDate.requires = IS_DATE(format=('%d.%m.%Y'))


db.define_table(
    'upload',
    Field('LastName', required=True),
    Field('FirstName', required=True),
    Field('EMail', required=True),
    Field('AttendingClass', required=True),
    Field('Teacher', db.auth_user, required=True),
    Field('Task', db.task, required=True),
    Field('Token', 'string'),
    Field('UploadedFile', 'upload'),
    auth.signature,
)

db.upload.LastName.requires = IS_NOT_EMPTY()
db.upload.FirstName.requires = IS_NOT_EMPTY()
db.upload.AttendingClass.requires = IS_NOT_EMPTY()
db.upload.EMail.requires = IS_EMAIL()
# define foreign keys
#db.upload.Teacher.requires = IS_IN_DB(db, 'auth_user.id', '%(last_name)s', zero=T('choose one'))
#db.upload.Task.requires = IS_IN_DB(db, 'task.id', '%(Name)s', zero=T('choose one'))
# define upload limits
db.upload.UploadedFile.requires = [IS_LENGTH(5242880, 0),IS_NOT_EMPTY()]

