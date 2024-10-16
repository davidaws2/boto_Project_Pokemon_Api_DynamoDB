import boto3
import requests
import random
from botocore.exceptions import ClientError

# DynamoDB table name
TABLE_NAME = "PokemonCollection"

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

# Function to get a Pokemon from DynamoDB
def get_pokemon(name):
    try:
        response = table.get_item(Key={'name': name})
        return response.get('Item')
    except ClientError as e:
        print(f"Error retrieving Pokemon from DynamoDB: {e}")
        return None

# Function to save a Pokemon to DynamoDB
def save_pokemon(pokemon):
    try:
        table.put_item(Item=pokemon)
        print(f"Successfully saved {pokemon['name']} to DynamoDB.")
    except ClientError as e:
        print(f"Error saving Pokemon to DynamoDB: {e}")

# Function to get a random Pokemon from the API
def get_random_pokemon():
    # Get a list of all Pokemon
    response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=100")
    all_pokemon = response.json()["results"]
    
    # Choose a random Pokemon
    random_pokemon = random.choice(all_pokemon)
    
    # Get details of the chosen Pokemon
    pokemon_url = random_pokemon["url"]
    response = requests.get(pokemon_url)
    pokemon_data = response.json()
    
    # Extract the information we want to save
    pokemon_info = {
        "name": pokemon_data["name"],
        "type": pokemon_data["types"][0]["type"]["name"],
        "ability": pokemon_data["abilities"][0]["ability"]["name"]
    }
    
    return pokemon_info

# Main program
def main():
    while True:
        # Ask the user if they want to draw a Pokemon
        choice = input("Would you like to draw a Pokemon? (yes/no): ").lower()
        
        if choice == "yes":
            # Get a random Pokemon
            pokemon = get_random_pokemon()
            
            # Check if we already have this Pokemon
            existing_pokemon = get_pokemon(pokemon["name"])
            if existing_pokemon:
                print(f"You already have {pokemon['name']}!")
                pokemon = existing_pokemon
            else:
                # Add the new Pokemon to our collection
                save_pokemon(pokemon)
                print(f"You got a new Pokemon: {pokemon['name']}!")
            
            # Display Pokemon info
            print(f"Name: {pokemon['name']}")
            print(f"Type: {pokemon['type']}")
            print(f"Ability: {pokemon['ability']}")
            
        elif choice == "no":
            print("Thanks for playing! Goodbye!")
            break
        
        else:
            print("Please enter 'yes' or 'no'.")

# Run the main program
if __name__ == "__main__":
    main()
