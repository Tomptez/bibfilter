from flask import Flask, render_template, url_for, request
from flask_table import Table, Col
import sqlite3
import sys
from wtforms import Form, IntegerField, StringField, validators
from psycopg2 import sql

app = Flask(__name__)

# Declare your table
class ItemTable(Table):
    thead_classes = ["table","thead-dark","sticky-top" ]
    classes = ["table", "table-hover", "table-striped", "ht-tm-element"]
    no_items = "No literature could be found"

    title = Col('Title')
    author = Col('Author')
    year = Col("year")
    
    ## saves the filter content to the table, so when we want to sort, we can recreate the table as well
    def get_urlatt(self, urlatt):
        self.title = urlatt["title"]
        self.timestart = urlatt["timestart"]
        self.until = urlatt["until"]
        self.author = urlatt["author"]
    

    allow_sort = True
    
    def get_tr_attrs(self, item):
        return {'class': 'lit'}
    
    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = "desc"
        else:
            direction = "asc"
        return url_for("home", sort=col_key, direction=direction, title=self.title, timestart=self.timestart, until=self.until, author=self.author)

class MyForm(Form):
    title = StringField('Title: ')
    author = StringField('Author: ')
    timestart = IntegerField('From: ')
    until = IntegerField('Until: ')

app.config["SECRET_KEY"] = "'242ee0fe4f0762eba895e9832724975286fb'"

@app.route("/", methods=["POST", "GET"])
@app.route("/home", methods=["POST", "GET"])
def home():
    

    urlatt = {
            "item":request.args.get('sort', 'year'),
            "direction": request.args.get("direction", "desc"),
            "title":request.args.get("title",""), 
            "author":request.args.get("author", ""),
            "timestart":request.args.get("timestart", ""), 
            "until":request.args.get("until", ""),
            "cnt":request.args.get('cnt', 0)
    }
    form = MyForm()
    form.title.default = urlatt["title"]
    form.author.default = urlatt["author"]
    form.timestart.default = urlatt["timestart"]
    form.until.default = urlatt["until"]
    form.process()

    item = "year" if urlatt["item"] == None else urlatt["item"] 
    direction = "asc" if urlatt["direction"] == None else urlatt["direction"]
    timestart = 0 if urlatt["timestart"] == None or urlatt["timestart"] == "" else int(urlatt["timestart"])
    until = 2100 if urlatt["until"] == None or urlatt["until"] == "" else int(urlatt["until"])
    title = [""] if urlatt["title"] == None else urlatt["title"].split(" ")
    author = [""] if urlatt["author"] == None else urlatt["author"].split(" ")

    isinTitle = "("
    for i in range(0,len(title)):
        isinTitle += f" title LIKE '%{title[i]}%' "
        if i +1 < len(title):
            isinTitle += "OR"
    isinTitle += ")"

    isinAuthor = "("
    for i in range(0,len(author)):
        isinAuthor += f" author LIKE '%{author[i]}%' "
        if i +1 < len(author):
            isinAuthor += "OR"
    isinAuthor += ")"

    is_reversed = urlatt["direction"] == "desc"
    conn = sqlite3.connect("bib.db")
    c = conn.cursor()


    # ToDo: protect against SQL-injection
    
    c.execute(f"""
    SELECT
        title, author, year 
    FROM 
        literature 
    WHERE 
        {isinTitle}
    AND 
        {isinAuthor}
    AND 
        year >= {timestart}
    AND 
        year <= {until}
    ORDER BY 
        {item} {direction.upper()}
    """)
    
    
    items = []
    for each in c.fetchall():
        items.append(dict(title=each[0], author=each[1], year=each[2]))
    table = ItemTable(items, sort_by=urlatt["item"], sort_reverse=is_reversed)
    # needed if table will be sorted at later time
    table.get_urlatt(urlatt)

    # count results
    command = f"""SELECT COUNT(title) FROM literature 
    WHERE {isinTitle} 
    AND {isinAuthor}
    AND year >= {timestart}  AND year <= {until}
    """
    c.execute(command)
    counter = c.fetchall()[0][0]
    urlatt["cnt"]= counter

    return render_template('home.html', form=form, content=table, urlatt=urlatt)

@app.route("/test", methods=["POST", "GET"])
def test():
    return render_template("test.html")

if __name__ == '__main__':
    app.run(debug=True)