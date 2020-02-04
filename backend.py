from flask import Flask, request, jsonify, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import pre_dump, post_dump, Schema
from flask_cors import CORS
from sqlalchemy.sql.expression import asc, desc, or_, and_
from pprint import pprint
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser
import os
from flask_basicauth import BasicAuth

#init app
app = Flask(__name__)

def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)

# the URI for the Databse depend on your setup and 
# should be setup as an environment variable DATABASE_URL (for example in your .env file)
#
# Examples
# DATABASE_URL = "postgresql://postgres:mypassword@localhost/bibfilter"
# DATABASE_URL = "sqlite:///new.db"

app.config['SQLALCHEMY_DATABASE_URI'] = get_env_variable("DATABASE_URL")

# Set Up Username and Password for Basic Auth as environment variables APP_USERNAME annd APP_PASSWORD
app.config['BASIC_AUTH_USERNAME'] = get_env_variable("APP_USERNAME")
app.config['BASIC_AUTH_PASSWORD'] = get_env_variable("APP_PASSWORD")

# silence the deprecation warning
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

# Don't sort json elements alphabetically 
app.config['JSON_SORT_KEYS'] = False

# Init Cors (needed to communicate properly on local server)
CORS(app)
# Init db
db = SQLAlchemy(app)
# Init Marshmallow
ma = Marshmallow(app)
# Init BasicAuth
basic_auth = BasicAuth(app)

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
        fields = ("author","year", "title", "journal", "doi")
        ordered = True

class ArticleSchemaAdmin(ma.Schema):

    class Meta:
        fields = ("ID","author","year", "title", "journal", "doi")
        ordered = True

class BibliographySchema(ma.Schema):
    SKIP_VALUES = set([None, "NaN"])

    # don't include NULL or "NaN" values in output JSON
    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items() if value not in self.SKIP_VALUES
        }

    class Meta:
        fields = ("title", "author","ID", "ENTRYTYPE", "year", "abstract", "volume", "number", "journal", "doi")

# Init schema
article_schema = ArticleSchema()
articles_schema = ArticleSchema(many=True)

bibliography_schema = BibliographySchema(many=True)

articles_schema_admin = ArticleSchemaAdmin(many=True)

## API: return .bib as string
@app.route("/bibfile", methods=["POST"])
def get_bibfile():
    req_data = request.get_json()
    entries = selectEntries(req_data)
    result = bibliography_schema.dump(entries)
    print(f"JSON returned of length {len(result)}")

    dbib = BibDatabase()
    dbib.entries = result
    bibtex_str = bibtexparser.dumps(dbib)
    return bibtex_str

## API: Return Articles
@app.route("/articles", methods=["POST"])
def get_articles():
    req_data = request.get_json()
    entries = selectEntries(req_data)
    result = articles_schema.dump(entries)
    print(f"JSON returned of length {len(result)}")

    return jsonify(result)

## API: Return Articles for Admin page
@app.route("/articles_admin", methods=["POST"])
def get_admin():
    req_data = request.get_json()
    entries = selectEntries(req_data)
    result = articles_schema_admin.dump(entries)
    print(f"JSON returned of length {len(result)}")
    return jsonify(result)

# API: Delete an article
@app.route("/delete/<key>", methods=["GET"])
@basic_auth.required
def delete_article(key):
    article = db.session.query(Article).filter(Article.ID == key).first()
    if article != None:
        print(f" Deleted Article: {article.title}")
        db.session.delete(article)
        # db.session.commit()
    return redirect("/admin")

## Frontend: Return our frontend
@app.route("/", methods=["GET"])
def main():
    return render_template("main.html")

## Frontend: Return admin page
@app.route("/admin", methods=["GET"])
@basic_auth.required
def admin():
    return render_template("admin.html")


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
    timestart = request_json["timestart"] if len(request_json["timestart"]) == 4 and request_json["timestart"].isdigit else str(1800)
    until = request_json["until"] if len(request_json["until"]) == 4 and request_json["until"].isdigit else str(2200)
    articletype = "%" if request_json["type"] == "all" else request_json["type"]
    
    titlelist = title.split(" ")
    or_filter_title = [Article.title.ilike(f'%{term}%') for term in titlelist]
    authorlist = author.split(" ")
    or_filter_author = [Article.author.ilike(f'%{term}%') for term in authorlist]
    direction = desc if sortorder == 'desc' else asc

    requested_articles = db.session.query(Article).\
        filter(or_(*or_filter_title), or_(*or_filter_author),\
            and_(Article.year >= timestart, Article.year <= until,\
                Article.ENTRYTYPE.like(articletype))).\
            order_by(direction(getattr(Article, sortby)))
    return requested_articles

# run Server
if __name__ == "__main__":
    app.run(debug=True)