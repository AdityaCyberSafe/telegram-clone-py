#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Dict, Any, List
import datetime

import bcrypt
import jwt

from rest import Rest, Method
from models import Session, User
from response import response, Status

CONFIG_PATH = f"{Path(__file__).parent.absolute()}{os.sep}config.json"

rest: Rest = Rest(CONFIG_PATH)

secret = rest.get_secret()


@rest.route("/create/user", Method.POST)
def create_user(payload: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Creates a User from POST payload

    Parameters
    ----------

    payload: Dict[Any, Any]
         Payload of the form
         {
          "email": "email_here",
          "password": "password_here",
          "handle": "handle_here",
          "public_key": "public_key_here"
         }

    Returns
    -------

    User (without encrypted password)
    """
    user = User(
        email=payload["email"],
        public_key=bytes(payload["public_key"].encode()),
        password=bcrypt.hashpw(payload["password"].encode(), bcrypt.gensalt()),
        handle=payload["handle"],
    )
    Session.add(user)
    # Handle error with invalid email
    Session.commit()
    return response(Status.Success, user.to_json())


@rest.route("/login/<email>", Method.POST)
def login(email: str, payload: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Logins in a User

    Parameters
    ----------

    email: str
         Email for User

    payload: Dict[Any, Any]
         Payload sent as {"password": "password_here"}

    Returns
    -------

    No User Exists or
    Password is incorrect or
    JSON Web Token to authenticate user
    """
    user = Session.query(User).filter(User.email == email).first()
    if not user:
        return response(Status.Error, f"No user with email: {email}")
    if not bcrypt.checkpw(payload["password"].encode(), user.password):
        return response(Status.Failure, f"Password is incorrect")
    return response(
        Status.Success, create_jwt(user.email, user.password, secret).decode()
    )


@rest.route("/user/delete/<email>/<token>", Method.DELETE)
def delete_user(email: str, token: str) -> Dict[Any, Any]:
    """
    Deletes a User

    Parameters
    ----------

    email: str
         Email of User to delete

    token: str
         JWT to authenticate User

    Returns
    -------

    No User with email: {email}
    Invalid token
    Successfully deleted {email}
    Failed to validate Token
    """
    user = Session.query(User).filter(User.email == email).first()
    if not user:
        return response(Status.Failure, f"No User with email: {email}")
    try:
        json = jwt.decode(token, secret, algorithms=["HS256"])
        if json["email"] != email and json["password"] == user.password:
            return response(Status.Error, "Invalid token")
        Session.delete(user)
        Session.commit()
        return response(Status.Success, f"Successfully deleted {email}")
    except jwt.DecodeError:
        return response(Status.Error, "Failed to validate token")


@rest.route("/update/user/<email>/<token>", Method.PUT)
def update_user(email: str, token: str, payload: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Updates a User

    Parameters
    ----------

    email: str
         Email to query for

    jwt: str
         JSON Web Token to validate User to permit updating

    payload: Dict[Any, Any]
         Payload of the form
         {
          "password": "password_here",
          "handle": "handle_here",
          "public_key": "public_key_here"
          "bio": "bio_here"
         }

    Returns
    -------

    No User with email: {email}
    Updated User information
    """
    user = Session.query(User).filter(User.email == email)
    if not user:
        return response(Status.Failure, f"No User with email: {email}")
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.DecodeError:
        return response(Status.Error, "Failed to validate token")
    user.update(payload)
    Session.commit()
    return response(Status.Success, user.to_json())


@rest.route("/user/<email>", Method.GET)
def get_user(email: str) -> Dict[Any, Any]:
    """
    Gets a User by Email

    Parameters
    ----------

    email: str
         Email to query for

    Returns
    -------

    User information including public_key, bio, and handle
    """
    user = Session.query(User).filter(User.email == email).first()
    if not user:
        return response(Status.Failure, f"No Users with email: {email}")
    return response(Status.Success, user.to_json())


@rest.route("/list/users", Method.GET)
def list_users() -> Dict[Any, Any]:
    """
    Lists all Users by Email

    Returns
    -------

    List[str] of User emails
    """
    users: List[User] = Session.query(User).all()
    users_json: List[Dict[str, str]] = [user.email for user in users]
    return response(Status.Success, users_json)


def create_jwt(email: str, password: bytes, secret: str, duration: int = 24) -> str:
    """
    Constructs a JSON Web Token

    Parameters
    ----------

    email: str
         User Email address

    password: bytes
         User encrypted password

    secret: str
         Server secret passcode

    duration: int
         Hours to allow defaults to 24

    Returns
    -------

    A JWT with all this information encrypted
    """
    return jwt.encode(
        {
            "email": email,
            "password": password.decode(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        },
        secret,
        algorithm="HS256",
    )


rest.run()
