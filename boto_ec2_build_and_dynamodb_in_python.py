import boto3
import sys
import time

# Set variables
REGION = "us-west-2"
INSTANCE_TYPE = "t2.micro"
AMI_ID = "ami-0d081196e3df05f4d"  # Amazon Linux 2 AMI in us-west-2
INSTANCE_NAME = "pokiapi"
KEY_NAME = "poki_game_key"
DYNAMODB_TABLE_NAME = "PokemonCollection"

# Initialize boto3 clients
ec2 = boto3.client('ec2', region_name=REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION)
dynamodb = boto3.client('dynamodb', region_name=REGION)

def create_key_pair():
    print(f"Creating new key pair: {KEY_NAME}")
    try:
        key_pair = ec2.create_key_pair(KeyName=KEY_NAME)
        with open(f"{KEY_NAME}.pem", 'w') as key_file:
            key_file.write(key_pair['KeyMaterial'])
        print(f"Key pair saved as {KEY_NAME}.pem")
    except ec2.exceptions.ClientError as e:
        print(f"Error: Failed to create key pair. {e}")
        sys.exit(1)

def get_vpc_id():
    print("Available VPCs:")
    vpcs = ec2.describe_vpcs()
    for vpc in vpcs['Vpcs']:
        vpc_name = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
        print(f"VPC ID: {vpc['VpcId']}, Name: {vpc_name}")

    vpc_id = input("Enter the VPC ID you want to use: ")
    try:
        ec2.describe_vpcs(VpcIds=[vpc_id])
        print(f"Using VPC: {vpc_id}")
        return vpc_id
    except ec2.exceptions.ClientError:
        print(f"Error: VPC '{vpc_id}' not found. Please enter a valid VPC ID.")
        sys.exit(1)

def create_security_group(vpc_id):
    security_group_name = "pokemon-collector-sg"
    try:
        security_group = ec2.create_security_group(
            GroupName=security_group_name,
            Description="Security group for Pokemon Collector",
            VpcId=vpc_id
        )
        security_group_id = security_group['GroupId']
        print(f"Created Security Group: {security_group_id}")

        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
        return security_group_id
    except ec2.exceptions.ClientError as e:
        print(f"Error creating security group: {e}")
        sys.exit(1)

def create_ec2_instance(security_group_id):
    try:
        instances = ec2_resource.create_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            KeyName=KEY_NAME,
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[security_group_id],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': INSTANCE_NAME
                        },
                    ]
                },
            ]
        )
        instance = instances[0]
        print(f"Created EC2 instance: {instance.id}")
        return instance
    except ec2.exceptions.ClientError as e:
        print(f"Error creating EC2 instance: {e}")
        sys.exit(1)

def create_dynamodb_table():
    try:
        table = dynamodb.create_table(
            TableName=DYNAMODB_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'name',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"Creating DynamoDB table {DYNAMODB_TABLE_NAME}...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=DYNAMODB_TABLE_NAME)
        print(f"DynamoDB table {DYNAMODB_TABLE_NAME} created successfully.")
    except dynamodb.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"DynamoDB table {DYNAMODB_TABLE_NAME} already exists.")
        else:
            print(f"Error creating DynamoDB table: {e}")
            sys.exit(1)

def main():
    create_key_pair()
    vpc_id = get_vpc_id()
    security_group_id = create_security_group(vpc_id)
    instance = create_ec2_instance(security_group_id)
    create_dynamodb_table()

    print("Waiting for the instance to be running...")
    instance.wait_until_running()
    instance.reload()

    public_ip = instance.public_ip_address
    print(f"EC2 instance '{INSTANCE_NAME}' is now running with IP: {public_ip}")
    print(f"You can SSH into the instance using: ssh -i {KEY_NAME}.pem ec2-user@{public_ip}")
    print(f"DynamoDB table '{DYNAMODB_TABLE_NAME}' is ready for use.")

if __name__ == "__main__":
    main()
