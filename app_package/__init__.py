from flask import Flask
from sc_config import ConfigLocal, ConfigDev, ConfigProd
import os
import logging
from logging.handlers import RotatingFileHandler
from pytz import timezone
from datetime import datetime

if os.environ.get('CONFIG_TYPE')=='local':
    config = ConfigLocal()
    print('- Personalwebsite/__init__: Development - Local')
    # print('SQL_URI: ',config.SQL_URI)
elif os.environ.get('CONFIG_TYPE')=='dev':
    config = ConfigDev()
    print('- Personalwebsite/__init__: Development')
elif os.environ.get('CONFIG_TYPE')=='prod':
    config = ConfigProd()
    print('- Personalwebsite/__init__: Configured for Production')



if not os.path.exists(os.path.join(os.environ.get('PROJ_ROOT_PATH'),'logs')):
    os.makedirs(os.path.join(os.environ.get('PROJ_ROOT_PATH'), 'logs'))

# timezone 
def timetz(*args):
    return datetime.now(timezone('Europe/Paris') ).timetuple()

logging.Formatter.converter = timetz


#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

logger_init = logging.getLogger('__init__')
logger_init.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJ_ROOT_PATH'),'logs','__init__.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
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

logger_init.info(f'--- Starting ws08web ---')


def create_app(config_class=config):
    app = Flask(__name__)   
    app.config.from_object(config_class)
    
    from app_package.main.routes import main

    app.register_blueprint(main)

    return app