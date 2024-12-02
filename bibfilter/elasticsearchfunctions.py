import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

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

ELASTIC_URL = os.environ.get("ELASTICSEARCH_URL", None)
ELASTIC_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD", None)
ELASTIC_USERNAME = os.environ.get("ELASTICSEARCH_USERNAME", "elastic")
ELASTIC_CERTIFICATE = os.environ.get("ELASTICSEARCH_CERTIFICATE", None)

def getElasticClient():
    """
    Connects to elasticsearch. If password is specified in the .env file, consider env variables
    """
    try:
        if not ELASTIC_PASSWORD:
            es = Elasticsearch(ELASTIC_URL)
        elif not ELASTIC_CERTIFICATE:
            es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD))
        else:
            es = Elasticsearch(ELASTIC_URL, ca_certs=ELASTIC_CERTIFICATE, basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD))
    except Exception as e:
        print("ERROR: getElasticClient() couldn't connect to elasticsearch")
        print(e)
    #print(f"getElasticClient(): Able to connect to elasticsearch? {es.ping()}")
    return es

def elasticsearchIndex():
    return_val = True
    try:
        es = getElasticClient()
    except Exception as e:
        return False

    # return if no connection possible
    if es.ping() == False:
        return es.ping()

    try:
        if not es.indices.exists(index="bibfilter-index"):
            es.indices.create(index="bibfilter-index", body=elasticMapping)
            print("Created Elasticsearch index")
        es.close()
    except elasticsearch.exceptions.RequestError as ex:
        # can in some use cases happen even though indices.exists() was checked before
        if ex.error == 'resource_already_exists_exception':
            pass # Index already exists. Ignore.
    except Exception as e:
        print("ERROR: elasticsearchIndex() Could not create index")
        print(e)
        return_val = False
    finally:
        return return_val
    

# Check if the elasticsearch environment variable is set, if a connection is possible and bibfilter-index exists
def elasticsearchCheck():    
    if os.environ.get("USE_ELASTICSEARCH").upper() == "TRUE":
        useElasticSearch = elasticsearchIndex()
        if useElasticSearch == False:
            elastic_vars={"ELASTIC_URL": None if ELASTIC_URL == None else "set", "ELASTIC_PASSWORD": None if ELASTIC_PASSWORD == None else "set", "ELASTIC_USERNAME":None if ELASTIC_USERNAME == None else "set", "ELASTIC_CERTIFICATE": None if ELASTIC_CERTIFICATE == None else "set"}
            print(f"Couldn't connect to Elasticsearch. \nEnvironment variables: {elastic_vars}")
        return useElasticSearch
    else:
        return False

if __name__ == "__main__":
    pass
