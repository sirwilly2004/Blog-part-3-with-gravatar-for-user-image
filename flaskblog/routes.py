from functools import wraps
from flask import render_template,abort,flash,redirect,url_for,request
import time
from flask_login import login_user, login_required, current_user, logout_user
from flaskblog import app,login_manager, db, MY_EMAIL,RECIPIENT_EMAIL,MY_PASSWORD,current_year
from flaskblog.model import User, BlogPost, Comment 
from flaskblog.form import RegisterForm, LoginForm, CommentForm, CreatePostForm
from datetime import datetime
from flask import jsonify
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import bleach
import werkzeug



ALLOWED_TAGS = [
    'a', 'b', 'i', 'strong', 'em', 'p', 'ul', 'ol', 'li', 'br', 'span', 'div', 'blockquote',
    'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'tr', 'td', 'tbody', 'th', 'img'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'width', 'height'],
    'table': ['border', 'cellpadding', 'cellspacing', 'style'],
    'td': ['style'],
    'tr': ['style'],
    'th': ['style'],
    'div': ['class'],
    'span': ['class'],
}

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)        
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/insert_data')
def sample_data():
    database_post = BlogPost.query.all()
    # Add some sample data (this should have real data)
    sample_posts = [
            {
                "title": "The Future of Remote Work",
                "body": "Remote work has transformed the workplace landscape. Companies are now adopting hybrid models that combine in-office and remote work. This shift requires new management strategies and tools to maintain productivity and team cohesion.",
                "author": "Sarah Johnson",
                "subtitle": "Navigating the new normal of work-life balance.",
                "date": "2023-09-25"
            }
             ]
 
    with app.app_context():  
        for post_data in sample_posts:  
        # Convert date string to datetime object  
            post_data['date'] = datetime.strptime(post_data['date'], '%Y-%m-%d')  
            post = BlogPost(**post_data)  # Unpack the dictionary into the Post constructor  
            # Check if there is an existing post with the same title  
            check = BlogPost.query.filter_by(title=post.title).first()  
            if not check:  
                db.session.add(post) 
        db.session.commit()
    return jsonify({"message": "Sample data inserted successfully!"})  

def send_email(name, email, phone, message):
    subject = "New User for the Coding Class Whitelist"
    body = f"""
    Name: {name}
    Email: {email}
    Phone: {phone}
    Message: {message}
    """
    # Create the MIMEText object
    msg = MIMEMultipart()
    msg['From'] = MY_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Secure the connection
            server.login(MY_EMAIL, MY_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route("/")
def home_page():
    posts = BlogPost.query.all()
    return render_template("index.html", year=current_year, all_post=posts)

@app.route('/about')
def about():
    return render_template('about.html', year=current_year, logged_in=current_user.is_authenticated)

@app.route("/post/<int:post_id>" , methods=['POST', 'GET'])
def show_post(post_id):
    requested_post = db.session.query(BlogPost).filter_by(id=post_id).first()
    if requested_post is None:
        return "Post not found", 404
    # Format the date before passing it to the template
    formatted_date = requested_post.date.strftime('%B %d, %Y')
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))
        new_comment = Comment(
            text=form.comment.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template("post.html", post=requested_post, year=current_year, 
                           formatted_date=formatted_date, 
                           logged_in=current_user.is_authenticated, 
                           comment_form=form)


@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email_address = request.form.get('email_address')
        phone_number = request.form.get('phone_number')
        messages = request.form.get('messages')

        if not name or not email_address or not messages:
            flash('Please fill out all required fields.')
        time.sleep(50)
        send_email(name, email_address, phone_number, messages)
        flash('Your message has been sent successfully!')
        return render_template("contact.html", msg_sent=True, year=datetime.now().year)
    return render_template("contact.html", msg_sent=False, year=datetime.now().year, logged_in=current_user.is_authenticated)

@app.route('/new_post', methods=["GET", "POST"])
@admin_only
def new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        sanitized_body = bleach.clean(form.body.data, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            author_id=current_user.id,  # Use author_id
            img_url=form.img_url.data,
            author=current_user,
            body=sanitized_body
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home_page'))
    return render_template('new-post.html', form=form, year=current_year, new_pos=True, logged_in=current_user.is_authenticated)

@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    if requested_post is None:
        return "Post not found", 404
    edit_form = CreatePostForm(
        title=requested_post.title,
        subtitle=requested_post.subtitle,
        img_url=requested_post.img_url,
        author=current_user,
        body=requested_post.body
    )
    if edit_form.validate_on_submit():
        sanitized_body = bleach.clean(edit_form.body.data, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        requested_post.title = edit_form.title.data
        requested_post.subtitle = edit_form.subtitle.data
        requested_post.img_url = edit_form.img_url.data
        requested_post.body = sanitized_body
        requested_post.author=current_user
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))
    return render_template('new-post.html', form=edit_form, post=requested_post, year=datetime.now().year)

@app.route('/delete_post/<post_id>')
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    if post_to_delete is None:
        return "Post not found", 404
    else:
        db.session.delete(post_to_delete)
        db.session.commit()
    return redirect(url_for('home_page'))

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
        # user = User.query.filter_by(email=email).first()
        if not user:
            entered_password = request.form['password']
            hashed_pass = werkzeug.security.generate_password_hash(entered_password, method='pbkdf2:sha256', salt_length=8)
            name = request.form['name']
            new_user = User(
                email = email,
                password = hashed_pass,
                name = name
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home_page"))
        else:
            flash('Email already exists, please login')
            return redirect(url_for('login'))
    form = RegisterForm()
    return render_template("register.html", form=form, year=current_year)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form['email']
        password = request.form['password']
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
        if user and werkzeug.security.check_password_hash(user.password, password):
            login_user(user)
            print(f'{user.name} logged in')
            return redirect(url_for('home_page'))
        else:
            flash('Username or Password is wrong')
            return render_template("login.html", form=form) 
    return render_template("login.html", form=form, year=current_year)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home_page'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        # Assuming you have a method to search posts
        results = BlogPost.query.filter(BlogPost.title.contains(query)).all()  # Adjust as needed
    else:
        results = []
    
    return render_template('search_results.html', results=results, query=query)