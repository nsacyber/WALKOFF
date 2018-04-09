from unittest import TestCase
import json
from uuid import uuid4

from walkoff.server.endpoints.triggers import get_authorized_execution_ids
from walkoff.serverdb import db, User, Role
from walkoff.serverdb.message import Message, MessageHistory


class TestTriggerHelpers(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.uid1 = str(uuid4())
        cls.uid2 = str(uuid4())
        cls.uid3 = str(uuid4())
        cls.uids = {cls.uid1, cls.uid2, cls.uid3}
        from flask import current_app
        cls.context = current_app.test_request_context()
        cls.context.push()
        db.create_all()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        for message in Message.query.all():
            db.session.delete(message)
        db.session.commit()

    def setUp(self):
        self.user = User('username', 'password')
        self.user2 = User('username2', 'password2')

        self.role = Role('visitor')
        db.session.add(self.role)
        db.session.commit()
        self.user3 = User('username3', 'password3', roles=[self.role.id])
        db.session.add(self.user)
        db.session.add(self.user2)
        db.session.add(self.user3)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        for message in Message.query.all():
            db.session.delete(message)
        for history_entry in MessageHistory.query.all():
            db.session.delete(history_entry)
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    def create_messages(self, auths):
        if self.uid1 in auths:
            message = Message('subject here', json.dumps({'message': 'some message'}), self.uid1,
                              users=auths[self.uid1][0], roles=auths[self.uid1][1],
                              requires_reauth=True, requires_response=True)
            db.session.add(message)

        if self.uid2 in auths:
            message = Message('subject here', json.dumps({'message': 'some message'}), self.uid2,
                              users=auths[self.uid2][0], roles=auths[self.uid2][1],
                              requires_reauth=True, requires_response=True)
            db.session.add(message)

        if self.uid3 in auths:
            message = Message('subject here', json.dumps({'message': 'some message'}), self.uid3,
                              users=auths[self.uid3][0], roles=auths[self.uid3][1],
                              requires_reauth=True, requires_response=True)
            db.session.add(message)
        db.session.commit()

    def test_get_authorized_uids_no_uids_supplied(self):
        self.assertTupleEqual(get_authorized_execution_ids(set(), 42, [3, 4]), (set(), set()))

    def test_get_authorized_uids_no_authorizations_required(self):
        self.assertTupleEqual(get_authorized_execution_ids(self.uids, 42, [3, 4]), (self.uids, set()))

    def test_get_authorized_uids_all_require_authorizations(self):
        auths = {self.uid1: ([self.user], [self.role]),
                 self.uid2: ([self.user], [self.role]),
                 self.uid3: ([self.user], [self.role])}
        self.create_messages(auths)
        self.assertTupleEqual(get_authorized_execution_ids(self.uids, self.user.id, [self.role.id]), (set(), self.uids))

    def test_get_authorized_users_some_not_authorized(self):
        auths = {self.uid1: ([self.user], []),
                 self.uid2: ([self.user2], [self.role]),
                 self.uid3: ([self.user2], [])}
        self.create_messages(auths)
        self.assertTupleEqual(get_authorized_execution_ids(self.uids, self.user.id, [self.role.id]),
                              (set(), {self.uid1, self.uid2}))

    def test_get_authorized_users_mixed(self):
        auths = {self.uid1: ([self.user], [self.role]),
                 self.uid3: ([self.user2], [])}
        self.create_messages(auths)
        self.assertTupleEqual(get_authorized_execution_ids(self.uids, self.user.id, [self.role]),
                              ({self.uid2}, {self.uid1}))
