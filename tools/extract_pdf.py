import camelot
from PyPDF2 import PdfFileReader
from PIL import Image
from pdf2image import convert_from_path
import os

folder = os.environ["PDF_FOLDER"]
fileName = "engel"
filepath = os.path.join(folder,fileName+".pdf")

os.makedirs(os.path.join(folder,fileName),exist_ok=True)

pdfFile = PdfFileReader(open(filepath, 'rb'))
totalPages = pdfFile.getNumPages()

# Get document dimensions from page 1
pdfHeight = float(pdfFile.getPage(1).mediaBox[-1])
pdfWidth = float(pdfFile.getPage(1).mediaBox[-2])
imgHeight = float(convert_from_path(filepath, first_page=1, last_page=1)[0].size[-1])
imgWidth = float(convert_from_path(filepath, first_page=1, last_page=1)[0].size[-2])
factor = imgHeight / pdfHeight

tableCount = 0
for p in range(1,totalPages+1):

    tables = camelot.read_pdf(filepath, pages=str(p), flavor='stream')

    for eachTable in tables:
        if eachTable.shape[1] < 3:
            continue
        if eachTable.whitespace > 35:
            continue
        print(f"parsing: {eachTable.parsing_report}")
        tableCount += 1
        left = eachTable.cols[0][0] * factor - imgWidth / 15
        right = eachTable.cols[-1][1] * factor + imgWidth / 15
        top = (pdfHeight - eachTable.rows[0][1]) * factor - imgHeight / 20
        # make sure top isn't negative
        top = 0 if top < 0 else top
        bottom = (pdfHeight - eachTable.rows[-1][0]) * factor + imgHeight / 10 
        # make sure bottom isn't less than the page height
        bottom = imgHeight if bottom > imgHeight else bottom

        #eachTable.to_html('/home/minze/Programming/Projects/LitFilter_Repo/tools/table.csv')

        
        page = convert_from_path(filepath, first_page=p, last_page=p)[0]

        # Handle horizontal format
        if right > imgWidth:
            page = page.rotate(-90, expand=True)
            #page.save(os.path.join(folder,fileName,f"{p:02d}_Table_{tableCount:02d}_ENTIRE.jpg"), 'jpeg')
            
            imgHeight, imgWidth = page.size
            left = eachTable.cols[0][0] * factor - imgWidth / 20
            right = eachTable.cols[-1][1] * factor + imgWidth / 20
            top = (pdfWidth - eachTable.rows[0][0]) * factor - imgHeight / 25
            # make sure top isn't negative
            top = 0 if top < 0 else top
            bottom = (pdfWidth - eachTable.rows[-1][1]) * factor + imgHeight / 17
            # make sure bottom isn't less than the page height
            bottom = imgHeight if bottom > imgHeight else bottom
        
        page = page.crop((left, top, right, bottom))

        page.save(os.path.join(folder,fileName,f"{p:02d}_Table_{tableCount:02d}_shp{eachTable.shape[1]}_wht_{eachTable.whitespace}.jpg"), 'jpeg')

            
# TODO: page 29 Table 2: Implied Gini coefficient and income rank
# todo change eachTable.rows?
# Todo: If certain percent of page take the entire page