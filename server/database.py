import flask_sqlalchemy
import json
db = flask_sqlalchemy.SQLAlchemy()
userRoles = {}


def initialize_user_roles(urls):
    """Initializes the roles dictionary, used in determining which role can access which page(s).
    
    Args:
        urls (list[str]): The list of all root endpoints.
    """
    for url in urls:
        userRoles[url] = ["admin"]


def add_to_user_roles(role_name, urls):
    """Adds a role to the list of allowed roles for a list of root endpoints.
    
    Args:
        role_name (str): The name of the role to add to the allowed roles list.
        urls (list[str]): The list of root endpoints to which to add the role.
    """
    for url in urls:
        userRoles[url].append(role_name)


# Base Class for Tables
class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class Role(Base):
    __tablename__ = 'auth_role'
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    pages = db.Column(db.String(255))

    def __init__(self, name, description, pages):
        """Initializes a Role object. Each user has one or more Roles associated with it, which determines the user's
            permissions.
            
        Args:
            name (str): The name of the Role.
            description (str, optional): A description of the role.
            pages (list[str]): The list of root endpoints that a user with this Role can access.
        """
        self.name = name
        self.description = description
        self.pages = pages

    @staticmethod
    def create_role(name, description, pages):
        role = Role(name=name, description=description, pages=json.dumps(pages))
        db.session.add(role)
        db.session.commit()
        return role

    @staticmethod
    def add_role_to_user(user, role):
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()

    def set_description(self, description):
        """Sets the description of the Role.
        
        Args:
            description (str): The description of the Role.
        """
        self.description = description

    def as_json(self):
        """Returns the dictionary representation of the Role object.
        
        Returns:
            The dictionary representation of the Role object.
        """
        return {"name": self.name, "description": self.description}

    def display(self):
        """Returns the dictionary representation of the Role object.
        
        Returns:
            The dictionary representation of the Role object.
        """
        return {"name": self.name,
                "description": self.description}

class User(Base):
    # Define Models
    roles_users = db.Table('roles_users',
                           db.Column('user_id', db.Integer(), db.ForeignKey('auth_user.id')),
                           db.Column('role_id', db.Integer(), db.ForeignKey('auth_role.id')))

    __tablename__ = 'auth_user'
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(45))
    current_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer)

    def __init__(self, email, password, active):
        self.email = email
        self.password = password
        self.active = active

    @staticmethod
    def create_user(email, password, active=False):
        user = User(email=email, password=password, active=active)
        db.session.add(user)
        db.session.commit()
        return user

    def display(self):
        """Returns the dictionary representation of a User object.
        
        Returns:
            The dictionary representation of a User object.
        """
        return {"id": self.id,
                "username": self.email,
                "roles": [role.as_json() for role in self.roles],
                "active": self.active}

    def set_roles(self, roles):
        """Adds the given list of roles to the User object.
        
        Args:
            roles (list[str]): A list of Role names with which the User will be associated.
        """
        for role in roles:
            if role['name'] and not self.has_role(role['name']):
                q = Role.query.filter_by(name=role['name']).first()
                if q:
                    self.roles.append(q)
                    db.session.commit()

    def has_role(self, role):
        return

    def __repr__(self):
        return self.email


class UserDataStore(object):
    def __init__(self):
        pass


    @staticmethod
    def get_user(*args, **kwargs):
        if args:
            query = User.query.filter_by(email=args[0]).first()
        if kwargs.get("username", None):
            query = User.query.filter_by(email=kwargs.get("username")).first()
        elif kwargs.get("id", None):
            query = User.query.filter_by(id=kwargs.get("id")).first()
        if query:
            print(query)
            return query



    @staticmethod
    def delete_user(username):
        if User.query.filter_by(email=username.email).first():
            User.query.filter_by(email=username.email).delete()
            db.session.commit()

    @staticmethod
    def create_role(name, description="", pages=""):
        role = Role.create_role(name, description, pages)
        return role

    @staticmethod
    def create_user(email, password, active=False):
        user = User.create_user(email, password, active)
        return user