# Bibfilter
A Searchable Literature database interface

The Backend is using flask.
The front-end, which can be found under templates/main.html is being served from flask but is written in plain html/css and javascript so it can be used without flask.

![Screenshot](/img/Screenshot.png?raw=true "Screenshot")

## How to run the application on your local computer

First make sure you have `bash`, `python` (including `pip`) and `git` installed.

Next, clone the repository to your local machine from your bash terminal

    git clone https://gitlab.com/mx.tom/bibfilter.git

and then open the cloned directory

    cd bibfilter

The next step is to create a virtual environment and install all the required modules using `pipenv`.
First make sure you have `pipenv` installed by running

    pip install pipenv

After that we initiate the virtual environment and install all required modules by running

    pipenv install --dev

Before we can start the application, we need to set our environment variables.
To do so, create a new file in the main directory (in which the Pipfile sits) called `.env` where you define the environment variables which we will use in the project.
The `.env` file should look something like this:

    DATABASE_URL = "sqlite:///mydatabase.db"
    APP_USERNAME = "username"
    APP_PASSWORD = "password"

You can change the values of `APP_USERNAME` and `APP_PASSWORD` to whatever you like. They will be used for the login for the `/admin` page.

For testing you can leave the `DATABASE_URL` untouched (it will use a simple sqlite3 database). For serious development and actual production it would be best to first install and setup [PostgreSQL](https://www.postgresql.org/download/) and create a new Database called bibfilter.
You can then change `DATABASE_URL` to the following value (replacing `myusername` and `mypassword` with your actual username/password and `bibfilter` with whatever you called your database)

    DATABASE_URL = "postgresql://myusername:mypassword@localhost/bibfilter"


Then you can activate the environment via

    pipenv shell

To create the database you should export a .csv file from zotero, put it in the `bibfilter` folder with the name `bibliography.csv` and run

    python tools/convert_sqal.py

If there's any errors, there is probably an issue with your postgreql setup.
If not, you have successfully setup the database and can now start the application with

    python backend.py

In you browser you can now find the page at the URL http://127.0.0.1:5000/ 