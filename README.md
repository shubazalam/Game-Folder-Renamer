# Game Folder Renamer

A Docker-based tool that automatically renames your PC game folders using IGDB.com data. It adds release years and cleans up folder names, transforming folders like `Dead.Space-RUNE` into `Dead Space (2008)`.

> **Note**: This tool is designed for organizing archived game folders (like GOG downloads stored on a NAS) and not for renaming installed games. It's perfect for cleaning up your game backup folders, ensuring consistent naming across your collection.

## Features

- Automatically fetches correct game names and release years from IGDB
- Handles multiple matches for games (e.g., remakes vs originals)
- Cleans up release group names and version numbers for consistent naming
- Cleans up common naming patterns (release groups, dots, underscores)
- Runs in Docker for easy deployment on any system

## Use Case

This tool is ideal for scenarios like:
- Organizing GOG game downloads in your backup storage
- Maintaining a clean game archive on your NAS
- Standardizing folder names in your game collection

It is **not** intended for:
- Renaming installed games
- Modifying game installation directories
- Renaming active game folders

## Prerequisites

- Docker installed on your system
  - [Install Docker for Windows](https://docs.docker.com/desktop/install/windows-install/)
  - [Install Docker for Mac](https://docs.docker.com/desktop/install/mac-install/)
  - [Install Docker for Linux](https://docs.docker.com/engine/install/)
- IGDB API credentials (free)
  - Sign up at [IGDB](https://api.igdb.com)
  - Create a Twitch application to get your credentials

## Setup

1. Clone this repository or download the files:
   ```bash
   git clone https://github.com/yourusername/game-folder-renamer.git
   cd game-folder-renamer
   ```

2. Get your IGDB API credentials:
   - Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
   - Create a new application
   - Note down your Client ID and Client Secret

3. Build the Docker image:
   ```bash
   docker-compose build
   ```

## Usage

### Using Docker Compose

1. Edit the docker-compose.yml file to set your games folder path:
   ```yaml
   services:
     game-renamer:
       image: game-renamer
       build: .
       environment:
         - IGDB_CLIENT_ID=your_client_id_here     # Get from Twitch Developer Console
         - IGDB_CLIENT_SECRET=your_secret_here    # Get from Twitch Developer Console
       volumes:
         - "/path/to/games:/games"  # Windows example
   ```

2. Run the container:
   ```bash
   docker-compose run --rm -it game-renamer
   ```

   The flags:
   - `--rm`: Automatically remove the container when it exits
   - `-it`: Enable interactive mode (required for command input)

3. Once the container is running, you'll see an interactive prompt. Type `rename` to start the renaming process:
   ```
   Game Folder Renamer - Interactive Mode
   ------------------------------------
   Commands:
     rename  - Scan and rename game folders
     help    - Show this help message
     exit    - Exit the container
   
   Enter command: rename
   ```

### Using Docker directly

Run the container interactively:
```bash
docker run -it --rm \
  -e IGDB_CLIENT_ID=your_id \
  -e IGDB_CLIENT_SECRET=your_secret \
  -v "/path/to/games:/games" \
  game-renamer
```

Then use the `rename` command when you want to process your folders.

#### Example Commands

- `rename` - Start the folder renaming process
- `help` - Show available commands
- `exit` - Exit the container

## How It Works

1. The script scans the specified games folder
2. For each folder:
   - Cleans up the name for searching
   - Queries IGDB for matching games
   - If multiple matches are found, prompts for selection
   - Renames the folder with the correct name and release year

## Version Numbers

For better organization, it's recommended to keep version information inside the game folder rather than in the folder name. For example:

```
Dead Space (2008)/
├── Dead Space v1.2.exe
├── version.txt
└── ...
```

This keeps the main folder names clean and consistent while maintaining version information where it belongs - with the game files themselves.

### Example Transformations

```
Before                          After
-------                         -----
Dead.Space.v1.2              → Dead Space (2008)
Warhammer.40000.SM.2-RUNE    → Warhammer 40000 Space Marine II (2024)
A.Plague.Tale.Innocence      → A Plague Tale Innocence (2019)
```
 
