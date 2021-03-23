from time import time
from threading import Timer
from random import shuffle, choice
from string import ascii_letters as letters
from fl_networking_tools import get_binary, send_binary
import socket, multiprocessing, sys, os, ipaddress, logging


'''
Responses
LIST YOUR RESPONSE CODES HERE
1 - Player has joined game
2 - Start game notification
3 - Question details
4 - Continue/Eject decision
5 - Final score / end of game
6 - Rejected JOIN
'''

SERVER_PORT = 2065                        # server port to connect to 
Q_TIMER = 15                              # maximum time allowed to answer question

the_rules1 = '''\
Welcome to my Quiz Game

These are the rules.

When you start the client software you will be asked to input the 
IP address of the quiz server and a name (1-14 characters) for the 
team.
 
Once the first player connects to the server a “welcome and please 
wait” message is displayed and a timer started to allow other players
to join the game.

At the end of the timer period you will be told who is playing and 
the game will start.  Any attempt to join the game after it starts
will be rejected.

You will be asked a series of multiple choice questions and you have 
to input the number corresponding to the correct answer. Note that 
any invalid input or no input will be treated as a wrong answer.
'''
the_rules2 = '''\

Your answers marked by the client and the result plus the time taken 
to answer will be sent to the server which maintains a running total 
of correct answers and time taken for each player.

After all the questions have been asked then a final count of correct 
answers and time taken is used to rank the players and select a winner 
based on the most questions answered correctly with the lowest time 
used to resolve any ties.  This information is then shown to all players.

In addition a player will be eliminated from the game if they answer more 
than 2 questions incorrectly.  An eliminated player can decide whether 
to disconnect immediately or remain connected to see the final result 
of the quiz.

Enjoy the game

'''                                  # text to display if --rules added to command line
the_help = '''\
Optional command line parameters:

 ? or -h or --help  show this help message and exit
 --rules        show the quiz rules before starting
 --log=<log level>                                    (default WARNING)

The log is written to file quiz_client_????.log in the current directory and
is overwritten each time the client is started.  The allowed values for
<log level> are  CRITICAL, ERROR, WARNING, INFO or DEBUG.

'''                                  # text to display if help is requested on command line

# ===== Workaround to stop one player not =====
# ===== answering hanging the whole quiz  =====
# based on Trent Bing's entry on stackoverflow.com

def get_input(prompt, timeout):

    '''get_input(prompt, timeout)
    Calling get_input will display 'prompt' and wait
    for 'timeout' seconds for user input. Anything  
    entered will be returned.  If the timeout expires 
    a message is displayed and an empty string returned.
    '''
    try:
        return _input_with_timeout(prompt, timeout)
    except:
        print("\nSorry, time's up")
    return ""

def _input_with_timeout(prompt, timeout=None):
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_input_with_timeout_process, 
        args=(sys.stdin.fileno(), queue, prompt )
    )
    process.start()
    try:
        process.join(timeout)
        if process.is_alive():
            raise ValueError("Timed out waiting for input.")
        return queue.get()
    finally:
        process.terminate()

def _input_with_timeout_process(stdin_file_descriptor, queue, prompt):
    sys.stdin = os.fdopen(stdin_file_descriptor)
    queue.put(input(prompt))


# ===== Main Program =====

if __name__ == '__main__':

    numeric_level = logging.WARNING

    for arg in sys.argv:

        if arg.lower().startswith("--log="):
            numeric_level = getattr(logging, arg[6:].upper(), None)
            if not isinstance(numeric_level, int):
                print("Invalid log level: %s, using WARNING instead." % arg[6:])
                numeric_level = logging.WARNING

        if arg.lower()=="--rules":
            print(the_rules1)
            input("Press <return> to continue:")
            print(the_rules2)

        if arg.lower()=="--help" or arg.lower()=="-h" or arg=="?":
            print(the_help)
            sys.exit(0)

    logname = "quiz_client_"+"".join(choice(letters) for _ in range(4))+".log"
    logging.basicConfig(filename=logname, 
                        filemode='w', 
                        level=numeric_level, 
                        format="%(asctime)s %(levelname)s: %(message)s")

    # === Collect info from user ===

    addr = input("\nIP address of server: ")
    try:
        if addr.count('.')==3:
            ipaddress.IPv4Address(addr)
            addr_family = socket.AF_INET
        else:
            ipaddress.IPv6Address(addr)
            addr_family = socket.AF_INET6
    except ipaddress.AddressValueError:
        print("Invalid IP address specified.")
        sys.exit(-1)

    invalid = True
    while invalid:
        team = input("Team name: ")
        if len(team)<1:
            print("You must specify a team name")
        elif len(team)>15:
            print("Team names must be less than 15 characters.")
        else:
            invalid = False

    # === Connect to the server ===

    logging.info("Connecting to %s:%d" % (addr,SERVER_PORT))
    quiz_server = socket.socket(addr_family, socket.SOCK_STREAM)
    quiz_server.connect((addr, SERVER_PORT))

    playing = True                              # flag to control quiz loop.
    eliminated = False                          # True if player eliminated

    send_binary(quiz_server, ["JOIN", team])    # ask to join the quiz
    logging.debug("JOIN sent for %s." % team)

    while playing:
        # The get_binary function returns a list of messages - loop over them
        for response in get_binary(quiz_server):
            logging.debug("Rcvd %d", response[0])

            # response is the command/response tuple - response[0] is the code
            if response[0] == 1:                         # The JOIN response
                print(response[1])                         # Display it to the user.

            elif response[0] == 2:                       # Game starting
                print("Playing today:", end=" ")
                for name in response[1]:
                    print("{},".format(name), end=" ")
                print("\n\nGame starting, get ready for your first question")
                send_binary(quiz_server, ["QUES", ""])
                logging.debug("Sent QUES")

            elif response[0] == 3:                       # Question details
                if eliminated:                                          # if already eliminated 
                    send_binary(quiz_server, ["ANS", [False, 0.0]])     # send dummy answer
                    logging.debug("Sent eliminated ANS")
                    continue

                question = response[1][0]                               # extract question
                answers = response[1][1]                                # and possible answers
                answer = answers[0]                                     # correct answer is first
                print("\nQuestion:", question, "?\nPossible answers:")
                shuffle(answers)
                for i in range(len(answers)):
                    print("  {}. {}".format(i+1, answers[i]))           # display the options

                t0 = time()                                             # start timer
                inp = get_input(
                    "Enter the number of your answer: ", 
                    Q_TIMER)                                            # ask for answer
                timer = time() - t0                                     # calculate time taken

                # Is answer correct?
                correct = False                                  # assume not correct
                if len(inp)>0 and inp.isdecimal():               # if digit
                    ans = int(inp)                               # convert to integer
                    if ans>0 and ans<=len(answers):              # in range
                        if answer==answers[ans-1]:               # and matches the right answer
                            correct = True                       # then result = correct

                send_binary(quiz_server, ["ANS", [correct, timer]])        # send the answer
                logging.debug("Sent ANS with %d, %.3f" % (correct,timer))

            elif response[0] == 4:                       # The Continue/Eject decision
                if eliminated:                                   # if already eliminated 
                    send_binary(quiz_server, ["QUES", ""])         # just ask for next question
                    logging.debug("Sent eliminated QUES")
                    continue

                print(response[1][1])                         # display result from server
                if response[1][0]:                            # if allowed to continue
                    send_binary(quiz_server, ["QUES", ""])      # get next question
                    logging.debug("Sent QUES")

                else:                                         # player eliminated
                    eliminated = True                         # remember that
                    y = get_input("\nDisconnect now (D) or wait (W) to see who wins? ", 10)

                    if y=="W" or y=="w":                              # if player wants to wait
                        send_binary(quiz_server, ["QUES", ""])          # get next question
                        logging.debug("User eliminated, QUES sent")
                    else:                                             # else
                        logging.info("User disconnecting")
                        playing = False                                 # exit
                        break

            elif response[0] == 5:                       # Final score / end of game
                print(response[1])                            # display result
                print("\nThank you for playing.  Goodbye.")
                logging.info("User disconnecting")
                playing = False                               # and exit
                break

            elif response[0] == 6:                       # Rejected JOIN request
                print(response[1])                            # display reason
                print("Goodbye.")
                logging.info("User disconnecting")
                playing = False                               # and exit
                break

            else:                                    # I don't know
                logging.warning("Unrecognised response received: %d", response[0])

    quiz_server.close()
