# This script is responsible to sync the database to zotero
# It is automatically started by dokku via the Procfile
# It regularly cheks the Zotero database for changes
# and also triggers analyzeArticles() from synchronize_pdf_contents to scrape PDF contents

import sys
sys.path.append(".")
import os
import datetime
import time
import schedule
from pytz import timezone
from pyzotero import zotero
from bibfilter import app, db
from bibfilter.models import Article
from bibfilter.elasticsearchfunctions import elasticsearchCheck, getElasticClient
from synchronize_pdf_content import analyzeArticles
from multiprocessing import Process, Queue
from sqlalchemy.sql import func

# List to store key of all items in zotero to later check if some of the items in the database have been deleted in zotero
zotero_keylist = []

# Count new and updated articles for finish report
report = {"new" : 0, "updated" : 0, "existed" : 0, "deleted": 0}

# Retrieve the environment variables regarding zotero
libraryID = os.environ["LIBRARY_ID"]
APIkey = os.environ["APIkey"]

try:
    collectionID = os.environ["COLLECTION_ID"]
except:
    collectionID = None

def deleteOld():
    """
    Deletes all articles from the database which don't exist in the current zotero library

    :returns: True
    """
    global report
    useElasticSearch = elasticsearchCheck()

    # Convert zotero keys from list to tuple to make iteration faster
    zoteroKeys = tuple(zotero_keylist)

    with app.app_context():
        session = db.session()

        # Select all entries in the database
        request = session.query(Article)

        # Delete each item from the database which isn't in the zotero database
        count = 0
        for entry in request:
            if entry.ID not in zoteroKeys:
                print(f"delete {entry.title}")
                ## If article was indexed by elasticsearch but elasticsearch server is down, do nothing
                if entry.elasticIndexed and not useElasticSearch:
                    print(f"Couldn't connect to elasitcsearch. Therefore didn't delete {entry.title}")
                    break
                # If indexed by Elasticsearch delete from elasticsearch
                elif entry.elasticIndexed and useElasticSearch:
                    es = getElasticClient()
                    es.delete(index='bibfilter-index', id=entry.ID, refresh=True)

                session.delete(entry)
                session.commit()
                count +=1

        session.close()

    report["deleted"] = count
    return True

def formatArticleData(item):
    """
    String formatting of zotero item data

    :param data: pyzotero API item
    :returns: Dictionary of formatted data
    """
    data = item["data"]
    content = {"title": "","url":"", "key":"" ,"itemType":"", "DOI": "", "ISSN":"", "publicationTitle":"","journalAbbreviation":"","abstractNote":"","pages":"","language":"","volume":"","issue":"","dateAdded":"","dateModified":"","ISBN":"", "numPages":"", "author": "", "authorlast": "", "itemYear": ""}
    
    # Get Article attributes and make sure to skip KeyError (not all entrytype e.g. journal book etc. have the same attributes)
    for key in content:
        try:
            content[key] = data[key]
        except KeyError:
            pass

    # Get year        
    try:
        content["itemYear"] = item["meta"]["parsedDate"].split("-")[0]
    except KeyError:
        pass
    
    # Get author names
    author, authorlast = "", ""
    try:
        for dic in data["creators"]:
            try:
                # Entriers without firstName use "name", otherwise firstName and lastName
                if "name" in dic:
                    if len(authorlast) > 0:
                        authorlast += "; " + dic["name"]
                    else:
                        authorlast = dic["name"]
                    if len(author) > 0:
                        author += "; " + dic["name"]
                    else:
                        author = dic["name"]

                else:
                    if len(authorlast) > 0:
                        authorlast += "; " + dic["lastName"]
                    else:
                        authorlast = dic["lastName"]

                    if len(author) > 0:
                        author += "; " + dic["lastName"] + ", " + dic["firstName"]
                    else:
                        author = dic["lastName"] + ", " + dic["firstName"]
            except Exception as e:
                pass
        content["author"] = author
        content["authorlast"] = authorlast
    except Exception as e:
        print("data has no ḱey 'creator'. Entry may be only file without metadata. Skipping")
        raise
    return content

def checkItem(item):
    """
    Adds an zotero Item to DB if it didn't exist before, updates it if it has changed or does nothing if it exists an hasn't changed

    :param item: Item of a zotero library given by pyzotero API
    :returns: (1,0,0) when adding new item, (0,1,0) when updating, (0,0,1) when item existed
    """
    global zotero_keylist
    global report

    useElasticSearch = elasticsearchCheck()
    
    # Create the session in app context
    with app.app_context():
        session = db.session()
        data = item["data"]

        ## Adding each key the keylist which is needed by deleteOld()
        zotero_keylist.append(data["key"])

        req = session.query(Article).filter(Article.ID == data["key"])
        reqlen = req.count()
        # If article exists and hasn't been modified, update last sync date and return
        # Get date. If timezone environment variable exists, use it
        try:
            zone = os.environ["TIMEZONE"]
            date_str = datetime.datetime.now(timezone(zone)).strftime("%Y-%m-%d %H:%M")
        except:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        if reqlen > 0 and req[0].date_modified == data["dateModified"]:
            req[0].date_last_zotero_sync = date_str
            session.commit()
            session.close()
            report["existed"] += 1
            return False
        # If the item existed but has been modified delete it now and continue to add it again
        elif reqlen > 0 and req[0].date_modified != data["dateModified"]:
            if req[0].elasticIndexed and useElasticSearch:
                es = getElasticClient()
                es.delete(index='bibfilter-index', id=req[0].ID, refresh=True)
            session.delete(req[0])
            session.commit()
            report["updated"] += 1
        else:
            report["new"] += 1
    
        try:
            content = formatArticleData(item)
        except:
            return False

        csv_bib_pattern = {"journalArticle": "article", "book": "book", "conferencePaper": "inproceedings", "manuscript": "article", "bookSection": "incollection", "webpage": "inproceedings", "techreport": "article", "letter": "misc", "report": "report", "document": "misc", "thesis": "thesis"}

        # Create a new Database entry with all the attributes
        new_art = Article(title = content["title"],
                            url = content["url"],
                            # publisher=publisher, 
                            ID = content["key"], 
                            ENTRYTYPE = csv_bib_pattern[content["itemType"]],
                            author = content["author"],
                            authorlast = content["authorlast"],
                            year = content["itemYear"],
                            doi = content["DOI"],
                            issn = content["ISSN"],
                            isbn = content["ISBN"],
                            publication = content["publicationTitle"],
                            journal = content["publicationTitle"] if not  content["itemType"].startswith("book") else "",
                            booktitle = content["publicationTitle"] if content["itemType"].startswith("book") else "",
                            journal_abbrev = content["journalAbbreviation"],
                            abstract = content["abstractNote"],
                            pages = content["pages"] if content["pages"] != "" else content["numPages"],
                            language = content["language"],
                            volume = content["volume"], 
                            number = content["issue"],
                            icon = "book" if content["itemType"].startswith("book") else csv_bib_pattern[content["itemType"]], 
                            articleFullText = "",
                            references = "",
                            searchIndex = " ".join([content["title"], content["author"], content["publicationTitle"], content["abstractNote"], content["DOI"], content["ISSN"], content["ISBN"]]),
                            date_last_zotero_sync = date_str,
                            date_added = content["dateAdded"],
                            date_modified = content["dateModified"],
                            contentChecked = False,
                            elasticIndexed = False,
                            date_modified_pretty = content["dateModified"].split("T")[0] + " " + content["dateModified"].split("T")[1][:-4],
                            date_added_pretty = content["dateAdded"].split("T")[0] + " " + content["dateAdded"].split("T")[1][:-4])
                            
        
        session.add(new_art)
        session.commit()
        session.close()

    return True

def getZoteroItems(Q):
    """
    Functions that retrieves all items of Zotero library or zotero collection if collectionID env var is set. Results are put into Queue.

    :param Q: Multiprocessing Queue
    :returns: Nothing
    """
    # Connect to the zotero database
    zot = zotero.Zotero(libraryID, "group", api_key = APIkey)
    items = None
    
    try:
        # Retrieve all items in zotero library
        # Uses the COLLECTION_ID if one is provided as environment variable
        if collectionID == None:
            items = zot.everything(zot.top())
        else:
            items = zot.everything(zot.collection_items_top(collectionID))
    except Exception as e:
        print(e)
    finally:    
        Q.put(items)
        return

def synchronizeZoteroDB():
    """
    Synchronizes the postgresQL Database with the zotero library it is supposed to mirror
    """
    print("Started syncing with zotero collection")
    # Make variables alterable inside the function
    global zotero_keylist
    global report

    ## Use multiprocessing to handle zotero server connection timing out
    Q = Queue()
    p1 = Process(target=getZoteroItems, args=(Q,))
    p1.start()
    try:
        items = Q.get(timeout=360)
        if items == None:
            print("Couldn't connect to zotero server, Trying again later.")
            return
        else:
            print(f"Retrieved {len(items)} items from Zotero database")
    except Exception as e:
        print(e)
        print("Connection to Zotero was interrupted. Stop synchronization")
        return
    finally:
        p1.kill()
        p1.join()
        p1.close()

    # Iterate over every single entry
    for item in items:
        checkItem(item)
        
    # Delete all articles which are not in zotero anymore
    deleteOld()
    
    with app.app_context():
        # Count how many items are in the database in total
        session = db.session()
        total = session.query(Article).count()
        session.close()
        
    print("Summary of synchronization with Zotero:")
    print(f"{report['existed']} entries existed already. {report['new']} new entries were added.\n")
    print(f"Updated {report['updated']} entries\nDeleted {report['deleted']} articles.")
    print(f"Total Articles: {total}")
    print("------------------------------------")

    # Reset the counters and the keylist
    report = {"new" : 0, "updated" : 0, "existed" : 0, "deleted": 0}
    zotero_keylist = []
 
def updateDatabase():
    """
    Checks the newest item of the zotero library. If it detects a change in the library, starts synchronization.
    """
    try:
        # Create the database if it doesn't exist
        with app.app_context():
            db.create_all()
        
        # Connect to the zotero database
        zot = zotero.Zotero(libraryID, "group")

        if collectionID == None:
            items = zot.top(limit=1)
        else:
            items = zot.collection_items_top(collectionID, limit=1)

        newestModified = items[0]["data"]["dateModified"]
        
        with app.app_context():
            newestInDB = db.session.query(func.max(Article.date_modified)).scalar()
            syncNeeded = (newestModified != newestInDB) 
            
        if syncNeeded:
            synchronizeZoteroDB()
            analyzeArticles()
        else:
            print("Checked Zotero for new articles: Nothing to update")        
        
    except Exception as e:
        print(e)
        print("Problem: Unable to retrieve dateModified of newest zotero item. Possible reeasons: Zotero server is down, COLLECTION_ID or LIBRARY_ID wrong or library is not accessible through the API")
    
    with app.app_context():
        session = db.session()
        article = session.query(Article).filter(Article.contentChecked == False).first()
        ### Check whether still scraping should take place in case the process was interrupted before
        if article != None:
            print("Run analyzeArticles()")
            analyzeArticles()
        else:
            print("Nothing to analyze. Sleep...")
    return
     
# Sync once with the zotero library, after that, regularly check whether new articles or updated articles are found
if __name__ == "__main__":
    updateDatabase()
    
    schedule.every(10).minutes.do(updateDatabase)
    
    while True:
        schedule.run_pending()
        time.sleep(30)
