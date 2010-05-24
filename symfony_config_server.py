from socket import *
import thread, getopt, sys, os

def usage():
    print "usage: \n-s <path>: symfony path\n-p <port>: port to listen on\n-l <ip>: ip to listen on\n-h: help\n-v: verbose"


def symfony_get_config(yml_string, app='frontend'):
    """Read either cached or raw YAML config files"""
    yml_string.strip(os.linesep)
    app.strip(os.linesep)
    stringy = app, yml_string
    return ''.join(stringy)


def handler(clientsock,addr):
    """Handle the connections, parse received requests and send results back"""
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
    """Spawn listener threads"""
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


def daemonize():
    # http://code.activestate.com/recipes/278731-creating-a-daemon-the-python-way/
    """Detach a process from the controlling terminal and run it in the background as a daemon"""

    UMASK = 0
    WORKDIR = "/"
    MAXFD = 1024

    if (hasattr(os, "devnull")):
        REDIRECT_TO = os.devnull
    else:
        REDIRECT_TO = "/dev/null"

    try:
        pid = os.fork()
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)

    if (pid == 0):
        os.setsid()
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)

        if (pid == 0):
            os.chdir(WORKDIR)
            os.umask(UMASK)
        else:
            os._exit(0)
    else:
        os._exit(0)

    import resource      
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = MAXFD
  
    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError: 
            pass

    os.open(REDIRECT_TO, os.O_RDWR)  # standard input (0)
    os.dup2(0, 1)            # standard output (1)
    os.dup2(0, 2)            # standard error (2)
    return(0)
            

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

    # fork
    retCode = daemonize()

    # spawn listening server
    listener(ip, port)




if __name__=='__main__': 
    main()
