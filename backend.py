from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from sqlalchemy.sql.expression import asc, desc, or_

#init app
app = Flask(__name__)

#Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bib_sq.db"

#only needed so the console doesn't complain
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Don't sort json elements alphabetically 
app.config['JSON_SORT_KEYS'] = False

# Init db
CORS(app)
db = SQLAlchemy(app)
## Init Marshmallow
ma = Marshmallow(app)

## Define Article Class
class Article(db.Model):
    __tablename__ = "Article"
    #__table_args__ = {'sqlite_autoincrement': True}
    
    #tell SQLAlchemy the name of column and its attributes:    
    id = db.Column(db.Integer, primary_key=True, nullable=False) 
    key = db.Column(db.String)
    ltype = db.Column(db.String)
    title = db.Column(db.String)
    author = db.Column(db.String)
    year = db.Column(db.Integer)
    publication = db.Column(db.String)
    doi = db.Column(db.String)
    pages = db.Column(db.Integer)
    issue = db.Column(db.String)
    volume = db.Column(db.String)
    tags = db.Column(db.String)

    # ToDo: needed?
    # def __init__(self, name, description, price, qty):
    #     self.name = name
    #     self.description = description
    #     self.price = price
    #     self.qty = qty

# Create DB
# db.create_all()

# Article Schema
class ArticleSchema(ma.Schema):
    class Meta:
        fields = ("title", "author", "year")
        ordered = True

# Init schema
article_schema = ArticleSchema()
articles_schema = ArticleSchema(many=True)

## Return Articles
@app.route("/articles", methods=["POST"])
def get_articles():
    """ 
    JSON SCHEME
    {
        'title': 'mytitle', 
        'author': 'myauthor', 
        'sortby': 'author', 
        'sortorder': 'asc'}
    }
    """
    req_data = request.get_json()
    print(req_data)

    title =  req_data["title"]
    author = req_data["author"]
    sortby = req_data["sortby"]
    sortorder = req_data["sortorder"]
    
    titlelist = title.split(" ")
    or_filter_title = [Article.title.like(f'%{term}%') for term in titlelist]
    authorlist = author.split(" ")
    or_filter_author = [Article.author.like(f'%{term}%') for term in authorlist]

    direction = desc if sortorder == 'desc' else asc

    all_articles = db.session.query(Article).\
        filter(or_(*or_filter_title), or_(*or_filter_author)).\
            order_by(direction(getattr(Article, sortby)))
    result = articles_schema.dump(all_articles)

    return jsonify(result)

# run Server
if __name__ == "__main__":
    app.run(debug=True)