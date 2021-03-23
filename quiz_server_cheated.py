# ===== Imports =====

from time import sleep
from random import shuffle
from collections import namedtuple
from threading import Event, Timer
from fl_networking_tools import get_binary, send_binary
import socketserver, socket, json, os, sys, ipaddress, logging

# ===== Docstring =====

'''
Commands:
PLACE YOUR COMMANDS HERE
JOIN - request to join the game
QUES - question command
ANS  - was answer correct
'''

# ===== Definitions =====

# Named tuples are extensions of the tuple structure, with contents you can refer to by name.
# In this case, the question will be held in a variable named q and the answer in answer.
Question = namedtuple('Question', ['q', 'answer'])         # Structure of a question

# ===== Global variables =====

the_help = '''\
Optional command line parameters:

 ? or -h or --help  show this help message and exit
 --ip=<IPV4 address to bind to>                       (default 127.0.0.1)
 --port=<IP port to listen on>                        (default 2065)
 --log=<log level>                                    (default WARNING)

The log is written to file quiz_server.log in the current directory and
is overwritten each time the server is started.  The allowed values for
<log level> are  CRITICAL, ERROR, WARNING, INFO or DEBUG.

You can add your own questions by including them in file questions.json in
the current directory.
'''

# === Program parameters ===

IP_FAM = socket.AF_INET          # default to IPV4
IP_ADDR = "127.0.0.1"            # default IPV4 address to bind to
IP_PORT = 2065                   # default IP port to listen on for connection requests
Q_FILE = "questions.json"        # file contaning questions (change help if this changes)
QMAX = 4                         # number of questions per game
WRONG_LIMIT = 2                  # number of wrong answers before player eliminated
WAIT_TIME = 10.0                 # max time to wait for players to join
MAX_PLAYERS = 3                  # Maximum of players allowed
LOG_FILE = "quiz_server.log"     # Name of log file (change help text if this is changed)

# === Global variables ===

questions = []                   # list of questions to ask
q_index = 0                      # index into list of questions (used by get_question)
q_count = 0                      # count of questions asked
q_next = None                    # next question to ask (defined here to shut lint check up)
ready_to_start = Event()         # event to synchronise start of game
wait_for_answers = Event()       # event to wait until all answers collected
wait_for_result = Event()        # event to wait for result to be calculated
ans_count = 0                    # count of answers received to a question
game_open = True                 # True if new joiners are allowed
t = None                         # Timer - made global in case of 2 activations
players = {}                     # list of active players, dictionary entries use
                                 # the team name as a key and contain a list of 
                                 # [correct_answers, time taken, wrong_answers]
result = ""                      # result of game, set by end_of_game(), sent to all

# ===== Function to give next question =====
# ===== wrapping at end of list if rqd =====

def get_question():
    global q_index, questions
    if len(questions)==0:                # load file if required
        get_questions(Q_FILE)
    q_index += 1                         # increment pointer
    if q_index>=len(questions):          # wrap back to start of list from end
        q_index = 0
    return questions[q_index-1]          # [-1] is allowed = the last item

# ===== Load questions from file =====

def get_questions(filename):
    global questions

    # default questions
    q = [["Expand the acronym ALU", 
         ["Arithmetic Logic Unit", "Active Level Upgrade", "Antenna Loading Unit"]],
         ["In networking what does WDP mean", 
         ["Wireless Datagram Protocol", "World Day of Prayer", "Web Design and Programming"]],
         ["In networking what does FEC mean", 
         ["Forward Error Correction", "False Echo Control", "Forward Echo Cancellation"]],
         ["What happened during the 1989 Christmas holidays",
         ["Python was created", "Guido van Rossum was born", "I swallowed a fly"]]]

    if os.path.isfile(filename):                 # if data file exists
        try:
            with open(filename, 'r') as f:         # load from file
                df = json.load(f)
                logging.info("Questions loaded from file.")
        except:
            df = q                                 # hide exception and use defaults
            logging.error("Unable to load questions file.")
    else:                                        # no file  
        df = q                                     # use default questions
        logging.warning("Question file not found.")

    questions = []
    for q in df:                                 # convert to list
        questions.append(Question(q[0], q[1]))   # of Question tuples
    shuffle(questions)                           # and shuffle the list

# ===== Timer expiry =====

def timeout():                                   # waiting time elapsed
    ready_to_start.set()                         # so start game

# ===== End of game calculations =====

def end_of_game():
    global result
    if len(result)==0:                       # first caller does the work
        result = "Busy"                      # make sure length check fails

        # sort by score in descending order then time taken in ascending order
        ordered = sorted(players.items(), 
                         key=lambda item: (item[1][0], 99999-item[1][1]), 
                         reverse=True)
        layout = "{0:<15} {1[0]:^5d}  {1[1]:>5.2f}\n"
        result = "The winner is {}\n\n".format(ordered[0][0])
        result += "Team            Score   Time\n"
        #          --------------- -----  -----          delete me
        for item in ordered:
            result += layout.format(item[0], item[1])
            
        wait_for_result.set()
 
    wait_for_result.wait()      # everyone else waits here
    return result


# ===== Class to support threading =====

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# ===== The socketserver module uses 'Handlers' to interact with =====
# ===== connections. When a client connects a version of this    =====
# ===== class is made to handle it.                              =====

class QuizGame(socketserver.BaseRequestHandler):

    # === New handler thread spun up ===
    
    def setup(self):
        logging.info("%s:%d has connected." % (
            self.client_address[0],
            self.client_address[1]))
        self.team = "Unknown"                 # create it in case of no JOIN

    # === Main handler for clients ===

    # The handle method is what actually handles the connection
    def handle(self):
        global q_count, q_next, ans_count, players, game_open, t

        for request in get_binary(self.request):        # retrieve command
            if request[0] == "JOIN":
                if game_open==False:
                    logging.info("JOIN from %s:%d rejected." % (
                        self.client_address[0],
                        self.client_address[1]))
                    text = "Sorry this game has started.  Please try again later."
                    send_binary(self.request, (6, text))
                    continue

                if len(players)==0:                    # new game
                    result = ""
                    q_count = 0                        # reset question count
                    ready_to_start.clear()             # hold for sychronised start
                    wait_for_result.clear()            # hold for result calculation
                    t = Timer(WAIT_TIME, timeout)      # max wait time for other JOINs
                    t.start()                          # start timer

                if request[1] in players:
                    logging.info("Duplicated JOIN from %s at %s:%d rejected." % (
                        self.team,
                        self.client_address[0],
                        self.client_address[1]))
                    text = f"Sorry we already have a {request[1]} playing."
                    send_binary(self.request, (6, text))
                else:
                    self.team = request[1]
                    logging.debug("%s has joined the game from %s:%d." % (
                        self.team,
                        self.client_address[0],
                        self.client_address[1]))
                    players[self.team] = [0, 0.0, 0]
                    text = f"Hello {self.team}.\nThe game will start soon."
                    send_binary(self.request, (1, text))

                    if len(players)>=MAX_PLAYERS:               # if max number of players
                        t.cancel()                                # cancel timer
                        ready_to_start.set()                      # and start immediately

                    ready_to_start.wait()                       # else wait for start of game
                    game_open = False                           # close game to new JOINs
                    logging.debug("Game started")
                    send_binary(self.request, (2, list(players)))  # say starting

            elif request[0] == "QUES":
                logging.debug("%s requested a question." % self.team)
                if q_count>=QMAX:                               # if question limit
                    # end of game
                    result = end_of_game()                      # rank the teams
                    send_binary(self.request, (5, result))      # send end of game
                    logging.debug("Game over for %s" % self.team)

                else:
                    # send next question
                    logging.debug("Question %d sent to %s: %s" % (
                        q_count+1, 
                        self.team,
                        q_next.q))
                    send_binary(self.request, (3, [q_next.q, q_next.answer]))   # send question

            elif request[0] == "ANS":

                # collect answers until all received

                logging.debug("Answer from %s:%d." % (self.team, request[1][0]))

                ans_count += 1                                  # increment answer count
                if ans_count>=len(players):                     # if all answers in
                    q_count += 1                                  # increment question count
                    q_next = get_question()                       # get next question
                    ans_count = 0                                 # reset answer counter
                    wait_for_answers.set()                        # and continue

                wait_for_answers.wait()                     # else wait here

                # continue here once all answers received

                if request[1][0]==True:                          # correct answer
                    players[self.team][0] += 1                     # increment score
                    players[self.team][1] += request[1][1]         # add time to total
                    keepon = True                                  # and keep going
                    text = "Correct, your score is now {}".format(
                        players[self.team][0])                     # with a message
                else:                                            # wrong answer 
                    players[self.team][1] += request[1][1]         # add time to total
                    players[self.team][2] += 1                     # increment wrong count
                    if players[self.team][2]>=WRONG_LIMIT:         # if at limit
                        keepon = False                               # eliminated
                        text = "\nWrong answer.\nYou scored "
                        text += "{0[0]} in {0[1]:.1f} seconds\n".format(
                            players[self.team],
                            )
                        text += "Sorry but you have been eliminated."# and say so
                    else:
                        keepon = True                                # keep going
                        ll = WRONG_LIMIT-players[self.team][2]
                        if ll==1:
                            text = "\nWrong answer (only 1 life left)."
                        else:
                            text = f"\nWrong answer (only {ll} lives left)."

                logging.debug("Reply to ANS for %s. Status: %d, %d, %.2f, %d" % (
                    self.team,
                    keepon,
                    players[self.team][0],
                    players[self.team][1],
                    players[self.team][2]
                ))                            
                send_binary(self.request, (4, [keepon, text]))   # send the reply
                wait_for_answers.clear()                    # then be ready to wait again

            else:
                logging.warning("Unrecognised request from %s:%d: %s" % (
                    self.client_address[0],
                    self.client_address[1],
                    request[0]))

    # === Thread ending ===
    
    def finish(self):
        global players, game_open, result
        logging.info("%s @ %s:%d has disconnected." % (
            self.team,
            self.client_address[0],
            self.client_address[1]))
        if self.team in players:
            del players[self.team]
        if len(players)==0:
            game_open = True
            result = ""

# ===== Main program =====

addr_family = IP_FAM
addr = IP_ADDR                                   # in case no command line parameter
port = IP_PORT
numeric_level = logging.WARNING

# === Parse command line arguments ===

for arg in sys.argv:
    if arg.lower()=="--help" or arg.lower()=="-h" or arg=="?":
        print(the_help)
        sys.exit(0)

    if arg.lower().startswith("--ip="):
        addr = arg[5:]
        try:
            if addr.count('.')==3:
                ipaddress.IPv4Address(addr)
                addr_family = socket.AF_INET
            else:
                ipaddress.IPv6Address(addr)
                addr_family = socket.AF_INET6
                # don't appear to be able to *easily* change 
                # socketserver address_family so IPV6 banned
                print("Sorry IPV6 addresses are not supported.")
                print(f"Using default of {IP_ADDR}")
                addr = IP_ADDR
        except ipaddress.AddressValueError:
            print("Invalid IP address specified, using default of {IP_ADDR}.")
            addr_family = IP_FAM
            addr = IP_ADDR

    if arg.lower().startswith("--port="):
        port = int(arg[7:])
        if port<0 or port>65535:
            print("Invalid IP port specified, using default of {IP_PORT}.")
            port = IP_PORT

    if arg.lower().startswith("--log="):
        numeric_level = getattr(logging, arg[6:].upper(), None)
        if not isinstance(numeric_level, int):
            print("Invalid log level: %s, using WARNING instead." % arg[6:])
            numeric_level = logging.WARNING

logging.basicConfig(filename=LOG_FILE, 
                    filemode='w', 
                    level=numeric_level, 
                    format="%(asctime)s %(levelname)s: %(message)s")

# === Set up ===

q_next = get_question()       # prepare first question (forces read questions from file)

# === Open the quiz server and bind it to a port ===

quiz_server = ThreadedTCPServer((addr, port), QuizGame)

logging.info("Server starting at %s:%d" % (addr, port))
print("Server starting")
quiz_server.serve_forever()
