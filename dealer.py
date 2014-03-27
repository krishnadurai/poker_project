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
NO_OF_PLAYERS = 5
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
last_raised_by = small_blind_amt * 2

# Money in players hand
players_money = []
for i in range(0, NO_OF_PLAYERS):
    players_money.append(INITIAL_MONEY/(i+1))
    if i == 2:
        players_money[2] = 1000
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
    global current_player, live_players
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

    # Game Starts now
    while(True):
        no_of_pots= 1
        # Will be chaged when pot life ends
        # pot_players = [[1,1,1,1,1,1,1,1]]
        pot_players = []
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
            data = 'req=data:' + 'nop=' + str(NO_OF_PLAYERS) + ';live=' + str(live_players) + ';yourPos=' + str(i) + ";sb=" + str(small_blind) + ";current_player=" + str(current_player) + ";NO_OF_POTS=" + str(no_of_pots) + ";players_money=" + str(players_money) + ";pot_investment=" +str(pot_investment) + ";last_raised_amt=" + str(last_raised_amt) + ';pot_money=' + str(pot_money) + ';last_raised_by=' + str(last_raised_by) + '$'
            threads.append(threading.Thread(target = send_data, args = (data,i,)))
            threads[i].start()
            i += 1

        for t in threads:
            t.join()
        
        del threads
        threads = []
        # Rounds start now
        print ' GAME STARTS NOW>>>>>>>>>'
        for current_round in all_rounds:
            # ALL play
            side_pot = False
            current_rnd_pot = no_of_pots - 1
            # updated_live_players = []
            if current_round[1] == 1:
                current_rnd_pot_amt = 0
            else:
                current_rnd_pot_amt = pot_money[current_rnd_pot]
            somebody_raised = False
            p_list = get_player_list(current_round[1])
            print p_list
            for player in p_list:
                if get_no_of_live_players() <= 1:
                    print 'Only one Player le/ft'
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
                    # Kick out of all pots code.
                    removeFromPots(current_player, pot_players)
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
                        side_pot = True
                        players_money[current_player] = 0
                        pot_investment[current_player] = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2])
                        live_players[current_player] = 2
                        no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)


            print 'somebody_raised is ' + str(somebody_raised)
            # If somebody raised 
            # raise wala code
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
                        print '------IN Raise play (raiseTO) side_pot is : ' + str(side_pot)
                        if side_pot:
                            pot_investment[current_player] = last_raised_amt
                            # updated_live_player,no_of_pot = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)
                            no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)
                        else:
                            pot_money[no_of_pots - 1] += (last_raised_amt - pot_investment[current_player])
                            pot_investment[current_player] = last_raised_amt
                            send_them_all('req=data:current_player=' + str(current_player) + ';last_raised_amt=' + str(last_raised_amt) + ';last_raised_by=' + str(last_raised_by) + ';players_money=' + str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + '$')
                    elif req_type == 'fold':
                        print str(current_player) + '  folded'
                        live_players[current_player] = 0
                        removeFromPots(current_player, pot_players)
                        send_them_all('req=data:live=' + str(live_players) + '$')
                    elif req_type == 'call':
                        print str(current_player) + '  called'
                        if (last_raised_amt == int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2])):
                            if players_money[current_player] + pot_investment[current_player] >= last_raised_amt:
                                players_money[current_player] -= (last_raised_amt - pot_investment[current_player])
                                if side_pot:
                                    pot_investment[current_player] = last_raised_amt
                                    no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)
                                else:
                                    pot_money[no_of_pots - 1] += (last_raised_amt - pot_investment[current_player])
                                    pot_investment[current_player] = last_raised_amt
                                    send_them_all('req=data:players_money='+str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + '$')
                            else:
                                print 'player ',current_player,' has ',players_money[current_player],' money, req is ',last_raised_amt
                        else:
                            side_pot = True
                            players_money[current_player] = 0
                            pot_investment[current_player] = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2])
                            # updated_live_player,no_of_pot = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)
                            live_players[current_player] = 2
                            no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)
                            
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
            # if side_pot:
                # live_players = updated_live_players #Check for 2's and merge properly
            print '---------------End of round--------------------'
            print 'current players is  => ',current_player 
            print 'last_raised is  => ',last_raised
            print 'players_money is => ',players_money
            print 'pot_investment is => ',pot_investment
            print '----------------------------------------------'

        sys.exit()

def side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot):
    global current_player, live_players, NO_OF_PLAYERS
    global last_raised_amt, last_raised_by
    # Still a dark, untested piece of shit. 
    # Make a Side pot when someone goes all-in
    # Find minimum non-zero pot investment

    # Making copies of all looser's money. I wish I could earn out of it.
    pot_inv_copy = [(p, i) for i, p in enumerate(pot_investment)]
    pot_inv_copy.sort(reverse=True)
    while pot_inv_copy[-1][0]==0 :
        pot_inv_copy.pop()
    print 'pot_inv_copy', pot_inv_copy
    print 'live players', live_players
    pot_entries = [] # pot_entries are the entry amounts for the pots made in the round.
    for inv in pot_inv_copy:
        if live_players[inv[1]] == 2:
            pot_entries.append(inv)
    if pot_entries[0][0] != pot_inv_copy[0][0]:
        pot_entries.insert(0, pot_inv_copy[0])
    print 'pot entries', pot_entries
    # Investments are subject to market risks. Just Kidding. Initializing to round begin values.
    i = len(pot_money)-1
    while i!=current_rnd_pot:
        pot_money.pop()
        pot_players.pop()
        i -= 1
        no_of_pots -= 1
    pot_money[-1] = current_rnd_pot_amt

    # Leading life is impossible without this. This is the answer to life, universe and everything. 42. Ok, setting pot values.
    pot_players_tracker = [0] * NO_OF_PLAYERS
    for inv in pot_inv_copy:
        if live_players[inv[1]] != 0:
            pot_players_tracker[inv[1]] = 1
    print 'pot_players_tracker initial', pot_players_tracker

    prev_min_inv_amt = 0
    i = current_rnd_pot
    min_investor = pot_entries.pop()
    for inv in pot_inv_copy:
        if inv[0] > prev_min_inv_amt:
            if min_investor[0] - prev_min_inv_amt > inv[0] - prev_min_inv_amt:
                pot_money[i] += inv[0] - prev_min_inv_amt
            else:
                pot_money[i] += min_investor[0] - prev_min_inv_amt
    print 'pot money current rnd', pot_money[i]
    prev_min_inv_amt = min_investor[0]
    pot_players.append([p for p in pot_players_tracker])
    pot_players_tracker[min_investor[1]] = 0
    print 'pot_players_tracker', pot_players_tracker

    while pot_entries:
        min_investor = pot_entries.pop()
        print 'prev min inv amt', prev_min_inv_amt
        if prev_min_inv_amt < min_investor[0]:
            pot_money.append(0)
            i = i + 1
            no_of_pots += 1
            for inv in pot_inv_copy:
                if inv[0] > prev_min_inv_amt:
                    if min_investor[0] - prev_min_inv_amt > inv[0] - prev_min_inv_amt:
                        pot_money[i] += inv[0] - prev_min_inv_amt
                    else:
                        pot_money[i] += min_investor[0] - prev_min_inv_amt
                print 'for investment ', inv[0],'for pos ', inv[1], 'pot money is ', pot_money[i]
            print 'pot money next pots', pot_money[i]
            pot_players.append([p for p in pot_players_tracker])
            prev_min_inv_amt = min_investor[0]
        pot_players_tracker[min_investor[1]] = 0
    print 'pot_players_tracker', pot_players_tracker

    # updated_live_players = mergeSidePotAndLivePlayers(pot_players.pop())
    pot_players.pop()
    print "pot players -> last",pot_players[-1]
    # print "updated live players",updated_live_players
    # How would they know if there were no papers? Send them all.
    send_them_all('req=data:live=' + str(live_players) + ";NO_OF_POTS=" + str(no_of_pots) + ';pot_money=' + str(pot_money) + ';players_money=' + str(players_money) + ';pot_investment=' + str(pot_investment) + '$')
    # return updated_live_players,no_of_pots
    return no_of_pots

def removeFromPots(player,pot_players):
    for pot_livers in pot_players:
        pot_livers[player] = 0

def mergeSidePotAndLivePlayers(side_pot_players):
    global live_players
    updated_live_players = []
    for i in range(0,len(live_players)):
        if live_players[i] == 2:
            updated_live_players.append(2)
        else:
            updated_live_players.append(side_pot_players[i])
    return updated_live_players

if __name__  ==  '__main__':
    main()
