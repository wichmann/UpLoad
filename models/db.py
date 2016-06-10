# -*- coding: utf-8 -*-

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()


## get application configuration
from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
upload_conf = AppConfig(reload=True)


## create database connection using SQLite
db = DAL(upload_conf.take('db.uri'), pool_size=upload_conf.take('db.pool_size', cast=int), check_reserved=['all'])


## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## choose a style for forms
response.formstyle = upload_conf.take('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = upload_conf.take('forms.separator')


## optimize handling of static files
#response.optimize_css = 'concat,minify,inline'
#response.optimize_js = 'concat,minify,inline'


from gluon.tools import Auth, Service, PluginManager, Recaptcha

auth = Auth(db)
service = Service()
plugins = PluginManager()

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else upload_conf.take('smtp.server')
mail.settings.sender = upload_conf.take('smtp.sender')
mail.settings.login = upload_conf.take('smtp.login')
mail.settings.tls = False

## configure auth policy
#auth.settings.registration_requires_verification = False
#auth.settings.registration_requires_approval = False
#auth.settings.reset_password_requires_verification = True
# deactive registration of new users
auth.settings.actions_disabled.append('register')

## set captchas to be used for registration
auth.settings.captcha = Recaptcha(request, upload_conf.take('captchas.public', cast=str),
                                  upload_conf.take('captchas.private', cast=str))
auth.settings.login_captcha = False

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)


## set SQLite to Write-Ahead-Logging to prevent blocking when one user writes to database
try:
   db.executesql("PRAGMA journal_mode=WAL;")
except:
    pass


# add field for all users to store whether they want to be informed via email for every update
auth.settings.extra_fields['auth_user']= [
    Field('SendMessages', 'boolean', label=T('SendMessages')),
]

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

# change appearance of users in all auto generated forms
db.auth_user._format = '%(last_name)s'


def initialize_admin():
    if not db(db.auth_user).select().first():
        # create administrator group if not already there
        #if db(db.auth_group.role == 'administrator').isempty():
        new_admin_group = auth.add_group('administrator')
        # create new administrator and add him to admin group
        new_user_id = db.auth_user.insert(
            password = db.auth_user.password.validate('1234')[0],
            email = 'null@null.com',
            first_name = 'System',
            last_name = 'Administrator',
        )
        auth.add_membership(new_admin_group, new_user_id)

# initialize administrator account
initialize_admin()
#cache.ram('db_initialized', lambda: initialize_admin(), time_expire=None)

