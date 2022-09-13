from flask import request, jsonify, render_template, redirect, url_for, Markup, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.sql.expression import asc, desc, or_, and_
from sqlalchemy.sql import func
from sqlalchemy.sql.functions import ReturnTypeFromArgs
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser
from bibfilter.models import Article, BibliographySchema
from bibfilter import app, basic_auth, db
from update_library import updateDatabase
from datetime import datetime
import os
from unidecode import unidecode
from dotenv import load_dotenv
from flask_table import Table, Col, OptCol
import time
from elasticsearch import Elasticsearch
from bibfilter.elasticsearchfunctions import elasticsearchCheck, getElasticClient, createElasticsearchIndex
from pprint import pprint
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q
from multiprocessing import Process, Queue
import io

load_dotenv()

# Rate limiting Setup
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100/minute"]
)

# Do you want to show quotes of the  Articles in the results (TRUE or FALSE)
showSearchQuotes = os.environ.get("SHOW_SEARCH_QUOTES").upper() == "TRUE"

if showSearchQuotes:
    try:
        quoteSize = int(os.environ.get("SEARCH_QUOTE_SIZE"))
        if quoteSize > 1200:
            quoteSize = 1200
    except:
        quoteSize = 300
else:
    print("SHOW_SEATCH_QUOTES not set or set to FALSE")

# Link where Literature suggestions can be submitted
suggestLink = os.environ["SUGGEST_LITERATURE_URL"]

# Connect to elasticSearch if it's suppoed to be used
useElasticSearch = elasticsearchCheck()
if useElasticSearch:
    es = getElasticClient()

######################################## ADMIN #####################

## Get Date of last sync between zotero and database
def zotero_last_sync_date():
    max_value = db.session.query(func.max(Article.date_last_zotero_sync)).scalar()

    # If the database is empty
    if max_value == None:
        max_value = ""    
    return max_value

p1 = Process(target=updateDatabase)

## Admin API: Clear the database
@app.route("/clearDB", methods=["GET"])
@limiter.limit("5/day")
@basic_auth.required
def clearDB():
    global p1
    print("/clearDB, Delete Database and elasticsearch index")
    # Stop manual resyncDB if it is  currently running
    if p1.is_alive():
        print("Terminate manual resyncDB Process")
        p1.terminate()
        p1.join()
    engine = db.engine
    Article.__table__.drop(engine)
    db.create_all()
    print("Created database")
    if useElasticSearch:
        es.indices.delete(index='bibfilter-index', ignore=[400, 404])
        createElasticsearchIndex()
    
    return redirect("/admin")

## Admin API: Sync the database
@app.route("/resyncDB", methods=["GET"])
@limiter.limit("20/hour")
@basic_auth.required
def resyncDB():
    print("/resyncDB, running updateDatabase() in background")
    global p1
    
    # Stop manual resyncDB if it is  currently running
    if p1.is_alive():
        print("Terminate manual resyncDB Process")
        p1.terminate()
        p1.join()
    p1 = Process(target=updateDatabase)
    p1.start()
    return redirect("/admin")

## Return admin page
@app.route("/admin", methods=["GET"])
@basic_auth.required
def admin():
    arguments = request.args
    table, args, args_get_str, numResults, suggestLink = createTable(arguments)
    lastSync = zotero_last_sync_date()
    return render_template("admin.html", table=table, args=args, getStr=args_get_str, numResults=numResults, suggestLink=suggestLink, lastSync=lastSync)

######################################### ADMIN END ########################

def cleanArguments(arguments):
    args = {"title":"", "author":"", "timestart":"", "until":"", "type":"all", "sort":"author", "direction":"asc", "search":""}
    args.update(arguments)
    args["reverse"] = True if args["direction"] == "desc" else False
    return args

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

# Class needed to ignore accents when using SQL. Not that the unaccent extension needs to be installed in postgreSQL
class unaccent(ReturnTypeFromArgs):
    pass

# Function to Select the correct articles from SQL based on the selection done by the user in the frontent
def selectEntries(searchDict, bibfile=False):
    """ 
    Example DICT:
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
    
    timestart = searchDict["timestart"] if len(searchDict["timestart"]) == 4 and searchDict["timestart"].isdigit else None
    until = searchDict["until"] if len(searchDict["until"]) == 4 and searchDict["until"].isdigit else "3000"
    article_type = "%" if searchDict["type"] == "all" else searchDict["type"]
    direction = desc if searchDict["direction"] == 'desc' else asc

    title_list = searchDict["title"].split()
    search_term_list = searchDict["search"].split()
    author_list = searchDict["author"].split()

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
    
    # How to order the results
    orderby = direction(getattr(Article, searchDict["sort"]))
    
    # Desired columns
    columns = [Article.icon, Article.authorlast, Article.year, Article.title, Article.publication, Article.url, Article.abstract]            
    
    ## Return all columns when exporting as bibfile, otherwise only return columns needed for the table
    if bibfile:
        requested_articles = db.session.query(Article).\
            filter(*filters).order_by(orderby)
    else:
        requested_articles = db.session.query(*columns).\
            filter(*filters).order_by(orderby)
                
    return requested_articles

class ItemTable(Table):
    def __init__(self, args, **kwargs):
        ## First get __init__ from parent class Table, then extend it
        self.args = args
        super().__init__(**kwargs)
        
    icons = {"book": f'<img src="/static/img/book.png" class="typeicon">', "article":f'<img src="/static/img/article.png" class="typeicon">', "other":f'<img src="/static/img/other.png" class="typeicon">'}
    
    no_items = "No literature was found"
    table_id = "literature"
    
    icon = OptCol(' ', choices=icons, default_key="other", column_html_attrs={"class":"colIcon"})
    authorlast = Col('Author', column_html_attrs={"class":"colAuthor"})
    year = Col('Year', column_html_attrs={"class":"colYear"})
    
    title = Col('Title', column_html_attrs={"class":"colTitle"})
    publication = Col('Publication', column_html_attrs={"class":"colPublication"})
    url = Col('URL', column_html_attrs={"class":"tableUrl colUrl"})
    abstract = Col('hidden', column_html_attrs={"class":"hiddenRowContent"})
    
    allow_sort = True

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction =  'desc'
        else:
            direction = 'asc'
        return url_for('main', sort=col_key, direction=direction, search=self.args["search"], title=self.args["title"], author=self.args["author"], timestart=self.args["timestart"], until=self.args["until"], type=self.args["type"])
    
    def get_tr_attrs(self, item):
        if item["abstract"] != "":
            return {'class': 'clickable'}
        else:
            return {}

def createTable(arguments, bibfile=False):
    args = cleanArguments(arguments)
    args_get_str = argsToStr(arguments)
    
    # Query items from database
    begin = time.time()
    
    # Use elasticsearch if enabled via environment variable
    if useElasticSearch:
        s = Search(using=es, index='bibfilter-index')
        if args["search"].strip() != "":
            q = Q("multi_match", type="phrase", slop=400, query=args["search"], fields=['title', 'author', "abstract", "articleFullText"], minimum_should_match="80%")
            s = s.query(q)
        if args["title"].strip() != "":
            s = s.query("match", title=args["title"])
        if args["author"].strip() != "":
            s = s.query("match", author=args["author"])
        if args["timestart"].strip() != "":
            s = s.query('range', **{'year': {'gte': int(args["timestart"].strip())}})
        if args["until"].strip() != "":
            s = s.query('range', **{'year': {'lte': int(args["until"].strip())}})
            
        arType = args["type"].strip()
        if arType == "other":
            s = s.exclude("match", icon="article")
            s = s.exclude("match", icon="book")
        elif arType == "article" or arType == "book":
            q = Q("match", icon=arType)
            s = s.query(q)
        
        s = s.highlight('abstract', number_of_fragments=0, pre_tags=["<mark>"], post_tags=["</mark>"])
        if showSearchQuotes:
            s = s.highlight("articleFullText", type="fvh", fragment_size=quoteSize, boundary_scanner="word", pre_tags=["<mark>"], post_tags=["</mark>"])
        
        # , max_analyzed_offset=1000000
        s = s.highlight_options(boundary_scanner="sentence", encoder="html", order="score", boundary_chars="\n")
            
        # Obtain number of results
        totalRes = s.count()
        # Specify to return ALL results and not only the first 10 (default)
        s = s[:totalRes]
        
        # Sort the results. If no attribute is specified, it is sorting by search score
        if arguments.get("sort") != None:
            order = arguments.get("sort")
            if order != "year":
                order += ".keyword"
            s = s.sort({order:{"order": args.get("direction")}})
        
        response = s.execute()
        
        if bibfile:
            return response
        
        items = []
        for each in response:
            item = {}
            
            cols = ["icon", "year", "authorlast", "title", "publication",]
            for col in cols:
                item[col] = each[col]
            
            if each["url"] != "":
                item["url"] = Markup(f'<a class="externalUrl" target="_blank" href="{each["url"]}">Source</a>')
            else:
                item["url"] = ""
            try:
                if hasattr(each.meta, 'highlight'):
                    if "abstract" in each.meta.highlight:
                        abstract = "".join(each.meta.highlight.abstract)
                    else:
                        abstract = each["abstract"]
                    if "articleFullText" in each.meta.highlight:
                        highlights = "<b>Text results</b><br>"+" (...)<br><br>".join(each.meta.highlight.articleFullText)
                    else:
                        highlights = ""
                else:
                    abstract = each["abstract"]
                    highlights = ""
                
                if abstract != "":
                    abstract = f"<b>Abstract</b><br>{abstract}<br><br>"
                if not (highlights == "" and abstract == ""):
                    item["abstract"] = Markup("<div class='hidden_content'>" + abstract + highlights +"</div>")
                else:
                    item["abstract"] = ""
                    
            except Exception as e:
                print(e)
                print("Error. No highlight available")
                item["abstract"] = Markup("<div class='hidden_content'> <b>Abstract</b><br></div>")
                
            items.append(item)
        
        table = ItemTable(args=args, items=items, sort_by=args["sort"], sort_reverse=args["reverse"])
        
        numResults = len(response)
        
        end = time.time()
        print(f"Finished loading in {end - begin:.4f} seconds\n")
        return table, args, args_get_str, numResults, suggestLink
    
    else:
        if bibfile:
            requested_articles = selectEntries(args, bibfile=True)
            return requested_articles
        else:
            requested_articles = selectEntries(args)
        
        items = []
    
        for ki, item in enumerate(requested_articles):
            item = dict(item)
                
            if item["url"] != "":
                item["url"] = Markup(f'<a class="externalUrl" target="_blank" href="{item["url"]}">Source</a>')
            
            if item["abstract"] == "":
                hiddentext = ""
            else:
                item["abstract"] = Markup(f'<div class="hidden_content"><b>Abstract</b><br>{item["abstract"]}</b><br></div>')
            
            if "wordcount" not in item:
                item["wordcount"] = 0
            items.append(item)
        
        # args need to be passed so the filter isn't reset when sorting
        table = ItemTable(args=args, items=items, sort_by=args["sort"], sort_reverse=args["reverse"])
        
        numResults = len(items)
        
        end = time.time()
        print(f"Finished loading in {end - begin:.4f} seconds\n")
        return table, args, args_get_str, numResults, suggestLink

# Declare bibliography schma as defined in models.py
bibliography_schema = BibliographySchema(many=True)

## API: return .bib as string
@app.route("/bibfile", methods=["GET"])
@limiter.limit("10/minute")
def get_bibfile():
    arguments = request.args
    articles = createTable(arguments, bibfile=True)
    # Clean up results to only contain needed attributes for bibfile and deleted missing fields
    articles = bibliography_schema.dump(articles)

    dbib = BibDatabase()
    dbib.entries = articles
    bibtex_str = bibtexparser.dumps(dbib)
    string_out = io.BytesIO(bytes(bibtex_str, 'utf-8'))
    return send_file(string_out, mimetype="text/plain", download_name="results.bib", as_attachment=True)

# Redirect to main page if you land at index
@app.route("/index", methods=["GET"])
def index():
    return redirect("/")

## Frontend: Return our frontend
@app.route("/", methods=["GET"])
@limiter.exempt
def main():
    arguments = request.args
    table, args, args_get_str, numResults, suggestLink = createTable(arguments)
    return render_template("main.html", table=table, args=args, getStr=args_get_str, numResults=numResults, suggestLink=suggestLink)