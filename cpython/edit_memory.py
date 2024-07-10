import sys, types, inspect, functools, ctypes, os, builtins

# Read-Only Class Type Flags
# From CPython's Header: object.h

Py_TPFLAGS_HAVE_FINALIZE                = (1 << 0)
Py_TPFLAGS_STATIC_BUILTIN               = (1 << 1)
Py_TPFLAGS_INLINE_VALUES                = (1 << 2)
Py_TPFLAGS_MANAGED_WEAKREF              = (1 << 3)
Py_TPFLAGS_MANAGED_DICT                 = (1 << 4)
Py_TPFLAGS_SEQUENCE                     = (1 << 5)
Py_TPFLAGS_MAPPING                      = (1 << 6)
Py_TPFLAGS_DISALLOW_INSTANTIATION       = (1 << 7)
Py_TPFLAGS_IMMUTABLETYPE                = (1 << 8)
Py_TPFLAGS_HEAPTYPE                     = (1 << 9)
Py_TPFLAGS_BASETYPE                     = (1 << 10)
Py_TPFLAGS_HAVE_VECTORCALL              = (1 << 11)
Py_TPFLAGS_READY                        = (1 << 12)
Py_TPFLAGS_READYING                     = (1 << 13)
Py_TPFLAGS_HAVE_GC                      = (1 << 14)
Py_TPFLAGS_HAVE_STACKLESS_EXTENSION     = (3 << 15)
Py_TPFLAGS_METHOD_DESCRIPTOR            = (1 << 17)
Py_TPFLAGS_VALID_VERSION_TAG            = (1 << 19)
Py_TPFLAGS_IS_ABSTRACT                  = (1 << 20)
Py_TPFLAGS_MATCH_SELF                   = (1 << 22)
Py_TPFLAGS_ITEMS_AT_END                 = (1 << 23)
Py_TPFLAGS_LONG_SUBCLASS                = (1 << 24)
Py_TPFLAGS_LIST_SUBCLASS                = (1 << 25)
Py_TPFLAGS_TUPLE_SUBCLASS               = (1 << 26)
Py_TPFLAGS_BYTES_SUBCLASS               = (1 << 27)
Py_TPFLAGS_UNICODE_SUBCLASS             = (1 << 28)
Py_TPFLAGS_DICT_SUBCLASS                = (1 << 29)
Py_TPFLAGS_BASE_EXC_SUBCLASS            = (1 << 30)
Py_TPFLAGS_TYPE_SUBCLASS                = (1 << 31)
Py_TPFLAGS_HAVE_VERSION_TAG             = (1 << 18)


# Example that shows how to edit readonly flags
# for a Python class / type using CPython API.

class MessWithPython():

    EditedObjectMap = {}

    def __init__( self ):
        ...

    # These don't need to be classmethods
    # just a convenience

    @classmethod
    def EditObjectFlags( cls, Object ):

        # First, get the current __flags__ value from the
        # normal Python class object's attributes.

        Flags = getattr( Object, '__flags__', None )

        if Flags == None:
            return False

        # Using ctypes, setup variables compatible with the
        # CPython runtime API that interfaces with the active runtime.
        # First, store the __flags__ value as an unsigned 64-bit integer.

        UInt64_Flags         = ctypes.c_uint64( Flags )

        # The normal python function: "id()" actually gives you
        # a value that is the memory address of where the object lives.
        # Create a ctypes UInt64 number for it.

        ObjectID             = id( Object )
        UInt64_ObjectID      = ctypes.c_uint64( ObjectID )

        # Check if we've already edited this object's flags before,
        # If the current value is different from how we set it
        # previously, then edit it again, otherwise exit

        if ObjectID in cls.EditedObjectMap:
            PreviousValue = cls.EditedObjectMap.get( ObjectID )
            if PreviousValue and ( PreviousValue == Flags ):
                return False

        # Now create a ctypes pointer to the object in memory.
        UInt64_ObjectIDPtr   = ctypes.pointer( UInt64_ObjectID )

        # Record the starting address of where the pointer is pointing.
        StartingOffset       = UInt64_ObjectIDPtr.contents.value

        # Extra variables
        PtrSize              = 8
        MaxLoops             = 100
        LoopCount            = 0

        # Now scroll through memory, one 64-bit value at a time,
        # looking for the __flags__ value we got from the python object.

        while LoopCount < MaxLoops:

            # Dereference the pointer to get the next value from memory.
            # Hopefully it's not pointing into NULL.  :-)

            MemoryValue  = ctypes.c_uint64.from_address(
                            UInt64_ObjectIDPtr.contents.value )

            # Yay, we're still alive.
            # Now compare the number we got with what we are looking for.

            if MemoryValue.value == UInt64_Flags.value:

                # Hooray we found it. Flip a few bits to ensure the object
                # is enabled for inheritance, disabled for immutable, and
                # disabled for disallowing instantiation.

                CurrentValue    = MemoryValue.value
                NewValue        = CurrentValue
                NewValue        = NewValue |  Py_TPFLAGS_BASETYPE
                NewValue        = NewValue & ~Py_TPFLAGS_IMMUTABLETYPE
                NewValue        = NewValue & ~Py_TPFLAGS_DISALLOW_INSTANTIATION

                # Write the updated flags to memory.
                MemoryValue.value = NewValue

                # Record the flags value we wrote in our dictionary so
                # we can remember what we did.

                cls.EditedObjectMap[ ObjectID ] = NewValue

                # Debug print
                print( f'Edited:{ObjectID} ' +
                       f'Offset:{StartingOffset}+{LoopCount} ' +
                       f'(PtrSize:{PtrSize}) ' +
                       f'PreviousValue:{CurrentValue} ' +
                       f'NewValue:{NewValue}' )

                # The Python source code has comments saying if you make
                # structural changes to existing classes / type objects,
                # to call this other CPython function to update a cache,
                # or something.

                cls.PyType_Modified( Object )

                # All done
                return True

            # Haven't found it yet, so advance the pointer forward
            UInt64_ObjectIDPtr.contents.value += PtrSize

            # Increment loop counter
            LoopCount += 1



    # This is the other CPython to notify the runtime that we made changes.
    # It uses a different technique with ctype pointers than the prior
    # function above.

    @classmethod
    def PyType_Modified( cls, Object ):

        ObjectID    = id( Object  )
        ObjectPtr   = ctypes.cast( ObjectID, ctypes.py_object )

        RuntimeFunction          =  ctypes.pythonapi.PyType_Modified
        RuntimeFunction.argtypes =  [ ctypes.py_object ]
        RuntimeFunction.restype  =  None

        return RuntimeFunction( ObjectPtr )



