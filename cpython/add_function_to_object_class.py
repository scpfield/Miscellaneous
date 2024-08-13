import sys, ctypes


# ----------------------------------------------------------------------
#
#  This is an example of adding a function to the normally immutable 
#  python class object: 'object', which I discovered how to do by 
#  experimentation and reading the Python source code.
#
#  There are two steps:
#
#  1. Turn off the Immutable bit in the normally read-only Flags field 
#     for the object class.
#
#  2. Use an editable version of the object class' namespace dictionary
#     (provided by a special CPython runtime function) to add the 
#     new function into.
#
#  The new function added to 'object' will instantly become part of every 
#  other object in the running system.
#
# -----------------------------------------------------------------------


#
#  The following ReadMemoryValue / WriteMemoryValue functions accept the
#  arguments:
#
#  1) Address (required), which can either be: 
#
#    A python integer value of a memory address that exists somewhere in 
#    the currently running runtime.
#
#    or:
#
#    A variable / reference to any python object in memory, which can 
#    either be:
#
#       An instance object of a class/type, or
#       The class/type object itself 
# 
#  2) Offset (optional) is how far past the Address to skip
#     before reading/writing a value in memory, in increments 
#     of DataType width.  Default is 0.
#
#     For example, if reading/writing a c_uint64 value (8 bytes width), 
#     specifying an Offset value of 2 will skip to the location at:
#     Address + 16 bytes.
#
#  3) DataType (optional) is the CType you want to read/write,
#     such as a c_byte, c_char, c_uint64, etc., which are defined
#     in the python 'ctypes' module.  Defaults to c_uint64.
#
#  4) Value (for the Write function).  The data to write to the
#     memory location.  It should be provided as a regular Python
#     data type, not as a ctype.
#

def ReadMemoryValue(  Address, 
                      Offset      = 0, 
                      DataType    = ctypes.c_uint64 ):

    if not isinstance( Address, int ):
        Address = id( Address )
    
    Address         =  ( Address + 
                       ( ctypes.sizeof( DataType ) * Offset ))
                       
    PointerType     =  ctypes.POINTER( DataType )                
    DataPointer     =  PointerType( DataType.from_address( Address ))

    return DataPointer.contents.value



def WriteMemoryValue(  Value,
                       Address, 
                       Offset      = 0, 
                       DataType    = ctypes.c_uint64 ):


    if not isinstance( Address, int ):
        Address = id( Address )
    
    Address         =  ( Address + 
                       ( ctypes.sizeof( DataType ) * Offset ))
                       
    PointerType     =  ctypes.POINTER( DataType )                       
    DataPointer     =  PointerType( DataType.from_address( Address ))

    DataPointer.contents.value = Value
    
    return True


#
# This is a function which calls the CPython runtime function:
#
#    PyType_GetDict
#
# Which returns an editable namespace dictionary for any class object, 
# including built-in type objects.  This allows us to add, change, 
# or delete anything in a class/type object.
#
# For built-in type objects, one must first turn off the Immutable
# bit in the type class before calling this function.
#
# The function accepts a single argument:  TypeObject
#
# Examples:  str, int, dict, list, object, even 'type', 
#            or any of your own classes
#

def PyType_GetDict( TypeObject ):

    TypeObjectAddress        =  id( TypeObject )
    
    TypeObjectPointer        =  ctypes.cast( TypeObjectAddress, 
                                             ctypes.py_object )
    
    CPythonFunction          =  ctypes.pythonapi.PyType_GetDict
    CPythonFunction.argtypes =  [ ctypes.py_object ]
    CPythonFunction.restype  =  ctypes.py_object

    return CPythonFunction( TypeObjectPointer )
    


# This is a sample function that will be added to the python "object" 
# type, and will become part of all python objects and class objects
# automatically.
#
# When this function is called by an instance object, args[0]
# will be 'self'.

def MyFunction( *args, **kwargs ):

    print()
    print( 'MyFunction called' )
    print( 'args   : ', args )
    print( 'kwargs : ', kwargs )
    print()
    
    return True
    

# From Python's object.h, the bit for Immutability
Py_TPFLAGS_IMMUTABLETYPE = (1 << 8)


# Let's go!

if __name__ == '__main__':


    # To show that our modification to the object type will take
    # effect to all objects created both retroactively and
    # afterwards, let's create a few objects before we do anything.
    
    RetroactiveString   = "Created before changing object type"
    RetroactiveList     = [ "Created before changing object type" ]
    RetroactiveDict     = { "Created before changing object type" : 1 }
    
    
    # First, we need to edit the memory of the object type
    # to disable its Immutability flag, which is located at
    # offset 23 from the start of the object in memory. 
    #
    # All python types/classes have the Flags value at the same 
    # offset (23).  It is a 64-bit unsigned int. Normally it is 
    # read-only, but we can edit it using the ctypes module.
    #
    # I originally found the location by searching memory, then
    # later on, I realized it's also documented in one of the
    # python C header files.
    
    
    # Read the current Flags value in memory for 'object'
    Flags = ReadMemoryValue( object, Offset = 23 )
   
    # Turn off the Immutable bit in the Flags value
    Flags = Flags & ~Py_TPFLAGS_IMMUTABLETYPE
    
    # Write the new Flags value to memory
    WriteMemoryValue( Flags, object, Offset = 23 )
    
    # Now we can get the namespace dictionary for 'object'
    ObjectDict = PyType_GetDict( object )

    # Add a new function to the object type class
    # (we could also make other changes if we wanted,
    # like replacing existing functions or deleting)

    ObjectDict[ 'MyFunction' ] = MyFunction
    
    # All done.
    #
    # Now call MyFunction in various objects.
    # Start with the object type itself

    print( "calling object.MyFunction()" )
    object.MyFunction()
    
    # We can call it on the objects we created
    # before we added the function to 'object'.
    
    print( "calling RetroactiveList.MyFunction()" )
    RetroactiveList.MyFunction()

    print( "calling RetroactiveDict.MyFunction()" )
    RetroactiveDict.MyFunction()

    print( "calling RetroactiveString.MyFunction()" )
    RetroactiveString.MyFunction()

    # Newly created objects have it
    
    NewDict = {}
    
    print( "calling NewDict.MyFunction()" )    
    NewDict.MyFunction()
    
    print( "calling [].MyFunction()" )
    [].MyFunction()
    
    MyString = "MyString"
    
    print( "calling MyString.MyFunction()" )
    MyString.MyFunction()
    
    print( 'calling "asdf".MyFunction()' )    
    "asdf".MyFunction()
    
    # 'type' and other class type objects have it
    
    print( 'calling type.MyFunction()' )
    type.MyFunction()
        
    print( 'calling str.MyFunction()' )
    str.MyFunction()

    print( 'calling list.MyFunction()' )
    list.MyFunction()

    print( 'calling int.MyFunction()' )
    int.MyFunction()
      
    # It is even part of itself:
    
    print( 'calling MyFunction.MyFunction()' )
    MyFunction.MyFunction()
    

    exit(0)
    

