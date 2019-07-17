from api_gateway.serverdb.user import User
from flask_jwt_extended import get_jwt_claims
from api_gateway.extensions import db


def auth_check(to_check, permission, resource_name):
    username = get_jwt_claims().get('username', None)
    curr_user = db.session.query(User).filter(User.username == username).first()

    for resource in curr_user.roles[0].resources:
        if resource.name == resource_name:
            if resource.operations:
                if to_check not in [elem.operation_id for elem in resource.operations]:
                    return False
                else:
                    for elem in resource.operations:
                        if elem.operation_id == to_check:
                            if permission not in elem.permissions_list:
                                return False
                            else:
                                if permission == "delete":
                                    resource.operations.remove(elem)
                                    db.session.commit()

                                # TODO: check if operations were updated during update
                                # if permission == "update":

                                return True
            else:
                return True
    return False
