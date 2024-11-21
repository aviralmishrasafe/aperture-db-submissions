import pandas as pd
from aperturedb import Utils
import time
# from aperturedb.CommonLibrary import create_connector

def load_users(db, users_csv):
    """
    Load users into ApertureDB from users_sp.csv. If the name matches, update the user_id.
    """
    users = pd.read_csv(users_csv).to_records(index=False)
    for user in users:
        find_query = [{
            "FindEntity": {
                "with_class": "User",
                "constraints": {
                    "name": ["==", user.user_name]
                },
                "results": {
                    "all_properties": True
                }
            }
        }]
        print(f"Executing FindEntity query for user: {user.user_name}")
        db.query(find_query)

        if not db.last_query_ok():
            print(f"Error Finding User: {user.user_name}")
            db.print_last_response()
            return

        response = db.response
        entities = response[0].get("FindEntity", {}).get("entities", [])

        if entities:
            existing_user_id = entities[0].get("user_id")
            print(f"User found: {user.user_name} with existing user_id: {existing_user_id}")

            update_query = [{
                "UpdateEntity": {
                    "with_class": "User",
                    "constraints": {
                        "name": ["==", user.user_name]
                    },
                    "properties": {
                        "user_id": int(user.user_id) 
                    }
                }
            }]
            print(f"Executing UpdateEntity query for user: {user.user_name}")
            db.query(update_query)

            if not db.last_query_ok():
                print(f"Error Updating User: {user.user_name}")
                db.print_last_response()
                return
        else:
            add_query = [{
                "AddEntity": {
                    "class": "User",
                    "properties": {
                        "name": user.user_name,
                        "user_id": int(user.user_id)
                    }
                }
            }]
            print(f"Executing AddEntity query for new user: {user.user_name}")
            db.query(add_query)

            if not db.last_query_ok():
                print(f"Error Adding User: {user.user_name}")
                db.print_last_response()
                return

def execute_with_retry(db, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            db.query(query)
            if db.last_query_ok():
                return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt + 1 == max_retries:
                return False
            time.sleep(1) 
    return False

def load_files_and_connections(db, files_csv):
    files = pd.read_csv(files_csv).to_records(index=False)

    for file in files:
        try:
            # Add the File entity
            add_file_query = [
                {
                    "AddEntity": {
                        "class": "File",
                        "_ref": 1,
                        "if_not_found": {
                            "path": ["==", file.file_path]
                        },
                        "properties": {
                            "name": file.file_name,
                            "path": file.file_path,
                            "type": "document"
                        }
                    }
                }
            ]
            print(f"Executing AddEntity query for file: {file.file_name}")
            db.query(add_file_query)

            if not db.last_query_ok():
                print(f"Error Adding File Entity: {file.file_name}")
                db.print_last_response()
                continue

            user_ids = [int(uid) for uid in str(file.user_ids).split(",")]

            for user_id in user_ids:
                connection_query = [
                    {
                        "FindEntity": {
                            "with_class": "User",
                            "_ref": 2,
                            "constraints": {
                                "user_id": ["==", user_id]
                            }
                        }
                    },
                    {
                        "FindEntity": {
                            "with_class": "File",
                            "_ref": 1,
                            "constraints": {
                                "path": ["==", file.file_path]
                            }
                        }
                    },
                    {
                        "AddConnection": {
                            "class": "FileAccess",
                            "src": 2,
                            "dst": 1
                        }
                    }
                ]

                print(f"Executing Connection query for User ID: {user_id} and File: {file.file_name}")
                db.query(connection_query)

                if not db.last_query_ok():
                    print(f"Error Adding Connection for User ID: {user_id} and File: {file.file_name}")
                    db.print_last_response()
                    continue

        except Exception as e:
            print(f"Unexpected error processing file {file.file_name}: {e}")
            continue




def main():
    users_csv = "users_sp.csv"
    files_csv = "files_sp.csv"

    db = Utils.create_connector()
    # db = create_connector()

    print("Loading Users...")
    load_users(db, users_csv)

    load_files_and_connections(db, files_csv)

    print("Data has been successfully loaded into ApertureDB!")


if __name__ == "__main__":
    main()