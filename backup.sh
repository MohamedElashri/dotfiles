#!/bin/bash

# Backup script for dotfiles

# Define colors for log messages
COLOR_RED="\033[0;31m"  # Red color for error messages
COLOR_GREEN="\033[0;32m"  # Green color for success messages
COLOR_YELLOW="\033[0;33m"  # Yellow color for warning messages
COLOR_BLUE="\033[0;34m"  # Blue color for informational messages
COLOR_RESET="\033[0m"  # Reset color to default

# Logging functions to provide colored log messages for different types of events
log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"
}

log_warning() {
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"
}

# Function to check if a file exists
# Takes a file path as an argument and logs the result
check_file_exists() {
    local file_path="$1"
    log_info "Checking if file '$file_path' exists."
    if [ -f "$file_path" ]; then
        return 0  # File exists
    else
        return 1  # File does not exist
    fi
}

# Function to copy file to backup location
# Takes the source file path and the target backup directory as arguments
backup_file() {
    local file_path="$1"
    local backup_dir="$2"
    local backup_path="$backup_dir/$(basename "$file_path")"  # Determine the target path for the backup
    
    log_info "Copying '$file_path' to '$backup_path'."
    cp "$file_path" "$backup_path" && \  # Copy the file and log the outcome
    log_success "Successfully backed up '$file_path' to '$backup_path'." || \  # Log success or error
    log_error "Failed to back up '$file_path'."
}

# Main backup function
# Takes the backup directory as an argument and performs the backup process
perform_backup() {
    local backup_dir="$1"
    
    log_info "Starting backup to directory '$backup_dir'."
    # Create backup directory if it does not exist
    mkdir -p "$backup_dir" || { log_error "Failed to create backup directory '$backup_dir'"; exit 1; }

    # List of directories and files to backup with target directories
    declare -A backup_items=(
        ["$HOME/.ssh/config"]="$backup_dir/ssh"  # Backup SSH config
        ["$HOME/.gitconfig"]="$backup_dir/git"  # Backup Git config
        ["$HOME/.stCommitMsg"]="$backup_dir/git"  # Backup Git commit message template
        ["$HOME/.zshrc"]="$backup_dir/zsh"  # Backup Zsh configuration
        ["$HOME"/*.zsh]="$backup_dir/zsh"  # Backup all .zsh files in the home directory
        ["$HOME/cli/*"]="$backup_dir/cli"  # Backup all files in the cli directory
    )

    # Loop through each file or directory and perform the backup
    for item in "${!backup_items[@]}"; do
        local target_dir="${backup_items[$item]}"
        log_info "Processing item '$item' with target directory '$target_dir'."
        # Create target directory if it does not exist
        mkdir -p "$target_dir" || { log_error "Failed to create target directory '$target_dir'"; continue; }
        # Loop through each file that matches the pattern in item
        for file in $item; do
            log_info "Handling file '$file'."
            if [ -e "$file" ]; then
                backup_file "$file" "$target_dir"
            else
                log_warning "Item '$file' not found. Skipping."  # Log if the file does not exist
            fi
        done
    done
}

# Entry point of the script
main() {
    local backup_dir="."  # Define the default backup directory
    log_info "Starting main backup process."
    perform_backup "$backup_dir"  # Call the main backup function
    log_info "Backup process completed. Please review any warnings."  # Log the completion of the process
}

main "$@"  # Call the main function with all command-line arguments