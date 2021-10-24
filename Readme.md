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
To do so, we need new file in the main directory (in which the Pipfile sits) called `.env` where you define the environment variables which we will use in the project. There is a sample .env file we can use as a template.
Let's copy it as our real .env file and edit it. I will use the terminal editor `nano`. In your bash terminal type

    cp sample.env .env
    nano .env

You can change the values of `APP_USERNAME` and `APP_PASSWORD` to whatever you like. They will be used for the login for the `/admin` page.
`LIBRARY_ID` and `COLLECTION_ID` should reflect the respective ID of your zotero Library and collection. You can retrieve these IDs from the adress field in your browser if you open the collection at zotero.org in your browser. Note that it has to be a public library, otherwise you also need to use an API-Key which this application does not yet account for.
`SUGGEST_LITERATURE_URL` should be the URL to a page where users can suggest articles to add.

You then change `DATABASE_URL`, so that `postgres` is your PostgreSQL username (postgres is the standard user which you can keep) and `mypassword` with the password that you chose for that user during the install.

You can now close the `nano` editor by hitting Ctr+X and then typing `Y` and then `Enter` to save the file


Now, you can activate the environment via

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

***

## Deploying the application

There are several ways to put the bibfilter application online. 
Here we will explain how to get it online using dokku.

***

### 1. Setting up the application for dokku

This assumes you have got a running instance of dokku on your server.

First you need to create a new dokku application

    dokku apps:create my_application_name

Next, you need to install postgres on dokku, create a new database and link it to the newly created application

    sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git
    dokku postgres:create my_database_name
    dokku postgres:link my_database_name my_application_name

The next step is to connect to the SQL interface of the database, to add the extension unaccent, which is required by bifilter.

    dokku postgres:connect my_database_name
    CREATE EXTENSION unaccent;
    \c
    exit
    
    
After that you need to create the required environment variables. Of course you need to change it to the correct values. Note: This command is supposed to be one line not seperate lines.

    dokku config:set my_application_name APP_USERNAME=my_admin_name APP_PASSWORD=my_password LIBRARY_ID=my_public_zotero_library_id COLLECTION_ID=my_public_zotero_collection_id SUGGEST_LITERATURE_URL=url_of_form_where_one_can_suggest_an_article

Lastly we want to add the letsencrypt plugin to the application, so that our application runs on a secure connection

    sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
    dokku config:set --no-restart my_application_name DOKKU_LETSENCRYPT_EMAIL=example@email-adress.com
    dokku letsencrypt my_application_name

***

### 2. Updating the application remotely

After you have set up the aplication on the dokku instance, you can basically use it the way you use a regular git repository and easily add any changes.
On your local computer you want to add the server and application-name as a git repository

    git remote add some_name dokku@134.102.137.46:my_application_name

Change 'some_name' to whatever you like. Then you can easily push the application using git. 
You do however need to make sure that you have the right to push to dokku. For that you might need an SSH-Key, which possibly has to be added to the whitelist of the server as well as to the whitelist of dokku. Depending on the setup of the server you might also need to be connected to a specific network (for example via VPN).

    git push some_name master

If there are problems online you might want to read to logs of your running application
    
    dokku logs my_application_name --tail
