# Indexes all words of a text to make the text easily searchable and to provide matching text passages.
# This script is mainly for testing to later implement this feature

import math
from textblob import TextBlob as tb
from textblob.download_corpora import download_lite
import nltk
download_lite()
nltk.download('punkt')
nltk.download('stopwords')
import sys
sys.path.append(".")
from bibfilter import db
from bibfilter.models import Article
import json
import re
import time
from nltk.corpus import stopwords  

def count_words(word, blob):
    return blob.words.count(word)

session = db.session()
req = session.query(Article)
session.close()

bloblist = []
bloblist2 = []
titleList = []
for article in req:
    if article.articleFullText is not None:
        blob = tb(str(article.articleFullText))
        bloblist.append(blob)
        titleList.append(article.title)

    else:
        print(f"{article.title} doesn't provide content")

def clean_tokens(blob):
    tokens = blob.tokens
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if len(token) > 2]
    tokens = [token for token in tokens if token.lower() not in stop_words]
    tokens = [token.lemmatize().lower() for token in tokens]
    return tokens

for each in bloblist:
    newtext = " ".join(clean_tokens(each))
    bloblist2.append(tb(newtext))

for i, blob in enumerate(bloblist2):
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
    print(f"Top words in {titleList[i]}")
    for word, score in sorted_words[:40]:
        
        print(f"Word: {word}, count: {score}")

    position_dict = {}
    
    for word, count in sorted_words:
        position_dict[word] = [m.start() for m in re.finditer(word, str(blob.lower()))][:4]
    
    session = db.session()
    article = session.query(Article).filter(Article.title==titleList[i])[0]
    
    article.importantWords = content_words
    article.importantWordsCount = json.dumps(scores)
    article.importantWordsLocation = json.dumps(position_dict)
    
    session.commit()
    session.close()


# Todo
# Ignore numbers?
# marshmellow functions? -> retrieve only part of column?
# Ignore PDFs with more than 60 pages
# Handle search for literal terms "literal"
# Use OCR for old pdfs
# Handle different languages
# Test if CID substitution works

# Actuall sort dict instead of using list? -> easier saving
# Don't include URLs or http

# Todo: Stolen Thunder? Huey Long's "Share Our Wealth," Political Mediation, and the Second New Deal
# doesn't really include any words