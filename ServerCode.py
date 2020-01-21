import socket
import time


def createSocket():
    try:
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
    except socket.error as error:
        print("Socket Creation Error: " + str(error))
    return serversocket

#bind socket to hostIp and specified port, retryCounter is used for saving number of tries
def bindSocket(serversocket, hostIP, port, retryCounter):    
    try:
        serversocket.bind((hostIP, port))
        serversocket.listen(5)
        print("server running..")
        bindingSuccessful = True
    except socket.error as error:
        retryCounter = retryCounter + 1
        #if binding fails, try 7 times to bind again
        if retryCounter < 8:
            print("Binding Error: " + str(error) + "\n" + "already retried: " + str(retryCounter) + " times" + "\n"+ "retrying..")
            bindSocket(serversocket, hostIP, port, retryCounter)
        else:
            print("Binding Error: " + str(error) + "\n" + "already retried: " + str(retryCounter) + " times" + "\n"+ "binding Socket failed")
            bindingSuccessful = False    
    return serversocket, bindingSuccessful

#reads html-file and returns it as string
def getHtml(filePath):
    with open(filePath, "r") as f:
       f = f.read()
    return f

def sendAndRecieve(serversocket, htmlFilePaths):
    #saves connected addresses, with time stamp of scooter and station scanning    
    connectedAddresses = {}
    #set default status = OK 
    status = {"OK":"HTTP/2.0 200 OK\r\n\r\n"}
    #time in sec for scanning
    secForScanning = 10
    #saves successful scooter parkings
    history = []    
    try:
        while True:
            (clientsocket, address) = serversocket.accept()
            request = clientsocket.recv(1024)
            request = request.decode()
            #check if valid request
            if not (request[5:12] == "scooter" or request[5:12] == "station" or request[5:12] == " HTTP/1"):
                continue
            #use only first 24Bit of client address
            address = address[0]
            address = address[:address.rfind(".")]
            #if client address connects for first time create listing for it
            if not address in connectedAddresses:
                connectedAddresses[address] = [[0,0],[0,0]]                    
            msg =  status["OK"] + getHtml(htmlFilePaths["generalPage"])

            if request[5:12] == "scooter":
                connectedAddresses[address][0] = [request[5:14], time.time()]
                msg = status["OK"]  + getHtml(htmlFilePaths["scooterPage"])
            elif request[5:12] == "station":
                connectedAddresses[address][1] = [request[5:14], time.time()]
                msg = status["OK"]  + getHtml(htmlFilePaths["stationPage"])
            
            #check scan times of scooter and station of current client address
            timeScooterScan = connectedAddresses[address][0][1]
            timeStationScan = connectedAddresses[address][1][1]
            timespan = abs(timeScooterScan - timeStationScan)
            if  timespan <= secForScanning and timespan > 0:
                scooter = connectedAddresses[address][0][0]
                station = connectedAddresses[address][1][0]
                print(scooter + " was succesfully parked at " + station)
                timestamp = time.gmtime(timeScooterScan - time.timezone)
                #save scooter, station and timestamp to history
                history.append([scooter, station, timestamp])
                msg = status["OK"]  + getHtml(htmlFilePaths["successPage"])
                #delete scooter and station time because both were already used
                connectedAddresses.__delitem__(address)                
            print(connectedAddresses)    
            msg = msg.encode(encoding="utf-8")
            clientsocket.send(msg)
            clientsocket.setblocking(1)
    except (Exception, KeyboardInterrupt):
        if Exception:
            print(str(Exception))    
        clientsocket.close()
        serversocket.close()
        for listing in history:
            print(listing + "\n")
        print("Server Off")   
    
    
    
#parameters
#IP_address = "192.168.2.115"
IP_address = "192.168.0.102"

port = 8000
htmlFilePaths = {"generalPage":"/var/www/html/index.html",
                 "scooterPage":"/var/www/html/scooter.html",
                 "stationPage":"/var/www/html/station.html",
                 "successPage":"/var/www/html/sucess.html"
                }

#excecute code
serversocket = createSocket()
serversocket, bindingSuccessful = bindSocket(serversocket, IP_address, port, 0)
if bindingSuccessful:
    sendAndRecieve(serversocket, htmlFilePaths)






