
#### Machine Specific Aliases ####


# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
if [ -x "/usr/local/anaconda3/bin/conda" ] || [ -r "/usr/local/anaconda3/etc/profile.d/conda.sh" ]; then
__conda_setup="$('/usr/local/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/usr/local/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/usr/local/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/usr/local/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
fi
# <<< conda initialize <<<

# Module management
if type module >/dev/null 2>&1; then
  module purge
  module load gcc/9.3/cuda/12.1
fi



alias mydata='cd /share/lazy/Mohamed/'

#### Machine Specific Aliases ####

