UpLoad
======

Description
-----------
Upload service for students to upload their assignments written in Python.

UpLoad is used to upload presentations, project documentation and tests. To
upload a file you have to fill out the form with information about the
uploader, the teacher and the task for which you want to upload a file. Then
you can choose a file to be uploaded. A maximum file size can be set.

After the file was uploaded, the chosen teacher will be informed by email.
The uploader also gets an email with the hash (SHA256) of the uploaded file.


Deployment
----------
1) Create an web2py directory to be used by your web server.

2) Clone UpLoad repository from Github [1] to web2py/applications/.

3) Change database and mail configuration in UpLoad/private/appconfig.ini.

4) Copy routes.root.py from repository to main web2py directory. 

5) Go to http://[server address]/Upload and log in as null@null.com with the
   admin password "1234".

6) Change the name and email address of the administrator account.

7) Create new accounts for teachers under /UpLoad/default/manage_teacher.

8) Create new task to upload files to under /UpLoad/default/manage.

[1] https://github.com/wichmann/UpLoad.git


License
-------
Upload is released under the GNU General Public License v2 or newer.


Translations
------------
Translations were provided by:
* German translation by Christian Wichmann


Requirements
------------
UpLoad requires Python ???


Problems
--------
Please go to http://github.com/wichmann/UpLoad to submit bug reports, request
new features, etc.


Third party software
--------------------
UpLoad includes parts of or links with the following software packages and
programs, so give the developers lots of thanks sometime!

* web2py - Best Python Web Framework (http://www.web2py.com/)
* SQLite (http://sqlite.org/) is a software library that implements a self-
  contained, serverless, zero-configuration, transactional SQL database engine.
  SQLite is in the public domain. No claim of ownership is made to any part of
  the code.
*
*
