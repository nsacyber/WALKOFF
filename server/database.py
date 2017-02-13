import app
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask.ext.security.utils import encrypt_password

#Database Connection Object
db = SQLAlchemy(app)

#Base Class for Tables
class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Role(Base, RoleMixin):
    __tablename__ = 'auth_role'
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def setDescription(self, description):
        self.description = description

    def toString(self):
        return {"name" : self.name, "description" : self.description}

    def __repr__(self):
        return '<Role %r>' % self.name

class User(Base, UserMixin):

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

    def display(self):
        result = {}
        result["username"] = self.email
        roles = []
        for role in self.roles:
            roles.append(role.toString())
        result["roles"] = roles
        result["active"] = self.active

        return result

    def setRoles(self, roles):
        for role in roles:
            if role.data != "" and not self.has_role(role.data):
                q = user_datastore.find_role(role.data)
                if q != None:
                    user_datastore.add_role_to_user(self, q)
                    print("ADDED ROLE")
                else:
                    print("ROLE DOES NOT EXIST")
            else:
                print("HAS ROLE")

    def __repr__(self):
        return '<User %r>' % self.email

# Setup Flask Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Creates Test Data
@app.before_first_request
def create_user(self):
    # db.drop_all()
    db.create_all()
    if not User.query.first():
        # Add Credentials to Splunk app
        # db.session.add(Device(name="deviceOne", app="splunk", username="admin", password="hello", ip="192.168.0.1", port="5000"))

        adminRole = user_datastore.create_role(name="admin", description="administrator")
        # userRole = user_datastore.create_role(name="user", description="user")

        u = user_datastore.create_user(email='admin', password=encrypt_password('admin'))
        # u2 = user_datastore.create_user(email='user', password=encrypt_password('user'))

        user_datastore.add_role_to_user(u, adminRole)

        db.session.commit()
