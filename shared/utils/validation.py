import uuid

def is_valid_uuid(uuid_to_test, version=4) -> bool:
    try:
        # check for validity of Uuid
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return True
