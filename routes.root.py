
default_application = 'upload'
default_controller = 'upload'
default_function = 'index'

# filter out the applications name
#PREFIX = '/upload/'
#routes_in = [('/$anything' , PREFIX + '$anything')]
#routes_out = [(PREFIX + '$anything', '$anything')]

# set path to favicon files
routes_in=(
  ('.*:/favicon.ico','/upload/static/images/favicon.ico'),
  ('.*:/robots.txt','/upload/static/robots.txt'),
)
