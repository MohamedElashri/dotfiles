################################## ME HEP dotfiles ##################################


## LHCb 
alias proxy='lhcb-proxy-init' # fire the cern lhcb proxy 
#alias conda='lb-conda' # My life has enough confusion
alias afs='cd /afs/cern.ch/work/m/melashri'  # go to my afs space
alias home='cd /afs/cern.ch/user/m/melashri' # go to my user-space 
alias work='cd /afs/cern.ch/work/m/melashri' # go to my work-space
alias eos='cd /eos/user/m/melashri' # go to my eos space
alias eos_lhcb='cd /eos/lhcb/user/m/melashri' # go to my eos lhcb space
#alias run='lb-run' # I will use LHCb only anyways

## Grid
alias kinit_='kinit -k -t /afs/cern.ch/user/m/melashri/private/key/melashri.keytab melashri@CERN.CH'





################# functions ###################

ktmux(){
     if [[ -z "$1" ]]; then #if no argument passed
        k5reauth -f -i 3600 -p melashri -k /afs/cern.ch/user/m/melashri/private/key/melashri.keytab -- tmux new-session
     else #pass the argument as the tmux session name
        k5reauth -f -i 3600 -p melashri -k /afs/cern.ch/user/m/melashri/private/key/melashri.keytab -- tmux new-session -s $1
        fi
                }


################# functions ###################


################################## ME HEP dotfiles ##################################
