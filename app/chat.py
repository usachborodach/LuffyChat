from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import User, Message, Group, GroupMember
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def index():
    users = User.query.filter(User.id != current_user.id).all()
    groups = Group.query.join(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    return render_template('index.html', users=users, groups=groups)

@chat_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    users = User.query.filter(
        User.id != current_user.id,
        (User.username.contains(query) | User.nickname.contains(query))
    ).all()
    return jsonify([{'id': u.id, 'username': u.username, 'nickname': u.nickname} for u in users])

@chat_bp.route('/chat/<int:user_id>')
@login_required
def chat_with_user(user_id):
    other = User.query.get_or_404(user_id)
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()
    return render_template('chat.html', user=other, messages=messages, chat_type='user')

@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form.get('receiver_id')
    group_id = request.form.get('group_id')
    content = request.form.get('content')
    
    if not content:
        return jsonify({'error': 'Empty message'}), 400

    msg = Message(
        content=content,
        sender_id=current_user.id,
        receiver_id=int(receiver_id) if receiver_id else None,
        group_id=int(group_id) if group_id else None
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({'status': 'ok', 'timestamp': msg.timestamp.isoformat()})

@chat_bp.route('/messages/<int:user_id>')
@login_required
def get_messages(user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()
    return jsonify([{
        'content': m.content,
        'sender_id': m.sender_id,
        'timestamp': m.timestamp.isoformat(),
        'is_mine': m.sender_id == current_user.id
    } for m in messages])