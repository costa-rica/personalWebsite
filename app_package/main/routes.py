from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, current_app, jsonify, \
    make_response, send_from_directory
import os
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import shutil


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
file_handler = RotatingFileHandler(os.path.join(os.environ.get('WEB_ROOT'),'logs','main_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
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
    
    social_posts_df = pd.read_pickle(os.path.join(current_app.config.get('DB_ROOT'), current_app.config.get('SOCIAL_DF_FILE_NAME')))
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
            temp_post_dict['counter'] = counter - 1
            display_post.append(temp_post_dict)

            # get next post
            display_post.append(post)
            break


    return render_template('main/home.html', display_post = display_post)



@main.route('/rest_of_posts', methods=['GET','POST'])
def rest_of_posts():

    social_posts_df = pd.read_pickle(os.path.join(current_app.config.get('PROJ_DB_PATH'), current_app.config.get('SOCIAL_DF_FILE_NAME')))
    # social_posts_df = pd.read_pickle(os.path.join(current_app.config.get('PROJ_DB_PATH'), 'df_existing.pkl'))
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
    # path_to_images = os.path.join(current_app.config.get('PROJ_DB_PATH'),'images/')
    sourcePath = os.path.join(current_app.config.get('PROJ_DB_PATH'),'images/')
    destinationPath = os.path.join(current_app.static_folder,"images","dossier")

    if not os.path.exists(destinationPath):
        #copy images to static/images/dossier
        shutil.copytree(sourcePath, destinationPath)

    # print("- Destintation of copy: ", dest_of_copy)
    picture = os.path.join(destinationPath, "NickAndMolly2022.jpg")
    print("Picture path:")
    print(picture)


    return render_template('main/dossier_location.html', path_to_images=picture)


@main.route('/telecharger', methods=['GET','POST'])
def telecharger_dossier():
    # path_to_images = os.path.join(current_app.config.get('PROJ_DB_PATH'),'images')
    destinationPath = os.path.join(current_app.static_folder,"images","dossier")
    # return render_template('dossier_location.html', path_to_images=path_to_images+"/NickAndMolly2022.jpg")
    return send_from_directory(directory=destinationPath, path="nick_rodriguez_dossier.pdf")