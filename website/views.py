from flask_pymongo import PyMongo
from flask import Blueprint, render_template, request, flash, redirect, url_for, Flask, session
import os
from .database import db
from .cache import cache

views = Blueprint('views', __name__)

@views.route('/')
#@cache.cached(timeout=3600, key_prefix='home')
def home():
    return render_template('home.html')