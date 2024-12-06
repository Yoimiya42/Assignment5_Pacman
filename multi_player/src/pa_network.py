import socket
import sys
import pickle # serializes and deserializes a Python object structure
import select
from time import sleep

class Network():
    def __init__(self, controller, password):
        self.__controller = controller
        self.__password = password
        self.__server = False
        self.__connected = False
        # Create a new socket using IPv4 addressing and TCP protocol
        try:
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as err: 
            print("socket creation failed with error %s" %(err))
            sys.exit()

        self.__recv_buf = bytes()
        self.get_local_ip_addr()


    def server(self, port):
        self.__server = True
        while True:
            try:
                self.__sock.bind(('', port))
                break
            except OSError as err:
                print(err)
                print("waiting, will retry in 10 seconds")
                sleep(10)
  
        # put the socket into listening mode 
        self.__sock.listen(5)
        print("listening for incoming connection...")

        while True: 
            # Establish connection with client. 
            c_sock, addr = self.__sock.accept() 
            # return:  new socket object, the address of the client
            # addr:  a pair of IP address and port number

            # The new socket is used to communicate with the client

            #print('Got connection from', addr)
            msg = c_sock.recv(1024)
            txt = msg.decode()
            if txt == self.__password:
                c_sock.send("OK\n".encode())
                # string.encode() returns a bytes object
                break
            else:
                c_sock.close()
        # swap the socket names so send/recv functions don't care if we're client or server
        self.__listen_sock = self.__sock # assign the socket used to listen to a new variable  
 
        self.__sock = c_sock
        self.__connected = True
            

    def client(self, ip, port):
        self.__sock.connect((ip, port))
        self.__sock.send(self.__password.encode())
        msg = self.__sock.recv(3) # expect 'OK\n', which is 3 bytes and represents the handshake
        txt = msg.decode()
        if txt == "OK\n":
            self.__connected = True
        else:
            print("handshake failed\n")

    def get_local_ip_addr(self):
        # ugly hacky way to find our IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # SOCK_DGRAM is the socket type to use for UDP sockets
        # Why UDP? Cause we don't actually intend to connect with a client
        
        s.connect(("128.16.66.166", 80)) # connect to nrg.cs.uc.ac.uk
        ip = s.getsockname()[0]  # return a tuple (IP address, port number)
        s.close()
        return ip
    
    @property
    def connected(self):
        """Check if the client connected successfully."""
        return self.__connected
     
    
    def send(self, msg):
        """Rewrite the send() method."""
        print(msg)
        send_bytes = pickle.dumps(msg)
        lenbytes = len(send_bytes).to_bytes(2, byteorder='big')
        # len() return the number of bytes in the argument
        # int.to_bytes(length, byteorder) 
        #  length: the number of bytes to return
        #  byteorder: 
        #     -'big': most significant -> least significant
        #     -'little': least significant -> most significant
        #  return: a bytes object
  
        self.__sock.send(lenbytes + send_bytes)
    """
    pickle.dumps(): Serialize the object into a bytes stream.
        parameter: a object of string, tuple, list, dictionary,etc.
        return:  a bytes object (a non-human-readable binary string, like b'\x80\x03\x00\x00...')

    encode(): Convert the string into bytes.
        object.encode(), object must be a string
        parameter: the encoding type, default is 'utf-8', also can be 'ascii', 'gbk'
        return:  a bytes object (a human-readable binary string, like b'hello')

    b: prefix for representing a bytes object

    """



    def send_maze(self, maze):
        msg = ["maze", maze]
        self.send(msg)



    #############################################################################################################
    def check_for_messages(self, now):
        rd, wd, ed = select.select([self.__sock],[],[],0)
        # blocking mode: if no data is available, the program will wait until data is available
        if not rd:
            pass
        else:
            try:
                recv_bytes = self.__sock.recv(10000)
            except ConnectionResetError as e:
                print("Remote game has quit: ", e)
                sys.exit()

            self.__recv_buf += recv_bytes  # concat onto whatever is left from prev receive
            # the first 2 bytes of __recv_buf is the length of the message, represented in bytes


            recv_len = int.from_bytes(self.__recv_buf[0:2], byteorder='big')  
            # int.from_bytes(bytes, byteorder): convert bytes to an integer
            # convert the first 2 bytes of __recv_buf (the length of message) to an integer

            while (len(self.__recv_buf) - 2 >= recv_len):
                # len(__recv_buf) is the length of the whole message,
                # 2(used to represent length of this message) + rest (the length of original message)
                # if true, it means we have a complete message

                self.parse_msg(self.__recv_buf[2:recv_len+2])
                # use the original message to parse

                self.__recv_buf = self.__recv_buf[recv_len+2:]
                # remove the original message from __recv_buf, 
                # and continue to check next message if there ia any l,eft
                if len(self.__recv_buf) > 2:
                    # if true: message left in the buffer

                    recv_len = int.from_bytes(self.__recv_buf[0:2], byteorder='big')
                    # continue to parse the next message until the buffer is empty
                    
        
    def parse_msg(self, buf):
        msg = pickle.loads(buf)
        # pickle.loads(): Deserialize the bytes stream to a Python object

####1-6#############################################################################################################

        if msg[0] == "maze":
            maze = msg[1]
            self.__controller.received_maze(maze)

        elif msg[0] == "newpacman":
            #A pacman has arrived message
            self.foreign_pacman_arrived(msg[1])

        elif msg[0] == "pacmanleft":
            #A pacman has left message
            self.foreign_pacman_left(msg[1])

        elif msg[0] == "pacmandied":
            #A pacman has left message
            self.foreign_pacman_died(msg[1])

        elif msg[0] == "pacmanhome":
            #Pacman go home!
            self.pacman_go_home(msg[1])
        ###########################################
        elif msg[0] == "pacman":
            #A pacman update message
            self.pacman_update(msg[1]) 
#####7-12#############################################################################################################      
        elif msg[0] == "ghost":
            #A ghost update message
            self.ghost_update(msg[1])

        elif msg[0] == "ghosteaten":
            #The foreign pacman ate our ghost!
            self.foreign_pacman_ate_ghost(msg[1])
        elif msg[0] == "eat":
            #A food update message
            self.eat(msg[1])
        elif msg[0] == "score":
            #A score update message
            self.score_update(msg[1])
        elif msg[0] == "lives":
            #A lives update message
            self.lives_update(msg[1])

        elif msg[0] == "status":
            #A status update message
            self.status_update(msg[1])
        else:
            print("Unknown message type: ", msg[0])


######## "newpacman"            
##################################################################
    def foreign_pacman_arrived(self, msg):
        #print("received pacman_arrived")
        self.__controller.foreign_pacman_arrived()

    def send_foreign_pacman_arrived(self):
        #print("send pacman_arrived")
        payload = []
        msg = ["newpacman", payload]
        self.send(msg)



######## "pacmanleft"
################################################################
    def foreign_pacman_left(self, msg):
        #print("received pacman_left")
        self.__controller.foreign_pacman_left()

    def send_foreign_pacman_left(self):
        #print("send pacman_left")
        payload = []
        msg = ["pacmanleft", payload]
        self.send(msg)



######## "pacmandied"
################################################################
    def foreign_pacman_died(self, msg):
        #print("received pacman_died")
        self.__controller.foreign_pacman_died()

    def send_foreign_pacman_died(self):
        #print("send pacman_died")
        payload = []
        msg = ["pacmandied", payload]
        self.send(msg)



######## "pacmanhome"
####################################################################
    def pacman_go_home(self, msg):
        self.__controller.pacman_go_home()

    def send_pacman_go_home(self):
        #print("send pacman_go_home")
        payload = []
        msg = ["pacmanhome", payload]
        self.send(msg)

######## "pacman"
#######################################
    def pacman_update(self, msg):
        #print("received pacman_update")
        pos = msg[0] #position in pixels
        dir = msg[1] #direction enum
        speed = msg[2]
        self.__controller.foreign_pacman_update(pos, dir, speed)

    def send_pacman_update(self, pos, dir, speed):
        #print("send pacman_update")
        payload = [pos, dir, speed]
        msg = ["pacman", payload]
        self.send(msg)

######### "ghost"
##########################################
    def ghost_update(self, msg):
        #print("received ghost_update")
        ghostnum = msg[0]
        pos = msg[1] #position in pixels
        dirn = msg[2] #direction enum
        speed = msg[3] 
        mode = msg[4] 
        self.__controller.remote_ghost_update(ghostnum, pos, dirn, speed, mode)

    def send_ghost_update(self, ghostnum, pos, dirn, speed, mode):
        #print("send ghost_update")
        payload = [ghostnum, pos, dirn, speed, mode]
        msg = ["ghost", payload]
        self.send(msg)



######## "ghosteaten"       
################################################################
    def send_foreign_pacman_ate_ghost(self, ghostnum):
        payload = [ghostnum] # probably shouldn't be a list - inefficient
        msg = ["ghosteaten", payload]
        self.send(msg)

    def foreign_pacman_ate_ghost(self, msg):
        ghostnum = msg[0]
        self.__controller.foreign_pacman_ate_ghost(ghostnum)





######## "eat"
################################################################
    def eat(self, msg):
        pos = msg[0]
        is_foreign = msg[1]
        is_powerpill = msg[2]
        if is_foreign:
            # A foreign pacman ate food on our screen
            self.__controller.foreign_eat(pos, is_powerpill)
        else:
            # Food was eaten on the remote screen
            self.__controller.remote_eat(pos, is_powerpill)

    def send_eat(self, pos, is_foreign, is_powerpill):
        payload = [pos, is_foreign, is_powerpill]
        msg = ["eat", payload]
        self.send(msg)



######## "score"
################################################################
    def score_update(self, msg):
        score = msg[0]
        self.__controller.update_remote_score(score)

    def send_score_update(self, score):
        payload = [score] # probably shouldn't be a list
        msg = ["score", payload]
        self.send(msg)





######## "lives"
################################################################
    def lives_update(self, msg):
        lives = msg[0]
        self.__controller.update_remote_lives(lives)

    def send_lives_update(self, lives):
        payload = [lives] # probably shouldn't be a list
        msg = ["lives", payload]
        self.send(msg)






######## "status"
################################################################
    def status_update(self, msg):
        status = msg[0]
        self.__controller.remote_status_update(status)

    def send_status_update(self, status):
        payload = [status] # probably shouldn't be a list
        msg = ["status", payload]
        self.send(msg)
        
