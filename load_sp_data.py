import redis
import csv
import boto3
import json

S3_BUCKET_NAME = "aperturedb-bucket"
S3_BUCKET_LOCATION = "us-west-2"

s3_client = boto3.client('s3', region_name=S3_BUCKET_LOCATION)

REDIS_PATH = "redis://localhost:6379/"
redis_client = redis.from_url(REDIS_PATH, decode_responses=True)

def fetch_file_from_s3(file_key):
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        file_content = response['Body'].read()
        return file_content
    except Exception as e:
        print(f"Error fetching file {file_key}: {e}")
        return None
    
def fetch_metadata_from_s3(file_key):
    metadata_key = f"{file_key}.metadata"  
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=metadata_key)
        metadata_content = response['Body'].read()
        metadata = json.loads(metadata_content)
        return metadata
    except Exception as e:
        print(f"Error fetching metadata for {file_key}: {e}")
        return None

def transform_s3_key(redis_key):
    """Transforms Redis-style key to S3-compatible key."""
    if redis_key.startswith("sharepoint:///"):
        return redis_key.replace("sharepoint:///", "sharepoint/", 1)
    return redis_key


def get_acl_from_redis():
    """Fetch ACLs from Redis and update paths to S3-compatible format."""
    user_to_resources = {}
    resources = redis_client.keys("*") 
    for resource in resources:
        transformed_resource = transform_s3_key(resource) 
        users = redis_client.smembers(resource)  
        for user in users:
            if user not in user_to_resources:
                user_to_resources[user] = []
            user_to_resources[user].append(transformed_resource)
    return user_to_resources


def write_users_csv(user_to_resources, output_file="users_sp.csv"):
    """Write user data to users_sp.csv."""
    users = list(user_to_resources.keys())
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["user_id", "user_name"])  
        for user in users:
            writer.writerow([hash(user), user]) 



def write_files_csv(user_to_resources, output_file="files_sp.csv"):
    """Write file and permission data to files_sp.csv."""
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["file_name", "file_path", "user_ids"])  
        file_permissions = {}
        
        for user, resources in user_to_resources.items():
            user_id = hash(user)  
            for resource in resources:
                file_name = resource.split("/")[-1]  
                file_path = f"s3://{S3_BUCKET_NAME}/{resource}" 


                if file_path not in file_permissions:
                    file_permissions[file_path] = {"file_name": file_name, "user_ids": []}
                file_permissions[file_path]["user_ids"].append(user_id)


        for file_path, data in file_permissions.items():
            writer.writerow([data["file_name"], file_path, ",".join(map(str, data["user_ids"]))])



if __name__ == "__main__":
    user_to_resources = get_acl_from_redis()

    write_users_csv(user_to_resources)
    write_files_csv(user_to_resources)

    print("CSV files have been generated successfully.")