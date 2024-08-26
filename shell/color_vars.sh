#!/bin/bash

#
# color_vars.sh
#
# Intended to be sourced by other scripts
# to use variables declared by this script.
#
# Variables for colors will be created for each 
# primary color in the 0->255 RBG palette ranges, 
# for both foregound (FG) + background (BG) colors, 
# for general-use and bash prompt-aware formats.
#
#  General-use color variables:
#
#  FG_RED0      ->  FG_RED255
#  FG_GREEN0    ->  FG_GREEN255
#  FG_BLUE0     ->  FG_BLUE255
#  FG_YELLOW0   ->  FG_YELLOW255
#  FG_MAGENTA0  ->  FG_MAGENTA255
#  FG_CYAN0     ->  FG_CYAN255
#  FG_WHITE0    ->  FG_WHITE255
#
#  Prompt-aware color variables:
#
#  P_FG_RED0      ->  P_FG_RED255
#  P_FG_GREEN0    ->  P_FG_GREEN255
#  P_FG_BLUE0     ->  P_FG_BLUE255
#  P_FG_YELLOW0   ->  P_FG_YELLOW255
#  P_FG_MAGENTA0  ->  P_FG_MAGENTA255
#  P_FG_CYAN0     ->  P_FG_CYAN255
#  P_FG_WHITE0    ->  P_FG_WHITE255
#
#  Background color variables are named with "BG".
#
#  Use like regular bash variables:
#
#     echo -e "${FG_BLUE125} blue text ${RESET}"
#
#     echo -e "${UNDERLINE}${FG_RED225} underlined red text ${RESET}"
#
#  Or in a bash prompt (using the prompt-aware vars):
#
#     PS1="${P_FG_YELLOW230}\w ${P_FG_GREEN230}$ ${P_RESET}"
#
#  etc..
#
#  To create new colors from the auto-generated variables, 
#  a bash function is provided at the end of this script, which 
#  applies a bitwise operator given two RGB values.
#
#  Operators:    OR, AND, XOR
#  Negations:   ~OR, ~AND, ~XOR
#
#  Usage:
#
#       MakeNewColor <COLOR1> <OPERATOR> <COLOR2>
#
#  Example, to combine $FG_RED100 and $FG_GREEN100:
#
#       MakeNewColor $FG_RED100 OR $FG_GREEN100
#  
#  Negation operators apply to the 2nd color value.  Example:
#
#       $FG_RED100 ~AND $FG_RED50
#
#  is the equivalent of:  $FG_RED100 & ~$FG_RED50
#
#  Function returns exit code status 0 (success) or 1 (failed).
#
#  The new color value or the failure reason are communicated
#  to the caller by echoing the value.
#
#  Suggested usage:
#  
#       NEW_COLOR=$(MakeNewColor $FG_RED100 OR $FG_GREEN100)
#
#       if [[ $? -eq 0 ]]; then
#
#           echo -e "$NEW_COLOR this is the new color $RESET"
#
#       else
#
#           echo "Failed: $NEW_COLOR"
#
#       fi
#


# Terminal escape code, either: \e[   or  \033[
ESC='\e['

# Non-Printable sequence start + ends for PS1 /
# bash prompts. Refer to bash manpage in the 
# PROMPTING section.
#
# Without these, bash prompts get mangled when
# using up/down arrows to view command history.

NPS='\['
NPE='\]'

# Various ANSI control sequences that should
# work on modern terminals.
#
# Both general and bash-prompt formats are 
# provided.

RESET="${ESC}0m"
ITALIC="${ESC}3m"
UNDERLINE="${ESC}4m"
BLINK="${ESC}5m"
REVERSE="${ESC}7m"
STRIKETHROUGH="${ESC}9m"
CLEARSCREEN="${ESC}2J"
ERASE_TO_EOL="${ESC}K"

P_RESET=${NPS}${RESET}${NPE}
P_ITALIC="${NPS}${ITALIC}${NPE}"
P_UNDERLINE="${NPS}${UNDERLINE}${NPE}"
P_BLINK="${NPS}${BLINK}${NPE}"
P_REVERSE="${NPS}${REVERSE}${NPE}"
P_STRIKETHROUGH="${NPS}${STRIKETHROUGH}${NPE}"

# Foreground / background sequences.
# Must be combined with a color.

FG=${ESC}'38;2;'
BG=${ESC}'48;2;'

#
# Now generate all the color variables.
#

PRIMARY_COLORS="RED GREEN BLUE YELLOW MAGENTA CYAN WHITE" 
COLOR=''

for PRIMARY_COLOR in $PRIMARY_COLORS; do

    for (( N = 0; N <= 255; N++ )); do
    
        case $PRIMARY_COLOR in

            "RED")                
                COLOR="${N};0;0m"
                ;;
            "GREEN")
                COLOR="0;${N};0m"
                ;;
            "BLUE")
                COLOR="0;0;${N}m"
                ;;
            "YELLOW")
                COLOR="${N};${N};0m"
                ;;
            "MAGENTA")
                COLOR="${N};0;${N}m"
                ;;
            "CYAN")
                COLOR="0;${N};${N}m"
                ;;
            "WHITE")
                COLOR="${N};${N};${N}m"
                ;;
        esac

        #
        # Dynamically generate bash variable names
        #

        # First put the names of the color variables 
        # as strings in these temp vars

        VAR_NAME_FG="FG_${PRIMARY_COLOR}${N}"
        VAR_NAME_P_FG="P_FG_${PRIMARY_COLOR}${N}"

        VAR_NAME_BG="BG_${PRIMARY_COLOR}${N}"
        VAR_NAME_P_BG="P_BG_${PRIMARY_COLOR}${N}"

        # Use an eval trick to dynamically create 
        # actual bash variables using the strings
        # in the values of the temp vars above

        eval declare '$VAR_NAME_FG="${FG}${COLOR}"'
        eval declare '$VAR_NAME_P_FG="${NPS}${FG}${COLOR}${NPE}"'

        eval declare '$VAR_NAME_BG="${BG}${COLOR}"'
        eval declare '$VAR_NAME_P_BG="${NPS}${BG}${COLOR}${NPE}"'

        #
        # The color variable is now usable, ex:
        #
        # $FG_RED150
        # $BG_RED150
        # $P_FG_RED150
        # $P_BG_RED150
        # 
        # Their values are the full ANSI escape sequences.
        #

    done

done


#
# This is a bash function to create new colors that are
# not part of the default set of colors automatically
# created.
#

function MakeNewColor {

    NEW_RGB=0
    FB_TYPE=0
    PT_TYPE=0

    [[ $# -lt 3 ]] && echo "Usage: COLOR1 OPERATOR COLOR2" && return 1
    
    COLOR1=$1
    COLOR2=$3
    OPERATOR=$2
    VALID_OPERATOR=0

    for OPERATOR_TYPE in OR ~OR AND ~AND XOR ~XOR; do

        [[ $OPERATOR == $OPERATOR_TYPE ]] && VALID_OPERATOR=1 && break
    
    done

    [[ $VALID_OPERATOR -eq 0 ]] && echo "Missing/Invalid operator: $OPERATOR" && return 1

    # Extract color values from args
    COLOR1VALS="$(echo $COLOR1 | tr -d '\\e[]m' | awk -F ';' '{print "FB1="$1"\n""R1="$3"\n""G1="$4"\n""B1="$5"\n"}')"
    COLOR1PVAL="$(echo $COLOR1 | grep -q ']'; echo $?)"

    COLOR2VALS="$(echo $COLOR2 | tr -d '\\e[]m' | awk -F ';' '{print "FB2="$1"\n""R2="$3"\n""G2="$4"\n""B2="$5"\n"}')"
    COLOR2PVAL="$(echo $COLOR2 | grep -q ']'; echo $?)"

    # Use eval trick to turn them into variables
    eval $COLOR1VALS
    eval $COLOR2VALS

    # Check for valid FG/BG data
    for FB in $FB1 $FB2; do

        if [[ $FB -ne 38 ]] && [[ $FB -ne 48 ]]; then

            echo "Incorrect FG/BG value: $FB"
            return 1

        fi

    done

    # Check for valid RGB color values
    for COLORVAL in $R1 $G1 $B1 $R2 $G2 $B2; do

        if [[ $COLORVAL -lt 0 ]] || [[ $COLORVAL -gt 255 ]]; then

            echo "Invalid color value: $COLORVAL"
            return 1

        fi

    done

    # Check color args are the same FG / BG type
    if [[ $FB1 -ne $FB2 ]]; then

        echo "Color FG and BG types must be the same: $FB1 != $FB2"
        return 1

    fi

    # Check that all args are the same PType
    if [[ $COLOR1PVAL -ne $COLOR2PVAL ]]; then

        echo "All P-type values must be the same: $COLORPVAL1 != $COLORPVAL2"
        return 1

    fi

    # Wold you believe it?  Bash supports bit shifting.

    RGB1=$(( $(( $R1 << 16 )) | $(( $G1 << 8 )) | $(( $B1 << 0 )) ))
    RGB2=$(( $(( $R2 << 16 )) | $(( $G2 << 8 )) | $(( $B2 << 0 )) ))

    case $OPERATOR in

        "OR")
            NEW_RGB=$(( $RGB1 | $RGB2 ))
            ;;
        "~OR")
            NEW_RGB=$(( $RGB1 | ~$RGB2 ))
            ;;
        "AND")
            NEW_RGB=$(( $RGB1 & $RGB2 ))
            ;;
        "~AND")
            NEW_RGB=$(( $RGB1 & ~$RGB2 ))
            ;;
        "XOR")
            NEW_RGB=$(( $RGB1 ^ $RGB2 ))
            ;;
        "~XOR")
            NEW_RGB=$(( $RGB1 ^ ~$RGB2 ))
            ;;
        *)
            echo "Invalid Operator: $OPERATOR"; return 1
            ;;

    esac

    # Create a new ANSI color string

    # Extract the individual RGB values
    NEW_R=$(( $(( $NEW_RGB & 0xFF0000 )) >> 16 ))
    NEW_G=$(( $(( $NEW_RGB & 0x00FF00 )) >> 8  ))
    NEW_B=$(( $(( $NEW_RGB & 0x0000FF )) >> 0  ))
    
    # Determine whether it is foreground or background
    NEW_FB=0

    if [[ $FB1 -eq 38 ]]; then 
        NEW_FB=$FG
    elif [[ $FB1 -eq 48 ]]; then
        NEW_FB=$BG
    fi
    
    # Make a new ANSI string
    NEW_COLOR="${NEW_FB}${NEW_R};${NEW_G};${NEW_B}m"

    # If this is a prompt-aware type, wrap it with the special tags
    [[ $COLOR1PVAL -eq 0 ]] && NEW_COLOR="${NPS}${NEW_COLOR}${NPE}"

    # Callers should capture this in a variable
    echo $NEW_COLOR

    # Return exit value 0 (success)
    return 0


}

