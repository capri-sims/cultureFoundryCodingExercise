import os, sys, requests, random, re

from flask import Flask, request, render_template, g, redirect, abort, jsonify, make_response, flash, url_for
from cultureFoundryCustomers.db import get_db
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.fields.html5 import  EmailField
from wtforms.validators import DataRequired, Email, Length, Regexp

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY = 'dev', #overwrite with random value when deploying
        DATABASE = os.path.join(app.instance_path, 'cultureFoundryCustomers.sqlite'),
    )

    from . import db
    db.init_app(app)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/', methods=['GET', 'POST'])
    def landing_page():
        form = customerForm(request.form)

        if form.validate_on_submit():
            firstName = form.firstName.data
            lastName = form.lastName.data 
            email = form.email.data 
            zipCode = form.zipCode.data 
            guid = request.cookies.get('tracking_guid')

            formInfo = {
                'firstName' : firstName,
                'lastName' : lastName,
                'email' : email,
                'zipCode' : zipCode,
                'guid' : guid
            }
            res = requests.post(request.host_url + '/api/customer', json=formInfo)
            if res.status_code == 201:
                return redirect('/review')
            else:
                flash('Error: ' + res.json().get('error', 'Unknown'))

        return render_template('landing_page.html', form=form)

    @app.route('/review')
    def review_page():
        guid = request.cookies.get('tracking_guid')

        if guid is not None:
            res = requests.get(request.host_url + '/api/customer/' + guid, timeout=5)
            userInfo = res.json()
            if userInfo.get('customerID', -1) == -1: #defaults to -1 if not found
                userInfo = None
        else:
            userInfo = None
        return render_template('review_page.html', userInfo=userInfo)

    @app.route('/api/generate_guid')
    def generate_guid():
        findingUniqueNumber = True
        while findingUniqueNumber:
            guid = random.randint(111111, 999999)
            queryResults = get_db().execute(
                'SELECT * FROM customer WHERE tracking_guid = ?', (guid,)
            ).fetchone()
            if(queryResults is None):
                findingUniqueNumber = False
        return str(guid)

    @app.route('/api/customer/<int:guid>', methods=['GET'])
    def get_customer(guid):
        data = get_db().execute(
            'SELECT * FROM customer WHERE tracking_guid = ?', (guid,)
        ).fetchone()
        if data is not None:
            userInfo = {
                'customerID' : data[0],
                'firstName' : data[1],
                'lastName' : data[2],
                'email' : data[3],
                'zipCode' : data[4],
                'guid' : data[5]
            }
        else:
            userInfo = {'customerID' : -1}
        return userInfo

    @app.route('/api/customer', methods=['POST'])
    def insert_customer():
        if not request.json:
            return jsonify({'error': 'Request is missing JSON'}), 400
        userInfo = request.json 
        firstName = userInfo.get('firstName', -1) #defaults to -1 if not found
        lastName = userInfo.get('lastName', -1)
        email = userInfo.get('email', -1)
        zipCode = userInfo.get('zipCode', -1)
        guid = userInfo.get('guid', -1)

        if firstName == -1 or lastName == -1 or email == -1 or zipCode == -1 or guid == -1:
            return jsonify({'error': 'Request is missing parameters'}), 406
        if len(firstName) < 1 or len(firstName) > 50 or re.search("^[a-zA-z '-]+$", firstName) is None:
            return jsonify({'error': 'First Name is invalid'}), 406
        if len(lastName) < 1 or len(lastName) > 50 or re.search("^[a-zA-z '-]+$", lastName) is None:
            return jsonify({'error': 'Last Name is invalid'}), 406
        if len(email) < 3 or len(email) > 75 or re.search("[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", email) is None:
            return jsonify({'error': 'Email is invalid'}), 406
        if len(zipCode) != 5 or re.search("^\d+$", zipCode) is None:
            return jsonify({'error': 'Zip Code is invalid'}), 406
        if len(guid) != 6 or re.search("^\d+$", guid) is None:
            return jsonify({'error': 'GUID is invalid'}), 406
        
        get_db().execute(
            "INSERT INTO customer (first_name, last_name, email, zip_code, tracking_guid) VALUES (?,?,?,?,?)", 
            (firstName, lastName, email, zipCode, guid,)
        )
        get_db().commit()
        return userInfo, 201 

    return app

class customerForm(FlaskForm):
    #Restrict characters to: A-Za-z spaces, hyphens, and apostrophes only
    firstName = StringField('First Name', validators=[Length(min=1, max=50), Regexp("^[a-zA-z '-]+$")])
    lastName = StringField('Last Name', validators=[Length(min=1, max=50), Regexp("^[a-zA-z '-]+$")])
    email = EmailField('Email', validators=[Email(), Length(min=3, max=75)])
    zipCode = StringField('Zip Code', validators=[Length(min=5, max=5), Regexp("^\d+$")])
    submit = SubmitField('Submit')