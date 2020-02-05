from flask import request, jsonify, render_template, redirect
from sqlalchemy.sql.expression import asc, desc, or_, and_
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser
from bibfilter.models import Article, ArticleSchema, ArticleSchemaAdmin, BibliographySchema
from bibfilter import app, basic_auth, db
from pprint import pprint

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

        # ToDo: uncomment to actually delete
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