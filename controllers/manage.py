# -*- coding: utf-8 -*-

"""
Provides a controller with all management functions to administrate UpLoad.

Author: Christian Wichmann
"""

import zipfile
import datetime
import os
import hashlib
import logging

from collections import defaultdict


# use mailer from Auth with credentials from appconfig.ini
mail = auth.settings.mailer

logger = logging.getLogger("web2py.app.upload")


@auth.requires_login()
def tasks():
    """
    Manages tasks to upload files to. New tasks can be created and existing
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
        fields = (db.task.Name, db.task.Teacher, db.task.DueDate, db.task.Token)
        message = T('Administrator view: Task of all users are shown!')
        headers = {'task.Name':   T('Name'),
                   'task.Teacher': T('Teacher'),
                   'task.DueDate': T('DueDate'),
                   'task.Token': T('Token')}
    else:
        fields = (db.task.Name, db.task.DueDate, db.task.Token)
        query = ((db.task.Teacher == auth.user))
        headers = {'task.Name':   T('Name'),
                   'task.DueDate': T('DueDate'),
                   'task.Token': T('Token')}
    default_sort_order=[db.task.DueDate]
    links = [dict(header=T('View uploads'),
                      body=lambda row: A(T('View uploaded files'),
                                         _href=URL('manage', 'collect', args=[row.id], user_signature=True)))]
    grid = SQLFORM.grid(query=query, fields=fields, headers=headers, orderby=default_sort_order, create=True,
                        links=links, deletable=True, editable=True, csv=False, maxtextlength=64, paginate=25,
                        onvalidation=validate_task_data) if auth.user else login
    return locals()


def validate_task_data(form):
    """
    Validates the given data of a form. This function checks whether a task
    with the given name has been created already. If the form data is not
    valid, an error message is stored in the form object.

    :param form: form to be checked
    """
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
def teachers():
    form = SQLFORM.grid(db.auth_user)
    return dict(form=form)


@auth.requires_login()
def download_task():
    if request.args:
        task_to_download = request.args[0]
        # TODO Check if at least one task was uploaded, else return a message?!
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
            list_of_files_till_now = defaultdict(int)
            for row in db(db.upload.Task == task_to_download).select(orderby=~db.upload.SubmissionTime):
                added_file_path = os.path.join(request.folder, 'uploads', row['UploadedFile'])
                # create directory name and add message if submission was late
                directory_in_zip_file_name = '{}, {}'.format(row['LastName'], row['FirstName'])
                if not row['SubmittedOnTime']:
                    directory_in_zip_file_name += T(' (late)')
                try:
                    archived_file_path = os.path.join(directory_in_zip_file_name, row['UploadedFileName'])
                    # FIXME Handle file name encoding inside ZIP archive currectly
                    #       -> .encode(upload_conf.take('handling.file_name_encoding')))
                    # check if this file name is already in archive (due to multiple
                    # uploads with same file name)
                    if archived_file_path in list_of_files_till_now:
                        archived_file_path += '_{}'.format(list_of_files_till_now[archived_file_path])
                    upload_collection.write(added_file_path, archived_file_path)
                    # store file name in dict to check for multiple uploads with the same file name
                    list_of_files_till_now[archived_file_path] += 1
                except UnicodeError:
                    logger.error('Encoding failure while creating ZIP file!')
                # TODO Unzip files into new ZIP file!
        # put file name of archive into database to be deleted at some point in the future
        db.created_archives.insert(FileName=archive_file_path)
        # transmit file to user
        r = response.stream(upload_collection.filename, request=request, attachment=True, filename=archive_file_name)
        return r
    else:
        raise HTTP(404, T('No task number given.'))


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
        fields = (db.upload.LastName, db.upload.FirstName, db.upload.AttendingClass,
                  db.upload.UploadedFile, db.upload.SubmittedOnTime)
        headers = {'db.upload.LastName':   T('LastName'),
                   'db.upload.FirstName': T('FirstName'),
                   'db.upload.AttendingClass': T('AttendingClass'),
                   'db.upload.UploadedFile': T('UploadedFile'),
                   'db.upload.SubmittedOnTime': T('SubmittedOnTime')}
        default_sort_order=[db.upload.LastName]
        grid = SQLFORM.grid(query=query, fields=fields, headers=headers,
                            orderby=default_sort_order, create=False, deletable=False,
                            editable=False, csv=False, maxtextlength=64, paginate=25)
        download_button = A(T('Download all uploaded files...'),
                            _href=URL(f='download_task', args=[task_to_be_looked_for]),
                            _class='btn btn-primary')
    else:
        # show all tasks of current user because no task was selected by the given argument
        fields = (db.task.Name, db.task.DueDate)
        headers = {'task.Name':   T('Name'),
                   'task.DueDate': T('DueDate')}
        default_sort_order=[db.task.DueDate]
        link_to_view = dict(header=T('View uploads'),
                      body=lambda row: A(T('View uploaded files'), _href=URL('manage', 'collect', args=[row.id], user_signature=True)))
        link_to_download = dict(header=T('Download files'),
                      body=lambda row: A(T('Download files'), _href=URL('manage', 'download_task', args=[row.id], user_signature=True)))
        links = [link_to_view, link_to_download]
        grid = SQLFORM.grid(query=tasks_of_current_user, fields=fields, headers=headers, orderby=default_sort_order,
                            create=False, deletable=False, editable=False, csv=False, links=links, maxtextlength=64,
                            paginate=25)
    return locals()


@auth.requires_login()
def help():
    help = 'The following pages are available:'
    list_of_pages = UL(LI('upload/upload'), LI('manage/tasks (restricted)'),
                       LI('manage/download_task/[task_nr] (restricted)'),
                       LI('upload/view/[hash]'), LI('manage/collect/[task_nr] (restricted)'),
                       LI('manage/teachers'))
    return locals()
