from flask import Blueprint, request, jsonify
from extensions import db
from models.request import Request
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

request_bp = Blueprint('request', __name__)

@request_bp.route('/', methods=['POST'])
@jwt_required()
def create_request():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    new_request = Request(
        title=data['title'],
        description=data['description'],
        category=data['category'],
        priority=data.get('priority', 'medium'),
        user_id=current_user_id
    )
    
    db.session.add(new_request)
    db.session.commit()
    
    return jsonify(new_request.to_dict()), 201

@request_bp.route('/', methods=['GET'])
@jwt_required()
def get_requests():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role == 'admin':
        requests = Request.query.all()
    else:
        requests = Request.query.filter_by(user_id=current_user_id).all()
    
    return jsonify([req.to_dict() for req in requests]), 200

@request_bp.route('/<int:request_id>', methods=['GET'])
@jwt_required()
def get_request(request_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    request_item = Request.query.get_or_404(request_id)
    
    if user.role != 'admin' and request_item.user_id != current_user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify(request_item.to_dict()), 200

@request_bp.route('/<int:request_id>', methods=['PUT'])
@jwt_required()
def update_request(request_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    request_item = Request.query.get_or_404(request_id)
    data = request.get_json()
    
    if user.role != 'admin' and request_item.user_id != current_user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Update allowed fields
    if user.role == 'admin':
        request_item.status = data.get('status', request_item.status)
        request_item.assigned_to = data.get('assigned_to', request_item.assigned_to)
    
    request_item.title = data.get('title', request_item.title)
    request_item.description = data.get('description', request_item.description)
    request_item.priority = data.get('priority', request_item.priority)
    
    db.session.commit()
    
    return jsonify(request_item.to_dict()), 200

@request_bp.route('/<int:request_id>', methods=['DELETE'])
@jwt_required()
def delete_request(request_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    request_item = Request.query.get_or_404(request_id)
    
    if user.role != 'admin' and request_item.user_id != current_user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    db.session.delete(request_item)
    db.session.commit()
    
    return jsonify({'message': 'Request deleted successfully'}), 200 