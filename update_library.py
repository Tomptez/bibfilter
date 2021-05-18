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
from pytz import timezone
import time
import schedule
from io import BytesIO
from pdfminer.high_level import extract_text
import re

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

def readAttachedPDF(articleID, title):
    
    def faceProblem(message):
        print(title)
        print(message+"\n")
        return ""
    
    try:
        libraryID = os.environ["LIBRARY_ID"]
        zot = zotero.Zotero(libraryID, "group")
        attachments = zot.children(articleID)

        content = ""
        references = ""
        
        # Goes through each attachment if there is any
        for each in attachments:
            try:
                # Notes are different from attachments and don't have contentType attribute
                if each["data"]["itemType"] == "attachment":
                    if each["data"]["contentType"] == 'application/pdf':
                        pdfID = each["data"]["key"]
                        
                        # get content of pdf
                        pdfBytes = zot.file(pdfID)
                        # convert bytes of bts to python object
                        pdfFile = BytesIO(pdfBytes)
                        content = extract_text(pdfFile)
                        
                        # Check length of content
                        if len(content) < 4000:
                            content = faceProblem("Problem: extracted content shorter than expected, aborted extraction")
                            break
                        
                        # Fix: ValueError: A string literal cannot contain NUL (0x00) characters. Caused by a problem with extract_text
                        content = content.replace("\x00", "")
                        
                        # Use end variable to look only after the dirst third of the document. Prevents mistakes in the rare cases that References is only mentioned on the first page
                        end = int(len(content) / 3.5)
                        
                        # Find the position of references to then only index text before the references. \W means any non-word character
                        iterString = 'REFERENCES|References|[\W|\n][R|r][E|e][F|f][E|e][R|r][E|e][N|n][C|c][E|e][S|s]|[\W|\n][R|r] [E|e] [F|f] [E|e] [R|r] [E|e] [N|n] [C|c] [E|e] [S|s]|[B|b][I|i][B|b][L|l][I|i][O|o][G|g][R|r][A|a][P|p][H|h][Y|y]'
                        
                        # Cover cases where there is tons of \n newlines in the scanned code:
                        if len(content) / content.count("\n") < 4:
                            content = content.replace("\n", "")
                            iterString = 'REFERENCES|References|[R|r][E|e][F|f][E|e][R|r][E|e][N|n][C|c][E|e][S|s]|[R|r] [E|e] [F|f] [E|e] [R|r] [E|e] [N|n] [C|c] [E|e] [S|s]|[B|b][I|i][B|b][L|l][I|i][O|o][G|g][R|r][A|a][P|p][H|h][Y|y]'
                            
                        i = re.finditer(iterString, content[end:])
                        # the variable last refers to the last "references" word in the text. It is used to crop off the references at the end of the articles. last.start() is the start of the word "references"
                        last = None
                        for last in i:
                            continue
                        
                        if last != None:
                            references = content[end+last.end():]
                            content = content[:end+last.start()]
                        else:
                            pass
                            
                        # Check if CID code / character Ratio. If too high don't use it
                        ratio = (len(re.findall("\(cid:\d+\)", content)) / len(content) * 100)
                        if (len(re.findall("\(cid:\d+\)", content)) / len(content) * 100) > 6:
                            content = faceProblem("Content contains mostly CID")
                            break
                        
                        # Recognize Problem with detecting space in the PDF file
                        entitysize = content.split()
                        if len(content)/20 > len(entitysize):
                            content = faceProblem("Problem when scraping pdf: Not detecting spaces")
                            break

                        # Remove all CID codes from content if there is any
                        content = re.sub("\(cid:\d+\)", '', content)
                        # Remove unnecessary whitespace
                        content = re.sub("\s{3,}", '\n\n', content)
                        
                        references = re.sub("\(cid:\d+\)", '', references)

                        break
            except Exception as e:
                    print(title)
                    print("Error when trying to read attachments/PDFs")
                    print(e)
                    
                    continue
    except Exception as e:
        print(title)
        print(e)
        return

    # Returns "" if there is no PDF attached, " " if theres a problem with the PDF, otherwise the full content of the PDF
    return content, references

def check_item(item):
    global zotero_keylist
    global report


    # Create the session
    session = db.session()
    data = item["data"]


    ## Adding each key the keylist which is needed by delete_old()
    zotero_keylist.append(data["key"])

    req = session.query(Article).filter(Article.ID == data["key"])
    # If article exists and hasn't been modified, update last sync date and return

    # Get date. If timezone environment variable exists, use it
    try:
        zone = os.environ["TIMEZONE"]
        date_str = datetime.datetime.now(timezone(zone)).strftime("%Y-%m-%d %H:%M")
    except:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if len(list(req)) > 0 and req[0].date_modified == data["dateModified"]:
        req[0].date_last_zotero_sync = date_str
        session.commit()
        session.close()
        report["existed"] += 1
        return False

    # If the item existed but has been modified delete it now and continue to add it again
    elif len(list(req)) > 0 and req[0].date_modified != data["dateModified"]:
        session.delete(req[0])
        session.commit()
        report["updated"] += 1

    else:
        report["new"] += 1
        #print("Adding ", data["title"], "to database.")

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
                # Entriers without first name use "name", otherwise firstName and lastName
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

    # Get the content of article content from attached PDFs
    articleContent, references = readAttachedPDF(data["key"], data['title'])
    
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
                        articleFullText = articleContent,
                        references = references,
                        importantWords = "",
                        importantWordsCount = "",
                        importantWordsLocation = "",
                        searchIndex = " ".join([content["title"], author, content["publicationTitle"], content["abstractNote"], content["DOI"], content["ISSN"], content["ISBN"]]),
                        date_last_zotero_sync = date_str,
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
        collectionID = "None"

    # Connect to the database
    zot = zotero.Zotero(libraryID, "group")
    
    # Retrieve the zotero items 50 at a time and get the number of items
    # Uses the COLLECTION_ID if one is provided as environment variable
    if collectionID == "None":
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

    # Count how many items are in the database in total
    session = db.session()
    total = len(list(session.query(Article)))
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
    
    schedule.every(1).hours.do(update_from_zotero)
    
    while True:
        schedule.run_pending()
        time.sleep(60)