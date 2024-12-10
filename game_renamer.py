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
        
        # Try different variations of the name
        search_variations = []
        
        # Clean up the search query
        search_query = self._clean_folder_name(game_name)
        
        # Add base search
        search_variations.append(search_query)
        
        # Common edition patterns to try removing
        edition_patterns = [
            r'\s*-?\s*Enhanced Edition$',
            r'\s*-?\s*Definitive Edition$',
            r'\s*-?\s*Anniversary$',
            r'\s*-?\s*Complete Edition$',
            r'\s*-?\s*Game of the Year Edition$',
            r'\s*-?\s*GOTY Edition$',
            r'\s*-?\s*Deluxe Edition$'
        ]
        
        # Try variations without edition names
        base_name = search_query
        for pattern in edition_patterns:
            cleaned_name = re.sub(pattern, '', base_name)
            if cleaned_name != base_name:
                base_name = cleaned_name
                search_variations.append(cleaned_name)
        
        # Add variation with colon
        if " " in base_name:
            first_word, rest = base_name.split(" ", 1)
            with_colon = f"{first_word}: {rest}"
            search_variations.append(with_colon)
        
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Try each variation until we find a match
        for query in search_variations:
            body = f'''
                search "{query}";
                fields name, first_release_date, version_parent;
                where category = 0 & platforms = (6);
                limit 15;  # Get more results but show 5 at a time
            '''
            
            response = requests.post(
                "https://api.igdb.com/v4/games",
                headers=headers,
                data=body
            )
            
            if response.status_code == 200:
                games = response.json()
                if games:
                    break  # Found some matches, stop trying variations
        else:
            return None  # No matches found with any variation
        
        if response.status_code == 200:
            games = response.json()
            if not games:
                return None
            
            if len(games) == 1:
                game = games[0]
                release_date = datetime.fromtimestamp(game["first_release_date"]).year
                return (game["name"], release_date)
            
            # Multiple matches found - ask user to choose
            page = 0
            page_size = 5
            
            while True:
                print(f"\nMultiple matches found for '{search_query}':")
                start_idx = page * page_size
                end_idx = min(start_idx + page_size, len(games))
                
                for i, game in enumerate(games[start_idx:end_idx], start_idx + 1):
                    year = datetime.fromtimestamp(game.get("first_release_date", 0)).year if game.get("first_release_date") else "TBA"
                    # Check if it's a remake/remaster
                    version_type = " (Remake/Remaster)" if "version_parent" in game else ""
                    print(f"{i}. {game['name']} ({year}){version_type}")
                
                if end_idx < len(games):
                    print("\nType 'm' for more results")

                while True:
                    try:
                        choice = input("\nPlease choose a number (or 's' to skip, 'm' for more): ").lower()
                        if choice == 's':
                            return None
                        if choice == 'm':
                            if end_idx < len(games):
                                page += 1
                                break  # Break inner loop to show next page
                            else:
                                print("No more results to show.")
                                continue
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(games):
                            game = games[choice_idx]
                            release_date = datetime.fromtimestamp(game.get("first_release_date", 0)).year if game.get("first_release_date") else "TBA"
                            return (game["name"], release_date)
                        else:
                            print("Invalid choice. Please try again.")
                    except ValueError:
                        print("Invalid input. Please enter a number, 's' to skip, or 'm' for more.")
                
                if choice != 'm':  # If we didn't request more results, exit the outer loop
                    break
    
        return None

    def _clean_folder_name(self, folder_name: str) -> str:
        """Clean up folder name for better search results"""
        # Remove common patterns that might interfere with search
        patterns = [
            r'-\w+$',  # Remove release group names like "-RUNE"
            r'v\d+(\.\d+)*',  # Remove version numbers like v1.0.12
            r'\([^)]*\)',  # Remove anything in parentheses
            r'Enhanced Edition$',  # Remove "Enhanced Edition" from the end
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