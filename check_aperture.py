from aperturedb import Utils
import argparse


def get_user_id(db, username):
    query = [
        {
            "FindEntity": {
                "with_class": "User",
                "constraints": {
                    "name": ["==", username]
                },
                "results": {
                    "all_properties": True
                }
            }
        }
    ]
    db.query(query)
    if not db.last_query_ok():
        print(f"Error fetching user ID for username: {username}")
        print(db.response)
        return None

    response = db.response
    users = response[0].get("FindEntity", {}).get("entities", [])
    if not users:
        print(f"No user found with username: {username}")
        return None

    return users[0].get("user_id")


def get_user_files(db, user_id):
    query = [
        {
            "FindEntity": {
                "with_class": "User",
                "_ref": 1,
                "constraints": {
                    "user_id": ["==", user_id]
                }
            }
        },
        {
            "FindEntity": {
                "with_class": "File",
                "is_connected_to": {
                    "ref": 1  
                },
                "results": {
                    "all_properties": True
                }
            }
        }
    ]
    print(f"Querying ApertureDB for files accessible by user_id: {user_id}")
    db.query(query)

    if not db.last_query_ok():
        print("Error fetching files for user.")
        print(db.response)
        return []

    response = db.response
    files = response[1].get("FindEntity", {}).get("entities", [])
    file_paths = [file.get("path") for file in files if "path" in file]
    print(f"User has access to {len(file_paths)} files.")
    return file_paths


def main():
    parser = argparse.ArgumentParser(description="Fetch all files accessible by a user.")
    parser.add_argument('--username', required=True, help="Username to check.")
    args = parser.parse_args()

    username = args.username
    db = Utils.create_connector()

    user_id = get_user_id(db, username)
    if not user_id:
        print(f"Failed to find user ID for username: {username}")
        return

    file_paths = get_user_files(db, user_id)

    if file_paths:
        print(f"Files accessible by {username}:")
        for path in file_paths:
            print(path)
    else:
        print(f"No files found for user: {username}")


if __name__ == "__main__":
    main()
