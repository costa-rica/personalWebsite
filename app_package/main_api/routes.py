from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, current_app, jsonify, \
    make_response
import os
# from app_package.models import SocialPosts, sess
# from sc_models import SocialPosts, sess
# from sqlalchemy import desc
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd


main_api = Blueprint('main_api', __name__)


#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_main_api = logging.getLogger(__name__)
logger_main_api.setLevel(logging.DEBUG)
# logger_terminal = logging.getLogger('terminal logger')
# logger_terminal.setLevel(logging.DEBUG)

#where do we store logging information
# file_handler = RotatingFileHandler(os.path.join(logs_dir,'users_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','main_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_main_api.addHandler(file_handler)
logger_main_api.addHandler(stream_handler)



@main_api.route('/check_api_post', methods=['GET','POST'])
def check_api_post():
    logger_main_api.info(f'--- check_api_post endpoint accessed ---')

    request_data = request.get_json()
    request_headers = request.headers

    if request_headers.get('password') == current_app.config.get('API_PASSWORD'):
        logger_main_api.info(f'--- check_api_post endpoint PASSWORD verified ---')

        f = open('check_api_post.txt', 'w')
        f.write("This works GRRREEAT!")
        f.close()

        return jsonify({"message": "successfully added new social activity"})
    else:
        logger_main_api.info(f'- password NOT verified -')
        return make_response('Could not verify',401)

@main_api.route('/collect_new_activity', methods=['GET','POST'])
def collect_new_activity():
    logger_main_api.info(f'--- collect_new_activity endpoint accessed ---')
    
    request_data = request.get_json()
    request_headers = request.headers

    # print(request_data.get('new_activity'))
    # print(type(request_data.get('new_activity')))

    if request_headers.get('password') == current_app.config.get('API_PASSWORD'):
        logger_main_api.info(f'--- collect_new_activity endpoint PASSWORD verified ---')
            
        # if request_data.get('new_activity')
        # print(len(request_data.get('new_activity')))
        # logger_main_api.info(f"new_activty is of tyep: {type(request_data.get('new_activity'))}")
        # logger_main_api.info(request_data.get('new_activity'))
        logger_main_api.info(f"length of received data list: {len(request_data.get('new_activity'))}")

        # put new post data into df_new_data
        # df_new_data = pd.DataFrame(json.loads(request_data.get('new_activity')))
        if isinstance(request_data.get('new_activity'),list):
            df_new_data = pd.DataFrame(request_data.get('new_activity'))
            logger_main_api.info(f"--- data sent is list ---")
        else:
            logger_main_api.info(f"--- data sent is NOT list - should be dict ---")
            df_new_data = pd.DataFrame([request_data.get('new_activity')])


        # logger_main_api.info(df_new_data.head())
        if len(df_new_data) == 0:
            logger_main_api.info(f'--- No new data from social aggregator call ---')
            return jsonify({"message": "successfully added new social activity"})

        else:
            logger_main_api.info(f"--- {len(df_new_data)} new items sent from social aggregator ---")
            

        if os.path.exists(os.path.join(current_app.config.get('DB_ROOT'),current_app.config.get('SOCIAL_DF_FILE_NAME'))):
            df_existing = pd.read_pickle(os.path.join(current_app.config.get('DB_ROOT'),current_app.config.get('SOCIAL_DF_FILE_NAME')))
            
            ### make unique index from network_post_id, social_name, title
            df_new_data.set_index(['network_post_id', 'social_name','title'], inplace=True)
            df_existing.set_index(['network_post_id', 'social_name','title'], inplace=True)

            df_to_add = df_new_data[~df_new_data.index.isin(df_existing.index)]

            #Append to df_exisitng
            df_mirror = pd.concat([df_existing, df_to_add]).reset_index()
            #df_existing to pickle
            df_mirror.to_pickle(os.path.join(current_app.config.get('DB_ROOT'),current_app.config.get('SOCIAL_DF_FILE_NAME')))
        
        else:# - All data is new
            df_new_data.to_pickle(os.path.join(current_app.config.get('DB_ROOT'),current_app.config.get('SOCIAL_DF_FILE_NAME')))

        return jsonify({"message": "successfully added new social activity"})
    else:
        logger_main_api.info(f'- password NOT verified -')
        return make_response('Could not verify',401)



@main_api.route('/latest_post_date', methods=['GET'])
def latest_post_date():
    logger_main_api.info(f'--- latest_post_date endpoint accessed ---')
    
    # request_data = request.get_json()
    request_headers = request.headers

    # print(request_data.get('new_activity'))
    # print(type(request_data.get('new_activity')))

    if request_headers.get('password') == current_app.config.get('API_PASSWORD'):
        logger_main_api.info(f'--- latest_post_date endpoint PASSWORD verified ---')

        df = pd.read_pickle(os.path.join(current_app.config.get('DB_ROOT'),current_app.config.get('SOCIAL_DF_FILE_NAME')))
        latest_post_date = df.post_date.max()
        logger_main_api.info(f'--- latest_post_date: {latest_post_date} ---')
        return jsonify({"date_of_last_post": latest_post_date})
    else:
        logger_main_api.info(f'- password NOT verified -')
        return make_response('Could not verify',401)
