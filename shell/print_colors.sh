#!/bin/bash

# 
# print_colors.sh
#
# For each primary color, prints the RGB colors
# in the 0->255 ranges for both foreground and
# background colors.
#

COLOR_VARS="./color_vars.sh"

if [[ ! -e $COLOR_VARS ]]; then

    echo
    echo "Missing $COLOR_VARS"
    echo
    exit

fi

source $COLOR_VARS

for PRIMARY_COLOR in $PRIMARY_COLORS; do

    for (( N = 0; N <= 255; N++ )); do
    
        eval "COLOR=\$FG_${PRIMARY_COLOR}${N}"
        echo -n -e "${COLOR}${N}${REVERSE}${N}${RESET}"

    done

    echo -e "${ERASE_TO_EOL}${RESET}"

done



