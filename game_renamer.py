import os
import re
from datetime import datetime
import requests
from typing import Optional, Tuple
import time

class IGDBClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires = 0

    def authenticate(self) -> None:
        """Get Twitch OAuth token for IGDB API access"""
        auth_url = "https://id.twitch.tv/oauth2/token"
        auth_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        response = requests.post(auth_url, data=auth_data)
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expires = time.time() + data["expires_in"]
        else:
            raise Exception("Authentication failed")

    def ensure_authenticated(self) -> None:
        """Check if token is expired and refresh if needed"""
        if not self.access_token or time.time() >= self.token_expires:
            self.authenticate()

    def search_game(self, game_name: str) -> Optional[Tuple[str, int]]:
        """Search for a game and return its official name and release year"""
        self.ensure_authenticated()
        
        # Clean up the search query
        search_query = self._clean_folder_name(game_name)
        
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }
        
        body = f'''
            search "{search_query}";
            fields name, first_release_date, version_parent;
            where category = 0 & platforms = (6);
            limit 5;
        '''
        
        response = requests.post(
            "https://api.igdb.com/v4/games",
            headers=headers,
            data=body
        )
        
        if response.status_code == 200:
            games = response.json()
            if not games:
                return None
            
            if len(games) == 1:
                game = games[0]
                release_date = datetime.fromtimestamp(game["first_release_date"]).year
                return (game["name"], release_date)
            
            # Multiple matches found - ask user to choose
            print(f"\nMultiple matches found for '{search_query}':")
            for i, game in enumerate(games, 1):
                year = datetime.fromtimestamp(game.get("first_release_date", 0)).year if game.get("first_release_date") else "TBA"
                # Check if it's a remake/remaster
                version_type = " (Remake/Remaster)" if "version_parent" in game else ""
                print(f"{i}. {game['name']} ({year}){version_type}")
            
            while True:
                try:
                    choice = input("\nPlease choose a number (or 's' to skip): ")
                    if choice.lower() == 's':
                        return None
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(games):
                        game = games[choice_idx]
                        release_date = datetime.fromtimestamp(game.get("first_release_date", 0)).year if game.get("first_release_date") else "TBA"
                        return (game["name"], release_date)
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number or 's' to skip.")
    
        return None

    def _clean_folder_name(self, folder_name: str) -> str:
        """Clean up folder name for better search results"""
        # Remove common patterns that might interfere with search
        patterns = [
            r'-\w+$',  # Remove release group names like "-RUNE"
            r'v\d+(\.\d+)*',  # Remove version numbers like v1.0.12
            r'\([^)]*\)',  # Remove anything in parentheses
        ]
        
        name = folder_name
        for pattern in patterns:
            name = re.sub(pattern, '', name)
            
        # Replace dots and underscores with spaces
        name = name.replace('.', ' ').replace('_', ' ')
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        return name

class GameFolderRenamer:
    def __init__(self, igdb_client: IGDBClient, base_path: str):
        self.igdb_client = igdb_client
        self.base_path = base_path
        self.stats = {
            'total': 0,
            'renamed': 0,
            'skipped': 0,
            'errors': 0
        }

    def process_folders(self) -> None:
        """Process all folders in the base path"""
        self.stats = {'total': 0, 'renamed': 0, 'skipped': 0, 'errors': 0}
        for folder_name in os.listdir(self.base_path):
            if os.path.isdir(os.path.join(self.base_path, folder_name)):
                self.stats['total'] += 1
                self._process_single_folder(folder_name)
        
        print(f"\nRename complete!")
        print(f"Found: {self.stats['total']} folders")
        print(f"Renamed: {self.stats['renamed']} folders")
        print(f"Skipped: {self.stats['skipped']} folders")
        if self.stats['errors'] > 0:
            print(f"Errors: {self.stats['errors']} folders")

    def _process_single_folder(self, folder_name: str) -> None:
        """Process a single folder and rename if necessary"""
        # Check if folder already follows naming convention
        if re.match(r'.+ \(\d{4}\)$', folder_name):
            print(f"Skipping {folder_name} - already properly named")
            self.stats['skipped'] += 1
            return

        # Search for game info
        game_info = self.igdb_client.search_game(folder_name)
        
        if game_info:
            game_name, release_year = game_info
            # Only add year if it's not TBA
            new_name = f"{game_name} ({release_year})" if release_year != "TBA" else game_name
            
            old_path = os.path.join(self.base_path, folder_name)
            new_path = os.path.join(self.base_path, new_name)
            
            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {folder_name} -> {new_name}")
                self.stats['renamed'] += 1
            except OSError as e:
                print(f"Error renaming {folder_name}: {e}")
                self.stats['errors'] += 1
        else:
            print(f"Could not find game info for: {folder_name}")
            self.stats['errors'] += 1