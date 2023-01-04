from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, current_app
import os
# from app_package.models import SocialPosts, sess
from sc_models import SocialPosts, sess
from sqlalchemy import desc
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd

main = Blueprint('main', __name__)



# if os.environ.get('CONFIG_TYPE')=='local':
#     config_context = ConfigLocal()
# elif os.environ.get('CONFIG_TYPE')=='dev':
#     config_context = ConfigDev()
# elif os.environ.get('CONFIG_TYPE')=='prod':
#     config_context = ConfigProd()


#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_main = logging.getLogger(__name__)
logger_main.setLevel(logging.DEBUG)
# logger_terminal = logging.getLogger('terminal logger')
# logger_terminal.setLevel(logging.DEBUG)

#where do we store logging information
# file_handler = RotatingFileHandler(os.path.join(logs_dir,'users_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJ_ROOT_PATH'),'logs','users_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_main.addHandler(file_handler)
logger_main.addHandler(stream_handler)


@main.route("/", methods=["GET","POST"])
def home():
    logger_main.info(f"- in home page: / ")
    # social_posts = sess.query(SocialPosts).order_by(desc(SocialPosts.post_date)).all()
    
    social_posts_df = pd.read_pickle(os.path.join(current_app.config.get('PROJ_DB_PATH'), 'df_existing.pkl'))
    social_posts_df['post_date_to_datetime'] = pd.to_datetime(social_posts_df['post_date'])
    social_posts_list_of_dicts = social_posts_df.sort_values('post_date_to_datetime', ascending=False).to_dict('records')

    social_posts_list = []
    for social_post in social_posts_list_of_dicts:
        temp_post_dict = {}
        temp_post_dict['username'] = social_post.get('username')
        temp_post_dict['title'] = social_post.get('title')
        temp_post_dict['description'] = social_post.get('description')
        temp_post_dict['url'] = social_post.get('url')
        if social_post.get('social_name') == 'Stack Overflow':
            temp_post_dict['social_name'] = "Stackoverflow"
        else:
            temp_post_dict['social_name'] = social_post.get('social_name')
        temp_post_dict['social_icon'] = social_post.get('social_icon')
        temp_post_dict['post_date'] = social_post.get('post_date')

        social_posts_list.append(temp_post_dict)

    # social_posts_list_2 = [social_posts_list[0]] + [social_posts_list[13]] + [social_posts_list[14]]
    display_post = []
    counter = 0
    for post in social_posts_list:
    # for post in social_posts_list_2:

        current_social = post.get('social_name')

        if counter == 0:# first social post
            display_post.append(post)
            counter += 1
        
        elif counter > 0 and display_post[-1].get('social_name') == current_social:
            #if second social post is same as first, count until is different
            social_name = post.get('social_name')
            social_icon = post.get('social_icon')
            counter += 1
        elif counter == 1 and display_post[-1].get('social_name') != current_social:
            # if second most recent post is not same as first add that and stop displaying
            print('-- SECOND and final --')
            print('Type: ', post.get('social_name'))
            display_post.append(post)
            break
        else:
            # after second post if all are same skip until a new social shows -> this will be the third line in recent posts section
            temp_post_dict = {}
            # append dict item with social_name and icon of previous social add count
            temp_post_dict['social_name'] = social_name
            temp_post_dict['social_icon'] = social_icon
            temp_post_dict['counter'] = counter
            display_post.append(temp_post_dict)

            # get next post
            display_post.append(post)
            break



    div_class = "Twitter"
    print('--- display_post ---')
    print("length: ", len(display_post))
    print(display_post)
    return render_template('home.html', display_post = display_post, div_class=div_class)


@main.route('/rest_of_posts', methods=['GET','POST'])
def rest_of_posts():


    social_posts_df = pd.read_pickle(os.path.join(current_app.config.get('PROJ_DB_PATH'), 'df_existing.pkl'))
    social_posts_df['post_date_to_datetime'] = pd.to_datetime(social_posts_df['post_date'])
    social_posts_list_of_dicts = social_posts_df.sort_values('post_date_to_datetime', ascending=False).to_dict('records')

    # social_posts = sess.query(SocialPosts).order_by(desc(SocialPosts.post_date)).all()
    
    # Create List of lists

    size_of_lists_for_pagination = 10
    counter = 0
    page_list = []
    social_posts_list = []
    for social_post in social_posts_list_of_dicts:

        temp_post_dict = {}
        temp_post_dict['username'] = social_post.get('username')
        temp_post_dict['title'] = social_post.get('title')
        temp_post_dict['description'] = social_post.get('description')
        temp_post_dict['url'] = social_post.get('url')
        if social_post.get('social_name') == 'Stack Overflow':
            temp_post_dict['social_name'] = "Stackoverflow"
        else:
            temp_post_dict['social_name'] = social_post.get('social_name')
        temp_post_dict['social_icon'] = social_post.get('social_icon')
        temp_post_dict['post_date'] = social_post.get('post_date')

        social_posts_list.append(temp_post_dict)

        if counter % size_of_lists_for_pagination == 0 and counter > 0:
            page_list.append(social_posts_list)
            social_posts_list = []
        counter += 1


    # Determine paginaiton variables 


    pagination_position = int(request.args.get('pagination_position')) - 1
    print('pagination_position (0 - # of pages -1): ', pagination_position)
    page_list_displayed = page_list[pagination_position]
    number_of_pages = len(page_list)

    pagination_position = pagination_position + 1

    # 1 - # number of pages
    if pagination_position > 1:
        page_previous = pagination_position - 1
    else:
        page_previous = pagination_position
    
    if pagination_position == number_of_pages:
        page_next = pagination_position
    else:
        page_next = pagination_position + 1

    pagination_tuple = (page_previous, pagination_position, page_next)
    pagination_dict = {'first':1, 'previous':page_previous, 'current':pagination_position, 'next': page_next, 'last_page': number_of_pages }
    print('- pagination_dict -')
    print(pagination_dict)
    if request.method == 'POST':
        formDict = request.forms.to_dict()
        print('formDict: ', formDict)

    return render_template('rest_of_posts.html', display_post = page_list_displayed, number_of_pages = number_of_pages,
        pagination_dict = pagination_dict)




@main.route('/more_about_me')
def more_about_me():
    return render_template('more_about_me.html')