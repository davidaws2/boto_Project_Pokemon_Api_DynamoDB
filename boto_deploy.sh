#!/bin/bash

# Update the system
sudo yum update -y

# Install git
sudo yum install git -y

# Install Python 3 and pip
sudo yum install python3 python3-pip -y

# Install required Python packages
sudo pip3 install boto3 requests

# Clone the GitHub repository
git clone https://github.com/davidaws2/boto_Project_Pokemon_Api_DynamoDB
cd boto_Project_Pokemon_Api_DynamoDB

# Copy the Python scripts to the home directory
cp boto_pokemonapi.py ~/pokemon_app.py
cp boto_ec2_build_and_dynamodb_in_python.py ~/setup_infrastructure.py

# Create a startup script
cat << EOF > ~/start_pokemon_app.sh
#!/bin/bash
python3 ~/pokemon_app.py
EOF

chmod +x ~/start_pokemon_app.sh

# Set up the application to run on startup
echo "@reboot /home/ec2-user/start_pokemon_app.sh" | sudo tee -a /etc/crontab

# Create a setup script for infrastructure (if needed)
cat << EOF > ~/setup_infrastructure.sh
#!/bin/bash
python3 ~/setup_infrastructure.py
EOF

chmod +x ~/setup_infrastructure.sh

# Add AWS credentials (you'll need to replace these with secure methods in production)
mkdir -p ~/.aws
cat << EOF > ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-west-2
EOF

# Display instructions
echo "Deployment completed. To start the application manually, run: ~/start_pokemon_app.sh"
echo "To set up the infrastructure (if needed), run: ~/setup_infrastructure.sh"
echo "The application will also start automatically on system reboot."
