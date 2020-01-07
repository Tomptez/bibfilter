from time import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from backend import Article, db

def Load_Data(file_name):
    data = pd.read_csv('OpinionPolicy.csv', sep=',',header=1)
    return data.values.tolist()

def create_db_from_csv():
    t = time()

    #Create the database
    db.create_all()

    #Create the session
    session = db.session()

    try:
        file_name = "OpinionPolicy.csv" #sample CSV file used:  http://www.google.com/finance/historical?q=NYSE%3AT&ei=W4ikVam8LYWjmAGjhoHACw&output=csv
        data = Load_Data(file_name) 
    
        for row in data:
            record = Article(**{
                "key" : row[0],
                "ltype" : row[1],
                "title" : row[4],
                "year" : row[2],
                "author" : row[3],
                "publication" : row[5],
                "doi" : row[8],
                "pages" : row[15],
                "issue" : row[17],
                "volume" : row[18],
                "tags" : row[39]
            })
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