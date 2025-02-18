import os
import boto3
from dotenv import load_dotenv

load_dotenv()


# Create an S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)

# Escrever em um bucket
bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")
object_name = "test.txt"
content = "Olá Mundo"

s3.put_object(Bucket=bucket_name, Key=object_name, Body=content)
