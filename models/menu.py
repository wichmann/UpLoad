response.logo = A('UpLoad', _class="navbar-brand",_href=URL('default', 'index'))
#response.logo = A(IMG(_src=URL('../logo.png'),_alt='UpLoad'),_class="navbar-brand",_href=URL('default', 'index'))

response.menu = []
response.menu.append(('Upload', False, URL('default', 'upload')))
if auth.is_logged_in():
    response.menu.append(('Download', False, URL('default', 'collect')))
    response.menu.append(('Manage', False, URL('default', 'manage')))
