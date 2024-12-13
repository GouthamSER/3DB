import pymongo
from sample_info import tempDict
from info import DATABASE_URI, DATABASE_NAME, SECONDDB_URI, THIRDDB_URI

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]
mycol = mydb['CONNECTION']

myclient2 = pymongo.MongoClient(SECONDDB_URI)
mydb2 = myclient2[DATABASE_NAME]
mycol2 = mydb2['CONNECTION']

myclient3 = pymongo.MongoClient(THIRDDB_URI)
mydb3 = myclient3[DATABASE_NAME]
mycol3 = mydb3['CONNECTION']

async def add_connection(group_id, user_id):
    query = mycol.find_one(
        {"_id": user_id},
        {"_id": 0, "active_group": 0}
    )
    if query is None:
        query = mycol2.find_one(
            {"_id": user_id},
            {"_id": 0, "active_group": 0}
        )
        if query is None:
            query = mycol3.find_one(
                {"_id": user_id},
                {"_id": 0, "active_group": 0}
            )

    if query is not None:
        group_ids = [x["group_id"] for x in query["group_details"]]
        if group_id in group_ids:
            return False

    group_details = {
        "group_id": group_id
    }

    data = {
        '_id': user_id,
        'group_details': [group_details],
        'active_group': group_id,
    }

    try:
        if (
            mycol.count_documents({"_id": user_id}) == 0 and
            mycol2.count_documents({"_id": user_id}) == 0 and
            mycol3.count_documents({"_id": user_id}) == 0
        ):
            if tempDict['indexDB'] == DATABASE_URI:
                mycol.insert_one(data)
            elif tempDict['indexDB'] == SECONDDB_URI:
                mycol2.insert_one(data)
            else:
                mycol3.insert_one(data)
            return True
        else:
            if mycol.count_documents({"_id": user_id}):
                mycol.update_one(
                    {'_id': user_id},
                    {
                        "$push": {"group_details": group_details},
                        "$set": {"active_group": group_id}
                    }
                )
            elif mycol2.count_documents({"_id": user_id}):
                mycol2.update_one(
                    {'_id': user_id},
                    {
                        "$push": {"group_details": group_details},
                        "$set": {"active_group": group_id}
                    }
                )
            else:
                mycol3.update_one(
                    {'_id': user_id},
                    {
                        "$push": {"group_details": group_details},
                        "$set": {"active_group": group_id}
                    }
                )
            return True
    except Exception as e:
        logger.exception('Some error occurred!', exc_info=True)
        return False

async def active_connection(user_id):
    query = mycol.find_one(
        {"_id": user_id},
        {"_id": 0, "group_details": 0}
    )
    if not query:
        query = mycol2.find_one(
            {"_id": user_id},
            {"_id": 0, "group_details": 0}
        )
    if not query:
        query = mycol3.find_one(
            {"_id": user_id},
            {"_id": 0, "group_details": 0}
        )
    if not query:
        return None
    group_id = query.get('active_group')
    return int(group_id) if group_id is not None else None

async def all_connections(user_id):
    query = mycol.find_one(
        {"_id": user_id},
        {"_id": 0, "active_group": 0}
    )
    if query is None:
        query = mycol2.find_one(
            {"_id": user_id},
            {"_id": 0, "active_group": 0}
        )
        if query is None:
            query = mycol3.find_one(
                {"_id": user_id},
                {"_id": 0, "active_group": 0}
            )
    if query is not None:
        return [x["group_id"] for x in query["group_details"]]
    return None

async def if_active(user_id, group_id):
    query = mycol.find_one(
        {"_id": user_id},
        {"_id": 0, "group_details": 0}
    )
    if query is None:
        query = mycol2.find_one(
            {"_id": user_id},
            {"_id": 0, "group_details": 0}
        )
        if query is None:
            query = mycol3.find_one(
                {"_id": user_id},
                {"_id": 0, "group_details": 0}
            )
    return query is not None and query['active_group'] == group_id

async def make_active(user_id, group_id):
    update = mycol.update_one(
        {'_id': user_id},
        {"$set": {"active_group": group_id}}
    )
    if update.modified_count == 0:
        update = mycol2.update_one(
            {'_id': user_id},
            {"$set": {"active_group": group_id}}
        )
    if update.modified_count == 0:
        update = mycol3.update_one(
            {'_id': user_id},
            {"$set": {"active_group": group_id}}
        )
    return update.modified_count != 0

async def make_inactive(user_id):
    update = mycol.update_one(
        {'_id': user_id},
        {"$set": {"active_group": None}}
    )
    if update.modified_count == 0:
        update = mycol2.update_one(
            {'_id': user_id},
            {"$set": {"active_group": None}}
        )
    if update.modified_count == 0:
        update = mycol3.update_one(
            {'_id': user_id},
            {"$set": {"active_group": None}}
        )
    return update.modified_count != 0

async def delete_connection(user_id, group_id):
    try:
        for collection in [mycol, mycol2, mycol3]:
            update = collection.update_one(
                {"_id": user_id},
                {"$pull": {"group_details": {"group_id": group_id}}}
            )
            if update.modified_count > 0:
                query = collection.find_one(
                    {"_id": user_id},
                    {"_id": 0}
                )
                if query and len(query["group_details"]) >= 1:
                    if query['active_group'] == group_id:
                        prvs_group_id = query["group_details"][-1]["group_id"]
                        collection.update_one(
                            {'_id': user_id},
                            {"$set": {"active_group": prvs_group_id}}
                        )
                else:
                    collection.update_one(
                        {'_id': user_id},
                        {"$set": {"active_group": None}}
                    )
                return True
        return False
    except Exception as e:
        logger.exception(f'Some error occurred! {e}', exc_info=True)
        return False
        
