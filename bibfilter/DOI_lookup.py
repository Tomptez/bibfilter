import requests
import sys
sys.path.append(".")
import time
import datetime
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bibfilter import db
from bibfilter.models import Article

def get_json_value(the_json, key_list, default_value):
    # get_json_value(result, ["title",0], "")
    # returns result["title"][0] if existing, otherwise uses default value ""

    current = the_json # start from the base json
    for key in key_list:
        if isinstance(current, dict) and key in current:
            current = current[key] # move to dictionary value
        elif isinstance(current, list) and key < len(current):
            current = current[key] # move to item in a list
        else:
            return default_value
    return current # return whatever value we reached

def add_item(doi):
    r = requests.get(f"https://api.crossref.org/works/{doi}")

    if r.text == "Resource not found.":
        return f'DOI "{doi}" not found'

    else:
        resultjson = r.json()
        result = resultjson["message"]

        #fields = ["title", "URL", "publisher", "type", "author", "published-print", "container-title", "volume", "issue"]

        try:
            title = get_json_value(result, ["title",0],"")

            author = ""
            if result.get("author") != None and len(result.get("author")) > 0:
                keyword = "author"
            else:
                keyword = "editor"
            for i in range(len(result.get(keyword))):
                if i > 0:
                    author += ";"
                author += f'{get_json_value(result, [keyword, i, "family"], "")}, {get_json_value(result, [keyword, i, "given"], "")}'
                if i == 3:
                    break
            authorlast = "; ".join([n.split(",")[0].strip(" ") for n in author.split(";")]),

            year = get_json_value(result, ["published-print", "date-parts", 0, 0], "")
            journal = get_json_value(result, ["container-title", 0], "")

            url = result.get("URL")
            publisher = result.get("publisher")
            ENTRYTYPE = result.get("type")
            volume = result.get("volume")
            number = result.get("issue")
            # pages = db.Column(db.String)

            ID = title.split()[1]+doi.replace("/","").replace(".","")

        except Exception:
            e = traceback.format_exc()
            print("ERROR:", e)
            return f"Couldn't receive required metadata of {doi}"

        # Create the session
        session = db.session()
        if title == "" or author == "":
            return f"Couldn't receive required metadata of {doi}"
        elif len(list(session.query(Article).filter(Article.ID == ID))) > 0:
            return f"Error:\n\n{title} already exists in the database."

        date_str_pretty = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str_zot = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M%:SZ")

        new_art = Article(title=title, url=url, publisher=publisher, ID=ID, ENTRYTYPE=ENTRYTYPE, 
                        author=author, authorlast=authorlast, year=year, doi=doi, journal=journal, publication=journal,
                        volume=volume, number=number, icon="article", date_added = date_str_zot, 
                        date_modified = date_str_zot, date_added_pretty = date_str_pretty, date_modified_pretty = date_str_pretty, 
                        date_last_zotero_sync = "",)
        session.add(new_art)
        session.commit()
        session.close()

        return f"Added article to the Database. \n\nTitle: {title}\nDOI: {doi}"

if __name__ == "__main__":
    doi = "10.1007/978-3-319-69626-3"
    print(add_item(doi))