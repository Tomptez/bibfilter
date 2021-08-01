from flask import request, jsonify, render_template, redirect, url_for, Markup, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.sql.expression import asc, desc, or_, and_
from sqlalchemy.sql import func
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser
from bibfilter.models import Article, Wordstat, BibliographySchema, TableSchema
from bibfilter import app, basic_auth, db
from update_library import update_from_zotero
from datetime import datetime
import os
from sqlalchemy.sql.functions import ReturnTypeFromArgs
from unidecode import unidecode
from dotenv import load_dotenv
import threading
import nltk
from nltk.corpus import stopwords 
from flask_table import Table, Col, OptCol
import time
import cProfile
import io
import pstats
import contextlib

ENGLISH_STOPWORDS = set(stopwords.words('english'))

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
table_schema = TableSchema(many=True)
bibliography_schema = BibliographySchema(many=True)

## API: return .bib as string
@app.route("/bibfile", methods=["GET"])
@limiter.limit("4/minute")
def get_bibfile():
    arguments = request.args
    args = cleanArguments(arguments);
    articles = selectEntries(args, bibfile=True)
    result = bibliography_schema.dump(articles)

    dbib = BibDatabase()
    dbib.entries = result
    bibtex_str = bibtexparser.dumps(dbib)
    string_out = io.BytesIO(bytes(bibtex_str, 'utf-8'))
    return send_file(string_out, mimetype="text/plain", download_name="results.bib", as_attachment=True)

## API Admin: Get Date of last sync between zotero and database
@app.route("/zotero_sync", methods=["GET"])
@basic_auth.required
def zotero_sync():
    max_value = db.session.query(func.max(Article.date_last_zotero_sync)).scalar()

    # If the database is empty
    if max_value == None:
        max_value = "00-00-00 00:00"    
    return max_value

## Admin API: Clear the database
@app.route("/clearDB", methods=["GET"])
@limiter.limit("5/day")
@basic_auth.required
def clearDB():
    articles = db.session.query(Article)

    numberDeleted = len(articles.all())

    # synchronize_session (strategy for the removal of matched objects from the session): 
    # False = don’t synchronize the session. This option is the most efficient and is reliable once the session is expired, which typically occurs after a commit()
    # https://docs.sqlalchemy.org/en/13/orm/query.html
    articles.delete(synchronize_session=False)
    db.session.commit()
    print("/clearDB, Deleted all articles from Databse")
    return redirect("/admin")

## Admin API: Sync the database
@app.route("/resyncDB", methods=["GET"])
@limiter.limit("10/day")
@basic_auth.required
def resyncDB():
    print("/resyncDB, running update_from_zotero in background")

    # Running update_from_zotero using threading
    thread_update = threading.Thread(target=update_from_zotero)
    thread_update.start()
    return redirect("/admin")

# Redirect to main page if you land at index
@app.route("/index", methods=["GET"])
def index():
    return redirect("/")

## Frontend: Return our frontend
@app.route("/", methods=["GET"])
@limiter.exempt
def main():
    arguments = request.args
    base_url = request.base_url
    icons = {"book": f'<img src="{base_url}/static/img/book.png" class="typeicon">', "article":f'<img src="{base_url}/static/img/article.png" class="typeicon">', "other":f'<img src="{base_url}/static/img/other.png" class="typeicon">'}
    
    class ItemTable(Table):
        def __init__(self, args, **kwargs):
            ## First get __init__ from parent class Table, then extend it
            self.args = args
            super().__init__(**kwargs)
        
        no_items = "No literature was found"
        table_id = "literature"
        
        icon = OptCol(' ', choices=icons, default_key="other", column_html_attrs={"class":"colIcon"})
        authorlast = Col('Author', column_html_attrs={"class":"colAuthor"})
        year = Col('Year', column_html_attrs={"class":"colYear"})
        title = Col('Title', column_html_attrs={"class":"colTitle"})
        publication = Col('Publication', column_html_attrs={"class":"colPublication"})
        url = Col('URL', column_html_attrs={"class":"tableUrl colUrl"})
        wordcount = Col('Occur', show=False)
        abstract = Col('hidden', column_html_attrs={"class":"hiddenRowContent"})
        
        allow_sort = True

        def sort_url(self, col_key, reverse=False):
            if reverse:
                direction =  'desc'
            else:
                direction = 'asc'
            return url_for('main', sort=col_key, direction=direction, search=self.args["search"], title=self.args["title"], content=self.args["content"], author=self.args["author"], timestart=self.args["timestart"], until=self.args["until"], type=self.args["type"])
        
        def get_tr_attrs(self, item):
            if item["abstract"] != "":
                return {'class': 'clickable'}
            else:
                return {}

    args = cleanArguments(arguments)
    args_get_str = argsToStr(arguments)
    
    # Query items from database
    begin = time.time()
    requested_articles = selectEntries(args)
    
    end = time.time()
    print(f"\nExecuting query took {end - begin:.4f} seconds")
    
    items = cleanResults(args, requested_articles)
    
    countsorting = False
    # Sort on wordcount if no other sorting is specified
    if arguments.get("content") != None and arguments.get("content") != "" and arguments.get("sort") == None:
        items = sorted(items, reverse=True, key=lambda k: k["wordcount"]) 
    
    sort = args["sort"]
    reverse = True if args["direction"] == "desc" else False
    # args need to be passed so the filter isn't reset when sorting
    table = ItemTable(args=args, items=items, sort_by=sort, sort_reverse=reverse)
    
    numResults = len(items)
    
    suggestLink = os.environ["SUGGEST_LITERATURE_URL"]
    
    end = time.time()
    print(f"Finished loading everything in {end - begin:.4f} seconds\n")
    return render_template("main.html", table=table, args=arguments, getStr=args_get_str, numResults=numResults, suggestLink=suggestLink)

  
## Frontend: Return admin page
@app.route("/admin", methods=["GET"])
@basic_auth.required
def admin():
    link = os.environ["SUGGEST_LITERATURE_URL"]
    return render_template("admin.html", suggestLink=link)


def cleanArguments(arguments):
    args = {"title":"", "author":"", "timestart":"", "until":"", "type":"all", "sort":"author", "direction":"asc", "content":"", "search":""}
    
    args.update(arguments)
    
    if args["content"] != "":
        # Lemmatize Content search words
        stemmer = nltk.stem.snowball.SnowballStemmer("english")
        # Split content searchstring into a list and remove special characters
        args["content"] = [''.join(e for e in word if e.isalnum()) for word in args["content"].split()]
        # Use only the root of the word
        args["content"] = [stemmer.stem(word) for word in args["content"]]
        # Ignore english stopwords
        args["content"] = [word for word in args["content"] if word not in ENGLISH_STOPWORDS]
    
    return args

def cleanResults(args, requested_articles):
    items = []
    
    for ki, item in enumerate(requested_articles):
        item = dict(item)
            
        if item["url"] != "":
            item["url"] = Markup(f'<a class="externalUrl" target="_blank" href="{item["url"]}">Source</a>')
        
        if args["content"] != "":
            for ji, li in enumerate(item["quotes"]):
                    item["quotes"][ji] = li.split(';SEP;')
        
        def formatQuotes():
            finalQuotes = ""
            count = 0
            # Take all 4 quotes available
            for i in range(4):
                for j, searchterm in enumerate(args["content"]):
                    count += 1
                    try:
                        if finalQuotes == "":
                            finalQuotes = item["quotes"][j][i]
                            # finalQuotes = item["quote"][searchterm][i]
                        else:
                            finalQuotes += "<p>" + item["quotes"][j][i] + "</p>"
                            # finalQuotes += "<p>" + item["quote"][searchterm][i] + "</p>"
                    except Exception as e:
                        # list index out of range (When there is less than 4 qzote available)
                        # if there are no quotes left for either searchterm return:
                        if j+1 == len(args["content"]):
                            return finalQuotes
                        else:
                            continue
                    
                    # Use six quotes at most (when using multiple searchterms)
                    if count == 6:
                        return finalQuotes
            return finalQuotes
        
        # Check whether environment variable is set to show search quotes            
        formattedAbstract = f'<b>Abstract</b><br>{item["abstract"]}</b><br>' if item["abstract"] != "" else ""         
        if args["content"] != "" and os.environ.get("SHOW_SEARCH_QUOTES") == "Yes":
            finalQuotes = formatQuotes()
            
            hiddentext = Markup(f'<div class="hidden_content">{formattedAbstract}<br><b>Search Results</b><br>{finalQuotes}</div>')
        else:
            if item["abstract"] != "":
                hiddentext = Markup(f'<div class="hidden_content">{formattedAbstract}</div>')
            else:
                hiddentext = ""
            
        item["abstract"] = hiddentext
        
        if "wordcount" not in item:
            item["wordcount"] = 0
        items.append(item)
    
    return items

def argsToStr(arguments):
    if len(arguments) > 0:
        args_get_str = "?"
        for key, val in arguments.items():
            if args_get_str != "?":
                args_get_str += "&"
            args_get_str += f"{key}={val}"
    else:
        args_get_str = ""
    return args_get_str

# Function to Select the correct articles based on the selection done by the user in the frontent
def selectEntries(request_json, bibfile=False):
    """ 
    Example JSON:
    {
        "title":        "mytitle",
        "author":       "authorname", 
        "timestart":    "1960", 
        "until":        "2010", 
        "type":         "all",
        "sortby":       "author",
        "sort_order":    "asc"
    }
    """
    
    search_term = request_json["search"]
    title =  request_json["title"]
    author = request_json["author"]
    
    sortby = request_json["sort"]
    sort_order = request_json["direction"]
    timestart = request_json["timestart"] if len(request_json["timestart"]) == 4 and request_json["timestart"].isdigit else None
    until = request_json["until"] if len(request_json["until"]) == 4 and request_json["until"].isdigit else "3000"
    article_type = "%" if request_json["type"] == "all" else request_json["type"]
    direction = desc if sort_order == 'desc' else asc

    title_list = title.split()
    search_term_list = search_term.split()
    author_list = author.split()
    content_list = request_json["content"]

    #ILIKE is similar to LIKE in all aspects except in one thing: it performs a case in-sensitive matching
    #Unidecode removes accent from the search string whereas unaccent removes accents from the database. The unaccent Extension has to be installed for postgresql
    title_filter = [unaccent(Article.title).ilike(f'%{unidecode(term)}%') for term in title_list]
    search_filter = [unaccent(Article.searchIndex).ilike(f'%{unidecode(term)}%') for term in search_term_list]
    author_filter = [unaccent(Article.author).ilike(f'%{unidecode(term)}%') for term in author_list]
    # time start is used as a filter, otherwise articles without a year are not selected, even if no year is specified
    timestart_filter = [Article.year >= timestart] if timestart != None else []
    until_filter = [Article.year <= until]
    # Filter by Article.icon because unlike Artikcle.ENTRYTYPE, Article.icon groups books and bookchapters together
    filter_type = [~Article.icon.like("book"), ~Article.icon.like("article")] if article_type == "other" else [Article.icon.like(article_type)]
    
    filters = title_filter + search_filter + author_filter + timestart_filter + filter_type + until_filter
    
    content_filter = [Wordstat.word == f"{unidecode(term)}" for term in content_list]
    
    # How to order the results
    orderby = direction(getattr(Article, sortby))
    
    # Desired columns
    columns = [Article.icon, Article.authorlast, Article.year, Article.title, Article.publication, Article.url, Article.abstract]            
    
    
    if len(content_list) == 0 and bibfile:
        requested_articles = db.session.query(Article).\
            filter(*filters).order_by(orderby)
    elif len(content_list) == 0:
        requested_articles = db.session.query(*columns).\
            filter(*filters).order_by(orderby)
    elif bibfile:    
        stmt = db.session.query(Wordstat.article_ref_id, func.sum(Wordstat.count).label("wordcount"), func.array_agg(Wordstat.quote).label("quotes")).\
            filter(or_(*content_filter)).group_by(Wordstat.article_ref_id).having(func.count('*') == len(content_list)).subquery()
        
        requested_articles = db.session.query(Article).\
            join(stmt, Article.dbid == stmt.c.article_ref_id).\
                filter(*filters).order_by(orderby)
    else:
        stmt = db.session.query(Wordstat.article_ref_id, func.sum(Wordstat.count).label("wordcount"), func.array_agg(Wordstat.quote).label("quotes")).\
            filter(or_(*content_filter)).group_by(Wordstat.article_ref_id).having(func.count('*') == len(content_list)).subquery()
        
        requested_articles = db.session.query(*columns, stmt.c.wordcount, stmt.c.quotes).\
            join(stmt, Article.dbid == stmt.c.article_ref_id).\
                filter(*filters).order_by(orderby)
                
    return requested_articles