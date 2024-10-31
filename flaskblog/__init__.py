from flask import Flask
from dotenv import load_dotenv
from datetime import datetime
import os
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_gravatar import Gravatar


app = Flask(__name__)
app.config['SECRET_KEY'] = '225635GDUETHIAHSGDY7333'
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Myblog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
db = SQLAlchemy(app)
load_dotenv()

# secret details
current_year = datetime.now().year
MY_EMAIL = os.getenv('MY_EMAIL')
MY_PASSWORD = os.getenv('MY_BLOG_PASSWORD')
RECIPIENT_EMAIL = MY_EMAIL

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='identicon',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
    
with app.app_context():
    db.create_all()

# Login Manager setup
login_manager = LoginManager()
login_manager.init_app(app)

from flaskblog import routes