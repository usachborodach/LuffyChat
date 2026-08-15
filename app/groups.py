from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Group, GroupMember, User, Message

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('Group name is required')
            return redirect(url_for('groups.create_group'))
        
        group = Group(name=name, created_by=current_user.id)
        db.session.add(group)
        db.session.commit()
        
        # Добавляем создателя в группу
        member = GroupMember(user_id=current_user.id, group_id=group.id)
        db.session.add(member)
        db.session.commit()
        
        flash(f'Group "{name}" created!')
        return redirect(url_for('chat.index'))
    return render_template('group_create.html')

@groups_bp.route('/<int:group_id>')
@login_required
def view_group(group_id):
    group = Group.query.get_or_404(group_id)
    if not GroupMember.query.filter_by(user_id=current_user.id, group_id=group_id).first():
        flash('You are not a member of this group')
        return redirect(url_for('chat.index'))
    
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()
    members = User.query.join(GroupMember).filter(GroupMember.group_id == group_id).all()
    return render_template('group.html', group=group, messages=messages, members=members)

@groups_bp.route('/<int:group_id>/invite', methods=['POST'])
@login_required
def invite_to_group(group_id):
    group = Group.query.get_or_404(group_id)
    if group.created_by != current_user.id:
        return jsonify({'error': 'Only group creator can invite'}), 403
    
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if GroupMember.query.filter_by(user_id=user_id, group_id=group_id).first():
        return jsonify({'error': 'User already in group'}), 400
    
    member = GroupMember(user_id=user_id, group_id=group_id)
    db.session.add(member)
    db.session.commit()
    return jsonify({'status': 'ok'})

@groups_bp.route('/<int:group_id>/messages')
@login_required
def group_messages(group_id):
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()
    return jsonify([{
        'content': m.content,
        'sender_id': m.sender_id,
        'sender_name': User.query.get(m.sender_id).nickname,
        'timestamp': m.timestamp.isoformat(),
        'is_mine': m.sender_id == current_user.id
    } for m in messages])