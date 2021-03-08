# Indexes all words of a text to make the text easily searchable and to provide matching text passages.
# This script is mainly for testing to later implement this feature
import math
from textblob import TextBlob as tb
import nltk
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

bloblist = []
bloblist2 = []
titleList = []
for article in req:
    # Find the position of references to then only index text before the references. \W means any non-word character
    i = re.finditer('\Wr e f e r e n c e s|\nr e f e r e n c e s|\nreferences|\Wreferences', article.articleFullText.lower())
    # the variable last refers to the last "references" word in the text. It is used to crop off the references at the end of the articles. last.start() is the start of the word "references"
    last = None
    for last in i:
        continue
    
    blob = tb(str(article.articleFullText)[:last.start()])
    bloblist.append(blob)
    titleList.append(article.title)

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

    # Get all occurences starting points
    kl = [m.start() for m in re.finditer('inequality', str(blob.lower()))]
    # Save dict scores as dic
    # save dict key in db
    # save starting points in db

    ## optional: sort and print
    # sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    # print(f"Top words in {titleList[i]}")
    # for word, score in sorted_words[:40]:
        
    #     print(f"Word: {word}, count: {score}")
    


# Todo
# Ignore numbers?
# save results as string and as dictionary
# marshmellow functions? -> retrieve only part of column?
# Ignore PDFs with more than 60 pages
# Handle search for literal terms "literal"
# Use OCR for old pdfs
# Handle different languages