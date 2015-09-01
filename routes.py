# -*- coding: utf-8 -*-

#
#  Router for UpLoad application
#

routers = dict(
    BASE = dict(
        default_application = 'upload',
        default_controller = 'upload',
        default_function = 'index',
        #functions = ['index', 'manage', 'collect', 'manage_teacher', 'upload',
        #             'view_upload', 'download_task', 'user', 'help'],
        )
)

# set path to favicon files
routes_in=(
  ('.*:/favicon.ico','/upload/static/images/favicon.ico'),
  ('.*:/robots.txt','/upload/static/robots.txt'),
)
