# from server.security import ResourcePermissions, roles_accepted_for_resources
# from flask_jwt_extended import jwt_required
# from server.returncodes import *
#
#
# def get_all_messages():
#     from server.context import running_context
#
#     @jwt_required
#     @roles_accepted_for_resources(ResourcePermissions('messages', ['read']))
#     def __func():
#         return [user.as_json() for user in running_context.User.query.all()], SUCCESS
#
#     return __func()



