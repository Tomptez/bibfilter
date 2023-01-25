import os
from elasticsearch import Elasticsearch

elasticMapping = {
    "settings": {
        "analysis": {
            "analyzer": {
                "default": {
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "apostrophe"
                    ]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "dbid": {"type": "text"},
            "ID": {"type": "text"},
            "ENTRYTYPE": {"type": "text"},
            "title": {"type": "text", "term_vector": "with_positions_offsets", "fields":{"keyword": {"type": "keyword"}}},
            "author": {"type": "text", "term_vector": "with_positions_offsets", "fields":{"keyword": {"type": "keyword"}}},
            "authorlast": {"type": "text", "fields":{"keyword": {"type": "keyword"}}},
            "year": {"type": "integer"},
            "journal": {"type": "text", "fields":{"keyword": {"type": "keyword"}}},
            "publication": {"type": "text", "fields":{"keyword": {"type": "keyword"}}},
            "booktitle": {"type": "text"},
            "isbn": {"type": "text"},
            "issn": {"type": "text"},
            "doi": {"type": "text", "fields":{"keyword": {"type": "keyword"}}},
            "pages": {"type": "text", "fields":{"keyword": {"type": "keyword"}}},
            "volume": {"type": "text"},
            "number": {"type": "text"},
            "tags": {"type": "text"},
            "icon": {"type": "text", "fields":{"keyword": {"type": "keyword"}}},
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
            "language": {"type": "text", "fields":{"keyword": {"type": "keyword"}}},
            "url": {"type": "text", "fields":{"keyword": {"type": "keyword"}}},
            "articleFullText": {"type": "text", "term_vector": "with_positions_offsets"},
            "importantWords": {"type": "text"},
            "contentChecked": {"type": "text"},
            "elasticIndexed": {"type": "text"},
            "references": {"type": "text"},
            "searchIndex": {"type": "text"},
            "date_added": {"type": "date", "format": "yyyy-MM-dd'T'HH:mm:ssX||epoch_millis"},
            "date_modified": {"type": "date", "format": "yyyy-MM-dd'T'HH:mm:ssX||epoch_millis"},
            "date_last_zotero_sync": {"type": "text"},
            "date_modified_pretty": {"type": "text"},
            "date_added_pretty": {"type": "text"},
        }
    }
}

ELASTIC_URL = os.environ.get("ELASTICSEARCH_URL")
ELASTIC_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD", None)
ELASTIC_USERNAME = os.environ.get("ELASTICSEARCH_USERNAME", "elastic")

def getElasticClient():
    """
    Connects to elasticsearch. If password is specified in the .env file, consider env variables
    """
    if not ELASTIC_PASSWORD:
        es = Elasticsearch(ELASTIC_URL)
    else:
        es = Elasticsearch(basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD))
    return es

def createElasticsearchIndex():
    es = getElasticClient()
    if not es.indices.exists(index="bibfilter-index"):
        es.indices.create(index="bibfilter-index", body=elasticMapping)
        print("Created Elasticsearch index")

# Check if the elasticsearch environment variable is set, if a connection is possible and bibfilter-index exists
def elasticsearchCheck():    
    if os.environ.get("USE_ELASTICSEARCH").upper() == "TRUE":
        try:
            es = getElasticClient()
            createElasticsearchIndex()
            useElasticSearch = True
            es.close()
        except Exception as e:
            print("Could not connect to Elasticsearch Server")
            useElasticSearch = False
        return useElasticSearch
    else:
        return False

if __name__ == "__main__":
    pass