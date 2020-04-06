from flask import request, jsonify, render_template, redirect
from sqlalchemy.sql.expression import asc, desc, or_, and_
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser
from bibfilter.models import Article, ArticleSchema, ArticleSchemaAdmin, BibliographySchema
from bibfilter import app, basic_auth, db
from pprint import pprint
from bibfilter.DOI_lookup import add_item
from datetime import datetime

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
        db.session.commit()

    return redirect("/admin")

# API: Delete an article
@app.route("/deleteTimePeriod/<dateFrom>/<dateUntil>", methods=["GET"])
@basic_auth.required
def deleteTimePeriod(dateFrom,dateUntil):
    datetimeFrom = datetime.strptime(dateFrom,"%Y-%m-%d")
    datetimeUntil = datetime.strptime(dateUntil,"%Y-%m-%d")
    
    articles = db.session.query(Article).filter(and_(Article._date_created >= datetimeFrom, Article._date_created <= datetimeUntil))
    if articles != None:
        numberDeleted = len(articles.all())
        articles.delete(synchronize_session=False)
        db.session.commit()
        print(f"Deleted {numberDeleted} Articles")
        return str(numberDeleted)
    else:
        return "0"

# API: Add an article
@app.route("/add/<prefix>/<suffix>", methods=["GET"])
def add_article(prefix, suffix):
    return add_item(prefix+"/"+suffix)

## Frontend: Return our frontend
@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def main():
    return render_template("main.html")

## Frontend: Return admin page
@app.route("/admin", methods=["GET"])
@basic_auth.required
def admin():
    return render_template("admin.html")

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
    or_filter_title = [Article.title.ilike(f'%{term}%') for term in titlelist]
    authorlist = author.split(" ")
    or_filter_author = [Article.author.ilike(f'%{term}%') for term in authorlist]
    direction = desc if sortorder == 'desc' else asc

    if timestart != "-1111" or until != "3333":
        requested_articles = db.session.query(Article).\
            filter(or_(*or_filter_title), or_(*or_filter_author),\
                and_(Article.year >= timestart, Article.year <= until,\
                    Article.ENTRYTYPE.like(articletype))).\
                order_by(direction(getattr(Article, sortby)))
    else:
        requested_articles = db.session.query(Article).\
            filter(or_(*or_filter_title), or_(*or_filter_author),\
                and_(Article.ENTRYTYPE.like(articletype))).\
                order_by(direction(getattr(Article, sortby)))

    return requested_articles