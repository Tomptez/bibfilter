import sys
sys.path.append(".")
import os
import datetime
import time
import schedule
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pprint import pprint
from pytz import timezone
from pyzotero import zotero
from bibfilter import db
from bibfilter.models import Article, Wordstat
from Analyze_content_for_search import analyzeArticles

# List to store key of all items in zotero to later check if some of the items in the database have been deleted in zotero
zotero_keylist = []

# Count new and updated articles for finish report
report = {"new" : 0, "updated" : 0, "existed" : 0, "deleted": 0}


def delete_old():
    global report

    # Convert zotero keys from list to tuple to make iteration faster
    zoteroKeys = tuple(zotero_keylist)

    session = db.session()

    # Select all entries in the database
    request = session.query(Article)

    # Delete each item from the database which isn't in the zotero database
    count = 0
    for entry in request:
        if entry.ID not in zoteroKeys:
            print(f"delete {entry.title}")
            session.delete(entry)
            session.commit()
            count +=1

    session.close()

    report["deleted"] = count
    return True

def delete_old_words():
    session = db.session()
    countwords = session.query(Wordstat).filter(Wordstat.article_ref_id == None).count()
    print(f"Delete {countwords} content_words for filtering that belonged to old or updated articles")
    session.query(Wordstat).filter(Wordstat.article_ref_id == None).delete(synchronize_session=False)
    session.commit()
    session.close()

def check_item(item):
    global zotero_keylist
    global report

    # Create the session
    session = db.session()
    data = item["data"]

    ## Adding each key the keylist which is needed by delete_old()
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
        dbid = req[0].dbid
        session.delete(req[0])
        session.commit()
        report["updated"] += 1

    else:
        report["new"] += 1

    csv_bib_pattern = {"journalArticle": "article", "book": "book", "conferencePaper": "inproceedings", "manuscript": "article", "bookSection": "incollection", "webpage": "inproceedings", "techreport": "article", "letter": "misc", "report": "report", "document": "misc", "thesis": "thesis"}

    content = {"title": "","url":"", "key":"" ,"itemType":"", "DOI": "", "ISSN":"", "publicationTitle":"","journalAbbreviation":"","abstractNote":"","pages":"","language":"","volume":"","issue":"","dateAdded":"","dateModified":"","ISBN":"", "numPages":""}
    
    # Get Article attributes and make sure to skip KeyError (not all entrytype e.g. journal book etc. have the same attributes)
    for key in content:
        k = False
        try:
            content[key] = data[key]
        except Exception as e:
            pass

    # Get year        
    try:
        itemYear = item["meta"]["parsedDate"].split("-")[0]
    except Exception as e:
        itemYear = ""
    
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
    except Exception as e:
        print("data has no ḱey 'creator'. Entry may be only file without metadata. Skipping")
        return False

    # Create a new Database entry with all the attributes
    new_art = Article(title=content["title"], 
                        url=content["url"], 
                        # publisher=publisher, 
                        ID=content["key"], 
                        ENTRYTYPE=csv_bib_pattern[content["itemType"]],
                        author=author,
                        authorlast=authorlast, 
                        year=itemYear, 
                        doi=content["DOI"],
                        issn = content["ISSN"],
                        isbn = content["ISBN"],
                        publication=content["publicationTitle"],
                        journal=content["publicationTitle"] if not  content["itemType"].startswith("book") else "",
                        booktitle=content["publicationTitle"] if content["itemType"].startswith("book") else "",
                        journal_abbrev = content["journalAbbreviation"],
                        abstract = content["abstractNote"],
                        pages = content["pages"] if content["pages"] != "" else content["numPages"],
                        language = content["language"],
                        volume=content["volume"], 
                        number=content["issue"], 
                        icon="book" if content["itemType"].startswith("book") else csv_bib_pattern[content["itemType"]], 
                        articleFullText = "",
                        references = "",
                        importantWords = "",
                        searchIndex = " ".join([content["title"], author, content["publicationTitle"], content["abstractNote"], content["DOI"], content["ISSN"], content["ISBN"]]),
                        date_last_zotero_sync = date_str,
                        date_added = content["dateAdded"],
                        date_modified = content["dateModified"],
                        contentChecked = False,
                        date_modified_pretty = content["dateModified"].split("T")[0] + " " + content["dateModified"].split("T")[1][:-4],
                        date_added_pretty = content["dateAdded"].split("T")[0] + " " + content["dateAdded"].split("T")[1][:-4],
                        _date_created_str = date_str,
                        _date_created = date_str)
    
    session.add(new_art)
    session.commit()
    session.close()

    return True

def update_from_zotero():
    print("Started syncing with zotero collection")
    # Make variables alterable inside the function
    global zotero_keylist
    global report

    session = db.session()
    # Create the database
    db.create_all()
    session.close()

    # Retrieve the environment variables
    libraryID = os.environ["LIBRARY_ID"]
    
    try:
        collectionID = os.environ["COLLECTION_ID"]
    except:
        collectionID = None

    # Connect to the database
    zot = zotero.Zotero(libraryID, "group")
    
    # Retrieve the zotero items 50 at a time and get the number of items
    # Uses the COLLECTION_ID if one is provided as environment variable
    if collectionID == None:
        items = zot.top(limit=50)
        size = zot.num_items()
    else:
        items = zot.collection_items_top(collectionID, limit=50)
        size = zot.num_collectionitems(collectionID)

    # Iterate over every single entry
    for num in range(size):

        for item in items:

            # check_item return (1,0,0) when adding new item, (0,1,0) when updating, (0,0,1) when item existed
            check_item(item)
        
        # Get next set of entries
        try:
            items = zot.follow()
        # Stop when there are no items left
        except Exception:
            break

    # Delete all articles which are not in zotero anymore
    delete_old()
    
    # Delete all words that belonged to deleted or modified entries
    delete_old_words()

    # Count how many items are in the database in total
    session = db.session()
    total = session.query(Article).count()
    session.close()
    print("------------------------------------")
    print("Summary of synchronization with Zotero:")
    print(f"Added {report['new']} new entries.\n{report['existed']} entries existed already.")
    print(f"Updated {report['updated']} entries\nDeleted {report['deleted']} articles.\n\nTotal Articles: {total}")

    # Reset the counters and the keylist
    report = {"new" : 0, "updated" : 0, "existed" : 0, "deleted": 0}
    zotero_keylist = []
    
    

# Sync once with the zotero library, after that sync ever hour
if __name__ == "__main__":
    update_from_zotero()
    analyzeArticles()
    
    schedule.every(1).hours.do(update_from_zotero)
    schedule.every(2).hours.do(analyzeArticles)
    
    while True:
        schedule.run_pending()
        time.sleep(60)