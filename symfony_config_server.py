from socket import *
import thread, getopt, sys, os, jsonlib2, yaml

def usage():
    print "usage: \n-s <path>: symfony path\n-p <port>: port to listen on\n-l <ip>: ip to listen on\n-h: help\n-v: verbose"


# TODO: for now only supports env-specific (not all:) vars in app.yml only
def symfony_get_config(yml_string, symfony_path, app='frontend', env='prod'):
    """Read raw app.yml"""

    # parse our conf path
    confpath = yml_string.split('_')

    # first member is always app, else its an error
    if "app" in confpath:
        confpath.remove('app')
    else:
        return "ERROR: Config path must start with app\n"

    # strip any weird chars
    confpath = [elem.strip() for elem in confpath]

    # TODO: cache this
    try:
        config = yaml.load(file(symfony_path + '/apps/' + app + '/config/app.yml', 'r'))
    except yaml.YAMLError, exc:
        return "ERROR: Cannot read YAML\n"

    try:
        curr = config[env]
    except KeyError:
        return "ERROR: Invalid environment\n"

    for elem in confpath:
        try:
            # see if we can find this element
            curr = curr[elem]
        except (TypeError, KeyError):
            # if not, lets try to take the rest of the elements, join them with _ and keep trying
            for elem in confpath:
                index = confpath.index(elem) + 1
                elem = elem + '_' + '_'.join(confpath[index:])
                try:
                    deep_curr = curr[elem]
                except (TypeError, KeyError):
                    continue

            try:
                curr = deep_curr
            except NameError:
                return "ERROR: Config variable not found\n"

                
    return jsonlib2.write(curr) + "\n"


def handler(clientsock,addr, symfony):
    """Handle the connections, parse received requests and send results back"""

    # default symfony app
    app = 'frontend'

    # default symfony env
    env = 'prod'

    BUFSIZ = 1024
    while 1:
        data = clientsock.recv(BUFSIZ)
        if not data: break 
        data = data.strip()
        

        # TODO: should not be startswith()
        if data.startswith('quit'):
            clientsock.close()
        elif data.startswith('app:'):
            app = data.split(':')
            app = app[1]
        elif data.startswith('env:'):
            env = data.split(':')
            env = env[1]
        else:
            yml_data = symfony_get_config(data, symfony, app, env)
            clientsock.sendall(yml_data)


def listener(ip, port, symfony):
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
        thread.start_new_thread(handler, (clientsock, addr, symfony))


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
        opts, args = getopt.getopt(sys.argv[1:], "hl:p:s:v", ["help", "listen=", "port=", "path=", "symfony="])
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
    listener(ip, port, symfony)




if __name__=='__main__': 
    main()
