# Native macOS command variants and applications.
unalias hn gen_pass firefox web orion bypass_xyz 2>/dev/null || true
alias ls='ls -G'
alias dls='cd "$HOME/Library/Services"'
if command -v clx >/dev/null 2>&1; then alias hn='clx'; fi

if [ -d '/Applications/Firefox Developer Edition.app' ]; then
  alias firefox='open -a "/Applications/Firefox Developer Edition.app"'
  alias web='firefox'
fi
if [ -d '/Applications/Orion RC.app' ]; then alias orion='open -a "/Applications/Orion RC.app"'; fi
alias safari='open -a "/Applications/Safari.app"'
alias hidedesktop='defaults write com.apple.finder CreateDesktop -bool false && killall Finder'
alias showdesktop='defaults write com.apple.finder CreateDesktop -bool true && killall Finder'
alias find_apps='mdfind kMDItemAppStoreHasReceipt=1'
alias badge='tput bel'
alias battery='pmset -g batt'

alias mac-update='sudo softwareupdate -i -a'
alias clear_dns='sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder'
alias localip='ipconfig getifaddr en0'
alias ip6_on='sudo networksetup -setv6automatic Wi-Fi'
alias ip6_off='sudo networksetup -setv6off Wi-Fi'
if command -v dnscrypt-proxy >/dev/null 2>&1; then
  alias bypass_xyz='dnscrypt-proxy -config "$HOME/.config/dnscrypt-proxy/dnscrypt-proxy.toml"'
fi
