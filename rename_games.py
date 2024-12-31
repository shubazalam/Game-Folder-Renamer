from game_renamer import IGDBClient, GameFolderRenamer
import os

def main():
    # Get credentials directly from environment variables
    client_id = os.environ.get('IGDB_CLIENT_ID')
    client_secret = os.environ.get('IGDB_CLIENT_SECRET')
    games_folder = os.environ.get('GAMES_FOLDER', '/games')
    dry_run = os.environ.get('DRY_RUN', 'false').lower()
    
    if not all([client_id, client_secret]):
        print("Please set IGDB_CLIENT_ID and IGDB_CLIENT_SECRET environment variables")
        return
    
    # Initialize IGDB client and renamer
    igdb_client = IGDBClient(client_id, client_secret)
    renamer = GameFolderRenamer(igdb_client, games_folder, dry_run)
    
    # Process all folders
    renamer.process_folders()

if __name__ == "__main__":
    main() 
