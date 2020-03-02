import requests
import sys
sys.path.append("..")
import time
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bibfilter import db
from bibfilter.models import Article

def add_item(doi):
    r = requests.get(f"https://api.crossref.org/works/{doi}")

    if r.text == "Resource not found.":
        return f"DOI not found"

    else:
        resultjson = r.json()

        result = resultjson["message"]

        title = result["title"][0]
        url = result["URL"]
        publisher = result["publisher"]
        ENTRYTYPE = result["type"]
        author = f'{result["author"][0]["family"]}, {result["author"][0]["given"]}'
        year = str(result["published-print"]["date-parts"][0][0])
        journal = result["container-title"][0]
        # pages = db.Column(db.String)
        volume = result["volume"]
        number = result["issue"]
        ID = title.split()[1]+result["author"][0]["family"]+year

        #Create the session
        session = db.session()

        if len(list(session.query(Article).filter(Article.ID == ID))) > 0:
            return f"{title} already exists in the database."

        new_art = Article(title=title, url=url, publisher=publisher, ID=ID, ENTRYTYPE=ENTRYTYPE, author=author, year=year, doi=doi, journal=journal, volume=volume, number=number, _date_created_int = time.time(), _date_created_str = str(datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")))

        session.add(new_art)

        session.commit()
        return f"Added article to the Database. \n\nTitle:{title}\nDOI: {doi}"

if __name__ == "__main__":
    doi = "10.1007/s11109-017-9399-3"
    add_item(doi)