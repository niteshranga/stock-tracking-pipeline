#!/bin/bash

# LocalStack S3 Initialization Script
# This script runs automatically when LocalStack starts
# It creates S3 buckets and folder structures needed for the pipeline

set -e

echo "==== Initializing LocalStack S3 ===="

# Wait for LocalStack to be ready
sleep 5

# Set AWS credentials for local access
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Create S3 buckets
echo "Creating S3 buckets..."

awslocal s3 mb s3://raw-stock-data --region us-east-1 2>/dev/null || echo "Bucket raw-stock-data already exists"
awslocal s3 mb s3://processed-stock-data --region us-east-1 2>/dev/null || echo "Bucket processed-stock-data already exists"
awslocal s3 mb s3://archive-stock-data --region us-east-1 2>/dev/null || echo "Bucket archive-stock-data already exists"

# Create folder structure in raw-stock-data bucket
echo "Creating folder structure in S3 buckets..."

# Create sample folders for current date (for testing)
YEAR=$(date +%Y)
MONTH=$(date +%m)
DAY=$(date +%d)

# Create raw data structure: s3://raw-stock-data/stock-data/raw/year=YYYY/month=MM/day=DD/
awslocal s3api put-object --bucket raw-stock-data --key "stock-data/raw/year=${YEAR}/month=${MONTH}/day=${DAY}/.gitkeep" 2>/dev/null || true

# Create processed data structure: s3://processed-stock-data/stock-data/processed/year=YYYY/month=MM/day=DD/
awslocal s3api put-object --bucket processed-stock-data --key "stock-data/processed/year=${YEAR}/month=${MONTH}/day=${DAY}/.gitkeep" 2>/dev/null || true

# Create archive structure
awslocal s3api put-object --bucket archive-stock-data --key "stock-data/archive/year=${YEAR}/month=${MONTH}/.gitkeep" 2>/dev/null || true

echo "Listing S3 buckets..."
awslocal s3 ls

echo "Listing raw-stock-data bucket contents..."
awslocal s3 ls s3://raw-stock-data --recursive

echo "==== LocalStack S3 initialization completed ===="
