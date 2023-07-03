from flask import Flask
from app_package.config import config
import os
import logging
from logging.handlers import RotatingFileHandler
from pytz import timezone
from datetime import datetime
from flask_mail import Mail
from app_package.models import login_manager


if not os.path.exists(os.path.join(os.environ.get('WEB_ROOT'),'logs')):
    os.makedirs(os.path.join(os.environ.get('WEB_ROOT'), 'logs'))

# timezone 
def timetz(*args):
    return datetime.now(timezone('Europe/Paris') ).timetuple()

logging.Formatter.converter = timetz


#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

logger_init = logging.getLogger('__init__')
logger_init.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('WEB_ROOT'),'logs','__init__.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)


stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

stream_handler_tz = logging.StreamHandler()

logger_init.addHandler(file_handler)
logger_init.addHandler(stream_handler)


#set werkzeug handler
logging.getLogger('werkzeug').setLevel(logging.DEBUG)
logging.getLogger('werkzeug').addHandler(file_handler)
#End set up logger

logger_init.info(f'--- Starting personalWebsite for iamnick.info ---')

mail = Mail()

def create_app(config_class=config):
    app = Flask(__name__)   
    app.config.from_object(config_class)
    login_manager.init_app(app)
    mail.init_app(app)
    
    from app_package.main.routes import main
    from app_package.main_api.routes import main_api
    from app_package.users.routes import users
    from app_package.blog.routes import blog
    from app_package.admin.routes import admin
    from app_package.error_handlers.routes import eh

    app.register_blueprint(main)
    app.register_blueprint(main_api)
    app.register_blueprint(users)
    app.register_blueprint(blog)
    app.register_blueprint(admin)
    app.register_blueprint(eh)

    return app