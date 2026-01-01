import boto3
import pandas as pd
import logging
from src.logger import logging
from io import StringIO

class s3_operations:
    def __init__(self,bucket_name,aws_access_key,aws_secret_key,region_name='us-east-1'):
        self.bucket_name=bucket_name
        self.s3_client=boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region_name
        )
        logging.info("Data_ingestion from s3 bucket has started")
    def fetch_file_from(self,file_key):
        try:
            logging.info(f"fetching file '{file_key}' from s3 bucket '{self.s3_client}'")
            obj=self.s3_client.get_object(Bucket=self.bucket_name,key=file_key)
            df=pd.read_csv(obj['body'].read().decode('utf-8'))
            logging.info(f"Successfully fetched and loaded '{file_key}' from S3 that has {len(df)} records.")
            return df
        except Exception as e:
            logging.exception(f"❌ Failed to fetch '{file_key}' from S3: {e}")
            return None