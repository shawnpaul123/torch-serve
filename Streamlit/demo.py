# Importing dependencies
import streamlit as st
import os
import yaml
from azure.storage.blob import ContainerClient
import requests

#Creating title for streamlit website
st.title('ASL app')

#Creating a button to upload an image
image = st.file_uploader("Upload an image")

#Creating a function to load the contents of the config file
def load_config():
    dir_root = os.path.dirname(os.path.abspath(__file__))
    with open (dir_root + "/config.yaml", "r") as yamlfile:
        return yaml.load(yamlfile, Loader=yaml.FullLoader)

#Creating a function to upload image to azure blob storage
def upload(image, connection_string, container_name):
    container_client = ContainerClient.from_connection_string(connection_string, container_name)
    print("Uploading files to blob storage...")
    blob_client = container_client.upload_blob(name = "img1", data = image)
    print(f'img1 uploaded to blob storage')

#Create a function to delete image in azure blob storage
def delete(image, connection_string, container_name):
    container_client = ContainerClient.from_connection_string(connection_string, container_name)
    print("Deleting files to blob storage...")
    container_client.delete_blobs("img1")
    print(f'img1 deleted from blob storage')

#Loading config parameters and uploading image to blob storage
config = load_config()
upload(image, config["azure_storage_connectionstring"], config["container_name"])

# Making a get request to get the json of the image
response = requests.get('https://prod-05.northcentralus.logic.azure.com:443/workflows/9d0aa73d77754b40821db349edfda90c/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=8VtSemSIBJiiYWrz2eKjJIFTNpP_iI-mIO0-ktYJeRE')
  
# print response
print(response)
  
# print json content
print(response.json())

#Clearing blob for next upload
delete(image, config["azure_storage_connectionstring"], config["container_name"])





     
