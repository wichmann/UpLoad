
import zipfile
import datetime
import os
import hashlib

# import config for UpLoad application
config = local_import('config')


if config.DO_MAIL:
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

#
# Cascading combobox:
# www.web2pyslices.com/slice/show/1724/cascading-dropdowns-simplified
# dev.s-cubism.com/plugin_lazy_options_widget
# http://www.web2pyslices.com/slice/show/1467/cascading-drop-down-lists-with-ajax
#
def upload():
    # TODO Storing the original filename (see: http://web2py.com/books/default/chapter/29/07/forms-and-validators#Storing-the-original-filename)
    form = SQLFORM(db.upload)
    # search for combo box to choose teacher and append call to JavaScript
    # function to fill combo box for tasks of the chosen teacher
    teacher_combo = form.element(_name='Teacher')
    script = SCRIPT("""
                    function onchange_teacher() {{
                        // drop all options in combobox and fill with jquery command from ajax call
                        $("#upload_Task").empty();
                        ajax('{task_url}', ['Teacher'], ':eval');
                    }};
                    """.format(task_url=URL('default', 'taskoptions')))
    teacher_combo['_onchange'] = XML('onchange_teacher();')
    # validate and process the form
    if form.process(onvalidation=validate_task_data).accepted:
        response.flash = T('File successfully uploaded!')
        # create hash for file and store it in database
        file_on_disk = os.path.join(request.folder, 'uploads', str(form.vars.UploadedFile))
        hash_of_file = hashlib.sha256(open(file_on_disk, 'rb').read()).hexdigest()
        # store original file name in database
        if form.vars.id:
            new_upload_entry = db(db.upload.id == form.vars.id).select().first()
            new_upload_entry.update_record(UploadedFileName=request.vars.UploadedFile.filename)
            new_upload_entry.update_record(FileHash=hash_of_file)
        if config.DO_MAIL:
            mail.send(request.vars.EMail, 'File successfully uploaded',
                      'Your file with the hash (SHA256) {hash} has been successfully uploaded.'.format(hash=hash_of_file))
    return locals()


def validate_task_data(form):
    # check if the task has opened for submissions
    open_for_submission = db(db.task.id == request.vars.Task).select().first()['OpenForSubmission']
    if not open_for_submission:
        form.errors.Task = T('Task is currently not open for submission.')
    # check if token is correct
    #token_for_task = db(db.task.id == request.vars.Task).select().first()['Token']
    #given_token = request.vars.Token
    #if given_token == token_for_task:
    #    form.errors.Token = T('Wrong token for given task.')
    # check if now is after start date
    start_date = db(db.task.id == request.vars.Task).select(db.task.StartDate).first()['StartDate']
    start_datetime = datetime.datetime.combine(start_date, datetime.datetime.min.time())
    if start_datetime > datetime.datetime.now():
        form.errors.Task = T('Submission for given task no yet allowed!')
    # check if task and teacher correspond correctly [DONE IN MODEL!]


def taskoptions():
    session.forget(response)
    tasks = db(db.task.Teacher == request.vars.Teacher).select(db.task.Name, db.task.id)
    options = '<option value=""></option>'
    # TODO Change this to use either the OPTION class from web2py or transmit the task data to js. Then the data could
    # TODO be evaluated at the user. This would prevent the page 'taskoptions' to return an otherwise unusable string!
    #options += [OPTION(t.Name, _value=str(t.id)) for t in tasks]
    options += ''.join(['<option value="{id}">{text}</option>'.format(text=t.Name, id=t.id) for t in tasks])
    return "$('#upload_Task').append('%s')" % options


@auth.requires_login()
def collect():
    # TODO Use arguments instead of GET/POST vars as parameter to determine which uploads to show???
    # TODO -> Preload value of options in select with URL to upload listing...
    # TODO -> onclick="ajax('{{=URL('default', 'ajax_test')}}', [], 'target')"
    # get all task that should be shown in the combo box
    if auth.has_membership('administrator'):
        tasks_of_current_user = (db.task.id > 0)
        message = T('Administrator view: Task of all users are shown!')
    else:
        tasks_of_current_user = (db.task.Teacher == auth.user)
    # check whether this function was called with arguments
    if request.args:
        # show requested task with all its uploads
        task_to_be_looked_for = request.args[0]
        query = (db.upload.Task == task_to_be_looked_for)
        fields = (db.upload.LastName, db.upload.FirstName, db.upload.AttendingClass, db.upload.UploadedFile, db.upload.SubmittedOnTime)
        headers = {'db.upload.LastName':   T('LastName'),
                   'db.upload.FirstName': T('FirstName'),
                   'db.upload.AttendingClass': T('AttendingClass'),
                   'db.upload.UploadedFile': T('UploadedFile'),
                   'db.upload.SubmittedOnTime': T('SubmittedOnTime')}
        default_sort_order=[db.upload.LastName]
        grid = SQLFORM.grid(query=query, fields=fields, headers=headers, orderby=default_sort_order,
                            create=False, deletable=False, editable=False, csv=False, maxtextlength=64, paginate=25)
        download_button = A(T('Download all uploaded files...'), _href=URL(f='download_task', args=[task_to_be_looked_for]),
                            _class='btn btn-primary')
    else:
        # show all tasks of current user because no task was selected by the given argument
        fields = (db.task.Name, db.task.DueDate)
        headers = {'task.Name':   T('Name'),
                   'task.DueDate': T('DueDate')}
        default_sort_order=[db.task.DueDate]
        link_to_view = dict(header=T('View uploads'),
                      body=lambda row: A(T('View uploaded files'), _href=URL('default', 'collect', args=[row.id], user_signature=True)))
        link_to_download = dict(header=T('Download files'),
                      body=lambda row: A(T('Download files'), _href=URL('default', 'download_task', args=[row.id], user_signature=True)))
        links = [link_to_view, link_to_download]
        grid = SQLFORM.grid(query=tasks_of_current_user, fields=fields, headers=headers, orderby=default_sort_order,
                            create=False, deletable=False, editable=False, csv=False, links=links, maxtextlength=64,
                            paginate=25)
    return locals()


def view_upload():
    """Shows information for a specific upload."""
    if request.args:
        upload_to_be_looked_for = request.args[0]
        upload = db(db.upload.FileHash == upload_to_be_looked_for).select().first()
        return locals()
    else:
        raise HTTP(404, T('No hash for upload given.'))


@auth.requires_login()
def download_task():
    if request.args:
        task_to_download = request.args[0]
        current_task_name = db(db.task.id == task_to_download).select(db.task.Name).first().Name
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        archive_file_name = '{}_{}.zip'.format(current_task_name, current_date)
        archive_file_path = os.path.join(request.folder, 'private', archive_file_name)
        # TODO Check if old file with same name exists?
        with zipfile.ZipFile(archive_file_path, 'w') as upload_collection:
            for row in db(db.upload.Task == task_to_download).select():
                added_file_path = os.path.join(request.folder, 'uploads', row['UploadedFile'])
                # TODO Add message if submission was late!
                directory_in_zip_file_name = '{}, {}'.format(row['LastName'], row['FirstName'])
                # TODO Make sure row['UploadedFileName'] is not None!
                archived_file_path = os.path.join(directory_in_zip_file_name,
                                                  row['UploadedFileName'].encode(config.FILE_NAME_ENCODING))
                upload_collection.write(added_file_path, archived_file_path)
                # TODO Unzip files into new ZIP file!
        # put file name of archive into database to be deleted at some point in the future
        #os.remove(temp_file.name)
        # transmit file to user
        r = response.stream(upload_collection.filename, request=request, attachment=True, filename=archive_file_name)
        return r
    else:
        raise HTTP(404, T('No task number given.'))


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
    links = [dict(header=T('View uploads'),
                      body=lambda row: A(T('View uploaded files'), _href=URL('default', 'collect', args=[row.id], user_signature=True)))]
    grid = SQLFORM.grid(query=query, fields=fields, headers=headers, orderby=default_sort_order, create=True,
                        links=links, deletable=True, editable=True, csv=False, maxtextlength=64, paginate=25) if auth.user else login
    return locals()


def user():
    return dict(form=auth())

