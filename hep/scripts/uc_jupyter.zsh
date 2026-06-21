#!/bin/zsh
# This script automates the process of starting a Jupyter Notebook on a remote server,
# checking for and handling already running instances, ensuring the specified port is available,
# and setting up SSH port forwarding. It allows configuration through command-line arguments.
#
# Usage Examples:
# - Using long names:
# ./uc_jupyter.zsh --host "sleepy-earth" --environment "bphysics" --remote-port "8765" --local-port "8765" --directory "~"
#
# - Using short names:
# ./uc_jupyter.zsh -h "sleepy-earth" -e "bphysics" -rp "8765" -lp "8765" -d "~"
#
# Arguments:
# -h, --host: Specifies the SSH host configuration name. Default is "sleepy-earth" (Connecting to UC sleepy machine using earth as proxy jump step).
# -e, --environment: Specifies the Conda environment to activate. Default is "bphysics" (my conda enviroment for 4-B decay).
# -rp, --remote-port: Specifies the remote port for the Jupyter Notebook server. Default is "8765" (I hope no one will use that).
# -lp, --local-port: Specifies the local port for SSH port forwarding. Default is "8765" (because I will forget if this changed anyway).
# -d, --directory: Specifies the directory on the remote server to start Jupyter Notebook in. Default is "~"".
#
# The script checks if the specified remote port is in use and suggests an alternative if necessary.
# It also checks for existing Jupyter Notebook processes, offering the option to kill them and start anew.
# Port forwarding is set up automatically, and the script extracts and displays the Jupyter Notebook URL for easy access.




# Default Configuration
HOST="sleepy-earth"
CONDA_ENV="bphysics"
REMOTE_PORT="8765"
LOCAL_PORT="8765"
NOTEBOOK_DIR="~"

# Parse command-line arguments
zparseopts -E -D -a opts \
  h:=host -host:=host \
  e:=env -environment:=env \
  rp:=remote_port -remote-port:=remote_port \
  lp:=local_port -local-port:=local_port \
  d:=directory -directory:=directory

for opt in "${(@)opts}"; do
  case "$opt" in
    (host) HOST="$opts[$opt+1]" ;;
    (env) CONDA_ENV="$opts[$opt+1]" ;;
    (remote_port) REMOTE_PORT="$opts[$opt+1]" ;;
    (local_port) LOCAL_PORT="$opts[$opt+1]" ;;
    (directory) NOTEBOOK_DIR="$opts[$opt+1]" ;;
  esac
done

# Function to check if a port is in use on the remote server
check_remote_port() {
    ssh $HOST "lsof -i:$1" > /dev/null 2>&1
    echo $?
}

# Function to suggest a new port
suggest_new_port() {
    echo $((RANDOM % 65535 + 1024)) # Suggest a port between 1024 and 65535
}

# Check remote port availability
PORT_STATUS=$(check_remote_port $REMOTE_PORT)
if [[ $PORT_STATUS -eq 0 ]]; then
    echo "Port $REMOTE_PORT is in use on the remote server."
    SUGGESTED_PORT=$(suggest_new_port)
    echo "Suggested alternative: $SUGGESTED_PORT"
    read "?Use suggested port (Yes), enter a new port (No), or exit (any other key)? [Y/n/exit] " user_choice

    case $user_choice in
        [Yy]* )
            REMOTE_PORT=$SUGGESTED_PORT
            LOCAL_PORT=$SUGGESTED_PORT
            ;;
        [Nn]* )
            read "?Enter a new port number: " user_port
            REMOTE_PORT=$user_port
            LOCAL_PORT=$user_port
            ;;
        * )
            echo "Exiting script."
            exit 0
            ;;
    esac
fi

# Check for existing Jupyter Notebook processes
echo "Checking for existing Jupyter Notebook processes on $HOST..."
EXISTING_NB=$(ssh $HOST "pgrep -af jupyter-notebook")

if [[ $EXISTING_NB ]]; then
    echo "Found existing Jupyter Notebook processes:"
    echo "$EXISTING_NB"
    read "?Do you want to kill existing processes and start a new one? [y/N] " user_choice
    if [[ "$user_choice" == [Yy]* ]]; then
        echo "Killing existing Jupyter Notebook processes..."
        ssh $HOST "pkill -f jupyter-notebook"
        echo "Existing processes killed."
    else
        echo "Exiting without starting a new Jupyter Notebook."
        exit 0
    fi
fi

# Start Jupyter Notebook on the remote server within the specified Conda environment
echo "Starting Jupyter Notebook on $HOST..."
JUPYTER_CMD="source ~/.zshrc; conda activate $CONDA_ENV; jupyter notebook --no-browser --port=$REMOTE_PORT --notebook-dir=$NOTEBOOK_DIR"
SSH_CMD="ssh -t $HOST \"$JUPYTER_CMD\""

# Execute SSH command and capture output to extract the URL
NOTEBOOK_URL=$(eval $SSH_CMD | tee /tmp/jupyter_log.txt | grep -oP 'http://127.0.0.1:'"$REMOTE_PORT"'/\?token=\S+')

if [ -z "$NOTEBOOK_URL" ]; then
    echo "Failed to start Jupyter Notebook. Check /tmp/jupyter_log.txt for errors."
    exit 1
fi

echo "Jupyter Notebook started successfully."

# Setup port forwarding in the background
echo "Setting up port forwarding from localhost:$LOCAL_PORT to $HOST:$REMOTE_PORT..."
ssh -N -f -L $LOCAL_PORT:localhost:$REMOTE_PORT $HOST
if [ $? -ne 0 ]; then
    echo "Failed to set up port forwarding. Check SSH configuration."
    exit 2
fi

echo "Port forwarding setup successfully."

# Extract and display the URL with the token, replacing the remote port with the local one
LOCAL_NOTEBOOK_URL=$(echo $NOTEBOOK_URL | sed "s/127.0.0.1:$REMOTE_PORT/localhost:$LOCAL
