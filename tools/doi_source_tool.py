import csv
import requests
import os
from pprint import pprint

# file which will be checked
filename = '../bibliography.csv'

doi_agency = []
noResult={}
noDOI = []

cnt=0
totallen = 0
ndoi=0
ydoi=0

totallen = sum(1 for row in csv.reader( open(filename) ) )

# function to clear the terminal
def cls():
    os.system('cls' if os.name=='nt' else 'clear')

with open(filename, newline='') as csvfile:
    literature = csv.reader(csvfile, delimiter=',')
    literature.__next__()
    
    for row in literature:

        # Clearing terminal and measuring progress
        cls()
        cnt+=1
        print("Checking DOIs...")
        print(f"Progress: {format(cnt/totallen*100, '.1f')}%")

        if row[8] != "":
            doi = row[8]
            r = requests.get(f"https://api.crossref.org/works/{doi}/agency")

            if r.text == "Resource not found.":
                # record dois and titles which couldn't be identified
                noResult[doi] = row[4]
            
            else:
                result = r.json()
                agency = result["message"]["agency"]["label"]
                
                if agency not in doi_agency:
                    doi_agency.append(agency)
            ydoi += 1
        else:
            noDOI.append(row[4])
            ndoi += 1

cls()
print(f"Finished.\n {ydoi+ndoi} articles. {ydoi} with DOI and {ndoi} without DOI")
print(f"CSV includes DOIs from the following agencies: {doi_agency}\n")
print(f"Wasn't able to resolve the following DOIs:")
pprint(noResult)
print("\n Following articles don't have a DOI:")
pprint(noDOI)