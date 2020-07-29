from flask import request, jsonify, render_template, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.sql.expression import asc, desc, or_, and_
from sqlalchemy.sql import func
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser
from bibfilter.models import Article, ArticleSchema, ArticleSchemaAdmin, BibliographySchema
from bibfilter import app, basic_auth, db
from update_library import update_from_zotero
from datetime import datetime
import os
from sqlalchemy.sql.functions import ReturnTypeFromArgs
from unidecode import unidecode
from dotenv import load_dotenv

load_dotenv()

# Class needed to ignore accents. Not that the unaccent extension needs to be installed in postgreSQL
class unaccent(ReturnTypeFromArgs):
    pass

# Rate limiting Setup
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100/minute"]
)

# Init schemas
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

## API: Return Articles for main page table
@app.route("/articles", methods=["POST"])
@limiter.exempt
def get_articles():
    req_data = request.get_json()
    entries = selectEntries(req_data)
    result = articles_schema.dump(entries)
    print(f"JSON returned of length {len(result)}")

    return jsonify(result)

## API: Return Articles for Admin page
@app.route("/articles_admin", methods=["POST"])
@basic_auth.required
def get_admin():
    req_data = request.get_json()
    entries = selectEntries(req_data)
    result = articles_schema_admin.dump(entries)
    print(f"JSON returned of length {len(result)}")
    return jsonify(result)

## API Admin: Get Date of last sync between zotero and database
@app.route("/zotero_sync", methods=["GET"])
@basic_auth.required
def zotero_sync():
    max_value = db.session.query(func.max(Article.date_last_zotero_sync)).scalar()
    return max_value

## Admin API: Reset the database
@app.route("/resetDB", methods=["GET"])
@limiter.limit("5/day")
@basic_auth.required
def resetDB():
    articles = db.session.query(Article)

    numberDeleted = len(articles.all())
    articles.delete(synchronize_session=False)
    db.session.commit()
    print("/resetDB, Deleted all articles, now starting to sync")
    update_from_zotero()
    return redirect("/admin")

## Frontend: Return our frontend
@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
@limiter.exempt
def main():
    link = os.environ["SUGGEST_LITERATURE_URL"]
    return render_template("main.html", suggestLink=link)

## Frontend: Return admin page
@app.route("/admin", methods=["GET"])
@basic_auth.required
def admin():
    link = os.environ["SUGGEST_LITERATURE_URL"]
    return render_template("admin.html", suggestLink=link)

# Function to Select the correct articles based on the selection done by the user in the frontent
def selectEntries(request_json):
    """ 
    Example JSON:
    {
        "title":        "mytitle",
        "author":       "authorname", 
        "timestart":    "1960", 
        "until":        "2010", 
        "type":         "all",
        "sortby":       "author",
        "sortorder":    "asc"
    }
    """
    title =  request_json["title"]
    author = request_json["author"]
    sortby = request_json["sortby"]
    sortorder = request_json["sortorder"]
    timestart = request_json["timestart"] if len(request_json["timestart"]) == 4 and request_json["timestart"].isdigit else str(-1111)
    until = request_json["until"] if len(request_json["until"]) == 4 and request_json["until"].isdigit else str(3333)
    articletype = "%" if request_json["type"] == "all" else request_json["type"]
    
    titlelist = title.split(" ")
    #ILIKE is similar to LIKE in all aspects except in one thing: it performs a case in-sensitive matching
    #Unidecode removes accent from the search string whereas unaccent removes accents from the database. The unaccent Extension has to be installed for postgresql
    title_filter = [unaccent(Article.title).ilike(f'%{unidecode(term)}%') for term in titlelist]
    authorlist = author.split(" ")
    author_filter = [unaccent(Article.author).ilike(f'%{unidecode(term)}%') for term in authorlist]
    direction = desc if sortorder == 'desc' else asc
    # Filter by Article.icon because unlike Artikcle.ENTRYTYPE, Article.icon groups books and bookchapters together
    filter_type = [~Article.icon.like("book"), ~Article.icon.like("article")] if articletype == "other" else [Article.icon.like(articletype)]

    if timestart != "-1111" or until != "3333":
        requested_articles = db.session.query(Article).\
            filter(and_(*title_filter), or_(*author_filter),\
                and_(Article.year >= timestart, Article.year <= until),\
                and_(*filter_type)).\
                order_by(direction(getattr(Article, sortby)))
    else:
        requested_articles = db.session.query(Article).\
            filter(and_(*title_filter), or_(*author_filter),\
                and_(*filter_type)).\
                order_by(direction(getattr(Article, sortby)))


    return requested_articles