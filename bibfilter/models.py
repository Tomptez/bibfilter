# In this file the Article Class is declared which defines how the articles are saved in the database
# Also the schemas are declared which define how the articles can be retrieved by the application in routes.py

from bibfilter import db, ma
from marshmallow import pre_dump, post_dump, Schema
import json

## Define Article Class
class Article(db.Model):
    __tablename__ = "Article"
    #__table_args__ = {'sqlite_autoincrement': True}
    
    # Define the name of columns and their attributes using SQLAlchemy:   
    # The naming of the collumns tries to follow the bibtex naming scheme https://www.bibtex.com/e/entry-types/
    dbid = db.Column(db.Integer, primary_key=True, nullable=False, index=True) 
    ID = db.Column(db.String)
    ENTRYTYPE = db.Column(db.String)
    title = db.Column(db.String)
    author = db.Column(db.String)
    authorlast = db.Column(db.String)
    year = db.Column(db.String)
    journal = db.Column(db.String)
    publication = db.Column(db.String)
    booktitle = db.Column(db.String)
    isbn = db.Column(db.String)
    issn = db.Column(db.String)
    doi = db.Column(db.String)
    pages = db.Column(db.String)
    volume = db.Column(db.String)
    number = db.Column(db.String)
    tags = db.Column(db.String)
    icon = db.Column(db.String)
    notes = db.Column(db.String)
    abstract = db.Column(db.String)
    editor = db.Column(db.String)
    tags_man = db.Column(db.String)
    tags_auto = db.Column(db.String)
    extra = db.Column(db.String)
    journal_abbrev = db.Column(db.String)
    address = db.Column(db.String)
    institution = db.Column(db.String)
    publisher = db.Column(db.String)
    language = db.Column(db.String)
    url = db.Column(db.String)
    articleFullText = db.Column(db.Text)
    contentChecked = db.Column(db.Boolean)
    elasticIndexed = db.Column(db.Boolean)
    references = db.Column(db.String)
    searchIndex = db.Column(db.String)
    date_added = db.Column(db.String)
    date_modified = db.Column(db.String)
    date_last_zotero_sync = db.Column(db.String)
    date_modified_pretty = db.Column(db.String)
    date_added_pretty = db.Column(db.String)
    
class BibliographySchema(ma.Schema):
    SKIP_VALUES = set([None, "NaN", "", "None"])

    # don't include NULL or "NaN" values in output JSON
    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items() if value not in self.SKIP_VALUES
        }

    class Meta:
        fields = ("address", "title", "author","ID", "pages", "ENTRYTYPE", "year", "publisher", "abstract", "volume", "institution", "number", "language", "journal", "booktitle", "url", "doi", "issn", "isbn")