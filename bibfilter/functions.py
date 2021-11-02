import os
from elasticsearch import Elasticsearch

elasticMapping = {
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
            "elasticIndexed": {"type": "text"},
            "references": {"type": "text"},
            "searchIndex": {"type": "text"},
            "date_added": {"type": "text"},
            "date_modified": {"type": "text"},
            "date_last_zotero_sync": {"type": "text"},
            "date_modified_pretty": {"type": "text"},
            "date_added_pretty": {"type": "text"},
        }
    }
}

elasticURL = os.environ.get("ELASTICSEARCH_URL")

def getElasticClient():
    es = Elasticsearch(elasticURL)
    return es

# Check if the elasticsearch environment variable is set, if a connection is possible and bibfilter-index exists
def elasticsearchCheck():    
    if os.environ.get("USE_ELASTICSEARCH").upper() == "TRUE":
        try:
            es = getElasticClient()
            if not es.indices.exists(index="bibfilter-index"):
                es.indices.create(index="bibfilter-index", body=elasticMapping)
            useElasticSearch = True
            es.close()
        except Exception as e:
            print(e)
            useElasticSearch = False
        return useElasticSearch
    else:
        return False