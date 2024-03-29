from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, current_app, jsonify, \
    make_response, send_from_directory
import os
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import shutil
from app_package.main.utils import create_social_posts_list, create_display_post, \
    create_blog_posts_list
from app_package.models import sess, Users, Blogposts


main = Blueprint('main', __name__)


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
file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','main_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
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
    
    # for Recent Posts Grid
    social_posts_list = create_social_posts_list()
    display_post = create_display_post(social_posts_list)

    blog_posts_list = create_blog_posts_list(3)

    return render_template('main/home.html', display_post = display_post,blog_posts_list=blog_posts_list )


@main.route('/rest_of_posts', methods=['GET','POST'])
def rest_of_posts():

    social_posts_df = pd.read_pickle(os.path.join(current_app.config.get('DB_ROOT'), current_app.config.get('SOCIAL_DF_FILE_NAME')))
    # social_posts_df = pd.read_pickle(os.path.join(current_app.config.get('DB_ROOT'), 'df_existing.pkl'))
    social_posts_df['post_date_to_datetime'] = pd.to_datetime(social_posts_df['post_date'])
    social_posts_list_of_dicts = social_posts_df.sort_values('post_date_to_datetime', ascending=False).to_dict('records')

    # social_posts = sess.query(SocialPosts).order_by(desc(SocialPosts.post_date)).all()
    
    # Create List of lists
    
    size_of_lists_for_pagination = int(request.args.get('size_of_lists_for_pagination'))

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

        try:
            social_posts_list_of_dicts[counter + 1]# check if there is one more post
            if counter % size_of_lists_for_pagination == 0 and counter > 0:
                page_list.append(social_posts_list)
                social_posts_list = []
        except IndexError:# <--- triggers when on the last post only. So just add this to list.
            page_list.append(social_posts_list)
            social_posts_list = []
        except ZeroDivisionError:# <--- triggers when user wants to see all posts in one page.
            page_list.append(social_posts_list)
            # social_posts_list = []
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
    # if request.method == 'POST':
    #     formDict = request.forms.to_dict()
    #     print('formDict: ', formDict)

    return render_template('main/rest_of_posts.html', display_post = page_list_displayed, number_of_pages = number_of_pages,
        pagination_dict = pagination_dict, size_of_lists_for_pagination = size_of_lists_for_pagination)



@main.route('/more_about_me')
def more_about_me():

    # search for more about me

    # get more about me file name

    return render_template('main/more_about_me.html')


@main.route('/dossier')
def dossier_location():

    #get path to database/images
    # path_to_images = os.path.join(current_app.config.get('DB_ROOT'),'images/')
    sourcePath = os.path.join(current_app.config.get('DB_ROOT'),'images/')
    destinationPath = os.path.join(current_app.config.get('DB_ROOT'),"dossier")

    if not os.path.exists(destinationPath):
        #copy images to static/images/dossier
        shutil.copytree(sourcePath, destinationPath)

    # print("- Destintation of copy: ", dest_of_copy)
    # picture = os.path.join(destinationPath, "NickAndMolly2022.jpg")
    # print("Picture path:")
    # print(picture)


    return render_template('main/dossier_location.html')


@main.route('/telecharger', methods=['GET','POST'])
def telecharger_dossier():
    # url_for('blog.custom_static', post_id_name_string=post_id_name_string,img_dir_name='index.fld', filename='image001.png')
    destinationPath = os.path.join(current_app.config.get('DB_ROOT'),"dossier")
    return send_from_directory(directory=destinationPath, path=current_app.config.get('DOSSIER_FILENAME'))