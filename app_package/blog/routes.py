from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request,current_app, get_flashed_messages, \
    send_from_directory
import os
from datetime import datetime
import time
from sqlalchemy import func
import json
from flask_login import login_user, current_user, logout_user, login_required
from app_package.blog.utils import  get_title, replace_img_src_jinja
from app_package.models import sess, Users, Blogposts
from sqlalchemy import func 
import shutil
import logging
from logging.handlers import RotatingFileHandler
import zipfile
from werkzeug.utils import secure_filename
import jinja2
from app_package.main.utils import create_blog_posts_list


#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_blog = logging.getLogger(__name__)
logger_blog.setLevel(logging.DEBUG)


#where do we store logging information
file_handler = RotatingFileHandler(os.path.join(os.environ.get('WEB_ROOT'),"logs",'blog_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_blog.addHandler(file_handler)
logger_blog.addHandler(stream_handler)

# blog = Blueprint('blog', __name__)
blog = Blueprint('blog', __name__, static_url_path=os.path.join(os.environ.get('WEB_ROOT'),"app_package","static"), 
    static_folder=os.path.join(os.environ.get('DB_ROOT'),"posts"))
    
@blog.route("/blog", methods=["GET"])
def index():


    blog_posts_list = create_blog_posts_list()
    items = ['date', 'title', 'description']


    # return render_template('blog/index.html', blog_dicts_for_index=blog_dict_for_index_sorted)
    return render_template('blog/index_table.html', blog_posts_list=blog_posts_list)


@blog.route("/blog/<blog_name>", methods=["GET","POST"])
def blog_template(blog_name):

    post_html = "blog/posts/" + blog_name + ".html"

    post=sess.query(Blogposts).filter_by(post_id_name_string=blog_name).first()
    post_date = post.date_published.strftime("%-d %B %Y")
    post_username = sess.query(Users).filter_by(id = post.user_id).first().username

    # get comments
    comments_query_list = sess.query(communitycomments).filter_by(post_id=post.id).all()

    comments_list = build_comment_dict(comments_query_list)



    if request.method == 'POST':
        formDict = request.form.to_dict()
        print("formDict: ", formDict)
        if current_user.guest_account == True:
            flash('Guest cannot edit data.', 'info')
            return redirect(url_for('blog.blog_template',blog_name=blog_name))
        
        elif formDict.get('submit_comment_add'):
            new_comment = communitycomments(user_id=current_user.id, post_id=post.id, comment=formDict.get('comment'))
            sess.add(new_comment)
            sess.commit()
            flash("Comment successfully added!", "success")
            return redirect(url_for('blog.blog_template',blog_name=blog_name))
        
        elif formDict.get('delete_comment'):
            comment_id_to_delete = formDict.get('delete_comment')
            sess.query(communitycomments).filter_by(id=int(comment_id_to_delete)).delete()
            sess.commit()
            flash(f"Deleted comment id: {comment_id_to_delete}", "warning")
            return redirect(url_for('blog.blog_template',blog_name=blog_name))


    return render_template('blog/view_post.html', post_html=post_html, post_date=post_date, post_username=post_username,
        comments_list = comments_list)


@blog.route("/view_post/<post_id_name_string>")
def view_post(post_id_name_string):

    templates_path_lists = [
        os.path.join(current_app.config.root_path,"templates"),
        os.path.join(current_app.config.get('DB_ROOT'),"posts", post_id_name_string)
    ]

    templateLoader = jinja2.FileSystemLoader(searchpath=templates_path_lists)

    templateEnv = jinja2.Environment(loader=templateLoader)
    template_parent = templateEnv.get_template("blog/view_post.html")
    template_layout = templateEnv.get_template("_layout.html")
    template_post_index = templateEnv.get_template("index.html")

    # If post has a sub folder

    # create a list called post_items_list

    #["<folder_name>/<file_name>"]

    return template_parent.render(template_layout=template_layout, template_post_index=template_post_index, \
        post_id_name_string=post_id_name_string, \
        url_for=url_for, get_flashed_messages=get_flashed_messages, )


@blog.route("/create_post", methods=["GET","POST"])
@login_required
def create_post():
    if not current_user.admin:
        return redirect(url_for('main.home'))

    logger_blog.info(f"- user has blog post permission -")

    default_date = datetime.utcnow().strftime("%Y-%m-%d")

    if request.method == 'POST':
        print("------------------------------")
        formDict = request.form.to_dict()
        print("formDict: ", formDict)
        request_files = request.files
        
        #######################################################
        # NOTE: Old method comes from whatSticks09web
        # It is deleted from code b
        ######################################################

        if request_files["new_method"].filename != "":
            logger_blog.info(f"- new_method -")

            # get data from form
            index_source = formDict.get('index_html_source')
            if formDict.get('date_published'):
                date_published_datetime = datetime.strptime(formDict.get('date_published'), "%Y-%m-%d")
                print(f"date_published: {date_published_datetime}")
            else:
                date_published_datetime = datetime.utcnow()
            post_zip = request_files["new_method"]
            post_zip_filename = post_zip.filename

            # create new_blogpost to get post_id number
            new_blogpost = Blogposts(user_id=current_user.id, date_published =date_published_datetime)
            sess.add(new_blogpost)
            sess.commit()

            # create post_id string and 
            new_blog_id = new_blogpost.id
            new_post_dir_name = f"{new_blog_id:04d}_post"
            new_blogpost.post_id_name_string = new_post_dir_name
            sess.commit()

            # save zip to temp_zip
            temp_zip_db_fp = os.path.join(current_app.config.get('DB_ROOT'),'temp_zip')
            if not os.path.exists(temp_zip_db_fp):
                os.mkdir(temp_zip_db_fp)
            else:
                shutil.rmtree(temp_zip_db_fp)
                os.mkdir(temp_zip_db_fp)
            
            post_zip.save(os.path.join(temp_zip_db_fp, secure_filename(post_zip_filename)))
            zip_folder_name_nospaces = post_zip_filename.replace(" ", "_")


            new_blog_dir_fp = os.path.join(current_app.config.get('DB_ROOT'), "posts", new_post_dir_name)
            logger_blog.info(f"- new_blog_dir_fp: {new_blog_dir_fp} -")

            # check new_blog_dir_fp doesn't already exists -- This is a weird check but let's just leave it in....
            if os.path.exists(new_blog_dir_fp):

                # delete db entery

                # delete db/posts/000_post dir

                flash(f"This blog post is trying to build a directory to store post, but one already exists in: {new_blog_dir_fp}","warning")
                return redirect(request.url)

            # decompress uploaded file in temp_zip
            with zipfile.ZipFile(os.path.join(temp_zip_db_fp, zip_folder_name_nospaces), 'r') as zip_ref:
                print("- unzipping file --")
                unzipped_files_foldername = zip_ref.namelist()[0]
                unzipped_temp_dir = os.path.join(temp_zip_db_fp, new_post_dir_name)
                print(f"- {unzipped_temp_dir} --")
                zip_ref.extractall(unzipped_temp_dir)

            logger_blog.info(f"- decompressing and extracting to here: {os.path.join(temp_zip_db_fp)}")

            unzipped_dir_list = [ f.path for f in os.scandir(unzipped_temp_dir) if f.is_dir() ]

            # delete the __MACOSX dir
            for path_str in unzipped_dir_list:
                if path_str[-8:] == "__MACOSX":
                    shutil.rmtree(path_str)
                    print(f"- removed {path_str[-8:]} -")

            # temp_zip path
            source = unzipped_temp_dir
            logger_blog.info(f"- SOURCE: {source}")


            # db/posts/0000_post
            destination = os.path.join(current_app.config.get('DB_ROOT'), "posts")

            dest = shutil.move(source, destination, copy_function = shutil.copytree) 
            logger_blog.info(f"Destination path: {dest}") 


            # beautiful soup to search and replace img src with {{ url_for('custom_static', ___, __ ,__)}}
            new_index_text = replace_img_src_jinja(os.path.join(new_blog_dir_fp,"index.html"))
            if new_index_text == "Error opening index.html":
                flash(f"Missing index.html? There was an problem trying to opening {os.path.join(new_blog_dir_fp,'index.html')}.", "warning")
                # return redirect(request.url)
                return redirect(url_for('blog.blog_delete', post_id=new_blog_id))

            # remove existing new_blog_dir_fp, index.html
            os.remove(os.path.join(new_blog_dir_fp,"index.html"))

            # write a new index.html with new_idnex_text
            index_html_writer = open(os.path.join(new_blog_dir_fp,"index.html"), "w")
            index_html_writer.write(new_index_text)
            index_html_writer.close()


            # delete compressed file
            shutil.rmtree(temp_zip_db_fp)

            # update new_blogpost.post_html_filename = post_id_post/index.html
            new_blogpost.post_html_filename = os.path.join(new_post_dir_name,"index.html")
            new_blogpost.title = get_title(os.path.join(new_blog_dir_fp,"index.html"), index_source)
            sess.commit()

            logger_blog.info(f"- filename is {new_post_dir_name} -")


        flash(f'Post added successfully!', 'success')
        return redirect(url_for('blog.blog_edit', post_id = new_blog_id))
        # return redirect(url_for('blog.create_post'))

    return render_template('blog/create_post.html', default_date=default_date)


@blog.route("/blog_user_home", methods=["GET","POST"])
@login_required
def blog_user_home():
    print('--- In blog_user home ----')
    logger_blog.info(f"- In blog_user_home -")

    if not current_user.admin:
        return redirect(url_for('main.home'))


    #check, create directories between db/ and static/
    # word_docs_dir_util()

    all_my_posts=sess.query(Blogposts).filter_by(user_id=current_user.id).all()
    # print(all_posts)
    posts_details_list=[]
    for i in all_my_posts:
        posts_details_list.append([i.id, i.title, i.date_published.strftime("%m/%d/%Y"),
            i.description, i.post_html_filename])
    
    column_names=['id', 'blog_title', 'delete','date_published',
         'blog_description','word_doc']

    if request.method == 'POST':
        formDict=request.form.to_dict()
        print('formDict::', formDict)
        if formDict.get('delete_record_id')!='':
            post_id=formDict.get('delete_record_id')
            print(post_id)

            return redirect(url_for('blog.blog_delete', post_id=post_id))
    #     elif formDict.get('edit_post_button')!='':
    #         print('post to delte:::', formDict.get('edit_post_button')[9:],'length:::', len(formDict.get('edit_post_button')[9:]))
    #         post_id=int(formDict.get('edit_post_button')[10:])
    #         return redirect(url_for('blog.blog_edit', post_id=post_id))
    return render_template('blog/user_home.html', posts_details_list=posts_details_list, len=len,
        column_names=column_names)


@blog.route("/delete/<post_id>", methods=['GET','POST'])
@login_required
def blog_delete(post_id):
    post_to_delete = sess.query(Blogposts).get(int(post_id))

    print("where did the reqeust come from: ", request.referrer)
    print("-------------------------------------------------")

    if current_user.id != post_to_delete.user_id:
        return redirect(url_for('blog.post_index'))
    logger_blog.info('-- In delete route --')
    logger_blog.info(f'post_id:: {post_id}')

    # delete word document in templates/blog/posts
    blog_dir_for_delete = os.path.join(current_app.config.get('DB_ROOT'), "posts",post_to_delete.post_id_name_string)

    try:
        shutil.rmtree(blog_dir_for_delete)
    except:
        logger_blog.info(f'No {blog_dir_for_delete} in static folder')

    # delete from database
    sess.query(Blogposts).filter(Blogposts.id==post_id).delete()
    sess.commit()
    print(' request.referrer[len("create_post")*-1: ]:::', request.referrer[len("create_post")*-1: ])
    if request.referrer[len("create_post")*-1: ] == "create_post":
        return redirect(request.referrer)

    flash(f'Post removed successfully!', 'success')
    return redirect(url_for('blog.blog_user_home'))


@blog.route("/edit/<post_id>", methods=['GET','POST'])
@login_required
def blog_edit(post_id):
    if not current_user.admin:
        return redirect(url_for('main.home'))

    post = sess.query(Blogposts).filter_by(id = post_id).first()
    title = post.title
    description = post.description
    post_time_stamp_utc = post.time_stamp_utc.strftime("%Y-%m-%d")

    # if post.date_published in ["", None]:
    #     post_date = post.time_stamp_utc.strftime("%Y-%m-%d")
    # else:
    if post.date_published in ["", None]:
        post_date = ""
    else:
        post_date = post.date_published.strftime("%Y-%m-%d")

    if request.method == 'POST':
        formDict = request.form.to_dict()

        title = formDict.get("blog_title")
        description = formDict.get("blog_description")
        date = formDict.get("blog_date_published")

        post.title = formDict.get("blog_title")
        post.description = formDict.get("blog_description")
        if formDict.get('blog_date_published') == "":
            post.date_published = None
        else:
            post.date_published = datetime.strptime(formDict.get('blog_date_published'), "%Y-%m-%d")
        sess.commit()

        flash("Post successfully updated", "success")
        return redirect(request.url)

    return render_template('blog/edit_post.html', title= title, description = description, 
        post_date = post_date, post_time_stamp_utc = post_time_stamp_utc)


# Custom static data
@blog.route('/<post_id_name_string>/<img_dir_name>/<filename>')
def custom_static(post_id_name_string,img_dir_name,filename):
    print("-- enterd custom static -")
    return send_from_directory(os.path.join(current_app.config.get('DB_ROOT'),"posts", post_id_name_string, img_dir_name), filename)



# Custom static data
@blog.route('/custom_static_dossier/<filename>')
def custom_static_dossier(filename):
    print("-- enterd custom_static_dossier -")
    return send_from_directory(os.path.join(current_app.config.get('DB_ROOT'),"dossier"), filename)




