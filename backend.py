from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import pre_dump, post_dump, Schema
from flask_cors import CORS
from sqlalchemy.sql.expression import asc, desc, or_
from pprint import pprint
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser

#init app
app = Flask(__name__)

#Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bib_sq.db"

#only needed so the console doesn't complain
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Don't sort json elements alphabetically 
app.config['JSON_SORT_KEYS'] = False

## needed to communicate properly on local server
CORS(app)

# Init db
db = SQLAlchemy(app)
## Init Marshmallow
ma = Marshmallow(app)

## Define Article Class
class Article(db.Model):
    __tablename__ = "Article"
    #__table_args__ = {'sqlite_autoincrement': True}
    
    #tell SQLAlchemy the name of column and its attributes:    
    dbid = db.Column(db.Integer, primary_key=True, nullable=False) 
    ID = db.Column(db.String)
    ENTRYTYPE = db.Column(db.String)
    title = db.Column(db.String)
    author = db.Column(db.String)
    year = db.Column(db.String)
    journal = db.Column(db.String)
    doi = db.Column(db.String)
    pages = db.Column(db.String)
    volume = db.Column(db.String)
    number = db.Column(db.String)
    tags = db.Column(db.String)
    abstract = db.Column(db.String)

    # needed?
    # def __init__(self, name, description, price, qty):
    #     self.name = name
    #     self.description = description
    #     self.price = price
    #     self.qty = qty

# Create DB / already done previously
# db.create_all()

# Article Schema
class ArticleSchema(ma.Schema):

    class Meta:
        fields = ("title", "author", "year")
        ordered = True

class BibliographySchema(ma.Schema):
    SKIP_VALUES = set([None])

    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items() if value not in self.SKIP_VALUES
        }

    class Meta:
        fields = ("title", "author","ID", "ENTRYTYPE", "year", "abstract", "volume", "number", "journal")

# Init schema
article_schema = ArticleSchema()
articles_schema = ArticleSchema(many=True)

bibliography_schema = BibliographySchema(many=True)

#return .bib as string
@app.route("/bibfile", methods=["POST"])
def get_bibfile():
    req_data = request.get_json()
    entries = selectEntries(req_data)
    result = bibliography_schema.dump(entries)
    print(result)
    
    dbib = BibDatabase()
    dbib.entries = result
    bibtex_str = bibtexparser.dumps(dbib)
    return bibtex_str

## Return Articles
@app.route("/articles", methods=["POST"])
def get_articles():
    req_data = request.get_json()
    entries = selectEntries(req_data)
    result = articles_schema.dump(entries)
    print(result)
    return jsonify(result)

def selectEntries(request_json):
    """ 
    JSON SCHEME
    {
        'title': 'mytitle', 
        'author': 'myauthor', 
        'sortby': 'author', 
        'sortorder': 'asc'}
    }
    """
    title =  request_json["title"]
    author = request_json["author"]
    sortby = request_json["sortby"]
    sortorder = request_json["sortorder"]
    
    titlelist = title.split(" ")
    or_filter_title = [Article.title.like(f'%{term}%') for term in titlelist]
    authorlist = author.split(" ")
    or_filter_author = [Article.author.like(f'%{term}%') for term in authorlist]

    direction = desc if sortorder == 'desc' else asc

    requested_articles = db.session.query(Article).\
        filter(or_(*or_filter_title), or_(*or_filter_author)).\
            order_by(direction(getattr(Article, sortby)))
    return requested_articles

# run Server
if __name__ == "__main__":
    app.run(debug=True)