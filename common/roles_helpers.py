from api_gateway.serverdb.user import User
from flask_jwt_extended import get_jwt_claims
from api_gateway.serverdb.role import Role
from api_gateway.serverdb.resource import Operation, Resource
from api_gateway.extensions import db

import logging
logger = logging.getLogger(__name__)


def auth_check(to_check, permission, resource_name, new_name=None, updated_roles=None):
    username = get_jwt_claims().get('username', None)
    curr_user = db.session.query(User).filter(User.username == username).first()
    curr_roles = curr_user.roles

    for role in curr_roles:
        for resource in role.resources:
            if resource.name == resource_name:
                if resource.operations:
                    logger.info(f"resource.operations -> {resource.operations}")
                    if to_check not in [elem.operation_id for elem in resource.operations]:
                        return False
                    else:
                        for elem in resource.operations:
                            if elem.operation_id == to_check:
                                if permission not in elem.permissions_list:
                                    return False
                                else:
                                    if permission == "delete":
                                        delete_operation(resource_name, to_check)
                                    if updated_roles:
                                        delete_operation(resource_name, to_check)
                                        if new_name:
                                            update_permissions(resource_name, new_name, new_permissions=updated_roles)
                                        else:
                                            update_permissions(resource_name, to_check, new_permissions=updated_roles)
                                    return True
                else:
                    return False
        return False


# deletes operation for specific resource in all roles
def delete_operation(resource_name, to_check):
    roles = db.session.query(Role).filter(Role.id != 1).all()
    for role in roles:
        for resource_elem in role.resources:
            if resource_elem.operations:
                if to_check in [elem.operation_id for elem in resource_elem.operations]:
                    for elem in resource_elem.operations:
                        if elem.operation_id == to_check:
                            resource_elem.operations.remove(elem)
                            db.session.commit()
    logger.info(f" Deleted operation for {resource_name} --> ({to_check})")


# updates permissions for specific resource
def update_permissions(resource_type, resource_indicator, new_permissions):
    # ensures super admin will always have access to the resource
    new_permissions = [{"role": 2, "permissions": ["delete", "execute", "read", "update"]}] + new_permissions
    logger.info(f"new permissions ->{new_permissions}")
    if new_permissions:
        for role_elem in new_permissions:
            role_id = role_elem['role']
            role_permissions = role_elem['permissions']
            for resource in db.session.query(Role).filter(Role.id == role_id).first().resources:
                if resource.name == resource_type:
                    if resource.operations:
                        final = [Operation(resource_indicator, role_permissions)] + resource.operations
                        setattr(resource, "operations", final)
                        db.session.commit()
                    else:
                        resource.operations = [Operation(resource_indicator, role_permissions)]
                        db.session.commit()
                    logger.info(f" Updated {resource_type} element {resource_indicator} permissions for role id {role_id}")


# sets default permissions for given resource type
def default_permissions(resource_type, resource_indicator, data):
    ret = []

    roles = db.session.query(Role).all()
    for role in roles:
        for resource in role.resources:
            if resource.name == resource_type:
                if resource.operations:
                    role_permissions = [permission.name for permission in resource.permissions
                                        if permission.name != "create"]
                    if "delete" in role_permissions:
                        role_permissions = ['read', 'update', 'delete', 'execute']
                    elif "execute" in role_permissions and "read" in role_permissions:
                        role_permissions = ['read', 'execute']
                    if role.id != 1 and role.id != 2:
                        to_append = {
                            "permissions": role_permissions,
                            "role": role.id
                        }
                        ret.append(to_append)
                    resource.operations = [Operation(resource_indicator, role_permissions)] + resource.operations
                    db.session.commit()
                else:
                    role_permissions = [permission.name for permission in resource.permissions
                                        if permission.name != "create"]
                    if "delete" in role_permissions:
                        role_permissions = ['read', 'update', 'delete', 'execute']
                    elif "execute" in role_permissions:
                        role_permissions = ['read', 'execute']
                    if role.id != 1 and role.id != 2:
                        to_append = {
                            "permissions": role_permissions,
                            "role": role.id
                        }
                        ret.append(to_append)
                    resource.operations = [Operation(resource_indicator, role_permissions)]
                    db.session.commit()

    data["permissions"] = ret
