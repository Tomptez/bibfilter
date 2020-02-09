# Bibfilter
A Searchable Literature database interface

The Backend is using flask.
The front-end, which can be found under templates/main.html is being served from flask but is written in plain html/css and javascript so it can be used without flask.

![Screenshot](/img/Screenshot.png?raw=true "Screenshot")

## How to run the application on your local computer

First make sure you have [git](https://github.com/git-for-windows/git/releases/latest), `bash` (which is comes with git) and Version 3.8.1 of [python](https://www.python.org/downloads/release/python-381/) (and `pip` which will be installed together with python on windows) installed.

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

Before we can start the application, we need to set our environment variables.
To do so, create a new file in the main directory (in which the Pipfile sits) called `.env` where you define the environment variables which we will use in the project.
To create it type we will use the terminal editor `nano`. In your bash terminal type

    nano .env

and type (or paste) in the following variables

    DATABASE_URL = "sqlite:///mydatabase.db"
    APP_USERNAME = "username"
    APP_PASSWORD = "password"

You can change the values of `APP_USERNAME` and `APP_PASSWORD` to whatever you like. They will be used for the login for the `/admin` page.

You can now close the `nano` editor by hitting Ctr+X and then typing `Y` and then `Enter` to save the file


>**Optional:**
> -----------
>For testing you can leave the `DATABASE_URL` untouched (it will use a simple sqlite3 database). For serious development and actual production it would be best to first install and setup [PostgreSQL](https://www.postgresql.org/download/) and create a new Database called bibfilter.
>You can then change `DATABASE_URL` to the following value (replacing `myusername` and `mypassword` with your actual username/password and `bibfilter` with whatever you called your database) 

>    `DATABASE_URL = "postgresql://myusername:mypassword@localhost/bibfilter"`


Then you can activate the environment via

    pipenv shell

You could now already open the application but it will not show any articles because we have no database yet.
To create the database you need to export a .csv file from zotero, put it in the folder of the repository (same as the `Pipfile`) with the name `bibliography.csv` and run

    python tools/convert_sqal.py

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