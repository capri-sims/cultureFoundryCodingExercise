# Culture Foundry Coding Exercise - Capri Sims

## To Install:
Have Python 3 installed

Create a virtualenv and activate it:
```
$ python3 -m venv venv
$ . venv/bin/activate
```
Or on Windows:
```
$ python -m venv venv
$ venv\Scripts\activate.bat
```
Install project:
```
$ pip install -e .
```
## To Run:
```
$ export FLASK_APP=cultureFoundryCustomers
$ export FLASK_ENV=development
$ flask init-db
$ flask run
```
Open http://127.0.0.1:5000 in a browser.