#
#  This is a basic message producer -> consumer using
#  the Python multiprocessing package and a shared queue, 
#  which is Python's solution for achieving parallel 
#  execution across multiple CPUs.  
#  
#  You can also write threads in Python but they can't
#  run in parallel due to the Global Interpeter Lock.
#  Python threads can run concurrently, but not in Parallel.
#
#  It is neat, with the multiprocessing package,
#  it's pretty much identical to how you code a 
#  multi-threaded program, and it runs in parallel 
#  across multiple CPUs, without very much extra work.
#
import sys, os, time, signal
import multiprocessing as mp
import multiprocessing.managers as mpm


# This is the Producer class, which is
# an OS Process that adds one message
# at a time to a shared queue.
#
class ProducerProcess( mp.Process ):

    # Constructor, accepts a QueueProxy
    # object that is managed by a "SyncManager"
    #
    def __init__(   self, 
                    Name        = "Producer", 
                    Daemon      = True, 
                    QueueProxy  = None, 
                     *args, 
                    **kwargs ):
                  
        super().__init__(   name    = Name, 
                            daemon  = Daemon, 
                             *args, 
                            **kwargs )
                          
        self.QueueProxy = QueueProxy
    

    #  Similar to a thread run(), this is 
    #  the start of the process execution
    #
    #  It simply adds an incrementing number
    #  to a proxy-queue object in an infinite loop
    #
    def run( self ):
        
        Count = 0
        while True:
        
            self.QueueProxy.put( Count, block = True )
            
            print(  f'{self.name}: Added Item = {Count}, ' + 
                    f'Queue Size = ' +
                    f'{str(self.QueueProxy.qsize())}' )
                    
            Count += 1
            

# This is the Consumer class, another
# OS Process which retrieves one message
# at a time from a shared proxy queue
#
class ConsumerProcess( mp.Process ):

    # Constructor
    #
    def __init__(   self, 
                    Name        = "Consumer", 
                    Daemon      = True, 
                    QueueProxy  = None, 
                     *args, 
                    **kwargs ):
                  
        super().__init__(   name    = Name, 
                            daemon  = Daemon, 
                             *args, 
                            **kwargs )
                          
        self.QueueProxy = QueueProxy
    

    # Similar to a thread run() function,
    # this is the start of the process execution,
    # infinite loop of receiving messages.
    #
    # Also this function checks to make sure that
    # each number value that it retrieves from the
    # shared Queue is consecutive, to check for
    # any data corruption or out-of-order messages
    #
    def run( self ):
    
        PrevItem = -1
        
        while True:
        
            Item    = self.QueueProxy.get( block = True )
            
            print(  f'{self.name}: Got Item   = {str(Item)}, ' +
                    f'Queue Size = ' +
                    f'{str(self.QueueProxy.qsize())}, ' )
                    
            if  ( Item - PrevItem ) != 1:
                print( "ERROR: Not consecutive items!" )
                raise SystemExit
                
            PrevItem = Item
            

# This is an OS signal handler because
# otherwise I run into issues with Control-C
# not responding, so this helps
#
def OSSignalHandler( Signal, Frame ):
    try:
        print( f'Caught Signal: ' +
               f'{signal.strsignal(Signal)}' )
    except SystemExit:
        print('SystemExit')
    except InterruptedError:
        print('InterruptedError')        
    except BaseException:
        print('Some other exception')
    finally:
        sys.exit(0)


# main function, required for multiprocessing
# on Windows because of something related to 
# Windows not having support for "fork()".

def main():

    # My signal handlers
    signal.signal( signal.SIGINT,   OSSignalHandler )
    signal.signal( signal.SIGBREAK, OSSignalHandler )
    signal.signal( signal.SIGABRT,  OSSignalHandler ) 
    
    try:

        # This is the SyncManager that Python provides
        # that provides "Proxy" objects for the shared
        # data.  It runs a separate server process that 
        # holds the actual concrete data objects.
        #
        # It supports the Python context feature "with".
        #
        # The default SyncManager has a dozen various
        # built-in object types to make proxies for,
        # like Queues, Events, dictionaries, lists, 
        # all the normal stuff.  You can also extend it 
        # to make proxies for any custom object you 
        # might want to do.
        #
        with mpm.SyncManager() as QueueManager:
        
            # This just creates a Queue to be managed.
            # It is actually a "Proxy" object.
            # At this point, the Server that will hold
            # the concrete Queue is already running.
            #
            MsgQueue = QueueManager.Queue()
            
            # Here we create the Producer + Consumer
            # Processes and give them the proxy object.
            #
            Producer = ProducerProcess( QueueProxy = MsgQueue )
            Consumer = ConsumerProcess( QueueProxy = MsgQueue )
            
            # Start 'em up.
            #
            Consumer.start()
            Producer.start()
            
            #  On my system I can't join indefinitely because 
            #  it won't respond to Control-C while the main thread 
            #  is blocked on the join.  It kind of sucks, I have 
            #  to loop every couple seconds for pending OS signals 
            #  to get processed.
            #
            while True:
                QueueManager.join( 2 )
        
            print('Exiting')
        
    except SystemExit:
        print('SystemExit')
    except InterruptedError:
        print('InterruptedError')        
    except BaseException:
        print('Something Else')


#
#  The Python docs specify you need to explicitly define 
#  a main function or else you get deadlocks when 
#  spawning child processes on Windows,
#  and they are right. Need the freeze_support() too.
#        
if __name__ == '__main__':
    mp.freeze_support()
    main()


# 
#  If you are still reading, so far in my performance
#  tests, I am getting suprisingly very good results.
#  