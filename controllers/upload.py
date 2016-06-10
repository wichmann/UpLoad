# -*- coding: utf-8 -*-

"""
Provides a controller with functions to upload files and view upload
information based on the files hash.

Author: Christian Wichmann
"""


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
    button = A(T('Upload file'), _href=URL('upload', 'upload'), _class='btn btn-primary')
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
    
    Todo:
     * Change to use HTML5-Upload with JQuery and stream file to server.
       (See http://www.web2pyslices.com/slice/show/1576/html5-file-uploads-with-jquery)
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
                    """.format(task_url=URL('upload', 'taskoptions')))
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
    if not upload_conf.take('handling.allow_multiple_uploads'):
        # TODO Use database field "MultipleUploadsAllowed" to check whether to allow multiple uploads.
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
    # return the read cursor to the start of the file because otherwise no content were written to file on disk
    request.vars.UploadedFile.file.seek(0)
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
    # find all tasks for the given teacher that are currently open for submission
    tasks = db((db.task.Teacher == request.vars.Teacher) & (db.task.OpenForSubmission == True)).select(db.task.Name, db.task.id)
    options = '<option value=""></option>'
    #options += [OPTION(t.Name, _value=str(t.id)) for t in tasks]
    options += ''.join(['<option value="{id}">{text}</option>'.format(text=t.Name, id=t.id) for t in tasks])
    return "$('#upload_Task').append('%s')" % options


def view():
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

