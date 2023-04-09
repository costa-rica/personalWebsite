from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request,current_app, get_flashed_messages, \
    send_from_directory
import os
from datetime import datetime
import time
from sqlalchemy import func
import json
from flask_login import login_user, current_user, logout_user, login_required
from app_package.blog.utils import create_new_html_text, get_title, save_post_html, \
    save_post_images, replace_img_src_jinja
from app_package.models import sess, Users, Blogposts
from sqlalchemy import func 
import shutil
import logging
from logging.handlers import RotatingFileHandler
import zipfile
from werkzeug.utils import secure_filename
import jinja2


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
def post_index():

    #make sure word doc folder exits with in static folder
    # word_docs_dir_util()

    #sorted list of published dates
    date_pub_list=[i.date_published for i in sess.query(Blogposts).all()]
    # create new list of sorted datetimes into increasing order
    sorted_date_pub_list = sorted(date_pub_list)
    #reverse new list
    sorted_date_pub_list.sort(reverse=True)

    #make dict of title, date_published, description
    items=['title', 'description','date_published' ]
    posts_list = sess.query(Blogposts).all()
    blog_dict_for_index_sorted={}
    for i in sorted_date_pub_list:
        for post in posts_list:
            if post.date_published == i:
                # temp_dict={key: (getattr(post,key) if key!='date_published' else getattr(post,key).strftime("%b %d %Y") ) for key in items}
                temp_dict = {key: getattr(post, key) for key in items}
                temp_dict['date_published'] = temp_dict['date_published'].strftime("%-d %b %Y")
                # temp_dict={key: getattr(post,key)  for key in items}
                temp_dict['blog_name']=post.post_id_name_string
                temp_dict['username'] = sess.query(Users).filter_by(id = post.user_id).first().username
                # temp_dict={key: (getattr(post,key) if key=='date_published' else getattr(post,key)[:9] ) for key in items}
                blog_dict_for_index_sorted[post.id]=temp_dict
                posts_list.remove(post)

    return render_template('blog/index.html', blog_dicts_for_index=blog_dict_for_index_sorted)


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


        if request_files["old_method_html"].filename != "":

            
            post_word_html_file = request.files.get('post_word_html_file')
            post_images_zip = request.files.get('post_images_zip')
            post_word_html_filename = post_word_html_file.filename

            logger_blog.info(f"- filename is {post_word_html_filename} -")

            file_path_str_to_db_templates_blog_posts = os.path.join(current_app.config.get('DB_ROOT'),"templates")
            file_path_str_to_db_static_blog_post_images = os.path.join(current_app.config.get('DB_ROOT'),"static")
            file_path_str_to_templates_blog_posts = os.path.join(current_app.config.root_path,"templates","blog","posts")
            

            # check if db_root/posts/post_id dir exists
            if not os.path.exists(file_path_str_to_db_dir_blog_posts):
                logger_blog.info(f"- making {file_path_str_to_db_dir_blog_posts} dir -")
                os.mkdir(file_path_str_to_db_dir_blog_posts)

            #check if templates/blog/posts exists
            if not os.path.exists(file_path_str_to_templates_blog_posts):
                logger_blog.info(f"- making templates/blog/posts dir -")
                os.mkdir(file_path_str_to_templates_blog_posts)

            # save 

            # check if file name already uploaded:
            existing_file_names_list = [i.name for i in os.scandir(file_path_str_to_templates_blog_posts)]
            if post_word_html_filename in existing_file_names_list:
                flash('A file with the same name has already been saved. Change file name and try again.', 'warning')
                return redirect(request.url)

            # Save blog_post_html to templates/blog/posts/
            post_id_name_string, blog_post_new_name = save_post_html(formDict, post_word_html_file, 
                                    file_path_str_to_templates_blog_posts, post_word_html_filename)

            # Save images to static/images/blog/000id/ <-- if there is a filename
            if post_images_zip.filename != "":
                logger_blog.info(f"- post_images_zip is not None -")
            
                # check if static/images/

                save_post_images(post_images_zip, post_id_name_string, blog_post_new_name)

        elif request_files["new_method"].filename != "":

            logger_blog.info(f"- !!!!!!! -")
            logger_blog.info(f"- in elif for post_html_file -")

            if formDict.get('date_published'):
                date_published_datetime = datetime.strptime(formDict.get('date_published'), "%Y-%m-%d")
                print(f"date_published: {date_published_datetime}")
            else:
                date_published_datetime = datetime.utcnow()

            post_zip = request_files["new_method"]
            post_zip_filename = post_zip.filename

            # create new_blogpost = sess.query(Blogpost).
            new_blogpost = Blogposts(user_id=current_user.id, title="temp_name")
            sess.add(new_blogpost)
            sess.commit()

            # blog_id = new_blogpost.id
            new_blog_id = new_blogpost.id
            new_post_dir_name = f"{new_blog_id:04d}_post"

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

            # check new_blog_dir_fp doesn't already exists -- This is a weird check but let's just leave it in....
            if os.path.exists(new_blog_dir_fp):
                flash(f"This blog post is trying to build a directory to store post, but one already exists in: {new_blog_dir_fp}","warning")
                return redirect(request.url)

            # decompress uploaded file in temp_zip
            with zipfile.ZipFile(os.path.join(temp_zip_db_fp, zip_folder_name_nospaces), 'r') as zip_ref:
                print("- unzipping file --")
                unzipped_files_foldername = zip_ref.namelist()[0]
                unzipped_temp_dir = os.path.join(temp_zip_db_fp, new_post_dir_name)
                print(f"- {unzipped_temp_dir} --")
                zip_ref.extractall(unzipped_temp_dir)

            print("- decompressing and extracting to here:")
            # print(f"- created: {os.path.join(temp_zip_db_fp, zip_folder_name_nospaces)}")
            print(f"- created: {os.path.join(temp_zip_db_fp)}")


            unzipped_dir_list = [ f.path for f in os.scandir(unzipped_temp_dir) if f.is_dir() ]

            # delete the __MACOSX dir
            for path_str in unzipped_dir_list:
                if path_str[-8:] == "__MACOSX":
                    shutil.rmtree(path_str)
                    print(f"- removed {path_str[-8:]} -")

            # temp_zip path
            source = unzipped_temp_dir
            print(f"- SOURCE: {source}")


            # db/posts/0000_post
            destination = os.path.join(current_app.config.get('DB_ROOT'), "posts")

            dest = shutil.move(source, destination, copy_function = shutil.copytree) 
            print("Destination path:", dest) 



            ###############################################################################
            # TODO: This beautiful soup needs to serach the index.html file in the rooot of the 0000_post
            # dir and replace the ______/filename.png with {{ url_for('custom_static', ___, __ ,__)}}
            # replace_img_src_jinja is almost doing this
            ##############################################################################
            print('---- Before beautiful soup stuff -')
            print("new_post_dir_name: ", os.path.join(new_blog_dir_fp,"index.html"))
            # beautiful soup to search and replace img src
            new_index_text = replace_img_src_jinja(os.path.join(new_blog_dir_fp,"index.html"))

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
            new_blogpost.post_id_name_string = new_post_dir_name
            new_blogpost.date_published = date_published_datetime
            new_blogpost.title = get_title(os.path.join(new_blog_dir_fp,"index.html"))
            sess.commit()

            logger_blog.info(f"- filename is {new_post_dir_name} -")


        flash(f'Post added successfully!', 'success')

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
    flash(f'Post removed successfully!', 'success')
    return redirect(url_for('blog.blog_user_home'))


@blog.route("/edit", methods=['GET','POST'])
@login_required
def blog_edit():
    if current_user.id != 1:
        return redirect(url_for('blog.post_index'))
    print('** Start blog edit **')
    post_id = int(request.args.get('post_id'))
    post = sess.query(Posts).filter_by(id = post_id).first()
    postHtml_list = sess.query(Postshtml).filter_by(post_id = post_id).all()[1:]
    published_date = post.date_published.strftime("%Y-%m-%d")

    # get list of word_row_id for post_id
    # put last object in first object's place
    merge_row_id_list = last_first_list_util(post_id)[1:]

    column_names = ['word_row_id', 'row_tag', 'row_going_into_html','merge_with_bottom']
    row_format_options = ['new lines','h1','h3', 'html', 'ul', 'ul and indent', 'indent',
        'image_title','image', 'codeblock','date_published']
    if request.method == 'POST':
        formDict=request.form.to_dict()
        # print('formDict::')
        # print(formDict)
        
        post.title = formDict.get('blog_title')
        post.description = formDict.get('blog_description')
        post.date_published = datetime.strptime(formDict.get('blog_pub_date'), '%Y-%m-%d')
        sess.commit()

        #update row_tag and row_going_into_html in Postshtml
        postHtml_update = sess.query(Postshtml).filter_by(post_id = post_id)
        
        #if title changed update first row psotHtml
        postHtml_title = postHtml_update.filter_by(word_row_id = 1).first()
        if post.title != postHtml_title.row_going_into_html:
            postHtml_title.row_going_into_html = post.title
            sess.commit()

        for i,j in formDict.items():
            
            if i.find('row_tag:'+str(post_id))>-1:
                word_row_id_temp = int(i[len('row_tag:'+str(post_id))+1:])
                update_row_temp=postHtml_update.filter_by(word_row_id = word_row_id_temp).first()
                update_row_temp.row_tag = j
                sess.commit()
            if i.find('row_html:'+str(post_id))>-1:
                word_row_id_temp = int(i[len('row_html:'+str(post_id))+1:])
                update_row_temp=postHtml_update.filter_by(word_row_id = word_row_id_temp).first()
                update_row_temp.row_going_into_html = j
                sess.commit()
        
        if formDict.get('delete_word_row'):
            row_to_delete = int(formDict.get('delete_word_row'))
            sess.query(Postshtml).filter_by(post_id = post_id,word_row_id = row_to_delete).delete()
            sess.query(Postshtmltagchars).filter_by(post_id = post_id,word_row_id = row_to_delete).delete()
            sess.commit()
        
        if formDict.get('start_cons_line') and formDict.get('end_cons_line'):
            #This will merge multiple rows if the start and end inputs are filled
            row_to_keep = int(formDict.get('start_cons_line'))
            row_to_move = row_to_keep + 1

            while row_to_move <= int(formDict.get('end_cons_line')):
                row_to_keep_obj=sess.query(Postshtml).filter_by(post_id=post_id, word_row_id=row_to_keep).first()
                row_to_move_obj=sess.query(Postshtml).filter_by(post_id=post_id, word_row_id=row_to_move).first()
                row_to_keep_obj.row_going_into_html=row_to_keep_obj.row_going_into_html+'<br>'+row_to_move_obj.row_going_into_html
                
                sess.query(Postshtml).filter_by(post_id=post_id, word_row_id=row_to_move).delete()
                sess.query(Postshtmltagchars).filter_by(post_id=post_id, word_row_id=row_to_move).delete()
                sess.commit()
                row_to_move += 1

            return redirect(url_for('blog.blog_edit',post_id=post_id ))

        if formDict.get('update_lines'):
            return redirect(url_for('blog.blog_edit',post_id=post_id ))

        else:
            #Merge one button pressed
            #This will merge the selected tbutton tothe row above
            for i in formDict.keys():# i is the merge button value
                if i[:1]=='_':
                    print('i that will become formDict_key: ', i, len(i))
                    formDict_key = i
                    print('int(i[6:]) that will become formDict_key: ', int(i[6:]))
                    row_to_move = int(i[6:])
            
            row_to_keep=int(formDict.get(formDict_key)[8:])
            row_to_keep_obj=sess.query(Postshtml).filter_by(post_id=post_id, word_row_id=row_to_keep).first()
            row_to_move_obj=sess.query(Postshtml).filter_by(post_id=post_id, word_row_id=row_to_move).first()
            row_to_keep_obj.row_going_into_html=row_to_keep_obj.row_going_into_html+'<br>'+row_to_move_obj.row_going_into_html
            
            sess.query(Postshtml).filter_by(post_id=post_id, word_row_id=row_to_move).delete()
            sess.query(Postshtmltagchars).filter_by(post_id=post_id, word_row_id=row_to_move).delete()
            sess.commit()

        return redirect(url_for('blog.blog_edit',post_id=post_id ))

    return render_template('blog/edit_template.html',post_id=post_id, post=post,
        postHtml_list=zip(postHtml_list,merge_row_id_list) , column_names=column_names, published_date=published_date,
        row_format_options=row_format_options )


# Custom static data
@blog.route('/<post_id_name_string>/<img_dir_name>/<filename>')
def custom_static(post_id_name_string,img_dir_name,filename):
    print("-- enterd custom static -")
    return send_from_directory(os.path.join(current_app.config.get('DB_ROOT'),"posts", post_id_name_string, img_dir_name), filename)


# Custom static data
@blog.route('/<post_id_name_string>/<filename>')
def custom_static_old(post_id_name_string,filename):
    print("-- enterd custom static -")
    return send_from_directory(os.path.join(current_app.config.get('DB_ROOT'),"posts", post_id_name_string,'articleDraft01.fld'), filename)
