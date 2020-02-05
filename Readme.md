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
To do so, create a new file in the main directory (bibfilter) called .env where you define the environment variables which we will use in the project.

As a database you can either use sqlite if you just want to have a look at the application for which you put a line in `.env`:

    DATABASE_URL = "sqlite:///mydatabase.db"

If you want to build the application for actual production it would be best to first install and setup [PostgreSQL](https://www.postgresql.org/download/) and create a new Database called bibfilter.
In your `.env` file you can then put the following line (replacing `myusername` and `mypassword` with your actual username/password and `bibfilter` with whatever you called your database)

    DATABASE_URL = "postgresql://myusername:mypassword@localhost/bibfilter"

For the admin page within we also need to set the admin username and password as an environment variable in `.env`. You can chage the values to whatever you like

    APP_USERNAME = "username"
    APP_PASSWORD = "password"

Then you can activate the environment via

    pipenv shell

To create the database you should export a .csv file from zotero, put it in the `bibfilter` folder with the name `bibliography.csv` and run

    python tools/convert_sqal.py

If there's any errors, there is probably an issue with your postgreql setup.
If not, you have successfully setup the database and can now start the application with

    python backend.py

In you browser you can now find the page at the URL http://127.0.0.1:5000/ 