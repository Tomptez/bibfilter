import pikepdf
from pdfminer.high_level import extract_text
import re

# with pikepdf.open('old1.pdf') as pdf:
#     num_pages = len(pdf.pages)
#     del pdf.pages[-1]
#     pdf.save('output.pdf')

l = extract_text("ocr2.pdf")
#print(l[2000:4000])

i = re.finditer('\Wr e f e r e n c e s|\nr e f e r e n c e s|\nreferences|\Wreferences', l.lower())
print(len(list(i)))