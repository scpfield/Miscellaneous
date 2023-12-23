import sys
import os
import operator
import gc
import ctypes
import tracemalloc
import linecache
from functools import wraps

# 
# This annotator takes before-and-after snapshots of memory usage
# using the Python 'tracemalloc' package that should exist in 
# Python 3.4 or higher.
#
# A full GC collection is performed both before and after executing
# the target function in an attempt to remove any pending garbage from 
# measurement.
#
# A sample target function is included that intentionally creates
# a memory leak.
#
# The output is currently verbose. If used on a permanent basis, 
# I would pare it down to a 1-liner / 1-value summary.
#
# For info on tracemalloc, refer to:
# https://docs.python.org/3/library/tracemalloc.html
#
# You may notice there is a @wraps annotator on the wrapper function.
#
# For info on @wraps, refer to: 
# https://docs.python.org/3.5/library/functools.html#functools.wraps
#
# For @wraps, I tried it, and it is true. Code inside of the 
# annotated function that checks its own '__name__' attribute will 
# get the wrapper function name unless you use the @wraps annotator 
# on the wrapper function.
#

def CheckMemory( TargetFunction ):
    
    @wraps( TargetFunction )
    def FunctionWrapper( *args, **kwargs ):
        
        # first, run full GC to clear everything it can
        gc.collect()
        
        # start the tracemalloc with 25 traceback frame history
        tracemalloc.start( 25 )

        # clear all prior trace data and reset peak data
        tracemalloc.clear_traces()
        tracemalloc.reset_peak()
    
        # before calling target function, get the current 
        # traced memory info that should be a decently clean state
        
        # get_traced_memory() returns a tuple of 2 ints 
        # representing bytes. I wanted megabytes so divide them
        # by 1024*1000 and round to 4 digits.

        MB = 1024 * 1000
        
        #
        # one way to make megabytes, converting the tuple of ints
        # to a list and using map to divide and round:
        #
        # HeapSize, PeakSize = map( round, map( operator.truediv,
        #                      list( tracemalloc.get_traced_memory() ), 
        #                      [MB, MB]), [2, 2])
        #
        # another way, converting the tuple to a list comprehension
        # then back to a tuple:
        #
        # HeapSize, PeakSize = tuple(
        #     list( *( (round( x / MB, 2), round( y / MB, 2))
        #     for x, y in ( tracemalloc.get_traced_memory(), ))))
        #
        # or just doing the simple thing:
        
        HeapSize, PeakSize = tracemalloc.get_traced_memory()
        HeapSize = round( HeapSize / MB, 4)
        PeakSize = round( PeakSize / MB, 4)
        
        print()
        print("------------------------------------------------------")
        print( f"Before calling        : {TargetFunction.__name__}" )
        print( f"Current Heap Size MB  : {HeapSize}")
        print( f"Peak Heap Size MB     : {PeakSize}" )
        print("------------------------------------------------------")
        print()
        
        # take the "before" tracemalloc snapshot
        Snapshot1  =  tracemalloc.take_snapshot()
        
        # run GC again just before calling function
        gc.collect()
        
        # call target function
        ReturnValue  =  TargetFunction( *args, **kwargs )
        
        # run GC again just after function returns
        gc.collect()
        
        # take the "after" tracemalloc snapshot
        Snapshot2  =  tracemalloc.take_snapshot()
        
        HeapSize, PeakSize = tracemalloc.get_traced_memory()
        HeapSize = round( HeapSize / MB, 4)
        PeakSize = round( PeakSize / MB, 4)
        
        print()
        print("------------------------------------------------------")
        print( f"After calling         : {TargetFunction.__name__}" )
        print( f"Current Heap Size MB  : {HeapSize}")
        print( f"Peak Heap Size MB     : {PeakSize}" )
        
        # get diff stats from snapshots
        SnapshotDiff = Snapshot2.compare_to(
                                 Snapshot1, 
                                 key_type = 'lineno' )
        
        # stop tracemalloc
        tracemalloc.stop()
        
        print()
        print( "Top Heap Differences:" )
        print()
        
        TotalDiff = 0.0
        
        for Idx, Stat in enumerate( SnapshotDiff[:5], 1 ):
        
            Frame       = Stat.traceback[0]
            DiffSize    = round( Stat.size_diff / MB, 4 )
            File        = Frame.filename.split( os.sep )[-1]
            Line        = Frame.lineno
            Code        = linecache.getline( File, Line ).strip()
            TotalDiff   += Stat.size_diff  

            print(f"{Idx}: Size: {DiffSize} MB, " +
                  f"File: {File}, Line: {Line}, " + 
                  f"Code: \"{Code}\"")
    
        TotalDiff = round( TotalDiff / MB, 4 )
        
        print()
        print(f"Total: {TotalDiff} MB")
        print()
        print("------------------------------------------------------")
        print()
        return ReturnValue    
    return FunctionWrapper
    ...

@CheckMemory
def CreateMemoryLeak():

    # this function allocates an object that is 1MB in size
    # then increments the reference count via the CPython code
    # and never decrements it.
    #
    # what is interesting:
    #
    # creating a list with a single element that is 1 MB characters long:
    #
    #    Data = [ 'X' * MB ]
    #
    # or with a single string that is 1 MB characters long:
    # 
    #    Data = 'X' * MB
    #
    # results in 1 MB used and 1 MB peak. 
    # 
    # however, creating a list with 1 MB number of elements, 
    # each element 1 character in size:
    # 
    #   Data = [ 'X' ] * MB
    #
    # results in 8 MB used and 8 MB peak
    #

    MB   = 1024 * 1000
    Data = 'X' * MB
    
    # This is the native C function call to CPython code
    # to increment a Python object reference count.
    # I found it on the Interwebs.
    
    IncRefCount          =  ctypes.pythonapi.Py_IncRef
    IncRefCount.argtypes =  [ ctypes.py_object ]
    IncRefCount.restype  =  None
    
    # NOTE: The __name__ attribute for this function will say
    # "FunctionWrapper" if the @wraps annotation is not used
    # otherwise it prints the expected function name "CreateMemoryLeak"
    
    print( f"{CreateMemoryLeak.__name__}: Data Length = {len( Data )}")
    print( f"{CreateMemoryLeak.__name__}: Current RefCount = {sys.getrefcount( Data )}" )
    print( f"{CreateMemoryLeak.__name__}: Incrementing RefCount" )
    
    # increment reference count
    IncRefCount( Data )
    
    print( f"{CreateMemoryLeak.__name__}: Current RefCount = {sys.getrefcount( Data )}" )
    ...
    

if __name__ == '__main__':

    CreateMemoryLeak()
    
    
