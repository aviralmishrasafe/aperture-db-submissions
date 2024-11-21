# LangSafe Demo

demo:
run run.sh - it will build then run the demo
storage is a directory created by aperturedb which stores the created graph
./data is a directory where you can pass files into client for easy testing.
enable the other command in client build to run tests by hand.

app:
load.py loads data into db.
check.py runs a permissions check
test_files.sh runs load then a bunch of checks.

description:
model.md explains what the model is

# Langsafe Submission

## Connecting to Sharepoint

The Sharepoint Connector is not public but when available, can make a request either through Postman
or the attached sharepoint_connection.py file to the /sharepoint/sync endpoint which populates our S3 Bucket and our Redis with permissions

## Loading CSV's

The load_sp_data.py file run with python load_sp_data.py
Creates two CSV's files that outline permissions and our users, users_sp.csv and files_sp.csv

## Loading to Aperture

load_aperture.py creates the relationships between users and files

## Verifying

Code in check_aperture can perform checks whenever individual checks are required

## Rag Chatbot

rag_chatbot.py takes advantage of langchain's basic rag implementions in order to create a Rag that forms embeddings from the S3 Bucket, and uses Aperture's Graph Structure with is_connected_to to verify if a user should be able to access a particular chunk or not.
