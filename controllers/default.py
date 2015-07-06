# -*- coding: utf-8 -*-

import zipfile
import datetime
import os
import hashlib


# use mailer from Auth with credentials from appconfig.ini
mail = auth.settings.mailer


def index():
    """
    Shows the index page with an explanation about this web application.
    """
    message = (T('UpLoad@BBS is used to upload presentations, project documentation and tests. To upload a file you have to fill out the form with information about the uploader, the teacher and the task for which you want to upload a file. Then you can choose a file to be uploaded. The maximum file size is 5MiB.'),
               T('After the file was uploaded, the chosen teacher will be informed by email. The uploader also gets an email with the hash (SHA256) of the uploaded file.'))
    button = A(T('Upload file'), _href=URL('default', 'upload'), _class='btn btn-primary')
    remove_warning = SCRIPT('$("#javascript_warning").empty();')
    javascript_warning = DIV(T('This page only works with JavaScript.'), _id='javascript_warning')
    return locals()


def upload():
    """
    Displays the main upload form.

    The upload form allows a visitor to upload a file for one of the previously
    defined tasks by a teacher. Every visitor can upload a file without logging
    in, if she has the correct token for an open task.

    More information about cascading combo boxes:
     * http://www.web2pyslices.com/slice/show/1724/cascading-dropdowns-simplified
     * http://dev.s-cubism.com/plugin_lazy_options_widget
     * http://www.web2pyslices.com/slice/show/1467/cascading-drop-down-lists-with-ajax
    """
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
    if form.process(onvalidation=validate_upload_data).accepted:
        response.flash = T('File successfully uploaded!')
        # store original file name in database
        if form.vars.id:
            new_upload_entry = db(db.upload.id == form.vars.id).select().first()
            new_upload_entry.update_record(UploadedFileName=request.vars.UploadedFile.filename)
            new_upload_entry.update_record(FileHash=form.hash_of_file)
            new_upload_entry.update_record(IPAddress=request.client)
        if upload_conf.take('handling.do_mail', cast=bool):
            # sent mail to uploader
            mail.send(request.vars.EMail, T('File successfully uploaded'),
                      T('Your file ({filename}) with the hash (SHA256) {hash} has been successfully uploaded.').format(hash=form.hash_of_file, filename=request.vars.UploadedFile.filename))
            # send mail to teacher of task
            task_name = db(db.task.id == request.vars.Task).select().first()['Name']
            teacher_email = db(db.auth_user.id == request.vars.Teacher).select().first()['email']
            message_teacher = T('A file ({filename}) was uploaded for task {task} by {firstname} {lastname} with the hash (SHA256) {hash}.')
            mail.send(teacher_email, T('File uploaded for task {task}').format(task=task_name),
                      message_teacher.format(hash=form.hash_of_file, filename=request.vars.UploadedFile.filename,
                                             task=task_name, firstname=request.vars.FirstName, lastname=request.vars.LastName))
    return locals()


def validate_upload_data(form):
    """
    Validates the given data of a form. This function checks whether a file
    can be uploaded depending on the information in the given form. Currently
    it checks only whether a student has already uploaded a file for the
    chosen task and whether the task is open for submissions at the moment.

    If the student already uploaded a file or the task is not yet open for
    submission, an error message is stored in the form object.

    Some validation is done in the model via Validator objects and the requires
    parameter. See file db_upload.py.

    :param form: form to be checked
    """
    # check if token is correct -> DONE IN MODEL!
    # check if task and teacher correspond correctly -> DONE IN MODEL!
    # check if the task has opened for submissions
    open_for_submission = db(db.task.id == request.vars.Task).select().first()['OpenForSubmission']
    if not open_for_submission:
        form.errors.Task = T('Task is currently not open for submission.')
    # check if now is after start date
    start_date = db(db.task.id == request.vars.Task).select(db.task.StartDate).first()['StartDate']
    start_datetime = datetime.datetime.combine(start_date, datetime.datetime.min.time())
    if start_datetime > datetime.datetime.now():
        form.errors.Task = T('Submission for given task no yet allowed!')
    # check if student has already a file uploaded for given task
    uploads_from_student = db((db.upload.Task==request.vars.Task) &
                              (db.upload.FirstName==request.vars.FirstName) &
                              (db.upload.LastName==request.vars.LastName) &
                              (db.upload.AttendingClass==request.vars.AttendingClass)).count()
    if uploads_from_student:
        form.errors.Task = T('You already uploaded a file for this task!')
    # check if this exact file was uploaded before
    validate_uploaded_file_hash(form)


def validate_uploaded_file_hash(form):
    # create hash for raw bytes stored in request
    hash_of_file = hashlib.sha256(request.vars.UploadedFile.file.read()).hexdigest()
    # store hash that was calculated in form object so that it has not to be caculated again
    form.hash_of_file = hash_of_file
    # check if hash is already in database
    hash_already_in_database = db(db.upload.FileHash == hash_of_file).count()
    if hash_already_in_database:
        form.errors.UploadedFile = T('This exact file has been uploaded already by a user.')


def taskoptions():
    """
    Collects valid task for given teacher and returns them as JavaScript
    snippet.

    This function returns a JavaScript snippet that fills out the task combo
    box with all valid tasks of a teacher after the combo box containing the
    teachers changed. The snippet has the format:

        $('#upload_Task').append('
            <option value="11">Presentation</option>
            <option value="17">Programming task</option>
            <option value="42">Essay</option>
        ')

    TODO:
     * Change this to use either the OPTION class from web2py or transmit the
       task data to js. Then the data could be evaluated at the user. This would
       prevent the page 'taskoptions' to return an otherwise unusable string!

    :return: snippet to fill task combo box with valid entries
    """
    session.forget(response)
    tasks = db(db.task.Teacher == request.vars.Teacher).select(db.task.Name, db.task.id)
    options = '<option value=""></option>'
    #options += [OPTION(t.Name, _value=str(t.id)) for t in tasks]
    options += ''.join(['<option value="{id}">{text}</option>'.format(text=t.Name, id=t.id) for t in tasks])
    return "$('#upload_Task').append('%s')" % options


@auth.requires_login()
def collect():
    """
    Shows all uploads for a given task.

    If this page is opened without giving an argument via the request, all tasks
    are shown. If an argument is provided, it is used as task number and all
    uploads for that task are provided. Each uploaded file for the task can be
    downloaded separately. Alternatively all uploaded files can be downloaded as
    a zip file.

    :return: local variables dictionary
    """
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
    """
    Shows information for a specific upload identified by its hash value. If
    multiple uploads have the same hash, only the first one is displayed in
    detail. But multiple uploads of the same file should be prevented when
    uploading it! See upload() and validate_upload_data().

    Returns all local variables if an upload with given hash exists. Otherwise
    it raises a HTTP error exception (404).
    """
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
        # delete file if it already exists
        try:
            os.remove(archive_file_path)
        except OSError:
            pass
        # build a zip file with all uploaded files for the task
        with zipfile.ZipFile(archive_file_path, 'w') as upload_collection:
            for row in db(db.upload.Task == task_to_download).select():
                added_file_path = os.path.join(request.folder, 'uploads', row['UploadedFile'])
                # create directory name and add message if submission was late
                directory_in_zip_file_name = '{}, {}'.format(row['LastName'], row['FirstName'])
                if not row['SubmittedOnTime']:
                    directory_in_zip_file_name += T(' (late)')
                try:
                    archived_file_path = os.path.join(directory_in_zip_file_name,
                                                      row['UploadedFileName'].encode(upload_conf.take('handling.file_name_encoding')))
                    upload_collection.write(added_file_path, archived_file_path)
                except UnicodeError:
                    pass
                # TODO Unzip files into new ZIP file!
        # put file name of archive into database to be deleted at some point in the future
        db.created_archives.insert(FileName=archive_file_path)
        # transmit file to user
        r = response.stream(upload_collection.filename, request=request, attachment=True, filename=archive_file_name)
        return r
    else:
        raise HTTP(404, T('No task number given.'))


@auth.requires_login()
def manage():
    """Manages tasks to upload files to. New tasks can be created and existing
       task can be changed or deleted. Every logged in user can only see and
       change her own tasks. Only the users in the administrator group can see
       all tasks.

       When deleting a task all uploads will also be deleted! The uploaded files
       may still be in the /UpLoad/uploads/ directory, but all information about
       who uploaded them and when are lost.
       """
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
                        links=links, deletable=True, editable=True, csv=False, maxtextlength=64, paginate=25,
                        onvalidation=validate_task_data) if auth.user else login
    return locals()


def validate_task_data(form):
    """Validates the given data of a form. This function checks whether a task
       with the given name has been created already. If the form data is not
       valid, an error message is stored in the form object.

       :param form: form to be checked"""
    # only validate when a new task is created
    if request.args[0] == 'new':
        # check if the task name has been used by this teacher before
        tasks_with_same_name = db((db.task.Name == request.vars.Name) &
                                  (db.task.Teacher == request.vars.Teacher)).count()
        if tasks_with_same_name:
            form.errors.Name = T('You already created a Task with the same name. Please delete the old task or rename this one.')
        # check if teacher adds task for himself
        if request.vars.Teacher != str(auth.user_id):
            form.errors.Teacher = T('You can only create tasks for yourself.')


@auth.requires_membership('administrator')
def manage_teacher():
    form = SQLFORM.grid(db.auth_user)
    return dict(form=form)


@auth.requires_login()
def help():
    help = 'The following pages are available:'
    list_of_pages = UL(LI('upload'), LI('manage (restricted)'),
                       LI('download_task/[task_nr] (restricted)'),
                       LI('view_upload/[hash]'), LI('collect/[task_nr] (restricted)'))
    return locals()


def user():
    """Shows the default user login form."""
    return dict(form=auth())

