import sys

try:

    import builtins, functools, inspect, threading
    import gc, pathlib, time, random, argparse
    
except:

    print()
    print( sys.exception() )
    exit(1)


#
# This file provides an implementation of a python decorator which 
# enables any python class or function to be a thread-safe class 
# or function.
#
# If applied to a class, the decorator replaces the functions in the 
# class with wrapped versions that use a shared mutex Lock to protect
# objects created from the class from being entered by multiple 
# threads at the same time, across all of the functions.  Each object 
# instance of a class has its own distinct Lock that applies to all the 
# functions for itself.
#
# If applied to a standalone function, the decorator will do the same
# thing but for just the single function.  It will prevent multiple 
# threads from executing the function at the same time by using a Lock
# stored in an attribute of the function.
#
# To apply the decorator to a whole class, simply add it to the class
# definition:
#
#
#    @Synchronized
#    class MyClass():
#        
#       def Function1(self):
#           ...
#       def Function2(self):
#           ...
#       def Function3(self):
#           ...
#
#
#    ..and all 3 functions will be protected with the same shared _Lock_.
#
#     standalone functions are the same:
#
#     @Synchronized
#     def Function1():
#       ...
#
#

#
# These first couple of items for retrieving caller info from the stack
# are for the debug output of the decorator so a person can see everything.
#
# The decorator function is below, and a test client.
#

class CallerInfo():

    def __init__( self ):
        self.File        = None
        self.Class       = None
        self.Function    = None
        self.LineNum     = None
        self.Code        = None
        self.ThreadName  = None

    def __str__( self ):
        OutputStr =  ''
        OutputStr += '['
        OutputStr += f'{self.ThreadName}'
        OutputStr += '|'
        OutputStr += f'{self.File}'
        OutputStr += ':'
        OutputStr += f'{self.LineNum}'        
        OutputStr += '|'        
        OutputStr += f'{self.Class}'
        OutputStr += '.'
        OutputStr += f'{self.Function}'
        OutputStr += ']'
        return( OutputStr )


def GetCallerInfo( Depth = 2 ):

    DepthIdx        = Depth - 1
    Frames          = list( inspect.stack() + inspect.trace() )

    if not Frames:  return None
    
    if len(Frames) < Depth: 
        Depth = len(Frames)
        DepthIdx = Depth -1
    
    FrameInfo       = Frames[DepthIdx]
    
    Code            = FrameInfo[0].f_code
    CodeStr         = str(Code)
    LineNum         = str(FrameInfo[2])
    Function        = str(FrameInfo[3])
    File            = str(pathlib.PurePath( FrameInfo[1] ).name)
    Referrers       = gc.get_referrers(Code)
    ThreadName      = str(threading.current_thread().name)
    ClassName       = None
    
    if not ClassName:
        FrameValue = FrameInfo[0].f_locals.get( 'cls' )
        if FrameValue: 
            ClassName = str( FrameValue.__name__ )

    if not ClassName:
        FrameValue = FrameInfo[0].f_locals.get( 'self' )
        if FrameValue:
            ClassName = str( FrameValue.__class__.__name__ )

    if not ClassName:
        FrameValue = FrameInfo[0].f_locals.get( '__name__' )
        if FrameValue:
            ClassName = str( FrameValue )

    if not ClassName:
        if len(Referrers) > 0:
            ClassName = str( Referrers[0] ).split('.')[0].split(' ')[1]

    if not ClassName:
        ClassName   = ''
        
    
    CallerData = CallerInfo()
    
    CallerData.File         = File
    CallerData.Class        = ClassName
    CallerData.Function     = Function
    CallerData.LineNum      = LineNum
    CallerData.Code         = CodeStr
    CallerData.ThreadName   = ThreadName
    
    return CallerData
 
 
#
# This is the decorator
#
def Synchronized( Target ):

    @functools.wraps( Target )
    def Wrapper( *args, **kwargs ):
               
        # For class decorator usage, we get called for two main scenarios:
        # First is for the class itself.
        # Second is when member functions are called by users.
        #
        # For standalone functions, we get called for the single instance
        # of the function, as many times as it is called by users.
        
        CallerInfo = GetCallerInfo(Depth=3)
        
        if type( Target ) == type:
        
            # This is the case for when the the target is a class object. 
            #
            # The caller is expecting us to return a fully-formed 
            # instance of the class.
            #
            # At this point, neither __new__ or __init__ have been called.
            #
            # We take this opportunity to modify the class object
            # and replace all the functions with wrapped / decorated
            # versions that will synchronize on a shared Lock.
            #
            # Every time a new instance of the class is created by a user, 
            # we get called to process the class object, which is the same
            # class object each time, so first check to make sure we haven't
            # processed this class before by checking a flag we set in the class.
            
            if not hasattr( Target, 'ClassSynchronized' ):
                
                # Iterate through the list of class member functions.
                # The python standard library package 'inspect' has a lot of useful things.
                
                for MemberName, MemberFunction in inspect.getmembers_static( Target ):
                    
                    # At the moment we need to skip these 6 functions because they end up
                    # called by this Wrapper function, and it triggers infinite loops.
                    # They are not important for our use-cases, so skip for now. 
                    # Also, skip __init__ and __new__, which don't need any Lock protection.                    
                    
                    if MemberName in [  '__repr__', 
                                        '__format__',       
                                        '__str__',
                                        '__getattribute__',
                                        '__init__', 
                                        '__new__' ]:
                        continue

                    if (( '<method'   in str( MemberFunction).strip() ) or
                        ( '<function' in str( MemberFunction).strip() ) or
                        ( '<slot'     in str( MemberFunction).strip() )):
                            
                            # Create a decorator-wrapper for the member function
                            SynchronizedFunction = Synchronized( MemberFunction )
                            
                            # Add a tag to the member function wrapper too
                            setattr( SynchronizedFunction, 'MemberSynchronized', True )
                            
                            # Replace the orignal function with our new one
                            setattr( Target, MemberName, SynchronizedFunction )
 
                            builtins.print( f'Replaced function : {MemberFunction} ' +
                                            f'with function     : {SynchronizedFunction}' )
 
                builtins.print()
                    
                # Set a tag on the class indicating we have already processed it
                setattr( Target, 'ClassSynchronized', True )
                
                
            # Now we can create a new object instance from the modified class.
            
            Instance = Target( *args, **kwargs )
            
            # Finally, create an RLock and add it to the new object instance
            # as one of its attributes.  Need to use object.__setattr_()
            # instead of setattr() or else infinite recursion.
            #
            # All the member functions we replaced will share this same Lock,
            # for this instance of the object.
            #
            # Originally I tried using only Locks but it seems to be more
            # reliable with the addition of an event signal as well.
            
            
            _Lock_  = threading.RLock()
            _Event_ = threading.Event()
            _Event_.set()
            
            object.__setattr__( Instance, '_Lock_', _Lock_)
            object.__setattr__( Instance, '_Event_', _Event_)
            
            # Return the new, fully formed object to the caller
            
            return( Instance )
            
        else:
            
            # Target is a function object.  It could either be a member
            # function of a object, or a standalone function.  It's not readily
            # obvious which case it is, since both types look very similar.
            # That is why we tagged the member wrapper functions with an attribute,
            # to make it easier to tell the difference.
            
            _Lock_       = None
            _Event_      = None
            ReturnValue  = None
            
            if hasattr( Wrapper, 'MemberSynchronized' ):
            
                # Here is where we handle the member function calls by the
                # user to the class functions we modified earlier, and
                # the calls to standalone functions that are decorated.
                #
                # First we need to find the Lock object.
                #
                # For member functions, it is located in the parent object 
                # instance where we put it, but all we have here is a function 
                # object.
                # 
                # Fortunately, Python provides the parent object instance of a 
                # function in the function's args[0] value, commonly known as "self".
        
                _Lock_  = getattr( args[0], '_Lock_' )
                _Event_ = getattr( args[0], '_Event_' )
                
            else:
            
                # For standalone functions, the first time the function is called 
                # we create a Lock object for it and store it in an attribute of
                # the function.  
                #
                # Subsequent calls to ths same function will have the Lock 
                # ready to use.
                
                if not hasattr( Target, '_Lock_' ):
                
                    _Lock_ = threading.RLock()
                    setattr( Target, '_Lock_', _Lock_ )
                
                if not hasattr( Target, '_Event_' ):
                
                    _Event_ = threading.Event()
                    setattr( Target, '_Event_', _Event_ )
                    
                _Lock_  = getattr( Target, '_Lock_' )
                _Event_ = getattr( Target, '_Event_' )
            

            # For some reason Python seems more reliable using the "with" 
            # context manager with locks, even when comparing against 
            # the equivalent try/except logic
            
            builtins.print( f'{CallerInfo} Waiting to acquire _Lock_, ' +
                            f'ID: {id(_Lock_)} for: {Target.__name__}' )

            # Wait for the lock to become available            
            with _Lock_:
                
                builtins.print( f'{CallerInfo}  Acquired Lock ID:{id(_Lock_)}, ' +
                                f'Waiting For Event ID: {id(_Event_)} For Function: ' +
                                f'{Target.__name__}' )

                # After acquiring the lock, then wait for the signal from the thread ahead
                # of it to say it is ok to proceed.                                
                _Event_.wait()
                
                builtins.print( f'{CallerInfo}  Event Is Signaled For Event ID: ' +
                                f'{id(_Event_)} For Function: {Target.__name__}' )

                # Immediately clear the event signal back to unsignaled state
                _Event_.clear()
                
                builtins.print( f'{CallerInfo}  Event Is Cleared For Event ID: {id(_Event_)} ' +
                                f'Calling Function: {Target.__name__}' )

                # Call the original function that we wrapped
                ReturnValue = Target( *args, **kwargs )
            
                builtins.print( f'{CallerInfo}  Completed Function Call For: {Target.__name__}' )
                
              
            # Coming out of the indended "with" section above is supposed to guarantee
            # the Lock is released.  Python runs an "__exit__" magic method that does it.
            # It is supposed to take care of exceptions and various edge cases for you.
            
            builtins.print( f'{CallerInfo}  Released Lock ID:{id(_Lock_)}, ' +
                            f'Signaling Event ID: {id(_Event_)}' )
            
            # Signal the event to allow another thread to move forward
            _Event_.set()

            # Return the result of the function call to the caller
            builtins.print( f'{CallerInfo}  Returning Result To Caller' )
            return ReturnValue
            
        
    return Wrapper
    
...  # End of the decorator
 
 
 
#
# This is all that is needed to make a fully thread-safe Python dictionary.
# Simply extend a dict and apply the decorator
#
@Synchronized
class SynchronizedDict( dict ):
    ...


#
# Utility function to generate random printable strings
#
def RandomString( Length = 10 ):
    RandBytes = bytearray( Length )
    for x in range( Length ):
        RandBytes[ x ] = random.randrange( 65,91 )
    return( RandBytes.decode().replace( " ", "_" ).lower() )
    

# 
# Multi-threaded test client
#
class ThreadTest():
            
    def __init__( self ):
    
        # Create a single instance of a synchronized dictionary
        # Multiple threads will be reading + writing to it
        
        self.Dict1 = SynchronizedDict()

        self.ThreadCount         = 5
        self.WorkerThreads       = []

        #
        # Create thread objects
        #
        
        for x in range(0, self.ThreadCount ):
        
            print( f'creating WorkerThread #{x}')
            
            self.WorkerThreads.append( threading.Thread( 
                                        target  = self.WorkerThread,
                                        name    = f'WorkerThread{x}',
                                        daemon  = False ))

        #
        # Launch threads
        #
        
        for x in self.WorkerThreads:

            # stagger the thread launches by 2 second so they 
            # are doing different activities at any given moment
            print( f'starting thread: {x}' )
            time.sleep(1)
            x.start()
            
        
        #
        # Wait for threads to finish
        #
        
        for x in self.WorkerThreads: 
        
            print( f'waiting for thread {x} to finish' )
            if x.is_alive():
                x.join()
            print( f'thread {x} has finished' )
     
     
    #
    #  Thread function
    # 
    
    def WorkerThread( self ):

        Count   = 2000
        Data    = []
        
        
        # 
        #  Loop 1000 times generating random strings and 
        #  calling functions that use the Python dictionary
        #
        
        for x in range( Count ):
       
            RandomKey1   = RandomString()
            RandomValue1 = RandomString()
            
            self.AddToDictionary(    self.Dict1, RandomKey1, RandomValue1 )
            self.ExistsInDictionary( self.Dict1, RandomKey1 )
            
            RandomKey2   = RandomString() 
            RandomValue2 = RandomString()
            
            self.UpdateDictionary(  self.Dict1, RandomKey2, RandomValue2 )
            self.GetFromDictionary( self.Dict1, RandomKey2 )
            self.PopDictionary(     self.Dict1, RandomKey1 )
            
           

    #
    # These are basic test functions that call into the dictionary.
    #
    
    def AddToDictionary( self, Dict, Key, Value ):
    
        Dict[ Key ] = Value
        
    def UpdateDictionary( self, Dict, Key, Value ):
    
        return ( Dict.update( { Key : Value } ))

    def PopDictionary( self, Dict, Key ):
    
        return ( Dict.pop( Key ))
        
    def PopItemDictionary( self, Dict ):
    
        return ( Dict.popitem() )
        
    def DeleteItemDictionary( self, Dict ):
    
        del Dict[ Key ]
        
    def GetFromDictionary( self, Dict, Key ):
    
        Value1 = Dict.get( Key )
        Value2 = self.GetFromDictionary2( Dict, Key )
        
        return ( Value1, Value2 )
       
    def GetFromDictionary2( self, Dict, Key ):
    
        return ( Dict[ Key ] )

    def GetKeysDictionary( self, Dict ):
    
        return ( Dict.keys() )

    def GetValuesDictionary( self, Dict ):
    
        return ( Dict.values() )

    def ClearDictionary( self, Dict ):
    
        return ( Dict.clear() )         
    
    def ReadDictionary( self, Dict ):
    
        Count = 0
        
        for Key, Value in Dict.items():
            Count += 1
            
        return Count
        
    def ExistsInDictionary( self, Dict, Key ):
    
        return ( Key in Dict )
        
    def CopyDictionary( self, Dict ):
    
        return ( Dict.copy() )
        
    def SizeOfDictionary( self, Dict ):
    
        return len( Dict )
        
...  # end of test client




if __name__ == '__main__':
        
    print()
    
    ArgParser = argparse.ArgumentParser( argument_default    = True,
                                         add_help            = True,
                                         description         = 'SynchronizingDictionary')

    ArgGroup  = ArgParser.add_argument_group()

    ArgGroup.add_argument(  '--run-test',
                            required    = False,
                            action      = 'store_true',
                            default     = False,
                            help        = 'Run Test' )

    Args    = ArgParser.parse_args()
 
 
    #MyDict = SynchronizedDict()
    
    #for x in range(10):
    
    #    MyDict[x] = 1
    
    if Args.run_test:
    
        Tester = ThreadTest()
        
   
    
    if not Args.run_test:
    
        print()
        print( 'There are only 2 arguments:  ' )
        print( ' --help' )
        print( ' --run-test' )
        
    print()
    print( 'Goodbye' )
    print()
    
    sys.exit(0)
    
    
    












'''
        builtins.print( f'-------------- Wrapper called-----------------------')
        builtins.print()
        builtins.print( f"Target            : {Target}" )
        builtins.print( f"TargetName        : {Target.__name__}" )
        builtins.print( f"Target Type       : {type(Target)}" )
        builtins.print( f"Target ID         : {id(Target)}" )
        
        if args:
            builtins.print()
            for idx, Arg in enumerate(args):
                builtins.print( f"Arg #{idx} Value = {Arg}  Type: {type(Arg)}" )

        if kwargs:
            builtins.print()
            for k, v in kwargs.items():
                builtins.print( f"kwarg: {k} = {v}   {type(k)} : {type(v)}" )
'''