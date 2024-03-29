# from docx2python import docx2python
import os
import json
from flask import current_app
from flask_login import current_user
from datetime import datetime
from app_package.models import sess, Users, Blogposts
import shutil
from bs4 import BeautifulSoup
import zipfile
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler

#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_blog = logging.getLogger(__name__)
logger_blog.setLevel(logging.DEBUG)


#where do we store logging information
file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),"logs",'blog_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_blog.addHandler(file_handler)
logger_blog.addHandler(stream_handler)


def get_title(html_file_path_and_name, index_source):
    print("- In: blog/utils/get_title() -")
    title = ""
    #read html into beautifulsoup
    with open(html_file_path_and_name) as fp:
        soup = BeautifulSoup(fp, 'html.parser')

    if index_source == "ms_word":
        try:
            title = soup.p.find('span').contents[0]
        except:
            logger_blog.info(f"- No title found ms_word -")

    elif index_source == "original_html":
        list_of_soup_searches = ["h1", "h2", "h3", "h4"]
        
        for tag in list_of_soup_searches:
            title_tag = soup.find(tag)
            print("title_tag: ", title_tag)
            print("Examining tag: ", tag)
            if title_tag != None:
                break
        try:
            print("Getting contents for tag: ", tag)
            print(title_tag.contents[0])
            title=title_tag.contents[0]
        except:
            logger_blog.info(f"- No title found origina_html  -")


    return title

# # Part of old method used by whatSticks09web
# def create_new_html_text(html_file_path_and_name, static_image_folder_path):
#     #read html into beautifulsoup
#     with open(html_file_path_and_name) as fp:
#         soup = BeautifulSoup(fp, 'html.parser')

#     #get all images tags in html
#     image_list = soup.find_all('img')

#     # check all images have src or remove
#     for img in image_list:
#         try:
#             if img.get('src') == "":
#                 image_list.remove(img)
#             else:
#                 #remove old folder name from image path reference
#                 img['src'] = img['src'][img['src'].find("/")+1:]
#         except AttributeError:
#             image_list.remove(img)
        
#     #loop thorugh image
#     for img in image_list:
#         img['src']=f"{static_image_folder_path}{img['src']}"

#     return str(soup)


def replace_img_src_jinja(blog_post_index_file_path_and_name):
    
    logger_blog.info(f"- Reading file to replace img src jinja: {blog_post_index_file_path_and_name} -")
    logger_blog.info(blog_post_index_file_path_and_name)
    
    try:
        #read html into beautifulsoup
        with open(blog_post_index_file_path_and_name) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
    except FileNotFoundError:
        return "Error opening index.html"

    #get all images tags in html
    image_list = soup.find_all('img')


    # check all images have src or remove
    # for img in image_list:
    for img in soup.find_all('img'):
        # temp_dict = {}
        try:
            if img.get('src') == "":
                image_list.remove(img)
                print("removed img")
            else:
                print("***** REPLACING src *****")
                img['src'] = "{{ url_for('blog.custom_static', post_id_name_string=post_id_name_string,img_dir_name='" + \
                    img['src'][:img['src'].find("/")] \
                    +"', filename='"+ img['src'][img['src'].find("/")+1:]+"')}}"
        except AttributeError:
            image_list.remove(img)
            print('removed img with exception')



    # print(soup)
    return str(soup)


# # Part of old method used by whatSticks09web
# def save_post_html(formDict, post_html_file, file_path_str_to_templates_blog_posts, post_html_filename):
#     # save file with regular name in tmpleates/blog/post
#     post_html_file.save(os.path.join(file_path_str_to_templates_blog_posts, post_html_filename))

#     title = get_title(os.path.join(file_path_str_to_templates_blog_posts, post_html_filename))
#     logger_blog.info(f"- title is {title} -")

#     date_published_datatime = datetime.strptime(formDict.get('date_published'), "%Y-%m-%d")
#     print(f"*** date_published_datatime:  {date_published_datatime}")
#     print(f"*** date_published_datatime:  {type(date_published_datatime)}")


#     # add to database
#     new_post = Blogposts(user_id = current_user.id, title=title, 
#                     description= formDict.get('blog_description'), date_published= date_published_datatime,
#                     post_html_filename=post_html_filename)
#     sess.add(new_post)
#     sess.commit()

#     # get id from databse sess.Blogposts(blog_id_string="")
#     new_post = sess.query(Blogposts).filter_by(post_id_name_string=None).first()

#     logger_blog.info(f"- new_post is {new_post} -")

#     # make name for post YYYYMMDD_id
#     post_id_name_string = "communitypost_" + datetime.now().strftime("%Y%m%d") + f"_{new_post.id:04d}"

#     logger_blog.info(f"- post_id_name_string is {post_id_name_string} -")

#     # rename templates/blog/post file
#     old_name = os.path.join(file_path_str_to_templates_blog_posts, post_html_filename)
#     blog_post_new_name = os.path.join(file_path_str_to_templates_blog_posts, post_id_name_string+".html")
#     os.rename(old_name, blog_post_new_name)

#     logger_blog.info(f"- post_id_name_string is SUCCESFULL -")


#     new_post.post_id_name_string = post_id_name_string
#     # new_post.post_html_filename = 
#     sess.commit()

#     return (post_id_name_string, blog_post_new_name)

# # Part of old method used by whatSticks09web
# def save_post_images(post_images_zip, post_id_name_string, blog_post_new_name):

#     # Get zip folder name
#     zip_folder_name = post_images_zip.filename

#     #save zip with regular name in static/images/temp_zip ---> evenutally to delete
#     temp_zip_static = os.path.join(current_app.static_folder,'images','temp_zip')

#     # Check for static/images/temp_zip <-- where images are uploaded and saved in temporarily before unzipping
#     if not os.path.exists(temp_zip_static):
#         os.mkdir(temp_zip_static)
#     else:
#         shutil.rmtree(temp_zip_static)
#         os.mkdir(temp_zip_static)

#     post_images_zip.save(os.path.join(temp_zip_static, secure_filename(zip_folder_name)))

#     # add "_" instead of spaces in zip_folder_name
#     zip_folder_name_nospaces = zip_folder_name.replace(" ", "_")

#     # unzip file
#     with zipfile.ZipFile(os.path.join(temp_zip_static, zip_folder_name_nospaces), 'r') as zip_ref:
#         print("- unzipping file --")
#         unzipped_images_foldername = zip_ref.namelist()[0]
#         unzipped_temp_dir = os.path.join(temp_zip_static, "temp_unzipped")
#         zip_ref.extractall(unzipped_temp_dir)

#     unzipped_dir_list = [ f.path for f in os.scandir(unzipped_temp_dir) if f.is_dir() ]

#     for path_str in unzipped_dir_list:
#         # print(path_str)
#         if path_str[-8:] == "__MACOSX":
#             shutil.rmtree(path_str)
#             # print("**** removed __MACOSX ****")
    
#     print("--- unzipped image folder in list ---")
#     unzipped_dir_list = [ f.path for f in os.scandir(unzipped_temp_dir) if f.is_dir() ]
#     print(unzipped_dir_list )
#     unzipped_folder_name_with_images = unzipped_dir_list[0]


#     # copy files from unzipped_dir_name to 
#     static_img_communityposts_folder = os.path.join(current_app.static_folder,'images','communityposts')
#     static_img_destination_folder = os.path.join(current_app.static_folder,'images','communityposts', post_id_name_string)

#     # Check and/or make static/images/communitposts/
#     if not os.path.exists(static_img_communityposts_folder):
#         os.mkdir(static_img_communityposts_folder)

#     # Check and/or make static/images/communitposts/post_id_name_string
#     if not os.path.exists(static_img_destination_folder):
#         os.mkdir(static_img_destination_folder)

#     # move each image file in the uploaded unzipped static/images/temp_zip to the static/communityposts/post_id_name_string/
#     for unzipped_filename in os.listdir(unzipped_folder_name_with_images):
#         source = os.path.join(unzipped_folder_name_with_images, unzipped_filename)
#         dest = os.path.join(static_img_destination_folder, unzipped_filename)
#         shutil.copy(source, dest)

#     # delete compressed file
#     shutil.rmtree(temp_zip_static)

#     # edit html file to find images in new folder name
#     static_image_folder_path = "../static/images/communityposts/" + post_id_name_string +"/"
    
#     # read uploaded html replace old folder name image path reference with blog_post_new_name
#     new_html_text = create_new_html_text(blog_post_new_name, static_image_folder_path)

#     # Save new soup html
#     with open(blog_post_new_name, "w") as new_file:
#         new_file.write(new_html_text)

