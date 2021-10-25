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


mapping = {
    "mappings": {
        "properties": {
            "dbid": {"type": "text"},
            "ID": {"type": "text"},
            "ENTRYTYPE": {"type": "text"},
            "title": {"type": "text", "term_vector": "with_positions_offsets"},
            "author": {"type": "text", "term_vector": "with_positions_offsets"},
            "authorlast": {"type": "text"},
            "year": {"type": "text"},
            "journal": {"type": "text"},
            "publication": {"type": "text"},
            "booktitle": {"type": "text"},
            "isbn": {"type": "text"},
            "issn": {"type": "text"},
            "doi": {"type": "text"},
            "pages": {"type": "text"},
            "volume": {"type": "text"},
            "number": {"type": "text"},
            "tags": {"type": "text"},
            "icon": {"type": "text"},
            "notes": {"type": "text"},
            "abstract": {"type": "text", "term_vector": "with_positions_offsets"},
            "editor": {"type": "text"},
            "tags_man": {"type": "text"},
            "tags_auto": {"type": "text"},
            "extra": {"type": "text"},
            "journal_abbrev": {"type": "text"},
            "address": {"type": "text"},
            "institution": {"type": "text"},
            "publisher": {"type": "text"},
            "language": {"type": "text"},
            "url": {"type": "text"},
            "articleFullText": {"type": "text", "term_vector": "with_positions_offsets"},
            "importantWords": {"type": "text"},
            "contentChecked": {"type": "text"},
            "references": {"type": "text"},
            "searchIndex": {"type": "text"},
            "date_added": {"type": "text"},
            "date_modified": {"type": "text"},
            "date_last_zotero_sync": {"type": "text"},
            "date_modified_pretty": {"type": "text"},
            "date_added_pretty": {"type": "text"},
            "_date_created_str": {"type": "text"},
            "_date_created": {"type": "text"}
        }
    }
}

def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d

def load_data():
    session = db.session()
    rows = db.session.query(Article).all()
    res = []
    for row in rows:
        res.append(row2dict(row))
    return res

# Resets/Deletes entire index
def delete():
    res = es.indices.delete(index="my-index")
    print(res)
    return


if __name__ == "__main__":
    
    #print(es.get("my-index", id="kjTFp3wBmVrKJdfo7MOi"))
    #print(es.indices.get_field_mapping(["title", "abstract"], "my-index"))
    
    shortenContent()
    delete()
    data = load_data()
    
    # Create Index
    es.indices.create(index="my-index", body=mapping)
    for a_data in data:
        res = es.index(index='my-index', body=a_data)
        pprint(res)

