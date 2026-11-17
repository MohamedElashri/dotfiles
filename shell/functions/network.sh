# Network, remote-file and upload helpers; network runs only on invocation.

unalias myip 2>/dev/null || true
myip() {
  [ "$#" -eq 0 ] || { echo 'Usage: myip' >&2; return 2; }
  curl --fail --show-error https://ifconfig.me && printf '\n'
}

_dotfiles_weather() {
  [ "$#" -eq 1 ] || { echo 'Weather shortcuts take no extra arguments.' >&2; return 2; }
  local forecast
  forecast=$(curl --fail --show-error "https://wttr.in/$1") || return
  printf '%s\n' "$forecast" | awk 'NR <= 7'
}

open_remote_pdf() {
  if [[ "$#" -ne 2 ]]; then
    echo "Usage: open_remote_pdf HOST /remote/path/file.pdf"
    return 2
  fi

  local host="$1"
  local remote_file="$2"
  local base tmp directory viewer result

  case "$(uname -s)" in Darwin) viewer=open ;; *) viewer=xdg-open ;; esac
  command -v "$viewer" >/dev/null 2>&1 || { echo "Install $viewer before opening a remote PDF." >&2; return 1; }

  base="$(basename "$remote_file")"
  directory="$(mktemp -d "${TMPDIR:-/tmp}/remote-pdf.XXXXXX")" || return
  tmp="$directory/$base"

  if scp -o ClearAllForwardings=yes -o ForwardX11=no \
    "${host}:${remote_file}" "$tmp"; then
    :
  else
    result=$?
    echo 'Failed to copy remote PDF' >&2
    command rm -f -- "$tmp"
    command rmdir -- "$directory"
    return "$result"
  fi

  if [[ "$viewer" == open ]]; then
    command open "$tmp"
  else
    command xdg-open "$tmp" >/dev/null 2>&1 &
  fi
}

cheat() {
  curl "https://cheat.sh/$1"
}

transfer() {
  local file
  local -a file_array
  file_array=("${@}")

  if [[ "$#" -eq 0 || "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "transfer - Upload arbitrary files to \"tr.melashri.eu.org\"."
    echo ""
    echo "Usage: transfer [options] [<file>]..."
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help"
    echo "      show this message"
    echo ""
    echo "EXAMPLES:"
    echo "  Upload a single file from the current working directory:"
    echo "      transfer \"image.img\""
    echo ""
    echo "  Upload multiple files from the current working directory:"
    echo "      transfer \"image.img\" \"image2.img\""
    echo ""
    echo "  Upload a file from a different directory:"
    echo "      transfer \"/tmp/some_file\""
    echo ""
    echo "  Upload all files from the current working directory. Be aware of the webserver's rate limiting!:"
    echo "      transfer *"
    echo ""
    echo "  Upload a single file from the current working directory and filter out the delete token and download link:"
    echo "      transfer \"image.img\" | awk --field-separator=\": \" '/Delete token:/ { print \$2 } /Download link:/ { print \$2 }'"
    echo ""
    echo "  Show help text from \"transfer.sh\":"
    echo "      curl --request GET \"https://tr.melashri.eu.org\""
    return 0
  fi

  for file in "${file_array[@]}"; do
    if [[ ! -f "${file}" ]]; then
      echo -e "\e[01;31m'${file}' could not be found or is not a file.\e[0m" >&2
      return 1
    fi
  done
  unset file

  local upload_files curl_output awk_output

  command du -L "${file_array[@]}" >&2 || return
  printf 'Upload these %s file(s) to tr.melashri.eu.org? [Y/n] ' "${#file_array[@]}" >&2
  IFS= read -r upload_files || return 1

  case "${upload_files:-y}" in
    "y"|"Y")
      for file in "${file_array[@]}"; do
        curl_output=$(curl --fail --show-error --request PUT --progress-bar --dump-header - --upload-file "${file}" "https://tr.melashri.eu.org/") || return
        awk_output=$(awk \
          'gsub("\r", "", $0) && tolower($1) ~ /x-url-delete/ \
          {
            delete_link=$2;
            print "Delete command: curl --request DELETE " "\""delete_link"\"";

            gsub(".*/", "", delete_link);
            delete_token=delete_link;
            print "Delete token: " delete_token;
          }

          END{
            print "Download link: " $0;
          }' <<< "${curl_output}")

        echo -e "${awk_output}\n"

        if (( ${#file_array[@]} > 4 )); then
          sleep 5
        fi
      done
      ;;
    "n"|"N")
      return 1
      ;;
    *)
      echo -e "\e[01;31mWrong input: '${upload_files}'.\e[0m" >&2
      return 1
      ;;
  esac
}
