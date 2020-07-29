# Bibfilter
A Searchable Literature database interface

The Backend is using flask.
The front-end, which can be found under templates/main.html is being served from flask but is written in plain html/css and javascript so it can be used without flask.

![Screenshot](/img/Screenshot.png?raw=true "Screenshot")

## How to run the application on your local computer

First make sure you have [git](https://github.com/git-for-windows/git/releases/latest), `bash` (which is comes with git) and the version of python that is specified in the runtime.txt [here]https://www.python.org/downloads/) (and `pip` which will be installed together with python on windows) installed.
You will also need [PostgreSQL](https://www.postgresql.org/download/) to create the database.

Next, clone the repository to your local machine from your (git) bash terminal

    git clone https://gitlab.com/mx.tom/bibfilter.git

and then open the cloned directory

    cd bibfilter

The next step is to create a virtual environment and install all the required modules using `pipenv`.
First make sure you have `pipenv` installed by running. 

    pip install pipenv

After that we initiate the virtual environment and install all required modules by running
This can take a while.

    pipenv install

To use the application, you will also need to create a `PostgreSQL` Database called bibfilter and install an extension called unaccent.
This is done by typing in you `command line cmd` (this may or may not work in git bash)

    psql -U postgres

Or if that not works the exact filepath of your postgres installation

    "C:\Program Files\PostgreSQL\12\bin\psql.exe" -U postgres
 
 To create the database you type

    CREATE DATABASE bibfilter;

Then you can select the database and install the unaccent extension

    \c bibfilter;
    CREATE EXTENSION unaccent;

Before we can start the application, we need to set our environment variables.
To do so, create a new file in the main directory (in which the Pipfile sits) called `.env` where you define the environment variables which we will use in the project.
To create it type we will use the terminal editor `nano`. In your bash terminal type

    nano .env

and type (or paste) in the following variables

    DATABASE_URL = "postgresql://postgres:mypassword@localhost/bibfilter"
    APP_USERNAME = "username"
    APP_PASSWORD = "password"
    LIBRARY_ID = "2364338"
    COLLECTION_ID = "VIZDZ4PX"
    SUGGEST_LITERATURE_URL="https://duckduckgo.com"

You can change the values of `APP_USERNAME` and `APP_PASSWORD` to whatever you like. They will be used for the login for the `/admin` page.
`LIBRARY_ID` and `COLLECTION_ID` should reflect the respective ID of your zotero Library and collection. You can retrieve these IDs from the adress field in your browser if you open the collection at zotero.org in your browser. Note that it has to be a public library, otherwise you also need to use an API-Key which this application does not yet account for.
`SUGGEST_LITERATURE_URL` should be the URL to a page where users can suggest articles to add.

You then change `DATABASE_URL` replacing `myusername` and `mypassword` with your actual username/password

You can now close the `nano` editor by hitting Ctr+X and then typing `Y` and then `Enter` to save the file


Then you can activate the environment via

    pipenv shell

You could now already open the application but it will not show any articles because we have no database yet.
To create the database you need run update_library.py

    python update_library.py

If this doesn't print anything you may need to close it forcefully with `Ctrl + C`.
If there's any errors, there is probably an issue with your postgreql setup.
If not, you have successfully setup the database and can now start the application with

    python app.py

In you browser you can now find the page at the URL http://127.0.0.1:5000/ 
If you want to close the server you can hit `Ctr+C`

If your are finished you can close the virtual environment by typing 

    exit

or just close the terminal.

## Normal Usage

After the initial setup when you want to start the application you should first open the repository folder in your bash terminal.

Then you can check whether there have been andy updates in the gitlab repository and if there is, download them by running

    git pull

to start the application, you always need to launch the virtual environment first

    pipenv shell

and then you can run the flask app with

    python app.py