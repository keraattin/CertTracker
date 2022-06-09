#!/usr/bin/env python3


# Libraries
##############################################################################
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass,asdict
import os

from .restrictions import LEN_ID,LEN_ID_POSTFIX
from .status_codes import (
    OK,CREATED,BAD_REQ,UNAUTHORIZED,FORBIDDEN,
    NOT_FND,CONFLICT,TOKEN_REQUIRED,SRV_ERR
)
from .timezone import TZ
##############################################################################

# Global Values
##############################################################################

##############################################################################

# Database Object
##############################################################################
db = SQLAlchemy()
##############################################################################

# Base Class
##############################################################################
@dataclass
class Base(db.Model):
    __abstract__ = True

    def create_custom_id(self):
        return str(os.urandom(LEN_ID_POSTFIX).hex())

    @classmethod
    def create(cls, *args):
        # This method is used to create class object

        try:
            # args default ({'name': '', 'description': ''},)
            args = args[0]
            # args converted {'name': '', 'description': ''}

            # Create Department Class Object
            obj = cls()

            # Iterate over args (key,value)
            for k,v in args.items():
                setattr(obj,k,v)
            
            # Set Custom ID
            obj.id = cls.create_custom_id()

            # Add Object to Session
            db.session.add(obj)
            # Commit Session
            db.session.commit()

            return jsonify(asdict(obj)),CREATED
        # If the value trying to create already exists
        except IntegrityError as e:
            db.session.rollback() # Rollback
            # Return error message as JSON
            return jsonify(
                {
                    "status":"fail",
                    "message":str(e.__dict__['orig'])
                }
            ),CONFLICT
        # If any error occurs
        except Exception as e:
            db.session.rollback() # Rollback
            # Return error message as JSON
            return jsonify(
                {
                    "status":"fail",
                    "message":str(e)
                }
            ),SRV_ERR

    @classmethod
    def get(cls, id):
        # This method is used to fetch class object with id 
        # This method takes id and return json or object
        
        try:
            # Get Object by id
            obj = cls.query.filter_by(id=id).first()

            # If Object found
            if obj:
                return jsonify(asdict(obj)),OK
            # If Object not found
            else:
                # Return error message as JSON
                return jsonify(
                    {
                        "status":"fail",
                        "message":"couldn't found "+str(id)
                    }
                ),NOT_FND
        # If any error occurs
        except Exception as e:
            db.session.rollback() # Rollback
            # Return error message as JSON
            print(str(e))
            return jsonify(
                {
                    "status":"fail",
                    "message":str(e)
                }
            ),SRV_ERR
    
    @classmethod
    def get_all(cls):
        # This method is used to fetch all class objects
        # This method return json type of all of object's list
        
        try:
            # Get Object by id
            objs = cls.query.all()

            # Create Object list
            obj_list = []

            # If Object found
            if objs:
                # Iterate over objects
                for obj in objs:
                    # Append Json type of objects to objects list
                    obj_list.append(asdict(obj))
                
            # Return Json type of objects list
            return jsonify(obj_list),OK
        # If any error occurs
        except Exception as e:
            db.session.rollback() # Rollback
            # Return error message as JSON
            return jsonify(
                {
                    "status":"fail",
                    "message":str(e)
                }
            ),SRV_ERR
    
    @classmethod
    def get_by(cls, *args):
        # This method is used to fetch class object with given params 
        # This method takes id and return json or object
        # If no 'ret_type' arguments are given, json is used.

        # args default ({'name': '', 'description': ''},)
        args = args[0]
        # args converted {'name': '', 'description': ''}

        try:
            # Get Object by given parameters
            obj = cls.query.filter_by(**args).first()

            # If Object found
            if obj:
                return asdict(obj)
            # If Object not found
            else:
                # Return error message as JSON
                return jsonify(
                    {
                        "status":"fail",
                        "message":"couldn't found "+str(args)
                    }
                ),NOT_FND
        # If any error occurs
        except Exception as e:
            db.session.rollback() # Rollback
            # Return error message as JSON
            return jsonify(
                {
                    "status":"fail",
                    "message":str(e)
                }
            ),SRV_ERR
    
    @classmethod
    def update(cls, id, *args):
        # This method is used to update class object with id
        # This method takes id and return json or objecet

        try:
            # args default ({'name': '', 'description': ''},)
            args = args[0]
            # args converted {'name': '', 'description': ''}

            # Get Object by id
            obj = cls.query.filter_by(id=id).first()

            # If Object found
            if obj:
                # Iterate over args (key,value)
                for k,v in args.items():
                    # Set Attributes to New Values
                    setattr(obj,k,v)

                # Commit changes
                db.session.commit()

                return jsonify(asdict(obj)),OK
            # If Object not found
            else:
                # Return error message as JSON
                return jsonify(
                    {
                        "status":"fail",
                        "message":"couldn't found "+str(id)
                    }
                ),NOT_FND
        # If unique constraint error occurs
        # If the value trying to update already exists
        except IntegrityError as e:
            db.session.rollback() # Rollback
            # Return error message as JSON
            return jsonify(
                {
                    "status":"fail",
                    "message":str(e.__dict__['orig'])
                }
            ),CONFLICT
        # If any other error occurs
        except Exception as e:
            db.session.rollback() # Rollback
            # Return error message as JSON
            return jsonify(
                {
                    "status":"fail",
                    "message":str(e)
                }
            ),SRV_ERR
    
    @classmethod
    def delete(cls, id):
        # This method is used to delete class object with id 
        # This method takes id and return json or object

        try:
            # Get Object by id
            obj = cls.query.filter_by(id=id).first()

            # If Object found
            if obj:
                # Delete Object
                db.session.delete(obj)
                # Commit changes
                db.session.commit()

                # Return successfully
                return jsonify(
                    {
                        "status":"ok",
                        "message":str(id)+" deleted successfully"
                    }
                ),OK
            # If Object not found
            else:
                # Return error message as JSON
                return jsonify(
                    {
                        "status":"fail",
                        "message":"couldn't found "+str(id)
                    }
                ),NOT_FND
        # If any error occurs
        except Exception as e:
            db.session.rollback() # Rollback
            # Return error message as JSON
            return jsonify(
                {
                    "status":"fail",
                    "message":str(e)
                }
            ),SRV_ERR
##############################################################################