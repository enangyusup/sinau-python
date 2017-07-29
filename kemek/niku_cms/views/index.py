# -*- coding: utf-8 -*-
from flask import render_template

from niku_cms.app import app


@app.route('/')
def index():
    return render_template('index.html')
