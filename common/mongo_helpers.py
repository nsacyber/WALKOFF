from typing import Union, Type
from uuid import UUID
import logging

from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection


logger = logging.getLogger(__name__)


async def get_all_items(collection: AsyncIOMotorCollection, model: Type[BaseModel]):
    """
    Retrieve all items from a collection

    :param collection: Collection to query
    :param model: Class which the JSON in the collection represents
    :return: List of objects in the collection
    """
    collection_json = await collection.find().to_list(None)
    r = []
    for item_json in collection_json:
        obj = model(**item_json)
        r.append(obj)
    return r
    # return [model(**item_json) for item_json in collection_json]


async def get_item(collection: AsyncIOMotorCollection, item_id: Union[UUID, str],
                   model: Union[Type[BaseModel], Type[dict]]):
    """
    Retrieve a single item from a collection
    :param collection: Collection to query
    :param item_id: UUID or name of desired item
    :param model: Class which the JSON in the collection represents
    :return: Requested object from collection
    """
    identifier = "id_" if type(item_id) is UUID else model._secondary_id
    item_json = await collection.find_one({identifier: item_id}, projection={'_id': False})

    if model is dict or item_json is None:
        return item_json
    else:
        return model(**item_json)


async def create_item(collection: AsyncIOMotorCollection, new_item_obj: BaseModel):
    """
    Create an item in the collection
    :param collection: Collection to query
    :param new_item_obj: Object to place in collection
    :return: Created object in collection
    """
    r = await collection.insert_one(dict(new_item_obj))
    if r.acknowledged:
        return await get_item(collection, new_item_obj.id_, type(new_item_obj))


async def update_item(collection: AsyncIOMotorCollection, old_item_id: Union[UUID, str], new_item_obj: BaseModel):
    """
    Update an item in the collection
    :param collection: Collection to query
    :param old_item_id: UUID or name of item to replace
    :param new_item_obj: Object to place in collection
    :return: Updated object in collection
    """
    old_item_obj = await get_item(collection, old_item_id, type(new_item_obj))
    if old_item_obj is not None:
        new_item_obj.id_ = old_item_obj.id_
        r = await collection.replace_one({"id_": old_item_obj.id_}, dict(new_item_obj))
        if r.acknowledged:
            return await get_item(collection, new_item_obj.id_, type(new_item_obj))


async def delete_item(collection: AsyncIOMotorCollection, old_item_id: Union[UUID, str]):
    """
    Delete an item in the collection
    :param collection: Collection to query
    :param old_item_id: UUID or name of item to delete
    :return: Whether the item was deleted
    """
    old_item_json = await get_item(collection, old_item_id, dict)
    r = await collection.delete_one(old_item_json)
    return r.acknowledged
