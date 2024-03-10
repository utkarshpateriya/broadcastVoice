import uuid

def generate_message_id():
    random_string = str(uuid.uuid4())
    return random_string