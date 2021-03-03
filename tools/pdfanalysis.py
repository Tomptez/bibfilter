from pdfminer.high_level import extract_text_to_fp
from pdfminer.high_level import extract_text
import sys
import os
from dotenv import load_dotenv
load_dotenv()

if sys.version_info > (3, 0):
    from io import StringIO
else:
    from io import BytesIO as StringIO
from pdfminer.layout import LAParams


filex = open(filePathExport, "w") 

#filex = StringIO()

def pdfToText(pdfFile):
    with open(pdfPath, 'rb') as fin:
        extract_text_to_fp(fin, filex, laparams=LAParams(), output_type='text', codec=None)
    filex.seek(0) 
    text = extract_text(pdfPath)

    return result

if __name__ == "__main__":
    folder = os.environ["PDF_FOLDER"]
    fileName = "svallfors"
    pdfPath = os.path.join(folder,fileName+".pdf")
    filePathExport = os.path.join(folder,fileName+".txt")