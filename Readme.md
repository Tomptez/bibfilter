# Bibfilter

A Searchable Literature database web-interface for use with [Zotero](https://www.zotero.org/). 

It is developed using python and flask and can easily be deployed using [Dokku](https://dokku.com/).

For advanced searching features, [Elasticsearch](https://www.elastic.co/) can be used as a backend for searching.

![Screenshot](/img/Screenshot.png?raw=true "Screenshot")

## Background

It was developed specifically as part of the German Science Foundation funded project "The Reciprocal Relationship of Public Opinion and Social Policy" ([BR 5423/2-1](https://www.socium.uni-bremen.de/projects/?proj=614)). As such it was designed to provide an interactive tool for searching through all known literature in the specific subject area of public preferences for social policy and redistribution. However, it can easily be deployed with any literature library contained in a Zotero folder. A current version of bibfilter is used on the webpage of the [_Social Policy Preferences Network_](https://sites.google.com/view/sppn/bibliography) with the server hosted by the University of Bremen's [Bremen International Graduate School of Social Sciences](https://www.bigsss-bremen.de/). 

## Table of contents

1. [How to run the application on your local computer](#howto)
   
   [1.1 Prerequisites](#pre)
   
   [1.2 Installation](#installation)
   
   [1.3 Setting up environment variables](#env-var)
   
   [1.4 Normal Usage](#normal)

2. [Deploying the application](#deploy)
   
   [2.1 Setting up the application for dokku](#setup)
   
   [2.2 Updating the application remotely](#update)
   
   [2.3 Restarting the Application](#restart)

<a id="howto"></a>

## How to run the application on your local computer

<a id="pre"></a>

### Prerequisites

First make sure you have installed [git](https://github.com/git-for-windows/git/releases/latest), `Bash` (which comes with git on windows) and [Python](https://www.python.org/downloads/) version 3.9 or newer. You also need `pip` which will usually be installed together with python on Windows and Mac.
You will also need [PostgreSQL](https://www.postgresql.org/download/) to create the database. For Mac, we recommend you to use [Postgres.app](https://postgresapp.com). Depending on your system you may need [Microsoft Visual C++](https://visualstudio.microsoft.com/visual-cpp-build-tools/) installed and/or updated.

#### Elasticsearch for testing
Optionally, if you want to make use of advanced searching capabilities and search through the fulltext of the articles, [Elasticsearch](https://github.com/elastic/elasticsearch) needs to be installed - [Windows instructions here](https://www.elastic.co/guide/en/elasticsearch/reference/current/zip-windows.html).

When using docker this can be done as follows (note that this installation is not a sufficient for production and should only be used for testing)

    docker pull docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    docker volume create es-data

Now you can run elasticsearch as follows

    docker run -p 127.0.0.1:9200:9200 -p 127.0.0.1:9300:9300 -e "discovery.type=single-node" -e "xpack.security.enabled=false" --mount source=es-data,target=/usr/share/elasticsearch/data docker.elastic.co/elasticsearch/elasticsearch:8.8.0


<a id="installation"></a>

### Installation

Next, clone the repository to your local machine from your (git) bash terminal

    git clone https://github.com/Tomptez/bibfilter.git

and then open the cloned directory

    cd bibfilter

The next step is to create a virtual environment and install all the required modules using `venv`.
First, create a new virtual environment called 'venv' and activate it. 

    python -m venv venv

MacOS and Linux

    source venv/bin/activate

Windows

    venv\Scripts\activate.bat
    
Note that "python" or "py" commands may not run. If this is the case it is likely due to one or both of the following. (A) Windows 10 default launching location for Python (and every app) is the AppData folder. So it tries to launch an app. If you installed Python from Python.org (recommended) rather than the Microsoft Store (not recommended) then you need to change the computer's environment variables. This is done by clicking the 'start' button which is now the Windows icon in the lower left corner, and type "Env". What should pop up is "Edit the system environment variables". Click on this, then click "EnvironmentVariables...", then select "Path" under "User variables" in the list and click "Edit". Create a "New" path and put in the exact directory where Python was installed (e.g. C:\Python311). then select this and click "Move Up" until it is at the top. (B) You need to turn of auto app launching. Go to "Apps" and click "App execution aliases". Turn off all App Installers associated with Python (there are usually two of them). After doing this, restart and try again.


You should now see (venv) in your command line. Now we need to make sure pip is up to date

    pip install --upgrade pip

After that we initiate the virtual environment by installing the exact packages and versions needed. This can take a while.

    pip install -r requirements.txt

To use the application, you will also need to create a `PostgreSQL` Database called bibfilter and install an extension called unaccent.
This is done by typing in your `command line cmd` (this may or may not work in git bash)

    psql -U postgres

If that does not work, you can specify the exact filepath of your postgres installation (for example)

    "C:\Program Files\PostgreSQL\12\bin\psql.exe" -U postgres
    
Or, you can follow the instructions above for setting Python PATH in your Windows Environment, and add two new lines that 
point directly at the \bin and \lib directories in your PostgreSQL\[version#]\ folder

For Mac, this is done by typing in your git bash 

    psql -d postgres

 To create the database you type

    CREATE DATABASE bibfilter;

Then you can select the database and install the unaccent extension

    \c bibfilter;
    CREATE EXTENSION unaccent;

<a id="env-var"></a>

### Setting up environment variables

---
**NOTE**

To open bash in Windows close the cmd window and type "bash" into the start icon. Then make sure to navigate to the bibfilter folder, e.g. by typing

    cd C:\bibfilter

---


Before we can start the application, we need to set our environment variables.

To do so, we need a new file in the main directory (in which the Pipfile sits) called `.env` where you define the environment variables which we will use in the project. There is an example.env file we can use as a template.
Let's copy it as our real .env file and edit it. We will use the terminal editor `nano`. In your bash terminal type

    cp example.env .env
    nano .env
    
You can change `DATABASE_URL`, so that `postgres` is your PostgreSQL username (postgres is the standard user which you can keep) and `mypassword` with the password that you chose for that user during the install.

For macOS, you can change `DATABASE_URL`, so that it matches with the connection URL that PostgreSQL server provides for the database bibfilter. This URL requires you to input the username `postgres` and the password you specified. In Windows for example this looks like ` "postgresql://postgres:[password you set previously]@localhost:5432/bibfilter"`. If you start your password with '@' it will not work!

You can then change the values of `APP_USERNAME` and `APP_PASSWORD` to whatever you like. They will be used for the login for the `/admin` page.
`LIBRARY_ID` and `COLLECTION_ID` should reflect the respective ID of your zotero Library and collection. You can retrieve these IDs from the adress field in your browser if you open the collection at zotero.org in your browser. Note that it has to be a public library, otherwise you also need to use an API-Key which this application does not yet account for.
`SUGGEST_LITERATURE_URL` should be the URL to a page where users can suggest articles to add.

If you also want to use elasticsearch, depending on your setup you might need to change the URL of your elasticsearch instance `ELASTICSEARCH_URL`, or might need to specify `ELASTICSEARCH_PASSWORD` or `ELASTICSEARCH_USERNAME`. In that case, uncomment and change these lines accordingly.

You can now close the `nano` editor by hitting Ctr+X and then typing `Y` and then `Enter` to save the file.

You could now already open the application but it will not show any articles because we have no database yet.
To create the database you need run update_library.py once

    python update_library.py
    
Note: if you are using a more recent version of Python3 you might have to update some of the requirements (schedule, pytz, etc), just type `pip install [name of package]`

If you see a report (`Summary of synchronization with Zotero`), you can stop the process using `Ctrl + C`.
If there's any errors, there is probably an issue with your postgreql setup.
If not, you have successfully setup the database and can now start the application with

    python app.py

In you browser, you can now find the page at the URL http://127.0.0.1:5000/ 
If you want to close the server, you can hit `Ctr+C`

If your are finished, you can close the virtual environment by typing 

    deactivate

or just close the terminal.

<a id="normal"></a>

### Normal Usage

After the initial setup when you want to start the application, you should first open the repository folder in your bash terminal.

Then you can check whether there have been any updates in the gitlab repository and if there is, download them by running

    git pull

to start the application, you always need to launch the virtual environment first

    source venv/bin/activate

After that, you should see a `(venv)` in your command prompt which indicates the venv is active. You can exit the venv by typing `exit`

After activating the virtual environment, you can start the flask app with

    python app.py

***
<a id="deploy"></a>
## Deploying the application

There are several ways to put the bibfilter application online. 
Here we will explain how to get bibfilter running on a servere using dokku.

<a id="setup"></a>
### 1. Setting up the application for dokku

This assumes you have got a running instance of dokku on your server.

First, you need to create a new dokku application

    dokku apps:create my_application_name

Next, you need to install postgres on dokku and create a new database.
Afterwards you need to connect to the SQL interface, add the extension unaccent and then link the database to the application.

    sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git
    dokku postgres:create my_database_name
    dokku postgres:connect my_database_name
    CREATE EXTENSION unaccent;
    exit
    dokku postgres:link my_database_name my_application_name

For flask_limiter, you also need to create a memcached service as a backend and link it to the application

    sudo dokku plugin:install https://github.com/dokku/dokku-memcached.git memcached
    dokku memcached:create memcached_backend
    dokku memcached:link memcached_backend my_application_name

After that, you need to create the required environment variables. Of course you need to change it to the correct values. Note: This command is supposed to be one line not seperate lines.

    dokku config:set my_application_name APP_USERNAME=my_admin_name APP_PASSWORD=my_password LIBRARY_ID=my_public_zotero_library_id COLLECTION_ID=my_public_zotero_collection_id SUGGEST_LITERATURE_URL=url_of_form_where_one_can_suggest_an_article SHOW_SEARCH_QUOTES = "TRUE" USE_ELASTICSEARCH = "FALSE"

Lastly, we want to add the letsencrypt plugin to the application, so that our application runs on a secure connection

    sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
    dokku config:set --no-restart my_application_name DOKKU_LETSENCRYPT_EMAIL=example@email-adress.com
    dokku letsencrypt my_application_name
    
We also want to setup letsencrypt to automatically update

With dokku it easy to create and renew the certificates. The documentation can be found  here

To renew all certificates once, just log into the server and run

`dokku letsencrypt:auto-renew`

To make dokku renew certificates automatically, run

`dokku letsencrypt:cron-job --add`

***
<a id="update"></a>
### 2. Updating the application remotely

After you have set up the aplication on the dokku instance, you can basically use it the way you use a regular git repository and easily add any changes.
On your local computer you want to add the server and application-name as a git repository

    git remote add remote_name dokku@IP.ADRE.SS:my_application_name

Change 'remote_name' to whatever you like. Then you can easily push the application using git. 
You do however need to make sure that you have the right to push to dokku. For that, you might need an SSH-Key, which possibly has to be added to the whitelist of the server as well as to the whitelist of dokku. Depending on the setup of the server you might also need to be connected to a specific network (for example via VPN).

    git push remote_name main

If there are problems online, you might want to read to logs of your running application

<a id="restart"></a>
### 3. Restarting the Application

In case of issues a restart may be necessary

1. Login to the server using SSH key. 
   - Open command prompt.
   - Connect to the server by typing (you need to be in the university or be connected to the VPN)
   - You might have to enter the password you chose when setting the ssh key up

<!-- comment to end list -->
    ssh dokku@IP.ADRE.SS

2. Check the logs

<!-- comment to end list -->
    dokku logs my_application_name --tail

3. Restart

<!-- comment to end list -->
    dokku ps:start bibfilter



## Contributors

[Tom Knuf](https://github.com/Tomptez/), [Nate Breznau](https://github.com/nbreznau), [Karen Kuribayashi](https://github.com/karenkuri)
