# This script goes through all articles which have been added using zotero and looks for a pdf file
# If a pdf file is found, the content will be scraped and added to the database and, if available, to elasticsearch
# analyzeArticles() is regularly scheduled from update_library.py if the server is running

import sys
sys.path.append(".")
from bibfilter import db, app
from bibfilter.models import Article
from bibfilter.elasticsearchfunctions import elasticsearchCheck, getElasticClient
import re
import time
from unidecode import unidecode
from pyzotero import zotero, zotero_errors
import os
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from PyPDF2 import PdfFileReader
from multiprocessing import Process, Queue
import time

def row2dict(row):
    """ Converts SQL article to dict to insert in elasticsearch """
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))
    return d
    
def addToElasticsearch(article):
    """
    Given an SQLAlchemy item, adds it to Elasticsearch index if elasticsearch is set to be used.
    
    :param article: SQLAlchemy Query item
    :returns: Boolean indicating whether an article was indexed or not
    """
    useElasticSearch = elasticsearchCheck()
    try:
        if useElasticSearch:
            body = row2dict(article)
            es = getElasticClient()
            ## Creates or updates a document in index.
            es.index(index='bibfilter-index', document=body, id=body["ID"])
            return True
        elif os.environ.get("USE_ELASTICSEARCH").upper() == "TRUE":
            raise ConnectionError("Error: USE_ELASTICSEARCH env is set to True, but cannot connect to elasticsearch. Abort and try later.")
        else:
            return False
    except Exception as e:
        raise ConnectionError(f"{e}\nCouldn't connect to elasticsearch")

def faceProblem(title, message):
    """ Format error messages for articles """
    print(title)
    print(message+"\n")
    return ""

def readAttachedPDF(articleID, title, Q):
    """
    Scrapes the content of the PDF file of a specified article and puts it in Queue.
    
    :param articleID: ID of zotero item
    :param title: Title of article for logging
    :param Q: multiprocessing Queue to be used
    :returns: Nothing
    """
    try:
        content = ""
        references = ""
        connectionError = False
        
        libraryID = os.environ["LIBRARY_ID"]
        APIkey = os.environ["APIkey"]
        zot = zotero.Zotero(libraryID, "group", APIkey)
        attachments = zot.children(articleID)

        # Goes through each attachment if there is any
        for each in attachments:
            content = ""
            try:
                # Notes are different from attachments and don't have contentType attribute
                if each["data"]["itemType"] == "attachment":
                    if each["data"]["contentType"] == 'application/pdf':
                        pdfID = each["data"]["key"]
                        # Save attachment as pdf
                        zot.dump(pdfID, 'zot_article.pdf')
                        
                        with open('zot_article.pdf', 'rb') as file:
                            pdfFile = PdfFileReader(file)
                            totalPages = pdfFile.getNumPages()
                        
                        # Parse only first 60 pages at maximum
                        totalPages = min(60, totalPages)
                        
                        # Set paramters of extraction
                        laparam = LAParams(detect_vertical=True)
                        # get content of pdf
                        # Parsing over only a few pages seperately may take longer but uses less memory
                        step = 3
                        for pg in range(0, totalPages, step):
                            content += extract_text('zot_article.pdf', page_numbers=list(range(pg, pg+step)), laparams=laparam)
                        
                        # Check length of content
                        if len(content) < 4000:
                            content = faceProblem(title, "Problem: extracted content shorter than expected, aborted extraction")
                            break
                        
                        # Fix: ValueError: A string literal cannot contain NUL (0x00) characters. Caused by a problem with extract_text
                        content = content.replace("\x00", "")
                        # Use end variable to look only after the dirst third of the document. Prevents mistakes in the rare cases that References is only mentioned on the first page
                        end = int(len(content) / 3.5)
                        
                        # Find the position of references to then only index text before the references. \W means any non-word character
                        iterString = 'REFERENCES|References|[\W|\n][R|r][E|e][F|f][E|e][R|r][E|e][N|n][C|c][E|e][S|s]|[\W|\n][R|r] [E|e] [F|f] [E|e] [R|r] [E|e] [N|n] [C|c] [E|e] [S|s]|[B|b][I|i][B|b][L|l][I|i][O|o][G|g][R|r][A|a][P|p][H|h][Y|y]'
                        
                        # Cover cases where there is tons of \n newlines in the scanned code:
                        if content.count("\n") > 0:
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
                            content = faceProblem(title, "Content contains mostly CID")
                            break
                        
                        # Recognize Problem with detecting space in the PDF file
                        entitysize = content.split()
                        if len(content)/20 > len(entitysize):
                            content = faceProblem(title, "Problem when scraping pdf: Not detecting spaces")
                            break

                        # Remove all CID codes from content if there is any
                        content = re.sub("\(cid:\d+\)", '', content)
                        # Remove unnecessary whitespace
                        content = re.sub("\s{3,}", '\n\n', content)
                        
                        references = re.sub("\(cid:\d+\)", '', references)

                        print("Successfully extracted content")
                        break
            except Exception as e:
                    print(title)
                    print("Error when trying to read attachments/PDFs")
                    print(e)
                    continue
    except zotero_errors.HTTPError:
        print("Experienced connection error")
        connectionError = True
        Q.put((content, references, connectionError))        
        return                
    except Exception as e:
        print(e)
        print(f"Error occured when checking {title}\n")
        return

    Q.put((content, references, connectionError))
    return

def progressMessage():
    """
    Prints progress of content scraping to the console
    
    :returns: Nothing
    """
    print()
    with app.app_context():
        session = db.session()
        checked = session.query(Article).filter(Article.contentChecked == True).count()
        notChecked = session.query(Article).count()
        print(f"Checked {checked} of {notChecked} articles")
        session.close()

def analyzeContent():
    """
    If at least one article has its property contentChecked set to False, scrapes content of PDF file if available and saves it in database. 
    Indexes Database items to Elasticsearch. Doesn't commit to Database if it encounters error when connecting to Elasticsearch.
    
    :returns: True if Elasticsearch Error was encountered, else False
    """
    progressMessage()
    
    with app.app_context():
        session = db.session()
        article = session.query(Article).filter(Article.contentChecked == False).first()
        
        if article == None:
            print("No articles left to analyze")
            return True
        
        articleID, articleTitle, articleSQLID = article.ID, article.title, article.dbid
        session.close()
    
    # Get the content of article content from attached PDFs
    print("Analyze:", articleTitle)
    Q = Queue()
    p1 = Process(target=readAttachedPDF, args=(articleID, articleTitle, Q))
    p1.start()
    try:
        articleContent, references, connectionError = Q.get(timeout=360)
    except Exception as e:
        print(e)
        print("Analyzing article didn't finish in expected time. Maybe the process was killed because of memory issue or the network connection was interrupted")
        print("For this article there will be no content available")
        
        with app.app_context():
            session = db.session()
            article = session.query(Article).filter(Article.ID == articleID).first()
            article.contentChecked = True
            # Add to elasticSearch and mark as indexed
            try:
                article.elasticIndexed = addToElasticsearch(article)
            except ConnectionError as e:
                print(e)
                return True
            session.commit()
            session.close()
        return False
    finally:
        p1.kill()
        p1.join()
        p1.close()
        
    if connectionError:
        print("There seems to be an issue with the zotero server. Will again try to connect later")
        return True
    
    if len(articleContent) > 0:    
        # Need to use unidecode to handle some misread OCR_characters
        articleContent = unidecode(articleContent)
        
        # Make sure articleFullText is at most 1000000 characters long
        if len(articleContent) > 1000000:
            articleContent =  articleContent[:1000000]
            print("Shorten articleContent because it exceeds max size of 1000000 chars")
    
    with app.app_context():
        session = db.session()
        article = session.query(Article).filter(Article.ID == articleID).first()
        article.articleFullText = articleContent
        article.contentChecked = True
        
        # Add to elasticSearch and mark as indexed
        try:
            article.elasticIndexed = addToElasticsearch(article)
        except ConnectionError as e:
            print(e)
            return True
        session.commit()
        session.close()
    return False
    
def analyzeArticles():
    """ Checks all items in database unless nothing to do or error when connecting to elasticsearch """
    while True:
        time.sleep(2)
        finished = analyzeContent()
        if finished:
            return

if __name__ == "__main__":
    analyzeArticles()