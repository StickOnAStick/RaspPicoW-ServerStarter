import network
import socket
from time import sleep
import machine
from machine import Pin
from secrets import secrets
import gc

ssid = secrets['ssid']
password = secrets['pw']
led = Pin("LED", Pin.OUT) #Onboard led 
led.off()

MAC = b"\x38\xd5\x47\xaf\x99\xd7" #38:d5:47:af:99:d7
BROADCAST_ADDR = '10.0.0.255'
PORT = 9
MSG = b'\xFF' * 6 + MAC * 16

#Web Stuff
def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print('WLAN ip: \t   ',ip)
    return ip

def open_socket(ip):
    #ip / port
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    print('Socket connection: ', connection)
    return connection

def webpage(temp, state):
    html = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
        </head>
    <body>
    <form action="./login" method="post">
        <input type="text" placeholder="Enter Pass" id="login" name="Pass">
        <input type="submit" value="submit">
    </form>
    <form action="./serverOn">
    <input type="submit" value="Server On" />
    </form>
    <p>Server is {state}</p>
    <p>Temperature is {temp}</p>
    </body>
    </html>
    """
    return str(html)

def serve(connection):
    state = 'OFF'
    temp = 0
    while True:
        client = connection.accept()[0]
        request = client.recv(1024) #buffer size to recieve for client.
        
        
        request = str(request)
        print("\n2nd Request: \n",request)
        
        
        try: 
            request = request.split()[1]
            
            
        except IndexError:
            pass
        
        if request == '/serverOn?':
            print("Turn Server on!")
            
            soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            soc.sendto(MSG, (BROADCAST_ADDR, PORT))
            #state
            state = 'ON' if state != 'ON' else 'OFF'
            led.toggle()
            gc.collect()
        elif request == '/login?':
            
            print('Login!')
            state = 'OFF'
            gc.collect()
            
        html = webpage(temp, state)
        #garbage collection
        if gc.mem_free() <= 142160: #arbitrary, based off 3 requests without cleanup
            gc.collect()
        print("Allocated: ", gc.mem_alloc(), "\nFree: ", gc.mem_free(),"\n")
        client.send(html)
        client.close()



try:
    gc.enable()
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    print("Error occured... Reseting")
    machine.soft_reset()
    