# -*- coding: utf-8 -*-
from flask import Flask

from niku import db_session


app = Flask('niku_cms')
app.config.from_object('niku_cms.config')

@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()
