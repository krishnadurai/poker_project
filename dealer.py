#!/usr/bin/python2.7
import itertools
import sys
import time
from socket import *
import random
#import hand_evaluator
import threading
import thread 

# Variable Initialisation
NO_OF_PLAYERS = 2
small_blind_amt = 1

INITIAL_MONEY = 1000

MINIMUM_RAISE = 1

all_rounds = [('preflop',1), ('flop',2), ('river',3), ('turn',4)] 

small_blind=random.randint(0, NO_OF_PLAYERS - 1)


# Received data from thread
class recvd_data_from_thread:
    curr_data_recvd = ''
    def __init__(self):
        pass

thread_recvd_data = recvd_data_from_thread()

# Players involved currently
live_players = []
for i in range(0, NO_OF_PLAYERS):
    live_players.append(1)


# implemented in all_rounds
#current_round = 1


# Player investment in round
pot_investment = [0] * NO_OF_PLAYERS
pot_investment[small_blind] = small_blind_amt
big_blind = (small_blind + 1) % NO_OF_PLAYERS
pot_investment[big_blind] = small_blind_amt * 2
current_player = (big_blind + 1 ) % NO_OF_PLAYERS
#current_player = 2
# Player who raised last
last_raised = big_blind
last_raised_amt = pot_investment[big_blind]
last_raised_by = 0

# Money in players hand
players_money = []
for i in range(0, NO_OF_PLAYERS):
    players_money.append(INITIAL_MONEY)
    players_money[i] -= pot_investment[i]


print "--------------------PLAYERS MONEY-----------------------"
print players_money



# data
SUITS = ('c', 'd', 'h', 's')
RANKS = ('2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')

#DECK stores all cards
DECK = tuple(''.join(card) for card in itertools.product(RANKS,SUITS))

# Generate Lookups
SUIT_LOOKUP = dict(zip(SUITS, range(4)))
RANK_LOOKUP = dict(zip(RANKS, range(13)))
ORDER_LOOKUP={}
i=0
for card in DECK:
    ORDER_LOOKUP[card] = SUIT_LOOKUP[card[1]] * 13 + RANK_LOOKUP[card[0]]
    i = i + 1


# Recv data funciton
def recv_data():
    done = 0
    while not done:
        #print 'inside recv data'
        try:
            data = recv_conn[current_player].recv(1024)
            if data != '':
                print 'Data received in recv data is ' + data
                done = 1
                thread_recvd_data.curr_data_recvd =  data
        except:
            print 'wtf in recv_data'

# Send Data func
def send_data(data,i):
    try:
        send_sock[i].send(data)
    except:
        print 'wtf in send_data'

# SendThemAll func
def send_them_all(data):
    for sock in send_sock:
        try:
            sock.send(data)
        except:
            print 'wtf in send_data'

# Get Number of live players
def get_no_of_live_players():
    total = 0
    for i in range(0,len(live_players)):
        total = total + live_players[i]
    return total
# Get Next player

def get_next_player(curr):
    i = (int(curr) + 1) % NO_OF_PLAYERS
    #print ' i is : ' + str(i)
    while(i != curr):
        if (live_players[i] == 1):
            return i
        i = (i + 1) % NO_OF_PLAYERS
    return curr
# get playerlist
def get_player_list(round_num):
    player_list = []
    if round_num == 1:
        player_num = (small_blind + 2) % NO_OF_PLAYERS
    else:
        player_num = small_blind
    for i in range(0, NO_OF_PLAYERS):
        if live_players[player_num] == 1:
            player_list.append(player_num)
        player_num = (player_num + 1) % NO_OF_PLAYERS 
    return player_list


# Main
send_sock=[]
recv_conn = []
def main():
    global current_player
    global last_raised_amt, last_raised_by
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    R_HOST = ''
    R_PORT = 11717
    s.bind((R_HOST, R_PORT))
    ip_array = []
    print 'OK ready for connection'
    while(1):
        s.listen(1)
        conn, addr = s.accept()
        recv_conn.append(conn)
        try:
            data = conn.recv(1024)
            if data == 'req':
                print addr[0]
                ip_array.append(addr[0])
        except:
            print 'we are unable to receive data from client or bad request'
        if(len(ip_array) == NO_OF_PLAYERS):
            break

    print ' connection req received from '
    print ip_array

    # Check conn
    i = 0
    S_PORT = 11716
    while(i < NO_OF_PLAYERS):
        S_HOST = ip_array[i]
        send_sock.append(socket(AF_INET, SOCK_STREAM))
        print ' Sending check data  to '
        print S_HOST
        send_sock[i].connect((S_HOST, S_PORT))
        data = 'req=check$'
        send_sock[i].send(data)
        i += 1

    # Round Starts now
    while(True):
        no_of_pots= 1
        # Will be chaged when pot life ends
        #pot_players = []
        pot_money = []
        pot_money.append(small_blind_amt * 3)
        i = 0
        threads = []
        # Sending details 
        while(i < NO_OF_PLAYERS):
            data = 'req=init:' +  'nop=' + str(NO_OF_PLAYERS) + ';yourPos=' + str(i) + ";sb=" + str(small_blind) + ";players_money=" + str(players_money) +'$'
            threads.append(threading.Thread(target = send_data, args = (data,i,)))
            threads[i].start()
            i += 1
        for t in threads:
            t.join()

        del threads
        threads = []
        #Sending card
        i = 0
        print ' Sending cards to players'
        cards = random.sample(DECK, 2 * NO_OF_PLAYERS + 8)
        while(i < NO_OF_PLAYERS):
            data = 'req=cards:' + cards[i * 2] + "," + cards[i * 2 + 1] + '$'
            threads.append(threading.Thread(target = send_data, args = (data,i,)))
            threads[i].start()
            i += 1
        for t in threads:
            t.join()


        del threads
        threads = []
        i = 0
        # Sending Public Data
        print 'sending data '
        while(i < NO_OF_PLAYERS):
            data = 'req=data:' + 'nop=' + str(NO_OF_PLAYERS) + ';live=' + str(live_players) + ';yourPos=' + str(i) + ";sb=" + str(small_blind) + ";current_player=" + str(current_player) + ";NO_OF_POTS=" + str(no_of_pots) + ";players_money=" + str(players_money) + ";pot_investment=" +str(pot_investment) + ";last_raised_amt=" + str(last_raised_amt) + ';pot_money=' + str(pot_money) + '$'
            threads.append(threading.Thread(target = send_data, args = (data,i,)))
            threads[i].start()
            i += 1

        for t in threads:
            t.join()
        
        del threads
        threads = []
        # Game starts now
        print ' GAME STARTS NOW>>>>>>>>>'
        for current_round in all_rounds:

            # ALL play
            somebody_raised = False
            p_list = get_player_list(current_round[1])
            print p_list
            for player in p_list:
                if get_no_of_live_players() <= 1:
                    print 'Only one Player left'
                    break

                current_player = player
                send_them_all('req=data:current_player=' + str(current_player) + '$')
                print ' in all play current_player = ' + str(current_player)

                t = threading.Thread(target = recv_data , args = ())
                t.start()
                t.join()
                print 'curr_data_recvd after join is ' + thread_recvd_data.curr_data_recvd
                req_type = thread_recvd_data.curr_data_recvd.partition(':')[0].partition('=')[2]
                if req_type == 'raiseTO':
                    print str(current_player) + '  raised'
                    somebody_raised = True
                    last_raised = current_player
                    if last_raised_by < int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) - last_raised_amt:
                        last_raised_by = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) - last_raised_amt
                    last_raised_amt = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) 
                    players_money[current_player] -= (last_raised_amt - pot_investment[current_player])
                    pot_money[no_of_pots - 1] += last_raised_amt - pot_investment[current_player]
                    pot_investment[current_player] = last_raised_amt
                    current_player = get_next_player(current_player)
                    send_them_all('req=data:current_player=' + str(current_player) + ';last_raised_amt=' + str(last_raised_amt) + ';last_raised_by=' + str(last_raised_by) + ';players_money=' + str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + '$')
                    break

                elif req_type == 'fold':
                    print str(current_player) + ' folded'
                    live_players[current_player] = 0
                    send_them_all('req=data:live=' + str(live_players) + '$')

                elif req_type == 'call':
                    print str(current_player) + '  called'
                    if (last_raised_amt == int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2])):
                        if players_money[current_player] >= (last_raised_amt - players_money[current_player]):
                            players_money[current_player] -= (last_raised_amt - pot_investment[current_player])
                            pot_money[no_of_pots - 1] += last_raised_amt - pot_investment[current_player]
                            pot_investment[current_player] = last_raised_amt
                            send_them_all('req=data:players_money='+str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + '$')
                        else:
                            print 'player ',current_player,' has ',players_money[current_player],' money, req is ',last_raised_amt
                    else:
                        pass
                        # Split pot


            print 'somebody_raised is ' + str(somebody_raised)
            # If somebody raised
            if somebody_raised:
                print 'current_player an last_raised are ' + str(current_player) + '  :::::  ' +  str(last_raised)

                while(current_player != last_raised): 
                    if get_no_of_live_players() <= 1:
                        print 'Only one Player left'
                        break

                    print ' in raise play current_player = ' + str(current_player)

                    t = threading.Thread(target = recv_data , args = ())
                    t.start()
                    t.join()

                    req_type = thread_recvd_data.curr_data_recvd.partition(':')[0].partition('=')[2]
                    if req_type == 'raiseTO':
                        last_raised = current_player
                        if last_raised_by < int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) - last_raised_amt:
                            last_raised_by = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) - last_raised_amt
                        last_raised_amt = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) 
                        players_money[current_player] -= (last_raised_amt - pot_investment[current_player])
                        pot_money[no_of_pots - 1] += last_raised_amt - pot_investment[current_player]
                        pot_investment[current_player] = last_raised_amt
                        send_them_all('req=data:current_player=' + str(current_player) + ';last_raised_amt=' + str(last_raised_amt) + ';last_raised_by=' + str(last_raised_by) + ';players_money=' + str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + '$')

                    elif req_type == 'fold':
                        print str(current_player) + '  folded'
                        live_players[current_player] = 0
                        send_them_all('req=data:live=' + str(live_players) + '$')

                    elif req_type == 'call':
                        print str(current_player) + '  called'
                        if (last_raised_amt == int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2])):
                            if players_money[current_player] >= last_raised_amt:
                                players_money[current_player] -= (last_raised_amt - pot_investment[current_player])
                                pot_money[no_of_pots - 1] += last_raised_amt - pot_investment[current_player]
                                pot_investment[current_player] = last_raised_amt
                                send_them_all('req=data:players_money='+str(players_money) + ';pot_investment=' + str(pot_investment) + '$')
                            else:
                                print 'player ',current_player,' has ',players_money[current_player],' money, req is ',last_raised_amt
                        else:
                            pass
                            # Split pot

                    current_player = get_next_player(current_player)
                    # Round ends Here
                    if current_player == last_raised:
                        sys.exit()
                    print '---------------END OF LOOP--------------------'
                    print 'current players is  => ',current_player 
                    print 'last_raised is  => ',last_raised
                    print 'players_money is => ',players_money
                    print 'pot_investment is => ',pot_investment
                    print '----------------------------------------------'

                    send_them_all('req=data:current_player=' + str(current_player) + '$')

            # Reinit for next round
            for i in range(0, NO_OF_PLAYERS):
                pot_investment[i] = 0

        sys.exit()

if __name__  ==  '__main__':
    main()
