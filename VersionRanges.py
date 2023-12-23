import sys


'''
    The HackerRank test specified the input data should be 
    a list of strings describing the start + end ranges of
    two version numbers, each having with 3 components, 
    in the following format:

    "a.b.c to x.y.z"

    There could potentially be an infinite number of 
    versions in between the start and end ranges.

    The following program will print all the version
    numbers in between the start + end versions with one 
    restriction:

    For each component of a version:

     major.minor.incremental

    Each is assumed to be 8 bits / 1 byte, which gives 
    the maximum integer ranges per component:

    (0 -> 255).(0 -> 255).(0 -> 255)
      major      minor       inc


    This program consists of 2 functions, one to parse
    the input data, and one to calculate + print the
    versions.

    There is a "main" at the bottom which can be used
    to customize the input data.

'''


def PrintFunction( VersionNumbers ):


    '''

    This is the main print function, which calculates
    and prints all the versions in between the start +
    end ranges from the input data.

    From the 3 component numbers, assuming to be max
    of 1-byte each, it creates 3-byte numbers by
    shifting the bits.

    Then it simply increments the starting number
    until it reaches the end number, extracting the
    updated component values as it goes.

    Example.  Given a range:

        1.0.0 to 1.2.5

    There will be version numbers generated for:

        1.0.(0 -> 255)
        1.1.(0 -> 255)
        1.2.(0 -> 5)
        
    '''
    
    FirstMajorVer   = VersionNumbers[0]
    FirstMinorVer   = VersionNumbers[1]
    FirstIncVer     = VersionNumbers[2]

    SecondMajorVer  = VersionNumbers[3]
    SecondMinorVer  = VersionNumbers[4]
    SecondIncVer    = VersionNumbers[5]
    
    FirstNum        = 0
    FirstNum        = (( FirstMajorVer << 16 )  |
                       ( FirstMinorVer << 8  )  |
                       ( FirstIncVer ))
                     
    SecondNum       = 0
    SecondNum       = (( SecondMajorVer << 16 )  |
                       ( SecondMinorVer << 8  )  |
                       ( SecondIncVer ))

    MajorVer        = 0
    MinorVer        = 0
    IncVer          = 0
    Num             = FirstNum
    
    while True:
        
        MajorVer    = ( Num & 0xFF0000 ) >> 16
        MinorVer    = ( Num & 0x00FF00 ) >> 8
        IncVer      = ( Num & 0x0000FF ) >> 0
        
        print( f"{MajorVer}.{MinorVer}.{IncVer}")
        
        if (( MajorVer == SecondMajorVer )  and
            ( MinorVer == SecondMinorVer )  and
            ( IncVer   == SecondIncVer   )):
             
             print("Done")
             break
        
        Num += 1
    ...
# End of PrintFunction

    
'''
    This function simply parses the input data
    and then calls the print function above.
'''

def ProcessData( VersionRanges, Function ):

    for Range in VersionRanges:
        
        print()
        print(f"Input Range Text: {Range}")
        
        RangeSplit          = Range.split(' to ')
        FirstVersion        = RangeSplit[0]
        SecondVersion       = RangeSplit[1]
        
        FirstVersionSplit   = FirstVersion.split('.')
        SecondVersionSplit  = SecondVersion.split('.')
        
        FirstMajorVer       = int(FirstVersionSplit[0])
        FirstMinorVer       = int(FirstVersionSplit[1])
        FirstIncVer         = int(FirstVersionSplit[2])

        SecondMajorVer      = int(SecondVersionSplit[0])
        SecondMinorVer      = int(SecondVersionSplit[1])
        SecondIncVer        = int(SecondVersionSplit[2])
                                      
        Function((
                    FirstMajorVer,  FirstMinorVer,  FirstIncVer, 
                    SecondMajorVer, SecondMinorVer, SecondIncVer
                ))
    ...
# End of ProcessData function



# Main
# Customize the input ranges here

if __name__ == '__main__':

    InputRanges =   [ 
                        "1.0.0 to 1.2.5", 
                        "25.1.5 to 26.9.14" 
                    ]

    ProcessData( InputRanges, PrintFunction )

