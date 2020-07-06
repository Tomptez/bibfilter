from flask import request, jsonify, render_template, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.sql.expression import asc, desc, or_, and_
from sqlalchemy.sql import func
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser
from bibfilter.models import Article, ArticleSchema, ArticleSchemaAdmin, BibliographySchema
from bibfilter import app, basic_auth, db
from pprint import pprint
from bibfilter.DOI_lookup import add_item
from bibfilter.convert_csv import create_db_from_csv
from datetime import datetime
from werkzeug.utils import secure_filename
import urllib.request
import os

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

## API: Return Articles
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

## API: Infos when last zotero sync occured
@app.route("/zotero_sync", methods=["POST"])
@basic_auth.required
def zotero_sync():
    max_value = db.session.query(func.max(Article.date_last_zotero_sync)).scalar()
    return max_value

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

# API: Delete timeperiod
# Todo
@app.route("/deleteTimePeriod/<dateFrom>/<dateUntil>/<dry>", methods=["GET"])
@basic_auth.required
def deleteTimePeriod(dateFrom,dateUntil,dry):
    datetimeFrom = datetime.strptime(dateFrom,"%Y-%m-%d")
    datetimeUntil = datetime.strptime(dateUntil,"%Y-%m-%d")
    
    articles = db.session.query(Article).filter(and_(Article._date_created >= datetimeFrom, Article._date_created <= datetimeUntil))
    if dry == "dry":
        numberDeleted = len(articles.all())
        return str(numberDeleted)
    elif dry == "delete":
        numberDeleted = len(articles.all())
        articles.delete(synchronize_session=False)
        db.session.commit()
        print(f"Deleted {numberDeleted} Articles")
        return str(numberDeleted)
    else:
        return 0

# API: Add an article
@app.route("/add/<doi>", methods=["GET"])
@limiter.limit("40/day")
def add_article(doi):
    # Convert the parameter back to the DOI by replacing all instances of '&&sl' with a slash '/'
    doi = doi.replace("&&sl","/")
    return add_item(doi)

## Frontend: Return our frontend
@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
@limiter.exempt
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
    #ILIKE is similar to LIKE in all aspects except in one thing: it performs a case in-sensitive matching
    or_filter_title = [Article.title.ilike(f'%{term}%') for term in titlelist]
    authorlist = author.split(" ")
    or_filter_author = [Article.author.ilike(f'%{term}%') for term in authorlist]
    direction = desc if sortorder == 'desc' else asc
    # Filter by Article.icon because unlike Artikcle.ENTRYTYPE, Article.icon groups books and bookchapters together
    filter_type = [~Article.icon.like("book"), ~Article.icon.like("article")] if articletype == "other" else [Article.icon.like(articletype)]

    if timestart != "-1111" or until != "3333":
        requested_articles = db.session.query(Article).\
            filter(or_(*or_filter_title), or_(*or_filter_author),\
                and_(Article.year >= timestart, Article.year <= until),\
                and_(*filter_type)).\
                order_by(direction(getattr(Article, sortby)))
    else:
        requested_articles = db.session.query(Article).\
            filter(or_(*or_filter_title), or_(*or_filter_author),\
                and_(*filter_type)).\
                order_by(direction(getattr(Article, sortby)))

    return requested_articles

# Upload .csv to update db
UPLOAD_FOLDER = 'csvupload'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['csv'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/file-upload', methods=['POST'])
@limiter.limit("15/day")
def upload_file():
    print("Running upload_file()")
    # check if the post request has the file part
    if 'file' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        print("No file part in the request")
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message' : 'No file selected for uploading'})
        print("No file selected for uploading")
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        cnt_add, cnt_exist, cnt_err = create_db_from_csv(filepath)
        print("Updated the database")
        resp = jsonify({'message' : f"File successfully uploaded. \n\nAdded {cnt_add} new Articles. {cnt_exist} Articles already existed in the database. {cnt_err} Articles couldn't be addded because of an error\n\nMaybe not all of the articles could be added because of a slow internet connection or the serverload. In this case, please upload the file again."})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message' : 'Allowed file type is .csv'})
        print("Wrong type")
        resp.status_code = 400
        return resp