from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request
import os
# from app_package.models import SocialPosts, sess
from sc_models import SocialPosts, sess
from sqlalchemy import desc
import logging
from logging.handlers import RotatingFileHandler

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
    social_posts = sess.query(SocialPosts).order_by(desc(SocialPosts.post_date)).all()
    
    # social_posts = social_posts[0] + social_posts[14]

    social_posts_list = []
    for db_post in social_posts:
        temp_post_dict = {}
        temp_post_dict['username'] = db_post.username
        temp_post_dict['title'] = db_post.title
        temp_post_dict['description'] = db_post.description
        temp_post_dict['url'] = db_post.url
        if db_post.social_name == 'Stack Overflow':
            temp_post_dict['social_name'] = "Stackoverflow"
        else:
            temp_post_dict['social_name'] = db_post.social_name
        temp_post_dict['social_icon'] = db_post.social_icon
        temp_post_dict['post_date'] = db_post.post_date

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




    social_posts = sess.query(SocialPosts).order_by(desc(SocialPosts.post_date)).all()
    
    # social_posts = social_posts[0] + social_posts[14]

    social_posts_list = []
    for db_post in social_posts:
        temp_post_dict = {}
        temp_post_dict['username'] = db_post.username
        temp_post_dict['title'] = db_post.title
        temp_post_dict['description'] = db_post.description
        temp_post_dict['url'] = db_post.url
        if db_post.social_name == 'Stack Overflow':
            temp_post_dict['social_name'] = "Stackoverflow"
        else:
            temp_post_dict['social_name'] = db_post.social_name
        temp_post_dict['social_icon'] = db_post.social_icon
        temp_post_dict['post_date'] = db_post.post_date

        social_posts_list.append(temp_post_dict)

    # social_posts_list_2 = [social_posts_list[0]] + [social_posts_list[13]] + [social_posts_list[14]]
    display_post = []
    counter = 0
    for post in social_posts_list:
                # if counter == 0:# first social post
        display_post.append(post)
        counter += 1

    return render_template('rest_of_posts.html', display_post = display_post)




@main.route('/more_about_me')
def more_about_me():
    return render_template('more_about_me.html')