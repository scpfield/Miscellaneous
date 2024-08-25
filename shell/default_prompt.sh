#!/bin/bash

#
# default_prompt.sh
#
# Source this file to get a default prompt that uses bash 
# prompt-aware color variables (sourced from color_vars.sh),
# so there is no garbled text when using up/down arrow keys
# to scroll through command-history.
#
# It has an example of making a new color.
#
# It also uses bash's $SHLVL to indicate if you are
# in a subshell.  If not it won't print anything.
#

source ./color_vars.sh

# If we're in a subshell, make a red tag to be shown in the prompt.

LEVEL=$( [[ ${SHLVL} > 1 ]] && echo "${P_FG_RED255}(Level:${SHLVL})${P_RESET} " )

# Combine GREEN128 and BLUE255 to make a light-blue color.

P_FG_LIGHTBLUE=$(MakeNewColor $P_FG_GREEN128 OR $P_FG_BLUE255)

# Make a basic prompt using the bash-aware color variables (P).

PS1="${LEVEL}${P_FG_LIGHTBLUE}\u@\h${P_FG_CYAN255} \w${P_FG_WHITE255} \$${P_RESET} "


