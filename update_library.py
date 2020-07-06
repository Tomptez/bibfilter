import sys
sys.path.append(".")
import os
import datetime
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bibfilter import db
from bibfilter.models import Article
from pyzotero import zotero
from pprint import pprint
import time

def update_from_zotero():
    session = db.session()
    #Create the database
    db.create_all()
    session.close()

    libraryID = os.environ["libraryID"]
    collectionID = os.environ["collectionID"]

    zot = zotero.Zotero(libraryID, "group")
    items = zot.collection_items_top(collectionID, limit=50)
    size = zot.num_collectionitems(collectionID)
    new, existed = 0, 0
    for num in range(size):

        for item in items:

            added = add_item(item)
            if added:
                new += 1
            else:
                existed += 1
        
        try:
            items = zot.follow()
        except Exception:
            print("Got all items")
            break

    session = db.session()
    total = len(list(session.query(Article)))
    session.close()
    print(f"Added {new} new articles.\n {existed} articles existed already.\n\nTotal Articles: {total}")



def add_item(item):
    # Create the session
    session = db.session()
    data = item["data"]

    req = session.query(Article).filter(Article.ID == data["key"])
    
    Checks if Article already exists
    if len(list(req)) > 0:
        req.date_last_zotero_sync = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        session.commit()
        session.close()
        return False

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
    
    # Get authornames
    author, authorlast = "", ""
    for dic in data["creators"]:
        try:
            if len(authorlast) > 0:
                authorlast += "; " + data["creators"][0]["lastName"]
            else:
                authorlast = data["creators"][0]["lastName"]

            if len(author) > 0:
                author += "; " + data["creators"][0]["lastName"] + ", " + data["creators"][0]["firstName"]
            else:
                authorlast = data["creators"][0]["lastName"] + ", " + data["creators"][0]["firstName"]
        except Exception as e:
            pass
    

    date_str = date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Create new Database entry with all the attributes
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
                        date_last_zotero_sync = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        date_added = content["dateAdded"],
                        date_modified = content["dateModified"],
                        date_modified_pretty = content["dateModified"].split("T")[0] + " " + content["dateModified"].split("T")[1][:-4],
                        date_added_pretty = content["dateAdded"].split("T")[0] + " " + content["dateAdded"].split("T")[1][:-4],
                        _date_created_str = date_str,
                        _date_created = date_str)
    session.add(new_art)
    session.commit()
    session.close()

    return True

if __name__ == "__main__":
    update_from_zotero()