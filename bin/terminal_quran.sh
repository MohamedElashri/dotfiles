#!/bin/bash

if [[ ${1:-} == -h || ${1:-} == --help ]]; then
    cat <<'HELP'
Usage: terminal_quran.sh [--help]
Display a random Quran verse. Zsh startup already calls this script.
To disable startup display, set this in ~/.config/dotfiles/local.zsh:
    export RUN_QURAN_VERSE_ON_STARTUP=false
HELP
    exit 0
fi

# Define an array of Quran verses
verses=(
    "Indeed, Allah is with the patient. [Quran 2:153]"
    "He created the heavens and earth in truth and formed you and perfected your forms, and to Him is the [final] destination. [Quran 64:3]"
    "And whoever relies upon Allah, then He is sufficient for him. Indeed, Allah will accomplish His purpose. Allah has already set for everything a [decreed] extent. [Quran 65:3]"
    "My mercy encompasses all things. [Quran 7:156]"
    "Indeed, I am near. [Quran 2:186]"
    "He knows what is in every heart. [Quran 67:13]"
    "Allah does not burden a soul beyond that it can bear. [Quran 2:286]"
    "So verily, with the hardship, there is relief. Verily, with the hardship, there is relief. [Quran 94:5-6]"
    "Do what is beautiful. Allah loves those who do what is beautiful. [Quran 2:195]"
    "This worldly life is no more than play and amusement. But the Hereafter is indeed the real life, if only they knew. [Quran 29:64]"
    "And so that Allah will help you tremendously. [Quran 48:3]"
    "You who believe, seek help through steadfastness and prayer, for God is with the steadfast. [Quran 2:153]"
    "And whoever puts all his trust in Allah, He will be enough for him. [Quran 65:3]"
    "And We have commanded people to honor their parents. Their mothers bore them through hardship upon hardship, and their weaning takes two years. So be grateful to Me and your parents. To Me is the final return. [Quran 31:14]"
    "People who repent and do good deeds truly return to God. [Quran 13:27]"
    "Except those who repent, believe, and do good deeds: God will change the evil deeds of such people into good ones. He is most forgiving, most merciful. [Quran 25:70]"
    "Yet I am most Forgiving towards those who repent, believe, do righteous deeds, and stay on the right path. [Quran 20:82]"
    "Do they not know that it is God Himself who accepts repentance from His servants and receives what is given freely for His sake? [Quran 9:104]"
    "And speak to people good words. [Quran 2:83]"
    "Keep up the prayer and pay the prescribed alms. Whatever good you store up for yourselves, you will find it with God: He sees everything you do. [Quran 2:110]"
    "So whoever does an atom's weight of good will see it. [Quran 99:7]"
    "For God is with those who are mindful of Him and who do good. [Quran 16:128]"
    "And so God gave them both the rewards of this world and the excellent rewards of the Hereafter: God loves those who do good. [Quran 3:148]"
    "Be steadfast: God does not let the rewards of those who do good go to waste. [Quran 11:115]"
    "Know that the life of this world is only play and amusement, pomp and mutual boasting among you, and rivalry in respect of wealth and children. [Quran 57:20]"
    "Is the reward for good [anything] but good. [Quran 55:60]"
    "Is it you who brought it down from the clouds, or is it We who bring it down? If We willed, We could make it bitter, so why are you not grateful? [Quran 56:69]"
)

# Generate a random number within the range of the verses array
index=$(($RANDOM % ${#verses[@]}))

# Select a random verse
random_verse=${verses[$index]}

# Define colors
GREEN="\033[92m" # Green color
BLUE="\033[94m" # Blue color
MAGENTA="\033[95m" # Magenta color
RESET="\033[0m" # Reset color

# Calculate the number of columns in the terminal once
COLS=${COLS:-$(tput cols 2>/dev/null || printf 80)}
case "$COLS" in ''|*[!0-9]*) COLS=80 ;; esac

# Define the header message
header_message="This is a self message from Quran:"

# Calculate the padding needed to center the header message
padding=$(( (COLS > ${#header_message} ? COLS - ${#header_message} : 0) / 2 ))

# Print the centered header message in magenta
printf "%${padding}s" "" # Add padding before the message
echo -e "${MAGENTA}${header_message}${RESET}\n"

# Define the Quran ASCII art
ascii_art="
  ██████╗ ██╗   ██╗██████╗  █████╗ ███╗   ██╗
 ██╔═══██╗██║   ██║██╔══██╗██╔══██╗████╗  ██║
 ██║   ██║██║   ██║██████╔╝███████║██╔██╗ ██║
 ██║▄▄ ██║██║   ██║██╔══██╗██╔══██║██║╚██╗██║
 ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██║ ╚████║
  ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
"

# Calculate padding to center the ASCII art
art_padding=$(( (COLS > 50 ? COLS - 50 : 0) / 2 )) # Assuming ASCII art width is 50

# Print the centered ASCII art
while IFS= read -r line; do
    printf "%${art_padding}s" ""
    echo -e "$line"
done <<< "$ascii_art"

# Split the verse into text and location based on the last occurrence of brackets
verse_text=${random_verse% [*}
verse_location="[${random_verse##* [}"

# Print the verse text in bold green and the location in blue
bold=$(tput bold 2>/dev/null || true)
normal=$(tput sgr0 2>/dev/null || true)
echo -e "${GREEN}${bold}${verse_text}${normal}${RESET} ${BLUE}${verse_location}${RESET}"

# Add a newline
echo -e "\n"
