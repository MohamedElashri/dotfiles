#!/bin/bash

# Backup script for dotfiles

# Define colors for log messages
COLOR_RED="\033[0;31m"
COLOR_GREEN="\033[0;32m"
COLOR_YELLOW="\033[0;33m"
COLOR_BLUE="\033[0;34m"
COLOR_RESET="\033[0m"

# Logging functions
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
check_file_exists() {
    local file_path="$1"
    if [ -f "$file_path" ]; then
        log_info "File '$file_path' found."
        return 0
    else
        log_warning "File '$file_path' not found. Skipping."
        return 1
    fi
}

# Function to copy file to backup location
backup_file() {
    local file_path="$1"
    local backup_dir="$2"
    local backup_path="$backup_dir/$(basename "$file_path")"
    
    if [ -f "$file_path" ]; then
        cp "$file_path" "$backup_path"
        if [ $? -eq 0 ]; then
            log_success "Successfully backed up '$file_path' to '$backup_path'."
        else
            log_error "Failed to back up '$file_path'."
        fi
    fi
}

# Main backup function
perform_backup() {
    local backup_dir="$1"
    
    # Create backup directory if it does not exist
    if [ ! -d "$backup_dir" ]; then
        log_info "Creating backup directory '$backup_dir'."
        mkdir -p "$backup_dir"
        if [ $? -ne 0 ]; then
            log_error "Failed to create backup directory '$backup_dir'."
            exit 1
        fi
    fi

    # List of directories to backup files to
    declare -A backup_dirs=(
        ["$HOME/.ssh/config"]="$backup_dir/ssh"
        ["$HOME/.gitconfig"]="$backup_dir/git"
        ["$HOME/.stCommitMsg"]="$backup_dir/git"
        ["$HOME/.zshrc"]="$backup_dir/zsh"
        ["$HOME"/*.zsh]="$backup_dir/zsh"
        ["$HOME/cli/*.*"]="$backup_dir/cli"
    )

    # Loop through each file and perform the backup
    for file_path in "${!backup_dirs[@]}"; do
        local target_dir="${backup_dirs[$file_path]}"
        mkdir -p "$target_dir"
        for file in $file_path; do
            if [ -e "$file" ]; then
                check_file_exists "$file" && backup_file "$file" "$target_dir"
            fi
        done
    done
}

# Entry point
main() {
    local backup_dir="."
    perform_backup "$backup_dir"
    log_info "Backup process completed. Please review any warnings."
}

main "$@"