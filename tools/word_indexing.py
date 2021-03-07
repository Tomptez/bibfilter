# Indexes all words of a text to make the text easily searchable and to provide matching text passages.
# This script is mainly for testing to later implement this feature
import math
from textblob import TextBlob as tb
import nltk
nltk.download('punkt')
import sys
sys.path.append(".")
from bibfilter import db
from bibfilter.models import Article
import json
import re
import time

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
    print(article.title)
    print(len(list(i)))
    last = None
    for last in i:
        continue

    blob = tb(article.articleFullText)
    bloblist.append(blob)
    titleList.append(article.title)

def prepare_text_for_lda(blob):
    tokens = blob.tokens
    tokens = [token for token in tokens if len(token) > 4]
    #tokens = [token for token in tokens if token not in en_stop]
    tokens = [token.lemmatize().lower() for token in tokens]
    return tokens

for each in bloblist:
    newtext = " ".join(prepare_text_for_lda(each))
    bloblist2.append(tb(newtext))

for i, blob in enumerate(bloblist2):
    print()
    # Count all the words if they appear at least twice
    scores = {}
    for word in blob.words:
        if blob.word_counts[word] > 1:
            scores[word] = blob.word_counts[word]
    ## optional: sort and print
    sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print(f"Top words in {titleList[i]}")
    for word, score in sorted_words[:3]:
        
        print(f"Word: {word}, count: {score}")
    
    #print(json.dumps(words))

    # Get all occurences starting points
    kl = [m.start() for m in re.finditer('inequality', str(blob.lower()))]
    #print(kl)




# Todo
# Remove stopwords of respective language
# Ignore numbers?
# save results as string and as dictionary
# marshmellow functions? -> retrieve only part of column?
# ignore references!
# Ignore PDFs with more than 60 pages
# Handle search for literal terms "literal"