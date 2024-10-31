from flaskblog import db
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_login import UserMixin


# database initialization
# child class 
class BlogPost(db.Model):
    __tablename__ = 'blog_post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Default to current time
    author_id = db.Column(db.Integer, db.ForeignKey("user.id")) # Foreign key to Users  
    subtitle = db.Column(db.String(200), nullable=False)  # Subtitle can be optional
    author = relationship("User", back_populates="posts") # This will allow us to access
    img_url = db.Column(db.Text(200), nullable=True)
    comments = relationship("Comment", back_populates="parent_post")

    def __repr__(self):
        return f'<Post {self.title}>'

# parent class 
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    comments = relationship("Comment", back_populates='comment_author')
    # define a one to many relationship between the code 
    posts = db.relationship('BlogPost', back_populates='author')
    
    def __repr__(self):  
        return f'<User {self.name}>'

class Comment(db.Model):
    __tablename__="comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    comment_author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comment_author = relationship("User", back_populates="comments")
    parent_post_id = db.Column(db.Integer, db.ForeignKey("blog_post.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
