from .. import main

def customer_collection():
    print(main.READ_DATABASE)
    return main.READ_DATABASE['CustomerCollections']