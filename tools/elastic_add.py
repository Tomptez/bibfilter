# Add articles to elasticsearch
# import the Elasticsearch low-level client library

import sys, os
sys.path.append(".")
from bibfilter import db
from bibfilter.models import Article
from pprint import pprint
from elasticsearch import Elasticsearch
from elasticsearch import helpers

es = Elasticsearch(host="localhost", port=9200)

def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d

def shortenContent():
    session = db.session()
    rows = db.session.query(Article).all()
    for row in rows:
        if len(row.articleFullText) > 1000000:
            print("Error. text is too long. This needs to be handled")
            exit()
    session.close()
    return

def load_data():
    session = db.session()
    rows = db.session.query(Article).all()
    res = []
    for row in rows:
        res.append(row2dict(row))
    return res

def delete():
    res = es.indices.delete(index="my-index")
    print(res)
    return

if __name__ == "__main__":
    shortenContent()
    delete()
    data = load_data()
    
    for a_data in data:
        res = es.index(index='my-index', body=a_data)
        pprint(res)