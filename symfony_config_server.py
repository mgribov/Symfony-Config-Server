from socket import *
import thread, getopt, sys, os

def usage():
    print "usage: \n-s <path>: symfony path\n-p <port>: port to listen on\n-l <ip>: ip to listen on\n-h: help\n-v: verbose"


def symfony_get_config(yml_string, app='frontend'):
    yml_string.strip(os.linesep)
    app.strip(os.linesep)
    stringy = app, yml_string
    return ''.join(stringy)

def handler(clientsock,addr):
    # default symfony app
    app = 'frontend'

    BUFSIZ = 1024
    while 1:
        data = clientsock.recv(BUFSIZ)
        if not data: break 
        data.strip(os.linesep)
        if data.startswith('quit'):
            clientsock.close()
        elif data.startswith('app:'):
            app = data.split(':')
            app = app[1]
        else:
            yml_data = symfony_get_config(data, app)
            clientsock.sendall(yml_data)


def listener(ip='localhost', port='21567'):
    HOST = ip
    PORT = int(port)
    ADDR = (HOST, PORT)
    serversock = socket(AF_INET, SOCK_STREAM)
    serversock.bind(ADDR)
    serversock.listen(2)
    while 1:
        print sys.argv[0], 'listening on ', ip, port
        clientsock, addr = serversock.accept()
        print 'connected from:', addr
        thread.start_new_thread(handler, (clientsock, addr))


def main():
    # affects logging
    verbose = False

    # get options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hl:p:s:v", ["help", "listen=", "port=", "path=", "symfony"])
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-l", "--listen"):
            ip = a
        elif o in ("-p", "--port"):
            port = a
        elif o in ("-s", "--path", "--symfony"):
            symfony = a
        else:
            assert False, "unknown option"

    # spawn listening server
    listener(ip, port)



if __name__=='__main__': 
    main()
