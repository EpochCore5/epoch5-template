#!/bin/bash
# Launcher script for EPOCH5 Agent Monitor Dashboard

# Colors for console output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default settings
HOST="0.0.0.0"
PORT=8050
BASE_DIR="./archive/EPOCH5"
DEBUG=false

# Print banner
echo -e "${BLUE}"
echo "    ______ ____   ____   ____ _    _______    ___                  __    "
echo "   / ____// __ \ / __ \ / __ \ |  / /__  /   /   |   ____ _ _____ / /__ "
echo "  / __/  / /_/ // / / // / / / | / /  / /   / /| |  / __ \`// ___// //_/"
echo " / /___ / ____// /_/ // /_/ /| |/ /  / /__ / ___ | / /_/ // /__ / ,<   "
echo "/_____//_/     \____/ \____/ |___/  /____//_/  |_| \__, / \___//_/|_|  "
echo "                                                   /____/               "
echo "                 __  ___             _ __                               "
echo "                /  |/  /____   ____(_) /__  ____   _____               "
echo "               / /|_/ // __ \ / __// // _ \/ __ \ / ___/               "
echo "              / /  / // /_/ // /_ / //  __/ / / // /                   "
echo "             /_/  /_/ \____/ \__//_/ \___/_/ /_//_/                    "
echo -e "${NC}"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --host=*)
      HOST="${1#*=}"
      shift
      ;;
    --port=*)
      PORT="${1#*=}"
      shift
      ;;
    --base-dir=*)
      BASE_DIR="${1#*=}"
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --help)
      echo -e "${YELLOW}Usage: $0 [options]${NC}"
      echo "Options:"
      echo "  --host=HOST         Host to listen on (default: 0.0.0.0)"
      echo "  --port=PORT         Port to listen on (default: 8050)"
      echo "  --base-dir=DIR      Base directory for EPOCH5 (default: ./archive/EPOCH5)"
      echo "  --debug             Run in debug mode"
      echo "  --help              Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information."
      exit 1
      ;;
  esac
done

# Check if required Python packages are installed
echo -e "${YELLOW}Checking required packages...${NC}"
REQUIRED_PACKAGES=("dash" "dash-bootstrap-components" "plotly" "pandas")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
  if ! python -c "import $package" &> /dev/null; then
    MISSING_PACKAGES+=("$package")
  fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
  echo -e "${RED}Missing required packages: ${MISSING_PACKAGES[*]}${NC}"
  echo -e "${YELLOW}Would you like to install them now? (y/n)${NC}"
  read -r install_choice
  
  if [[ $install_choice == "y" || $install_choice == "Y" ]]; then
    echo -e "${BLUE}Installing required packages...${NC}"
    pip install "${MISSING_PACKAGES[@]}"
  else
    echo -e "${RED}Required packages are missing. Cannot continue.${NC}"
    exit 1
  fi
fi

# Create base directory if it doesn't exist
if [ ! -d "$BASE_DIR" ]; then
  echo -e "${YELLOW}Creating base directory: $BASE_DIR${NC}"
  mkdir -p "$BASE_DIR"
fi

# Start the dashboard
echo -e "${GREEN}Starting EPOCH5 Agent Monitor Dashboard...${NC}"
echo -e "${BLUE}Host: $HOST${NC}"
echo -e "${BLUE}Port: $PORT${NC}"
echo -e "${BLUE}Base Directory: $BASE_DIR${NC}"
echo -e "${BLUE}Debug Mode: $DEBUG${NC}"

if [ "$DEBUG" = true ]; then
  python agent_monitor.py dashboard --host="$HOST" --port="$PORT" --base-dir="$BASE_DIR" --debug
else
  python agent_monitor.py dashboard --host="$HOST" --port="$PORT" --base-dir="$BASE_DIR"
fi
