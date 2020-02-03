# Bibilter
A Searchable Literature Database Interface

The Backend is using flask.
The front-end, which can be found under templates/main.html is being served from flask but is written in plain html and js so it can be used without flask.

## How to run the application on your local computer

First make sure you have bash, python (including pip) and git installed.

Next, clone the repository to your local machine

    git clone https://gitlab.com/mx.tom/bibfilter.git

and then open the cloned directory

    cd bibfilter

The next step is to create a virtual environment and install all the required modules using pipenv.
First make sure you hav pipenv installed by running

    pip install pipenv

After that we initiate the virtual environment and install all required modules by running

    pipenv install --dev

Before we can start the application, we need to set needed environment variables.
To do so, in the directory create a new file called .env where you define the environment variables which we will use in the project.

As a database you can either use sqlite if you just want to have a look at the application for which you put a line in .env:

    DATABASE_URL = "sqlite:///mydatabase.db"

If you want to build the application for actual production it would be best to first install and setup [PostgreSQL](https://www.postgresql.org/download/) and create a new Database called bibfilter.
In your .env file you can then put the following line (replacing myusername and my username with your actual username and password and bibfilter to however you called your database)

    DATABASE_URL = "postgresql://myusername:mypassword@localhost/bibfilter"

For the login page within .env you also need to set. You can chage the values to whatever you like

    APP_USERNAME = "username"
    APP_PASSWORD = "password"

then you can activate the environment via
    
    pipenv shell

to create the database you should export a .csv file from zotero, put it in the bibfilter folder and running

    python convert_sqal.py

If there's any errors, there is probably an issue with your postgreql setup.
If not, you have successfully setup the database and can now start the application with

    python backend.app

In you browser you can now open the page under the URL http://127.0.0.1:5000/ 