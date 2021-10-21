# Indexes all words of a text to make the text easily searchable and to provide matching text passages.

from textblob import TextBlob as tb
import nltk
# need NLTK data punkt, stopwords, wordnet, brown, averaged_perceptron_tagger
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

def analyzeContent():
    print("start analyzeContent()")
    session = db.session()
    articles = session.query(Article).filter(Article.importantWords.like(""))
    
    for article in articles:
    
        article.importantWords = ""
        article.importantWordsCount = ""
        article.importantWordsLocation = ""

        session.commit()
    session.close()


# Analyze the Content based on articleFullTExt of each Artice
# Once on start, after that every 1.1 hours (slighty unsynced from update_library.py)
if __name__ == "__main__":
    analyzeContent()