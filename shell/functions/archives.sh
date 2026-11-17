# Archive helpers shared by Bash and Zsh. Optional formats require their extractor.

zipf() {
  if [ "$#" -ne 1 ] || [ -z "${1:-}" ]; then echo 'Usage: zipf PATH' >&2; return 2; fi
  local source=$1
  while [ "$source" != / ] && [ "${source%/}" != "$source" ]; do source=${source%/}; done
  case "$source" in -*) source="./$source" ;; esac
  zip -r "$source.zip" "$source"
}

extract() {
  [ "$#" -eq 1 ] || { echo 'Usage: extract ARCHIVE' >&2; return 2; }
  local archive=$1
  case "$archive" in -*) archive="./$archive" ;; esac
  if [[ -f "$archive" ]]; then
    case "$archive" in
      *.tar.bz2) tar xjf "$archive" ;;
      *.tar.gz)  tar xzf "$archive" ;;
      *.bz2)     bunzip2 "$archive" ;;
      *.rar)     unrar e "$archive" ;;
      *.gz)      gunzip "$archive" ;;
      *.tar)     tar xf "$archive" ;;
      *.tbz2)    tar xjf "$archive" ;;
      *.tgz)     tar xzf "$archive" ;;
      *.zip)     unzip "$archive" ;;
      *.Z)       uncompress "$archive" ;;
      *.7z)      7z x "$archive" ;;
      *) echo "'$1' cannot be extracted via extract()" >&2; return 2 ;;
    esac
  else
    echo "'$1' is not a valid file" >&2
    return 1
  fi
}
