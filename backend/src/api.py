import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
    uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
'''
db_drop_and_create_all()

# ROUTES
''' 
    GET /drinks
    it should be a public endpoint
    it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    return jsonify({
        'drinks': [drink.short() for drink in Drink.query.all()],
        'success': True
    }), 200

'''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drink_detail(payload):
    return jsonify({
        'drinks': [drink.long() for drink in Drink.query.all()],
        'success': True
    }), 200


'''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    request_json = request.get_json()
    try:
        request_recipe = request_json['recipe']
        if isinstance(request_recipe, dict):
            request_recipe = [request_recipe]
        drink = Drink()
        drink.title = request_json['title']
        drink.recipe = json.dumps(request_recipe)  # convert object to a string
        drink.insert()
    except BaseException:
        abort(400)
    return jsonify({
        'drinks': [drink.long()],
        'success': True
    })

'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    request_json = request.get_json()
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if not drink:
        abort(404)
    try:
        request_title = request_json.get('title')
        request_recipe = request_json.get('recipe')
        if request_title:
            drink.title = request_title
        if request_recipe:
            drink.recipe = json.dumps(request_json['recipe'])
        drink.update()
    except BaseException:
        abort(400)
    return jsonify({
        'drinks': [drink.long()],
        'success': True
    }), 200

'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if not drink:
        abort(404)
    try:
        drink.delete()
    except BaseException:
        abort(400)
    return jsonify({
        'delete': id,
        'success': True
    }), 200


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": 404,
        "message": "resource not found",
        "success": False,
    }), 404

'''
    Error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "error": 401,
        "message": 'Unathorized',
        "success": False
    }), 401

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "error": 400,
        "message": 'Bad Request ',
        "success": False
    }), 400


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": 405,
        "message": 'Method Not Allowed ',
        "success": False
    }), 405
    
@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "error": 500,
        "message": 'Internal Server Error ',
        "success": False
    }), 500
    

@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "error": error.status_code,
        "message": error.error['description'],
        "success": False
    }), error.status_code


