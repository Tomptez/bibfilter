from pdfminer.high_level import extract_text_to_fp
from pdfminer.high_level import extract_text
import sys

if sys.version_info > (3, 0):
    from io import StringIO
else:
    from io import BytesIO as StringIO
from pdfminer.layout import LAParams
filex = open("text.html", "w") 
#filex = StringIO()

pdfpath = '/home/minze/Programming/Projects/LitFilter_Repo/tools/cruces.pdf'

with open(pdfpath, 'rb') as fin:
    extract_text_to_fp(fin, filex, laparams=LAParams(), output_type='html', codec=None)
filex.seek(0) 
text = extract_text(pdfpath)

filex.close()