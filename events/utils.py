import uuid
import boto3
from django.conf import settings

def upload_image_to_s3(file, folder="media/events"):
    # Generate a unique filename
    filename = f"{folder}/{uuid.uuid4()}_{file.name}"

    # Upload to S3 using boto3
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    s3.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, filename)

    # Return the full S3 URL
    return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{filename}"


def delete_image_from_s3(s3_url):
    # Extract the object key from the S3 URL
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    domain = settings.AWS_S3_CUSTOM_DOMAIN
    object_key = s3_url.replace(f"https://{domain}/", "")
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    try:
        s3.delete_object(Bucket=bucket_name, Key=object_key)
    except Exception as e:
        print(f"Error deleting image from S3: {e}")
