from logging import error
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
#----------------------------------------------------------------------------#
# General Functions
#----------------------------------------------------------------------------#
def get_error_message(error, default_text):
    try:
        return error['description']
    except TypeError:
        return default_text
'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()
#----------------------------------------------------------------------------#
# ROUTES
#----------------------------------------------------------------------------#
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def drinks():
    all_drinks = Drink.query.order_by(Drink.id).all()
    drinks = [drink.short() for drink in all_drinks]
    if drinks is None:
        abort(400, {'message': 'No drinks found in menu'})

    return jsonify({
        'success': True,
        'drinks': drinks
    })
'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail',  methods=['GET'])
@requires_auth('get:drinks-detail')
def drinks_detail(jwt):
    all_drinks = Drink.query.order_by(Drink.id).all()
    if not all_drinks:
        abort(400, {'message': 'No drinks found in menu'})
    drinks = [drink.long() for drink in all_drinks]
    
    if not drinks:
        abort(400, {'message': 'No drinks found in menu'})
        
    return jsonify({
        'success': True,
        'drinks': drinks
    })
'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    req = request.get_json()
    try:
        req_recipe = req['recipe']
        if isinstance(req_recipe, dict):
            req_recipe = [req_recipe]

        if req_recipe is not None:
            drink = Drink()
            drink.title = req['title']
            drink.recipe = json.dumps(req_recipe)  # convert object to a string
            drink.insert()
        else:
            abort(422, {'message': 'unable to create new drink'})
    except:
        abort(400, {'message': 'No new drinks added to menu'})


    return jsonify({'success': True, 'drinks': [drink.long()]})
'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>',  methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(jwt, drink_id):
    
    body = request.get_json()

    if not body:
      abort(400, {'message': 'request does not contain a valid JSON body.'})

    # Get drink by id
    drink = Drink().query.filter_by(id = drink_id).one_or_none()
    
    if drink is None:
        abort(404, {'message': 'Drink ID not found'})
        
    try:
        # Check fields that should be updated
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)

        
        if new_title:
            drink.title = body['title']

        if new_recipe:
            drink.recipe = """{}""".format(body['recipe'])

        drink.update()

        return jsonify({
            'success': True,
            'drinks': [Drink.long(drink)]
        })
    except Exception:
        abort(422, {'message': 'Drink can not be updated'})

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:drink_id>',  methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(jwt, drink_id):
   
    drink = Drink.query.filter_by(id = drink_id).one_or_none()
    if drink_id is None:
        abort(404, {'message': 'Please provide valid drink id'})
        
    try:
        if not drink:
            abort(
                422, {'message': 'Drink with id {} not found in database.'.format(drink_id)})

        drink.delete()

        return jsonify({
            'success': True,
            'delete': drink_id
        })
    except Exception:
        abort(422, {'message': 'Drink can not be deleted'})

## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": get_error_message(error, "unprocessable")
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
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": get_error_message(error, "resource not found")
    }), 400
    
    
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": get_error_message(error, "unathorized")
    }), 401
    

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": get_error_message(error, "method not allowed")
    }), 405

'''
@TODO implement error handler for 404
    error handler should conform to general task above 
'''
@app.errorhandler(404)
def ressource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": get_error_message(error, "resource not found")
    }), 404
'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''
@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
