
#response.logo = A('UpLoad', _class="navbar-brand",_href=URL('default', 'index'))
response.logo = A(IMG(_src=URL('static', 'images/logo.png'), _alt='UpLoad'), _class="navbar-brand", _href=URL('default', 'index'))

response.menu = []
response.menu.append((T('Upload file'), False, URL('default', 'upload')))
if auth.is_logged_in():
    response.menu.append((T('Download files'), False, URL('default', 'collect')))
    response.menu.append((T('Manage tasks'), False, URL('default', 'manage')))
