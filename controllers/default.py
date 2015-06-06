
DO_MAIL = False

if DO_MAIL:
    from gluon.tools import Mail
    mail = Mail()
    mail.settings.server = ''
    mail.settings.sender = ''
    mail.settings.login = ''


def index():
    message = ('UpLoad@BBS dient dem einfachen Abgeben von Projektarbeiten, Präsentationen und Klassenarbeiten durch die Schüler. Um eine Datei hochzuladen, müssen zunächst Informationen zu Absender und Lehrkraft angegeben werden. Anschließend ist die abzugebende Datei auszuwählen. Die maximal erlaubte Dateigröße beträgt 5MB. Schließlich kann ein zusätzlicher Kommentar hinzugefügt werden.',
    'Nach Betätigung des Upload-Buttons wird die Datei übermittelt und anschließend per Mail an die ausgewählte Lehrkraft versandt. Die Schülerin/der Schüler bekommt ebenfalls eine Benachrichtigungsmail.')
    button = A(T('Upload file'), _href=URL('default', 'upload'), _class='btn btn-primary')
    return locals()


def upload():
    # TODO Storing the original filename (see: http://web2py.com/books/default/chapter/29/07/forms-and-validators#Storing-the-original-filename)
    form = SQLFORM(db.upload)
    # check if token is correct
    # check if now is between start date and due date
    # check if task and teacher correspond correctly
    # if form correct perform the insert
    if form.process().accepted:
        response.flash = T('File successfully uploaded!')
        if DO_MAIL:
            mail.send(request.vars.EMail, 'File successfully uploaded',
                      'Your file with the hash (MD5) xxx has been successfully uploaded.')
    return locals()


@auth.requires_login()
def collect():
    # include java script to submit form when combo box is changed
    # TODO change default value of combobox to represent last clicked
    script = SCRIPT("""
                    $('document').ready(function(){
                        $('select').change(function(){
                            $('form').submit();
                        });
                    });
                    """)
    # create drop down field with all tasks of current user
    tasks = db(db.task.Teacher == auth.user).select()
    task_combo = SELECT(_name='taskselect', value= request.vars.taskselect if request.vars.taskselect else '',
                        *[OPTION(tasks[i].Name, _value=str(tasks[i].id)) for i in range(len(tasks))])
    task_chooser = FORM(TR(T('Choose a task:'), task_combo))#,TR(INPUT(_name='Select task...', _type='submit')))
    # show chosen task with all its uploads
    if request.vars.taskselect:
        # if form was send with a chosen task show this task...
        uploads = db(db.upload.Task == request.vars.taskselect).select()
    else:
        # ...else show the first task of current user if there is one
        if tasks:
            uploads = db(db.upload.Task == tasks[0].id).select()
    download_button = A(T('Download all uploaded files...'), _href=URL('default', 'download_task'), _class='btn btn-primary')
    return locals()


@auth.requires_login()
def download_task():
    pass


def taskoptions():
    session.forget(response)
    tasks = db(db.task.Teacher == request.vars.Teacher).select(db.task.Name)
    return dict(tasks=tasks)


@auth.requires_login()
def manage():
    # create button to get to the login page
    login = A(T('Login to UpLoad'), _href=URL('user/login'), _class='btn btn-primary')

    # define all necessary information for data grid and build it
    if auth.has_membership('administrator'):
        query = ((db.task.id > 0))
        message = T('Administrator view: Task of all users are shown!')
    else:
        query = ((db.task.Teacher == auth.user))
    fields = (db.task.Name, db.task.Teacher, db.task.DueDate, db.task.Token)
    headers = {'task.Name':   T('Name'),
               'task.Teacher': T('Teacher'),
               'task.DueDate': T('DueDate'),
               'task.Token': T('Token')}
    default_sort_order=[db.task.DueDate]
    links = [lambda row: A(T('Collect uploaded files'), _href=URL('default', 'collect', args=[row.id]))]
    grid = SQLFORM.grid(query=query, fields=fields, headers=headers, orderby=default_sort_order, create=True,
                        links=links, deletable=True, editable=True, csv=False, maxtextlength=64, paginate=25) if auth.user else login
    return locals()


def user():
    return dict(form=auth())

