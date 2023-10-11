from pymongo import MongoClient
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)

# Set the MongoDB URI in Flask's configuration
app.config['MONGO_URI'] = "mongodb+srv://restfulapi:NJN6nL7YpbfbitRP@cluster0.u6zpvfy.mongodb.net/"
mongo = PyMongo(app)

# Configure JWT
app.config['SECRET_KEY'] = '385ff4c74e83c02d41aeb7031f47bd69'
jwt = JWTManager(app)

# Endpoint for user registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    # Check if email already exists in the database
    existing_user = mongo.db.users.find_one({'email': data['email']})
    if existing_user:
        return jsonify({'message': 'Email already exists'}), 400
    
    # Hash the password before storing it
    hashed_password = generate_password_hash(data['password'], method='sha256')
    
    # Insert the new user into the database
    user_id = mongo.db.users.insert({
        'first_name': data['first_name'],
        'last_name': data['last_name'],
        'email': data['email'],
        'password': hashed_password
    })
    
    return jsonify({'message': 'User registered successfully'}), 201

# Endpoint for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = mongo.db.users.find_one({'email': data['email']})
    
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Create an access token using JWT
    access_token = create_access_token(identity=str(user['_id']))
    
    return jsonify({'access_token': access_token}), 200

# Template CRUD endpoints
@app.route('/template', methods=['POST'])
@jwt_required()
def create_template():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    template = {
        'user_id': current_user_id,
        'template_name': data['template_name'],
        'subject': data['subject'],
        'body': data['body']
    }
    template_id = mongo.db.templates.insert_one(template).inserted_id
    return jsonify({'message': 'Template created successfully', 'template_id': str(template_id)}), 201

@app.route('/template', methods=['GET'])
@jwt_required()
def get_all_templates():
    current_user_id = get_jwt_identity()
    templates = list(mongo.db.templates.find({'user_id': current_user_id}, {'user_id': 0}))
    return jsonify({'templates': templates}), 200

@app.route('/template/<template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    current_user_id = get_jwt_identity()
    template = mongo.db.templates.find_one({'_id': ObjectId(template_id), 'user_id': current_user_id}, {'user_id': 0})
    if template:
        return jsonify({'template': template}), 200
    else:
        return jsonify({'message': 'Template not found'}), 404

@app.route('/template/<template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    updated_template = {
        'template_name': data['template_name'],
        'subject': data['subject'],
        'body': data['body']
    }
    result = mongo.db.templates.update_one({'_id': ObjectId(template_id), 'user_id': current_user_id}, {'$set': updated_template})
    if result.modified_count > 0:
        return jsonify({'message': 'Template updated successfully'}), 200
    else:
        return jsonify({'message': 'Template not found or you do not have permission to update'}), 404

@app.route('/template/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    current_user_id = get_jwt_identity()
    result = mongo.db.templates.delete_one({'_id': ObjectId(template_id), 'user_id': current_user_id})
    if result.deleted_count > 0:
        return jsonify({'message': 'Template deleted successfully'}), 200
    else:
        return jsonify({'message': 'Template not found or you do not have permission to delete'}), 404

if __name__ == '__main__':
    app.run(debug=True)

