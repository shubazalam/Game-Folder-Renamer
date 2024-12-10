#!/bin/bash
set -e

echo "Game Folder Renamer - Interactive Mode"
echo "------------------------------------"
echo "Commands:"
echo "  rename  - Scan and rename game folders"
echo "  help    - Show this help message"
echo "  exit    - Exit the container"
echo ""

while true; do
    read -r -p "Enter command: " cmd
    case "${cmd}" in
        "rename")
            python rename_games.py
            ;;
        "help")
            echo "Commands:"
            echo "  rename  - Scan and rename game folders"
            echo "  help    - Show this help message"
            echo "  exit    - Exit the container"
            ;;
        "exit")
            exit 0
            ;;
        "")
            # Do nothing on empty input
            ;;
        *)
            echo "Unknown command. Type 'help' for available commands."
            ;;
    esac
    echo ""
done 