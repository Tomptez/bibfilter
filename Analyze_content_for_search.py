# Indexes all words of a text to make the text easily searchable and to provide matching text passages.

from textblob import TextBlob as tb
from textblob.download_corpora import download_lite
import nltk
download_lite()
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
import sys
sys.path.append(".")
from bibfilter import db
from bibfilter.models import Article
import json
import re
import time
from nltk.corpus import stopwords  
from unidecode import unidecode
import schedule

def clean_tokens(blob):
    tokens = blob.tokens
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if len(token) > 2]
    tokens = [token for token in tokens if token.lower() not in stop_words]
    return tokens

def lemmatize_tokens(blob):
    tokens = blob.tokens
    tokens = [token.lemmatize().lower() for token in tokens]
    return tokens

def count_words(word, blob):
    return blob.words.count(word)

def analyzeContent():
    session = db.session()
    req = session.query(Article).filter(Article.importantWords.like(""))
    session.close()

    origBlobList = []
    lemmaBlobList = []
    minimalBlobList = []

    titleList = []
    for article in req:
        
        # Ignore articles that don't have extracted text
        if article.articleFullText != "":
            # Need to use unidecode to handle some misread OCR_characters
            text = unidecode(str(article.articleFullText))
            blob = tb(text)
            origBlobList.append(blob)
            titleList.append(article.title)

    for each in origBlobList:
        lemmaText = tb(" ".join(lemmatize_tokens(each)))
        lemmaBlobList.append(lemmaText)
        cleanText = tb(" ".join(clean_tokens(lemmaText)))
        minimalBlobList.append(cleanText)

    for blobIndex, blob in enumerate(minimalBlobList):
        print()
        # Count all the words if they appear at least twice
        scores = {}
        for word in blob.words:
            if blob.word_counts[word] > 1:
                scores[word] = blob.word_counts[word]

        # optional: sort
        sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        content_words = " ".join(scores.keys())

        # optional: print
        print(f"Top words in {titleList[blobIndex]}")
        for word, score in sorted_words[:40]:
            
            print(f"Word: {word}, count: {score}")

        occurence_dict = {}
        
        for word, count in sorted_words:
            articleContent = " ".join(str(origBlobList[blobIndex]).split())[200:]
            occurList = [200+m.start() for m in re.finditer(word, articleContent)]
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
                
                textPart = " ".join(str(origBlobList[blobIndex]).split())[start:end]
                
                words = textPart.split(" ")
                cnt, wordIndex = 0, 0
                for ix, k in enumerate(words):
                    cnt += len(k)+1
                    if cnt > 162:
                        wordIndex = ix
                        break
                htmlWords = words[1:wordIndex] + [f"<b>{words[wordIndex]}</b>"] + words[wordIndex+1:-1]
                textFinal = "(...)" + " ".join(htmlWords) + "(...)"

                partList.append(textFinal)
                
                # Only use 4 quotes for each word
                if len(partList) > 3:
                    break
                
                oldInstance = instance
            
            occurence_dict[word] = partList
            
        session = db.session()
        article = session.query(Article).filter(Article.title==titleList[blobIndex])[0]
        
        article.importantWords = content_words
        article.importantWordsCount = json.dumps(scores)
        article.importantWordsLocation = json.dumps(occurence_dict)
        
        session.commit()
        session.close()
    print("Finished analyzeContent()...")

# Analyze the Content based on articleFullTExt of each Artice
# Once on start, after that every 1.1 hours (slighty unsynced from update_library.py)
if __name__ == "__main__":
    analyzeContent()
    
    schedule.every(1.1).hours.do(analyzeContent)
    
    while True:
        schedule.run_pending()
        time.sleep(60)