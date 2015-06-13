
# import config for UpLoad application
config = local_import('config')

import datetime
now=datetime.datetime.now()

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
if db(db.auth_group.role == 'administrator').isempty():
    auth.add_group('administrator')


# create table to store names and dates for all created archives
db.define_table(
    'created_archives',
    Field('FileName', required=True),
    Field('CreationTime', 'datetime', writable=False, readable=False, default=now),
    auth.signature,
)


db.define_table(
    'task',
    Field('Name', required=True),
    Field('Teacher', db.auth_user, required=True, label=T('Teacher')),
    Field('StartDate', 'date', required=True, label=T('StartDate')),
    Field('DueDate', 'date', required=True, label=T('DueDate')),
    Field('OpenForSubmission','boolean', label=T('OpenForSubmission')),
    #Field('MultipleUploadsAllowed','boolean', label=T('MultipleUploadsAllowed')),
    Field('Token', 'string'),
    auth.signature,
    format='%(Name)s'
)

db.task.Name.requires = IS_NOT_EMPTY()
# display only last name of user instead of his/her id
db.task.DueDate.requires = IS_DATE(format=('%d.%m.%Y'))
db.task.StartDate.requires = IS_DATE(format=('%d.%m.%Y'))


db.define_table(
    'upload',
    Field('LastName', required=True, label=T('Last Name')),
    Field('FirstName', required=True, label=T('First Name')),
    Field('EMail', required=True, label=T('E-mail')),
    Field('AttendingClass', required=True, label=T('Class')),
    Field('Teacher', db.auth_user, required=True, label=T('Teacher')),
    Field('Task', db.task, required=True, label=T('Task')),
    Field('Token', 'string', label=T('Token')),
    Field('FileHash', 'string', writable=False, readable=False, label=T('Hash')),
    Field('IPAddress', 'string', writable=False, readable=False, label=T('IP Address')),
    Field('UploadedFile', 'upload', label=T('File to be uploaded')), # autodelete=True,
    Field('UploadedFileName', writable=False, readable=False),
    Field('SubmissionTime', 'datetime', writable=False, readable=False, default=now),
    Field('SubmittedOnTime', 'boolean', compute=lambda row: db(db.task.id == row['Task']).select(db.task.DueDate).first()['DueDate'] > row['SubmissionTime'].date()),
    auth.signature,
)

db.upload.LastName.requires = IS_NOT_EMPTY()
db.upload.FirstName.requires = IS_NOT_EMPTY()
db.upload.AttendingClass.requires = IS_NOT_EMPTY()
db.upload.EMail.requires = IS_EMAIL()

# define upload limits
db.upload.UploadedFile.requires = [IS_LENGTH(config.MAX_FILE_LENGTH, 0, error_message=T('File size is to large!')),
                                   IS_NOT_EMPTY(error_message=T('Choose a file to be uploaded!'))]
                                   # IS_UPLOAD_FILENAME(extension='txt')

# check whether the task is really from the given teacher
# (See: https://web2py.wordpress.com/category/web2py-validators/)
db.upload.Task.requires = IS_IN_DB(db(db.task.Teacher == request.vars.Teacher), 'task.id', '%(Name)s', error_message=T('Given task and teacher does not match!'))

# check whether the token is really from the given task
db.upload.Token.requires = IS_IN_DB(db(db.task.id == request.vars.Task), 'task.Token', error_message=T('Wrong token given!'))
db.upload.Token.widget = SQLFORM.widgets.string.widget

# check whether the task has started yet
#if request.vars.Task:
#    start_date = db(db.task.id == request.vars.Task).select(db.task.StartDate).first()['StartDate']
#    start_datetime = datetime.datetime.combine(start_date, datetime.datetime.min.time())
#    db.upload.SubmissionTime.requires = IS_DATETIME_IN_RANGE(minimum=start_datetime, error_message=T('Submission for given task no yet allowed!'))

# check whether the task has opened for submissions
#if request.vars.Task:
#    opened = db(db.task.id == request.vars.Task).select(db.task.OpenForSubmission).first()['OpenForSubmission']

