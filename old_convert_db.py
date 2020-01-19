import csv
import sqlite3
import time, datetime, random

def create_table():
    c.execute("""CREATE TABLE IF NOT EXISTS literature(
        key TEXT,
        ltype TEXT,
        year INTEGER,
        author TEXT,
        title TEXT,
        publication TEXT,
        doi TEXT,
        pages REAL,
        issue TEXT,
        volume TEXT,
        tags TEXT
    )""")
conn = sqlite3.connect("bib.db")
c = conn.cursor()
create_table()

origFile = open("bibliography.csv")
csvObj  = csv.reader(origFile)

iterdb = iter(csvObj)
next(iterdb)

for row in iterdb:
    key = row[0]
    ltype = row[1]
    if row[2] != "":
        year = int(row[2])
    else:
        year = ""
    Author = row[3]
    Title = row[4]
    Publication = row[5]
    DOI = row[8]
    Pages = row[15]
    Issue = row[17]
    Volume = row[18]
    Tags = row[39]
    
    c.execute("INSERT INTO literature (key, ltype, year, author, title, publication, doi, pages, issue, volume, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (key, ltype, year, Author, Title, Publication, DOI, Pages, Issue, Volume, Tags))
    conn.commit()

c.close()
conn.close()