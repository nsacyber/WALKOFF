import flask_sqlalchemy
from sqlalchemy.ext.hybrid import hybrid_property
from passlib.hash import pbkdf2_sha512
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

db = flask_sqlalchemy.SQLAlchemy()

urls = ['/', '/key', '/playbooks', '/configuration', '/interface', '/execution/listener',
        '/execution/listener/triggers', '/metrics',
        '/roles', '/users', '/configuration', '/cases', '/apps', '/execution/scheduler']
default_urls = urls

page_roles = {}


def initialize_page_roles_from_cleared_database():
    """Initializes the roles dictionary, used in determining which role can access which page(s).
    
    Args:
        urls (list[str]): The list of all root endpoints.
    """
    for url in default_urls:
        page_roles[url] = {"admin"}


def initialize_page_roles_from_database():
    for page in Page.query.all():
        page_roles[page.url] = {role.name for role in page.roles}


def set_urls_for_role(role_name, urls):
    for url, roles in page_roles.items():
        if url in urls:
            roles.add(role_name)
        elif role_name in roles and url not in urls:
            roles.remove(role_name)
    new_urls = set(urls) - set(page_roles.keys())
    for new_url in new_urls:
        page_roles[new_url] = {role_name}


def clear_urls_for_role(role_name):
    for url, roles in page_roles.items():
        if role_name in roles:
            roles.remove(role_name)

user_roles_association = db.Table('user_roles_association',
                                  db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

roles_pages_association = db.Table('roles_pages_association',
                                   db.Column('page_id', db.Integer, db.ForeignKey('page.id')),
                                   db.Column('role_id', db.Integer, db.ForeignKey('role.id')))


class TrackModificationsMixIn(object):
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class User(db.Model, TrackModificationsMixIn):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roles = db.relationship('Role', secondary=user_roles_association,
                            backref=db.backref('users', lazy='dynamic'))
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password = db.Column('password', db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=False)
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    current_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer, default=0)

    def __init__(self, name, password):
        self.username = name
        self._password = pbkdf2_sha512.hash(password)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, new_password):
        self._password = pbkdf2_sha512.hash(new_password)

    def verify_password(self, password_attempt):
        return pbkdf2_sha512.verify(password_attempt, self._password)

    def set_roles(self, new_roles):
        self.roles[:] = []

        new_role_names = set(new_roles)
        new_roles = Role.query.filter(Role.name.in_(new_role_names)).all() if new_role_names else []
        self.roles.extend(new_roles)

        roles_not_added = new_role_names - {role.name for role in new_roles}
        if roles_not_added:
            logger.warning('Cannot add roles {0} to user {1}. Roles do not exist'.format(roles_not_added, self.id))

    def login(self, ip_address):
        self.last_login_at = self.current_login_at
        self.current_login_at = datetime.utcnow()
        self.last_login_ip = self.current_login_ip
        self.current_login_ip = ip_address
        self.login_count += 1
        self.active = True

    def logout(self):
        self.active = False
        if self.login_count > 0:
            self.login_count -= 1
        else:
            logger.warning('User {} logged out, but login count was already at 0'.format(self.id))
        db.session.commit()

    def has_role(self, role):
        return role in [role.name for role in self.roles]

    def as_json(self, with_user_history=False):
        """Returns the dictionary representation of a User object.

        Returns:
            The dictionary representation of a User object.
        """
        out = {"id": self.id,
               "username": self.username,
               "roles": [role.as_json() for role in self.roles]}
        if with_user_history:
            out.update({
                "active": self.active,
                "last_login_at": self.last_login_at,
                "current_login_at": self.current_login_at,
                "last_login_ip": self.last_login_ip,
                "current_login_ip": self.current_login_ip,
                "login_count": self.login_count})
        return out


class Role(db.Model, TrackModificationsMixIn):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    pages = db.relationship('Page', secondary=roles_pages_association,
                            backref=db.backref('roles', lazy='dynamic'))

    def __init__(self, name, description='', pages=None):
        """Initializes a Role object. Each user has one or more Roles associated with it, which determines the user's
            permissions.

        Args:
            name (str): The name of the Role.
            description (str, optional): A description of the role.
            pages (list[str]): The list of root endpoints that a user with this Role can access.
        """
        self.name = name
        self.description = description
        if pages is not None:
            self.set_pages(pages)

    def set_pages(self, new_pages):
        """Adds the given list of roles to the User object.

        Args:
            new_pages (list|set[str]): A list of Page urls with which the Role will be associated.
        """
        self.pages[:] = []
        new_page_urls = set(new_pages)
        new_pages = Page.query.filter(Page.url.in_(new_page_urls)).all() if new_page_urls else []
        self.pages.extend(new_pages)

        pages_not_added = new_page_urls - {page.url for page in new_pages}
        self.pages.extend([Page(url) for url in pages_not_added])

    def as_json(self, with_users=False):
        """Returns the dictionary representation of the Role object.

        Returns:
            The dictionary representation of the Role object.
        """
        out = {"id": self.id,
                "name": self.name,
                "description": self.description,
                "pages": [page.url for page in self.pages]}
        if with_users:
            out['users'] = [user.username for user in self.users]
        return out


class Page(db.Model):
    __tablename__ = 'page'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(255), unique=True, nullable=False)

    def __init__(self, url):
        self.url = url

    def as_json(self, with_roles=False):
        out = {'url': self.url}
        if with_roles:
            out["roles"] = [role.name for role in self.roles]
        return out


def add_user(username, password):
    if User.query.filter_by(username=username).first() is None:
        user = User(username, password)
        db.session.add(user)
        db.session.commit()
        return user
    else:
        return None


def remove_user(username):
    User.query.filter_by(username=username).delete()
