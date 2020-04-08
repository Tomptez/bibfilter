from time import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import math
import datetime
import traceback
import sys, os
sys.path.append(".")
# Old Syspath when the file was located somewhere different than the bibfilter directory
# from pathlib import Path
# parentDir = str(Path(os.path.realpath(__file__)).parent.parent)
# sys.path.append(parentDir)
from bibfilter import db
from bibfilter.models import Article

def Load_Data(file_name):
    data = pd.read_csv(file_name, sep=',',header=1)
    return data.values.tolist()

def create_db_from_csv(file_name):
    t = time()
    cnt_add, cnt_exist, cnt_err = 0, 0, 0

    #Create the database
    db.create_all()

    #Create the session
    session = db.session()

    try:
        data = Load_Data(file_name) 

        csv_bib_pattern = {"journalArticle": "article", "book": "book", "conferencePaper": "inproceedings", "manuscript": "Article", "bookSection": "book", "webpage": "inproceedings", "techreport": "article", "report": "article", "document": "misc", "thesis": "phdthesis"}

        # Skip already existing entries
        for row in data:
            try:
                if len(list(session.query(Article).filter(Article.ID == row[0]))) > 0:
                    cnt_exist += 1
                    continue

                record = Article(**{
                    "ID" : row[0],
                    "ENTRYTYPE" : csv_bib_pattern[row[1]],
                    "title" : row[4],
                    "author" : row[3],
                    "year" : int(row[2]) if not math.isnan(row[2]) else row[2],
                    # "journal" : row[5] if not str(row[5]) == "nan" else csv_bib_pattern[row[1]].title() if not str(csv_bib_pattern[row[1]]) == "nan" else "None",
                    "journal" : row[5] if not str(row[5]) == "nan" else "None",
                    "abstract": row[10],
                    "doi" : row[8],
                    "url" : row[9],
                    "pages" : row[15],
                    "volume" : row[18],
                    "publisher" : row[26],
                    "number" : row[17],
                    "tags" : row[39],
                    "_date_created" : datetime.datetime.now(),
                    "_date_created_str" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                #month??
                
                session.add(record) #Add all the records
                cnt_add += 1
            except Exception:
                e = traceback.format_exc()
                print(e)
                cnt_err += 1

        session.commit() #Attempt to commit all the records
    except Exception:
        e = traceback.format_exc()
        print(e)
        session.rollback() #Rollback the changes on error
    finally:
        session.close() #Close the connection
    
    print(f"Added {cnt_add} new Articles. {cnt_exist} Articles already existed in the database. {cnt_err} Articles couldn't be addded because of an error")
    print("Time elapsed: " + str(time() - t) + " s.") #0.091s
    return [cnt_add, cnt_exist, cnt_err]

if __name__ == "__main__":
    file_name = "bibliography.csv" 
    create_db_from_csv(file_name)