# T.set_current_languages('de', 'de-de')

def index():
    message = ('UpLoad@BBS dient dem einfachen Abgeben von Projektarbeiten, Präsentationen und Klassenarbeiten durch die Schüler. Um eine Datei hochzuladen, müssen zunächst Informationen zu Absender und Lehrkraft angegeben werden. Anschließend ist die abzugebende Datei auszuwählen. Die maximal erlaubte Dateigröße beträgt 5MB. Schließlich kann ein zusätzlicher Kommentar hinzugefügt werden.',
    'Nach Betätigung des Upload-Buttons wird die Datei übermittelt und anschließend per Mail an die ausgewählte Lehrkraft versandt. Die Schülerin/der Schüler bekommt ebenfalls eine Benachrichtigungsmail.')
    button = A('Upload file', _href=URL('default', 'upload'), _class='btn btn-primary')
    return locals()


def upload():
    form = SQLFORM(db.upload).process()
    # check if token is correct
    #if db.task[form.vars.Aufgabe]:
    #    response.flash = 'Korrekte Aufgabe!'
    #else:
    #    response.flash = 'Falsche Aufgabe!'
    # if form correct perform the insert
    if form.accepted:
        response.flash = 'Datei wurde hochgeladen!'
    return locals()
    #return dict(form=form)


@auth.requires_login()
def retrieve():
    uploads = db(db.upload).select()
    download_button = A('download zipped data', _href=URL('default', 'download_zip_file'), _class='btn btn-primary')
    return locals


@auth.requires_login()
def download_zip_file():
    pass


def user():
    return dict(form=auth())


def manage():
    login = A('login to upload', _href=URL('user/login'), _class='btn btn-primary')
    grid = SQLFORM.grid(db.task) if auth.user else login
    return locals()

