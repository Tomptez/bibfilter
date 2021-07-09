# Indexes all words of a text to make the text easily searchable and to provide matching text passages.

from textblob import TextBlob as tb
import nltk
# need NLTK data punkt, stopwords, wordnet, brown, averaged_perceptron_tagger
import sys
sys.path.append(".")
from bibfilter import db
from bibfilter.models import Article, Wordstat
import re
import time
from nltk.corpus import stopwords  
from unidecode import unidecode
from pyzotero import zotero
import os
from io import BytesIO
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from PyPDF2 import PdfFileReader
from multiprocessing import Process, Queue

def readAttachedPDF(articleID, title, Q):
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
                        # Save attachment as pdf
                        zot.dump(pdfID, 'zot_article.pdf')
                        
                        with open('zot_article.pdf', 'rb') as file:
                            pdfFile = PdfFileReader(file)
                            totalPages = pdfFile.getNumPages()
                        
                        # Parse only first 60 pages at maximum
                        totalPages = min(60, totalPages)
                        
                        # normal extract
                        laparam = LAParams(detect_vertical=True)
                        # get content of pdf
                        content = ""
                        # Parsing over only a few pages seperately may take longer but uses less memory
                        step = 3
                        for pg in range(0, totalPages, step):
                            content += extract_text('zot_article.pdf', page_numbers=list(range(pg, pg+step)), laparams=laparam)
                        
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

                        print("Successfully extracted content")
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

    Q.put((content, references))
    return

def clean_tokens(blob):
    tokens = blob.tokens
    stop_words = set(stopwords.words('english'))
    stemmer = nltk.stem.snowball.SnowballStemmer("english")
    tokens = [token for token in tokens if len(token) > 2]
    tokens = [stemmer.stem(token) for token in tokens]
    # tokens = [token.lemmatize().lower() for token in tokens]
    tokens = [token for token in tokens if token not in stop_words]
    return tokens

def analyzeContent():
    print()
    session = db.session()
    checked = session.query(Article).filter(Article.contentChecked == True).count()
    notChecked = session.query(Article).count()
    print(f"Checked {checked} of {notChecked} articles")
    article = session.query(Article).filter(Article.contentChecked == False).first()
    # article = session.query(Article).filter(Article.ID == "DUMD4NTK").first()
    
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
        articleContent, references = Q.get(timeout=360)
    except:
        print("Analyzing article didn't finish in expected time. Maybe the process was killed because of memory issue?")
        article.contentChecked = True
        session.commit()
        session.close()
        return False
    finally:
        p1.kill()
        p1.join()
        p1.close()
    
    # Need to use unidecode to handle some misread OCR_characters
    articleContent = unidecode(articleContent)
    session = db.session()
    article = session.query(Article).filter(Article.ID == articleID).first()
    article.articleFullText = articleContent
    
    if articleContent == "":
        article.contentChecked = True
        session.commit()
        session.close()
        return False
    else:
        session.commit()
        session.close()
        
    
    blob = tb(articleContent)
    blob = tb(" ".join(clean_tokens(blob)))

    # Count all the words if they appear at least twice
    scores = {}
    for word in blob.words:
        if blob.word_counts[word] > 1:
            scores[word] = blob.word_counts[word]

    # optional: sort
    sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # # optional: print
    # print(f"Top words in Article:")
    # for word, score in sorted_words[:40]:
    #     print(f"Word: {word}, count: {score}")

    articleContent = " ".join(articleContent.split())[200:]
    session = db.session()
    for word, count in sorted_words:
        regexp = f" {word.encode('unicode_escape').decode()}"
        occurList = [m.start() for m in re.finditer(regexp, articleContent, re.IGNORECASE)]
        partList = []
        oldInstance, end = 0, 0
        for instance in occurList:
            # Check whether occurence is already included in the last excerpt
            if instance < end:
                continue
            
            start = max(instance-160,0)
            end = min(instance+165,len(articleContent)-1)
            
            if oldInstance > start:
                del partList[-1]
            
            textPart = articleContent[start:end]
            
            words = textPart.split(" ")
            cnt, wordIndex = 0, 0
            for ix, k in enumerate(words):
                cnt += len(k)+1
                # instance-start+2 is usually 162, the exact center, except when the word is at the start of the article
                if cnt > instance-start+2:
                    wordIndex = ix
                    break
            htmlWords = words[1:wordIndex] + [f"<b>{words[wordIndex]}</b>"] + words[wordIndex+1:-1]
            textFinal = "(...)" + " ".join(htmlWords) + "(...)"
            
            partList.append(textFinal)
            
            # Only use 4 quotes for each word
            if len(partList) > 3:
                break
            
            oldInstance = instance
        
        # Make sure the word hasn't been added before e.g. the process was killed while adding words from this article
        if session.query(Wordstat).filter(Wordstat.word == word, Wordstat.article_ref_id == articleSQLID).first() == None:
            quote = ";SEP;".join(partList)
            newWord = Wordstat(word=word, count=scores[word], quote=quote, article_ref_id=articleSQLID)
            session.add(newWord)
            session.commit()
    
    content_words = " ".join(scores.keys())
    
    article = session.query(Article).filter(Article.ID == articleID).first()
    article.importantWords = content_words
    # article.importantWordsCount = json.dumps(scores)
    # article.importantWordsLocation = json.dumps(occurence_dict)
    article.contentChecked = True
    session.commit()
    session.close()
    
    return False
    

def analyzeSomeArticles():
    total_articles = db.session.query(Article).count()
    for i in range(total_articles):
        time.sleep(2)
        finished = analyzeContent()
        if finished:
            return

# Analyze the Content based on articleFullTExt of each Artice
# Once on start, after that every 1.1 hours (slighty unsynced from update_library.py)
if __name__ == "__main__":
    analyzeSomeArticles()