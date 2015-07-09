# -*- coding: utf-8 -*-

"""
Provides a default controller for application-level functions, like user profile and login.

Author: Christian Wichmann
"""


def index():
    """Redirect to index page of upload controller."""
    redirect(URL(request.application, 'upload', 'index'))
    return dict()


def user():
    """Shows the default user login form."""
    return dict(form=auth())

