import sys, os, time, signal, copy, random
import multiprocessing as mp
import multiprocessing.managers as mpm
import websocket
from util import *


class WebSocketProcess( mp.Process ):

    def __init__(self, URL, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.URL = URL
        
    def start(self):
        super().start()
    
    def run( self ):
        print("Got called")
        Count = 0
        while True:
            #print("CONSUMER: About to set data")
            self.Producer.SetData("Set By: " + str(self.pid) + '-')
            #print("CONSUMER: Finished setting data")
            Count += 1
            #time.sleep(1)
            

class ProducerProxy( mpm.BaseProxy ):

    _exposed_ = ( 'start', 'run', 'SetData', 'GetData', 'SetProxy' )
        
    def start(self):
        #print("Got called")
        return self._callmethod('start')
    
    def run(self):
        #print("Got called")
        return self._callmethod('run')
    
    def SetData(self, Data):
        #print("Got called")
        return self._callmethod('SetData', (Data, ))
    
    def GetData(self):
        #print("Got called")
        return self._callmethod('GetData')
        
    def SetProxy(self):
        #print("Got called")
        return self._callmethod('SetProxy', (self, ))
    
    
    
def main():

    '''
    p1 = mp.Process(target=ProcessFunction, args=())
    p2 = mp.Process(target=ProcessFunction, args=())
    p3 = mp.Process(target=ProcessFunction, args=())
    p1.start()
    p2.start()
    p3.start()
    Pause() 
    '''
    
    #mpm.SyncManager.register(   'Process',
    #                            mp.Process,
    #                            proxytype = ProcessProxy,
    #                            create_method = True )
     
 
    #mpm.SyncManager.register(   'ProducerProcess', 
    #                            ProducerProcess,
    #                            proxytype = ProducerProxy,
    #                            create_method = True)
 
                         
    '''
    mpm.SyncManager.register(   'ConsumerProcess', 
                                ConsumerProcess, 
                                proxytype = ConsumerProcessProxy )
    '''
    
    with mpm.SyncManager() as TheManager:
         
        for k, v in TheManager._registry.items():
            print(k, v)
        
        A, B = mp.Pipe()
        print(A)
        print(B)
        
        #Producer = TheManager.ProducerProcess()
        #Producer = ProducerProcess()
        #Consumer = ConsumerProcess()
        #Consumer.start()
        #Producer.start()
        
        ABCD = DevToolsClient.ChromeClient()
        ABCD.start()
        

        
        
        while True:
            print("Joining with Manager")
            TheManager.join(1)
        
    
        
    print('Exiting')

    
if __name__ == '__main__':

    #mp.freeze_support()
    main()

