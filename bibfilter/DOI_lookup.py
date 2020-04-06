import requests
import sys
sys.path.append(".")
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

        #fields = ["title", "URL", "publisher", "type", "author", "published-print", "container-title", "volume", "issue"]

        try:
            if result.get("title") != None and len(result.get("title")) > 0:
                title = result["title"][0]
            else:
                title = ""

            url = result.get("URL")
            publisher = result.get("publisher")
            ENTRYTYPE = result.get("type")

            if result.get("author") != None and len(result.get("author")) > 0:
                author = f'{result["author"][0].get("family","")}, {result["author"][0].get("given","")}'
            else:
                if result.get("editor") != None and len(result.get("editor")) > 0:
                    author = f'{result["editor"][0].get("family","")}, {result["editor"][0].get("given","")}'
                else:
                    author = ""

            if result.get("published-print") != None and len(result.get("published-print")) > 0:
                year = str(result["published-print"]["date-parts"][0][0])
            else:
                year = ""

            if result.get("container-title") != None and len(result.get("container-title")) > 0:
                journal = result["container-title"][0]
            else:
                journal = ""

            # pages = db.Column(db.String)
            volume = result.get("volume")
            number = result.get("issue")

            if result.get("author") != None and len(result.get("author")) > 0:
                ID = title.split()[1]+result["author"][0]["family"]+year
            else:
                ID = title.split()[1]+doi.replace("/","").replace(".","")
        except Exception as e:
            print("ERROR", e)

        if title == "" or author == "":
            return f"Couldn't receive required metadata of {doi}"
        elif len(list(session.query(Article).filter(Article.ID == ID))) > 0:
            return f"{title} already exists in the database."

        new_art = Article(title=title, url=url, publisher=publisher, ID=ID, ENTRYTYPE=ENTRYTYPE, author=author, year=year, doi=doi, journal=journal, volume=volume, number=number, _date_created_int = time.time(), _date_created_str = str(datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")))

        #Create the session
        session = db.session()
        session.add(new_art)
        session.commit()

        return f"Added article to the Database. \n\nTitle:{title}\nDOI: {doi}"

if __name__ == "__main__":
    doi = "10.1007/978-3-319-69626-3"
    add_item(doi)