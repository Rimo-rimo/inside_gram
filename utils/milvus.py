import dotenv
dotenv.load_dotenv()
import os
from pymilvus import MilvusClient
from pymilvus import model
import numpy as np
from pymilvus import MilvusClient, Collection, connections, DataType, CollectionSchema, FieldSchema

from utils.clova_studio import get_embedding

client = MilvusClient()

def get_memory(content, user_id):

    query_vectors = get_embedding(content)

    res = client.search(
        collection_name="inside_gram",  # target collection
        data=[query_vectors],  # query vectors
        limit=1,  # number of returned entities
        filter=f"user_id == '{user_id}'",
        output_fields=["text"]  # specifies fields to be returned
    )
    return res