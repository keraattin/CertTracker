#!/usr/bin/env python3


# Libraries
##############################################################################
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
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

# Schema Sync
##############################################################################
# db.create_all() creates missing tables but never touches existing ones,
# so a column added to a model stays invisible to an installation that
# already has a database. SQLite can add a column in place, which
# covers everything this project needs: the schema only grows.
#
# Table and column names come from the models, never from user input.
##############################################################################
def ensure_columns():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    for table in db.metadata.tables.values():
        if table.name not in tables:
            continue
        known = [column["name"] for column in inspector.get_columns(table.name)]
        for column in table.columns:
            if column.name in known:
                continue
            clause = (
                "ALTER TABLE " + table.name + " ADD COLUMN "
                + column.name + " " + column.type.compile(db.engine.dialect)
            )
            # A NOT NULL column can only be added when there is a default
            # to fill the rows that already exist with.
            default = column.server_default
            if default is not None:
                value = getattr(default.arg, "text", None)
                if value is None:
                    value = "'" + str(default.arg) + "'"
                clause += " DEFAULT " + value
                if not column.nullable:
                    clause += " NOT NULL"
            db.session.execute(text(clause))
    db.session.commit()
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
