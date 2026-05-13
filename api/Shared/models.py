#!/usr/bin/env python3


# Libraries
##############################################################################
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass, asdict
import os

from .restrictions import LEN_ID_POSTFIX
from .exceptions import NotFoundError, ConflictError
##############################################################################

# Database Object
##############################################################################
db = SQLAlchemy()
##############################################################################

# Base Class
##############################################################################
# Repository-style CRUD helpers. These return plain dicts or raise
# application exceptions; they never touch Flask Response objects. HTTP
# concerns live in the route layer (Shared/http.py).
##############################################################################
@dataclass
class Base(db.Model):
    __abstract__ = True

    @classmethod
    def create_custom_id(cls):
        return str(os.urandom(LEN_ID_POSTFIX).hex())

    @classmethod
    def create(cls, data):
        obj = cls()
        for k, v in data.items():
            setattr(obj, k, v)
        obj.id = cls.create_custom_id()
        try:
            db.session.add(obj)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ConflictError(str(e.__dict__.get('orig', e)))
        except Exception:
            db.session.rollback()
            raise
        return asdict(obj)

    @classmethod
    def get(cls, id):
        obj = cls.query.filter_by(id=id).first()
        if obj is None:
            raise NotFoundError("couldn't found " + str(id))
        return asdict(obj)

    @classmethod
    def get_all(cls):
        return [asdict(obj) for obj in cls.query.all()]

    @classmethod
    def get_by(cls, filters):
        obj = cls.query.filter_by(**filters).first()
        if obj is None:
            raise NotFoundError("couldn't found " + str(filters))
        return asdict(obj)

    @classmethod
    def update(cls, id, data):
        obj = cls.query.filter_by(id=id).first()
        if obj is None:
            raise NotFoundError("couldn't found " + str(id))
        for k, v in data.items():
            setattr(obj, k, v)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ConflictError(str(e.__dict__.get('orig', e)))
        except Exception:
            db.session.rollback()
            raise
        return asdict(obj)

    @classmethod
    def delete(cls, id):
        obj = cls.query.filter_by(id=id).first()
        if obj is None:
            raise NotFoundError("couldn't found " + str(id))
        try:
            db.session.delete(obj)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return {"id": id}
##############################################################################
