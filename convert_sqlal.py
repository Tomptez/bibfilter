from time import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from backend import Article, db
import math

def Load_Data(file_name):
    data = pd.read_csv('bibliography.csv', sep=',',header=1)
    return data.values.tolist()

def create_db_from_csv():
    t = time()

    #Create the database
    db.create_all()

    #Create the session
    session = db.session()

    try:
        file_name = "bibliography.csv" 
        data = Load_Data(file_name) 

        csv_bib_pattern = {"journalArticle": "article", "book": "book", "conferencePaper": "inproceedings", "manuscript": "Article", "bookSection": "book", "webpage": "inproceedings"}
        #techreport?
        #misc?
        #webpage
        #booksection

        for row in data:
            record = Article(**{
                "ID" : row[0],
                "ENTRYTYPE" : csv_bib_pattern[row[1]],
                "title" : row[4],
                "author" : row[3],
                "year" : int(row[2]) if not math.isnan(row[2]) else row[2],
                "journal" : row[5],
                "abstract": row[10],
                "doi" : row[8],
                "pages" : row[15],
                "volume" : row[18],
                "number" : row[17],
                "tags" : row[39]
            })
            #month??
            session.add(record) #Add all the records

        session.commit() #Attempt to commit all the records
    except Exception as e:
        print(e)
        session.rollback() #Rollback the changes on error
    finally:
        session.close() #Close the connection
    print("Time elapsed: " + str(time() - t) + " s.") #0.091s

if __name__ == "__main__":
    create_db_from_csv()