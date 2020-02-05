# In this file the Article Class is declared which defines how the articles are saved in the database
# Also the schemas are declared which define how the articles can be retrieved by the application in routes.py

from bibfilter import db, ma
from marshmallow import pre_dump, post_dump, Schema

## Define Article Class
class Article(db.Model):
    __tablename__ = "Article"
    #__table_args__ = {'sqlite_autoincrement': True}
    
    #tell SQLAlchemy the name of column and its attributes:    
    dbid = db.Column(db.Integer, primary_key=True, nullable=False) 
    ID = db.Column(db.String)
    ENTRYTYPE = db.Column(db.String)
    title = db.Column(db.String)
    author = db.Column(db.String)
    year = db.Column(db.String)
    journal = db.Column(db.String)
    doi = db.Column(db.String)
    pages = db.Column(db.String)
    volume = db.Column(db.String)
    number = db.Column(db.String)
    tags = db.Column(db.String)
    abstract = db.Column(db.String)

    # needed?
    # def __init__(self, name, description, price, qty):
    #     self.name = name
    #     self.description = description
    #     self.price = price
    #     self.qty = qty

# Create DB / already done previously
# db.create_all()

# Article Schema
class ArticleSchema(ma.Schema):

    class Meta:
        fields = ("author","year", "title", "journal", "doi")
        ordered = True

class ArticleSchemaAdmin(ma.Schema):

    class Meta:
        fields = ("ID","author","year", "title", "journal", "doi")
        ordered = True

class BibliographySchema(ma.Schema):
    SKIP_VALUES = set([None, "NaN"])

    # don't include NULL or "NaN" values in output JSON
    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items() if value not in self.SKIP_VALUES
        }

    class Meta:
        fields = ("title", "author","ID", "ENTRYTYPE", "year", "abstract", "volume", "number", "journal", "doi")