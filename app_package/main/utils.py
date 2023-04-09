import pandas as pd
import os
from flask import current_app
from app_package.models import sess, Users, Blogposts


def create_social_posts_list():
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
    
    return social_posts_list

def create_display_post(social_posts_list):
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
    
    return display_post


def create_blog_posts_list():
    #Blog
    blog_posts = sess.query(Blogposts).all()

    blog_posts_list =[]
    for post in blog_posts:
        if post.date_published in ["", None]:
            post_date = post.time_stamp_utc.strftime("%Y-%m-%d")
        else:
            post_date = post.date_published.strftime("%Y-%m-%d")
        post_title = post.title
        post_description = post.description
        post_string_id = post.post_id_name_string
        
        blog_posts_list.append((post_date,post_title,post_description,post_string_id))
    
    print("- blog_posts_list -")
    print(blog_posts_list)

    return blog_posts_list