import datetime

import bcrypt
from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
    redirect,
    render_template,
    url_for
)
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
)
from marshmallow import ValidationError

from libs import mailgun, token
from channelry.models import db
from channelry.models.account import User
from channelry.schemas.account import SignupSchema, LoginSchema


account_bp = Blueprint('account', __name__)


def jsonify_validation_error(validation_error: ValidationError):
    """Convert validation error messages to be parsable in the Dashboard.

    :param validation_error: ValidationError raised by marshmallow
    """
    message = {}
    for field, reason in validation_error.messages.items():
        message = {'field': field, 'reason': reason[0]}
    return message


@account_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return redirect(f'{current_app.config["DASHBOARD_URL"]}/signup')

    try:
        schema = SignupSchema(strict=True)
        email = request.json.get('email')
        fullname = request.json.get('fullname')
        password = request.json.get('password')
        confirm = request.json.get('confirm')
        data, _ = schema.load({
            'email': email,
            'fullname': fullname,
            'password': password,
            'confirm': confirm
        })

        user = User(email, password, fullname)
        user_exist = User.query.filter_by(email=email).first()
        if user_exist:
            return jsonify(field='email', reason='Email is already taken'), 400
        else:
            db.session.add(user)
            db.session.commit()

            confirmation_token = token.generate_confirmation_token(email)
            confirmation_url = url_for(
                'account.confirm_email',
                confirmation_token=confirmation_token,
                _external=True
            )
            html = render_template(
                'account/email/confirm_email.html',
                confirmation_url=confirmation_url
            )
            mailgun.send_email(
                'Confirm your Channelry email address!',
                [f'{fullname} {email}'],
                html=html,
            )

        return jsonify(message=f'{email} created'), 200

    except ValidationError as validation_error:
        return jsonify(jsonify_validation_error(validation_error)), 400


@account_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return redirect(f'{current_app.config["DASHBOARD_URL"]}/login')

    try:
        schema = LoginSchema(strict=True)
        email = request.json.get('email')
        password = request.json.get('password')
        data, _ = schema.load({
            'email': email,
            'password': password
        })

        user = User.query.filter_by(email=email).first()
        if user and user.password_match(password):
            access_token = create_access_token(identity=email)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify(message='Email or password is incorrect'), 400

    except ValidationError as validation_error:
        return jsonify(validation_error.messages), 400


@account_bp.route('/email/<confirmation_token>', methods=['GET'])
def confirm_email(confirmation_token):
    try:
        email = token.confirm_conformation_token(confirmation_token)
    except:
        return jsonify(message='Confirmation link is invalid or expired'), 400

    user = User.query.filter_by(email=email).first()
    if user.is_confirmed:
        return jsonify(message='Account already confirmed')
    else:
        user.is_confirmed = True
        db.session.add(user)
        db.session.commit()
        return jsonify(message='You have confirmed your account, thanks!')
