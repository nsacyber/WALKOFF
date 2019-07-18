from api_gateway.serverdb.user import User
from flask_jwt_extended import get_jwt_claims
from api_gateway.serverdb.role import Role
from api_gateway.serverdb.resource import Permission, Operation, Resource
from api_gateway.extensions import db


import logging
logger = logging.getLogger(__name__)


def auth_check(to_check, permission, resource_name, updated_roles=None):
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
                                    logger.info(
                                        f" Deleted operation for {resource_name} --> ({to_check})")
                                    delete_operation(resource_name, to_check, permission)
                                if updated_roles:
                                    delete_operation(resource_name, to_check, permission)
                                    update_permissions(resource_name, to_check, new_permissions=updated_roles)
                                return True
            else:
                # we know user has default privilege
                if permission == "delete":
                    logger.info(
                        f" Deleted operation for {resource_name} --> ({to_check})")
                    delete_operation(resource_name, to_check, permission)
                if updated_roles:
                    delete_operation(resource_name, to_checkcreate, permission)
                    update_permissions(resource.name, to_check, new_permissions=updated_roles)

                return True
    return False


# deletes operation for specific resource in all roles
def delete_operation(resource_name, to_check, permission):
    for resource_elem in db.session.query(Resource).filter(Resource.name == resource_name).all():
        if resource_elem.operations:
            if to_check in [elem.operation_id for elem in resource_elem.operations]:
                for elem in resource_elem.operations:
                    if elem.operation_id == to_check:
                        if permission in elem.permissions_list:
                            resource_elem.operations.remove(elem)
                            db.session.commit()


# updates permissions for specific resource
def update_permissions(resource_type, resource_indicator, new_permissions):
    for role_elem in new_permissions:
        role_name = role_elem[0]
        role_permissions = role_elem[1]
        for resource in db.session.query(Role).filter(Role.name == role_name).first().resources:
            if resource.name == resource_type:
                if "update" not in [elem.name for elem in resource.permissions]:
                    resource.permissions.append(Permission("update"))
                if "delete" not in [elem.name for elem in resource.permissions]:
                    resource.permissions.append(Permission("delete"))
                if resource.operations:
                    final = [Operation(resource_indicator, role_permissions)] + resource.operations
                    setattr(resource, "operations", final)
                    logger.info(f" Newly added operation for {resource_type} --> ({resource_indicator},{role_permissions})")
                    db.session.commit()
                else:
                    resource.operations = [Operation(resource_indicator, role_permissions)]
                    logger.info(f" Newly added operation for {resource_type} --> ({resource_indicator},{role_permissions})")
                    db.session.commit()
                logger.info(f" Updated {resource_type} element {resource_indicator} permissions for role type {role_name}")