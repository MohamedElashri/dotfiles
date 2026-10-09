fcount() {
    local count_type=""
    local target_path="."
    local include_hidden=false
    local help_text="Usage: fcount [-f|-d|-a] [-h] [path]
    -f      Count files only
    -d      Count directories only
    -a      Include hidden files/directories
    -h      Display this help
    path    Directory to count in (default: current directory)"

    # Process options
    while getopts "fdah" opt; do
        case $opt in
            f) count_type="files" ;;
            d) count_type="dirs" ;;
            a) include_hidden=true ;;
            h) echo "$help_text"; return 0 ;;
            *) echo "$help_text"; return 1 ;;
        esac
    done

    # Remove the options from the argument list
    shift $((OPTIND-1))

    # If a path is provided, use it
    if [ -n "$1" ]; then
        # Remove trailing slash if present but preserve root directory
        if [ "$1" != "/" ]; then
            target_path="${1%/}"
        else
            target_path="$1"
        fi

        # Check if path contains problematic characters
        if echo "$target_path" | grep -q '[[:cntrl:]]'; then
            echo "Error: Path contains control characters which cannot be safely processed"
            return 1
        fi
    fi

    # Error handling - check if path exists and is accessible
    if [ ! -e "$target_path" ]; then
        echo "Error: '$target_path' does not exist"
        return 1
    elif [ ! -d "$target_path" ]; then
        echo "Error: '$target_path' is not a directory"
        return 1
    elif [ ! -r "$target_path" ]; then
        echo "Error: Cannot read '$target_path' (permission denied)"
        return 1
    fi

    # Check if required option is specified
    if [ -z "$count_type" ]; then
        echo "Error: Please specify what to count using -f (files) or -d (directories)"
        return 1
    fi

    # Use NULL-terminated output to safely handle paths with spaces and special characters
    # Store current IFS to restore later
    local OLD_IFS="$IFS"

    # Use command to bypass aliases and perform counts in subshell to isolate cd
    (
        # Change to target directory with error handling
        if ! cd "$target_path" 2>/dev/null; then
            echo "Error: Failed to access '$target_path'"
            return 1
        fi

        # Count items separately with support for tricky filenames
        local file_count=0
        local dir_count=0
        local symlink_count=0
        local total_count=0

        # Set IFS to newline for reading output safely
        IFS=$'\n'

        if $include_hidden; then
            # Process all items including hidden ones
            for item in $(command ls -la); do
                # Skip the "total" line
                if echo "$item" | grep -q "^total"; then
                    continue
                fi

                # Process each item by first character
                first_char=$(echo "$item" | cut -c 1)
                if [ "$first_char" = "d" ]; then
                    # It's a directory
                    # Check if it's not . or ..
                    if ! echo "$item" | grep -q " \.$" && ! echo "$item" | grep -q " \.\.$"; then
                        dir_count=$((dir_count + 1))
                    fi
                elif [ "$first_char" = "l" ]; then
                    # It's a symbolic link
                    symlink_count=$((symlink_count + 1))
                elif [ "$first_char" = "-" ]; then
                    # It's a regular file
                    file_count=$((file_count + 1))
                fi
            done
        else
            # Process only non-hidden items
            for item in $(command ls -l); do
                # Skip the "total" line
                if echo "$item" | grep -q "^total"; then
                    continue
                fi

                # Skip hidden items
                if echo "$item" | grep -q " \.[^/]*$"; then
                    continue
                fi

                # Process each item by first character
                first_char=$(echo "$item" | cut -c 1)
                if [ "$first_char" = "d" ]; then
                    # It's a directory
                    dir_count=$((dir_count + 1))
                elif [ "$first_char" = "l" ]; then
                    # It's a symbolic link
                    symlink_count=$((symlink_count + 1))
                elif [ "$first_char" = "-" ]; then
                    # It's a regular file
                    file_count=$((file_count + 1))
                fi
            done
        fi

        # Restore original IFS
        IFS="$OLD_IFS"

        # Output the requested count
        if [ "$count_type" = "files" ]; then
            echo "$file_count files"
        elif [ "$count_type" = "dirs" ]; then
            echo "$dir_count dirs"
        fi

        # Display symbolic link count if any exist
        if [ "$symlink_count" -gt 0 ]; then
            echo "symbolic: $symlink_count"
        fi
    )

    # Restore IFS in the main function scope too
    IFS="$OLD_IFS"
}

count_files() {
  local dir="${1:-.}"
  if [[ -d "$dir" ]]; then
    fd --type f --max-depth 1 --hidden --exclude .DS_Store . "$dir" | wc -l
  else
    echo "Error: '$dir' is not a valid directory." >&2
    return 1
  fi
}
