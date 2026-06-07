# Optional Conda integration.

for _conda_prefix in \
  "$HOME/miniforge3" \
  "$HOME/miniconda3" \
  "$HOME/anaconda3" \
  "/opt/conda" \
  "/opt/homebrew/Caskroom/miniforge/base"
do
  if [[ -x "$_conda_prefix/bin/conda" ]]; then
    __conda_setup="$("$_conda_prefix/bin/conda" 'shell.zsh' 'hook' 2> /dev/null)"
    if [[ $? -eq 0 ]]; then
      eval "$__conda_setup"
    elif [[ -f "$_conda_prefix/etc/profile.d/conda.sh" ]]; then
      source "$_conda_prefix/etc/profile.d/conda.sh"
    fi
    unset __conda_setup
    break
  elif [[ -f "$_conda_prefix/etc/profile.d/conda.sh" ]]; then
    source "$_conda_prefix/etc/profile.d/conda.sh"
    break
  elif [[ -d "$_conda_prefix/bin" ]]; then
    _path_prepend "$_conda_prefix/bin"
    break
  fi
done
unset _conda_prefix

if command -v conda >/dev/null 2>&1 && [[ -z "${CONDA_EXE-}" ]]; then
  __conda_setup="$(conda 'shell.zsh' 'hook' 2> /dev/null)"
  if [[ $? -eq 0 ]]; then
    eval "$__conda_setup"
  fi
  unset __conda_setup
fi
