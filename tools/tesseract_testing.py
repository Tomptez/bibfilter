## Tool to OCR a PDF file and then extract its content.
# This is necessary if you want to obtain the content of PDF files that arent compatible with PDFMiner
# ocrmypdf needs to be isntalled on the computer

import tempfile
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError
from pdf2image import convert_from_path, convert_from_bytes
from pprint import pprint
import pikepdf
from pdfminer.high_level import extract_text
import ocrmypdf
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

def readAttachedPDF(articleID):
    try:
        libraryID = os.environ["LIBRARY_ID"]
        zot = zotero.Zotero(libraryID, "group")
        attachments = zot.children(articleID)

        content = ""
        for each in attachments:
            try:
                if each["data"]["contentType"] == 'application/pdf':
                    print("PDF File available")
                    pdfID = each["data"]["key"]
                    # get content of pdf
                    pdfBytes = zot.file(pdfID)
                    # convert bytes of bts to python object
                    pdfFile = BytesIO(pdfBytes)

                    folder = os.environ["PDF_FOLDER"]

                    #with tempfile.TemporaryDirectory() as path: 
                    
                    inputf = os.path.join(folder,"file_no_ocr_"+articleID+".pdf")
                    outputf = os.path.join(folder,"file_ocr_"+articleID+".pdf")

                    # Use pike to remove potential barriers which make ocr impossible
                    my_pdf = pikepdf.Pdf.open(pdfFile)
                    my_pdf.save(inputf)
                    
                    ocrmypdf.ocr(inputf, outputf, force_ocr=True)
                    content = extract_text(outputf)

                    # Fix: ValueError: A string literal cannot contain NUL (0x00) characters. Caused by a problem with extract_text
                    content = content.replace("\x00", "")
                    # Remove fulltext if it contains mostly cid specifications instead of actual test as pdfminer cannot handle some types of pdf
                    if len(re.findall("\(cid:\d+\)", content)) > 15:
                        content = " "
                        print("Content contains mostly CID")
                    # Recognize problems from scraping PDF, TODO -> handle differently
                    else:
                        entitysize = content.split()
                        for entity in entitysize:
                            if len(entity) > 400:
                                content = " "
                                print("Apparent problems when scraping pdf")
                    print("Got PDF content")

                    #save in .txt file
                    with open(os.path.join(folder,'file_ocr_'+articleID+'.txt'), 'w') as file: 
                        cnt = content.split("\n")
                        for line in cnt:
                            if len(line) > 2:
                                file.write(f"{line}\n")

                    #save in .txt file
                    with open(os.path.join(folder,'file_no_ocr_'+articleID+'.txt'), 'w') as file: 
                        file.write(extract_text(inputf))
                    
                    i = re.finditer('References|REFERENCES|[\W|\n][R|r] [E|e] [F|f] [E|e] [R|r] [E|e] [N|n] [C|c] [E|e] [S|s]|[\W|\n]references', content)
                    # the variable last refers to the last "references" word in the text. It is used to crop off the references at the end of the articles. last.start() is the start of the word "references"
                    last = None
                    for last in i:
                        continue
                    print(content[last.start():last.end()+60])

                    myi = extract_text(inputf)
                    cid_num = len(re.findall('\(cid:\d+\)', myi))
                    print(f"without OCR contains {cid_num} CID codes")

            except Exception as e:
                    print("Error when trying to read attachments/PDFs")
                    print(e)
                    continue
    except Exception as e:
        print(e)
        return

    return content

def check_item(item):
    global zotero_keylist
    global report

    # Create the session
    session = db.session()
    data = item["data"]

    req = session.query(Article).filter(Article.ID == data["key"])
    # If article exists and hasn't been modified, update last sync date and return

    if req[0].articleFullText == " ":
        print(f"{req[0].title}\n")
        # Get the content of article content from attached PDFs
        articleContent = readAttachedPDF(data["key"])
    
    
    session.commit()
    session.close()

def update_from_zotero():
    print("Started syncing with zotero collection")
    # Make variables alterable inside the function

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


    # Count how many items are in the database in total
    session = db.session()
    total = len(list(session.query(Article)))
    session.close()
    print("------------------------------------")
    print("Summary of synchronization with Zotero:")
    print(f"Updated. Total Articles: {total}")


update_from_zotero()