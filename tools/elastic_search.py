from elasticsearch import Elasticsearch
from pprint import pprint
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q

es = Elasticsearch(host="localhost", port=9200)



s = Search(using=es, index='my-index')
q = Q('match', abstract='Recent work on the issue')
s = s.query(q)
s = s.highlight('abstract', fragment_size=20)
response = s.execute()
for hit in response:
    pprint(hit.abstract)
    for fragment in hit.meta.highlight.abstract:
        print(fragment)
    
    