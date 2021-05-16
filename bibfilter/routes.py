from flask import request, jsonify, render_template, redirect, url_for, Markup
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.sql.expression import asc, desc, or_, and_
from sqlalchemy.sql import func
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser
from bibfilter.models import Article, ArticleSchema, BibliographySchema, TableSchema
from bibfilter import app, basic_auth, db
from update_library import update_from_zotero
from datetime import datetime
import os
from sqlalchemy.sql.functions import ReturnTypeFromArgs
from unidecode import unidecode
from dotenv import load_dotenv
import threading
from textblob import TextBlob as tb

import json
from flask_table import Table, Col, OptCol

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
table_schema = TableSchema(many=True)
bibliography_schema = BibliographySchema(many=True)

## API: return .bib as string
@app.route("/bibfile", methods=["POST"])
def get_bibfile():
    req_data = request.get_json()
    entries = selectEntries(req_data)
    result = bibliography_schema.dump(entries)

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

@app.route("/lemma", methods=["POST"])
@limiter.exempt
def get_lemma():
    req_data = request.get_json()
    content = req_data["content"]
    # Lemmatize words
    terms = [token.lemmatize().lower() for token in tb(content).tokens]
    
    result = {"terms":terms}
    return jsonify(result)


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

## Frontend: Return our frontend table
@app.route("/table", methods=["GET"])
@limiter.exempt
def table():
    arguments = request.args
    base_url = "http://127.0.0.1:5000"
    icons = {"book": f'<img src="{base_url}/static/img/book.png" class="typeicon">', "article":f'<img src="{base_url}/static/img/article.png" class="typeicon">', "other":f'<img src="{base_url}/static/img/other.png" class="typeicon">'}
    
    class ItemTable(Table):
        def __init__(self, args, **kwargs):
            ## First get __init__ from parent class Table, then extend it
            self.args = args
            super().__init__(**kwargs)
        
        no_items = "No literature was found"
        table_id = "literature"
        
        icon = OptCol(' ', choices=icons, default_key="other")
        authorlast = Col('Author')
        year = Col('Year')
        title = Col('Title')
        publication = Col('Publication')
        url = Col('URL', column_html_attrs={"class":"tableUrl"})
        importantWordsCount = Col('Occur')
        abstract = Col('hidden', column_html_attrs={"class":"hiddenRowContent"})
        
        allow_sort = True

        def sort_url(self, col_key, reverse=False):
            if reverse:
                direction =  'desc'
            else:
                direction = 'asc'
            return url_for('table', sort=col_key, direction=direction, search=self.args["search"], title=self.args["title"], content=self.args["content"], author=self.args["author"], timestart=self.args["timestart"], until=self.args["until"], type=self.args["type"])
        
        def get_tr_attrs(self, item):
            if item["abstract"] != "":
                return {'class': 'clickable'}
            else:
                return {}

    
    args = {"title":"", "author":"", "timestart":"", "until":"", "type":"all", "sort":"author", "direction":"asc", "content":"", "search":""}
    
    # Prioritize sorting on importantWordsCount if no manual sorting is in place
    if arguments.get("content") != None:
        args["sort"] = "importantWordsCount"
        
    args.update(arguments)
    
    # Lemmatize Content search words
    args["content"] = " ".join([token.lemmatize() for token in tb(args["content"]).tokens])
    
    # Query items from database
    requested_articles = selectEntries(args)
    items = table_schema.dump(requested_articles)
    
    # Select the count of only the words that have been searched for
    for item in items:
        contentSearchList = args["content"].lower().split()
        if args["content"] != "":
            # Todo take all words into account
            searchword = contentSearchList[0]
            item["importantWordsCount"] =  json.loads(item["importantWordsCount"])[searchword]
        else:
            item["importantWordsCount"] = ""
            
        if item["url"] != "":
            item["url"] = Markup(f'<a class="externalUrl" target="_blank" href="{item["url"]}">Source</a>')
        
        def formatQuotes():
            finalQuotes = ""
            quoteList = json.loads(item["importantWordsLocation"])
            count = 0
            for i in range(5):
                for word in contentSearchList:
                    try:
                        if finalQuotes == "":
                            finalQuotes = quoteList[word][i]
                        else:
                            finalQuotes += "<p>" + quoteList[word][i] + "</p>"
                        count += 1
                    except Exception as e:
                        pass
                    if count == 4:
                        return finalQuotes
        
        # Check whether environment variable is set to show search quotes            
        formattedAbstract = f'<b>Abstract</b><br>{item["abstract"]}<br><br>' if item["abstract"] != "" else ""         
        if args["content"] != "" and os.environ.get("showSearchQuotes") == "Yes":
            finalQuotes = formatQuotes()
            
            hiddentext = Markup(f'<div class="hidden_content">{formattedAbstract}<b>Search</b><br>{finalQuotes}</div>')
        else:
            if item["abstract"] != "":
                hiddentext = Markup(f'<div class="hidden_content">{formattedAbstract}</div>')
            else:
                hiddentext = ""
        item["abstract"] = hiddentext
        
    
    # Sort by importantWordsCount if the argument is passed
    if args["sort"] == "importantWordsCount":
        newlist = sorted(items, reverse=True, key=lambda k: k['importantWordsCount']) 
        items = newlist
    
    sort = args["sort"]
    reverse = True if args["direction"] == "desc" else False
    # args need to be passed so the filter isn't reset when sorting
    table = ItemTable(args=args, items=items, sort_by=sort, sort_reverse=reverse)
    
    numResults = len(items)

    return render_template("table.html", table=table, args=arguments, numResults=numResults)

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
        "sort_order":    "asc"
    }
    """

    search_term = request_json["search"]
    title =  request_json["title"]
    author = request_json["author"]
    content = request_json["content"]
    
    sortby = request_json["sort"]
    sort_order = request_json["direction"]
    timestart = request_json["timestart"] if len(request_json["timestart"]) == 4 and request_json["timestart"].isdigit else "0"
    until = request_json["until"] if len(request_json["until"]) == 4 and request_json["until"].isdigit else "3000"
    article_type = "%" if request_json["type"] == "all" else request_json["type"]
    direction = desc if sort_order == 'desc' else asc

    title_list = title.split()
    search_term_list = search_term.split()
    author_list = author.split()
    content_list = content.split()

    #ILIKE is similar to LIKE in all aspects except in one thing: it performs a case in-sensitive matching
    #Unidecode removes accent from the search string whereas unaccent removes accents from the database. The unaccent Extension has to be installed for postgresql
    title_filter = [unaccent(Article.title).ilike(f'%{unidecode(term)}%') for term in title_list]
    search_filter = [unaccent(Article.searchIndex).ilike(f'%{unidecode(term)}%') for term in search_term_list]
    author_filter = [unaccent(Article.author).ilike(f'%{unidecode(term)}%') for term in author_list]
    content_filter = [unaccent(Article.importantWords).ilike(f'% {unidecode(term)} %') for term in content_list]
    
    # Filter by Article.icon because unlike Artikcle.ENTRYTYPE, Article.icon groups books and bookchapters together
    filter_type = [~Article.icon.like("book"), ~Article.icon.like("article")] if article_type == "other" else [Article.icon.like(article_type)]

    if timestart != "None" or until != "None":
        requested_articles = db.session.query(Article).\
            filter(and_(*title_filter), or_(*author_filter), and_(*content_filter),\
                and_(Article.year >= timestart, Article.year <= until),\
                and_(*filter_type), and_(*search_filter)).\
                order_by(direction(getattr(Article, sortby)))
    else:
        requested_articles = db.session.query(Article).\
            filter(and_(*title_filter), or_(*author_filter), and_(*content_filter),\
                and_(*filter_type), and_(*search_filter)).\
                order_by(direction(getattr(Article, sortby)))

    return requested_articles