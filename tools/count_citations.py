# Tool which analyses citation counts of articles in a zotero library via data from crossref
# Takes an exported zotero library as .csv file as input
# Saves the result in three .csv files: most_cited.csv, noDOI.csv and noURLupdated.csv

import csv
import requests
import os
from pprint import pprint
from collections import Counter
import time

# file which will be checked
filename = 'bibliography.csv'

doi_agency = []
noResult={}
dictNoDOI = {}
dictNoURL = {}
dictNoURLbook = {}
dictNoURLbutDOI = {}
crossrefdois = []
rankedarticles = {}

cnt=0
totallen = 0
nodoi=0
hasdoi=0
nojournal = 1

totallen = sum(1 for row in csv.reader( open(filename) ) )

# function to clear the terminal
def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def checkdois():
    global doi_agency, noResult, dictNoDOI, dictNoURL, dictNoURLbook, dictNoURLbutDOI, crossrefdois, cnt, totallen, nodoi, hasdoi, nojournal
    try:
        with open(filename, newline='') as csvfile:
            literature = csv.reader(csvfile, delimiter=',')
            literature.__next__()
            
            for row in literature:
                time.sleep(0.1)
                # Clearing terminal and measuring progress
                cls()
                cnt+=1
                print("Checking DOIs...")
                print(f"Progress: {format(cnt/totallen*100, '.1f')}%")

                if row[1] == "journalArticle":
                    if row[8] != "":
                        doi = row[8]
                        hasdoi += 1
                        r = requests.get(f"https://api.crossref.org/works/{doi}/agency")

                        if r.text == "Resource not found.":
                            # record dois and titles which couldn't be identified
                            noResult[doi] = row[4]
                        
                        else:
                            result = r.json()
                            agency = result["message"]["agency"]["label"]
                            
                            doi_agency.append(agency)
                            if agency == "Crossref":
                                crossrefdois.append(doi)

                    else:
                        dictNoDOI[row[4]] = row[3]
                        nodoi += 1

                    if row[9] == "":
                        if row[8] != "":
                            dictNoURLbutDOI[row[4]] = row[3]
                        else: 
                            dictNoURL[row[4]] = row[3]
                else:
                    nojournal += 1
                    if row[9] == "":
                        dictNoURLbook[row[4]] = row[3]

    except KeyboardInterrupt:
        pass

def getReferenceCount():
    rankedarticles = {}
    for doi in crossrefdois:
        time.sleep(0.1y)
        r = requests.get(f"https://api.crossref.org/works/{doi}")
        if r.text == "Resource not found.":
            print(f"{doi} not found")
            continue
        resultjson = r.json()
        result = resultjson["message"]
        
        refs = result.get("is-referenced-by-count", "")
        if result.get("title") != None and len(result.get("title")) > 0:
            title = result["title"][0]
        else:
            title = ""

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

        if refs in rankedarticles:
            rankedarticles[refs].append({"title":title, "author":author, "year":year, "doi":doi})
        else:
            rankedarticles[refs] = [{"title":title, "author":author, "year":year, "doi":doi}]

    return dict(sorted(rankedarticles.items(), reverse=True))


if __name__ == "__main__":
    checkdois()
    allentries = nojournal+hasdoi+nodoi
    cls()
    print(f"Finished.\n{allentries} Entries. {nojournal} entries which are no article. {hasdoi} articles with DOI and {nodoi} without DOI")
    print(f"Article Agencies: {Counter(doi_agency)}\n")

    countedArticles = getReferenceCount()
    with open('most_cited.csv', 'w', newline='') as outputFile:
        outputWriter = csv.writer(outputFile)
        outputWriter.writerow(["Entries", "Articles", "Other entries", "Article with DOI", "Articles without DOI","", "DOI Agencies"])
        outputWriter.writerow([allentries, hasdoi+nodoi, allentries-nojournal, hasdoi, nodoi,"", dict(Counter(doi_agency))])
        outputWriter.writerow([""])

        outputWriter.writerow(["Most cited articles:"])
        outputWriter.writerow(["References", "Author", "Title", "Year", "DOI"])
        c = 0

        for refs in list(countedArticles)[0:100]:
            for each in countedArticles[refs]:
                outputWriter.writerow([refs, each["author"], each["title"], each["year"], each["doi"]])
    
    with open('noDOI.csv', 'w', newline='') as outputFile:
        outputWriter = csv.writer(outputFile)
        outputWriter.writerow(["Author", "Title"])
        for title, author in dictNoDOI.items():
            outputWriter.writerow([author, title])
        
        outputWriter.writerow([""])
        outputWriter.writerow(["DOI with no result:"])
        outputWriter.writerow(["DOI", "Title"])
        for doi, title in noResult.items():
            outputWriter.writerow([doi, title])

    with open('noURLupdated.csv', 'w', newline='') as outputFile:
        outputWriter = csv.writer(outputFile)
        outputWriter.writerow(["Author", "Title"])
        for title, author in dictNoURL.items():
            outputWriter.writerow([author, title])
        
        outputWriter.writerow([""])
        outputWriter.writerow(["no URL but DOI:"])
        outputWriter.writerow(["Author", "Title"])
        for title, author in dictNoURLbutDOI.items():
            outputWriter.writerow([author, title])

        outputWriter.writerow([""])
        outputWriter.writerow(["Books"])
        outputWriter.writerow(["Author", "Title"])
        for title, author in dictNoURLbook.items():
            outputWriter.writerow([author, title])
