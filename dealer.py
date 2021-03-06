#!/usr/bin/python2.7
import itertools
import sys
import time
from socket import *
import random
import threading
import thread
from pokereval import hand_evaluator

# Variable Initialisation
NO_OF_PLAYERS = int(sys.argv[1])
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
        #if  live_players[i] == 1 or live_players[i] == 2: Changed By durai in classroom
        if live_players[i] == 1:
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
players_nick = []
def main():
    global current_player, live_players, small_blind, small_blind_amt, big_blind
    global last_raised_amt, last_raised_by, last_raised
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
            print addr[0]
            players_nick.append(data[:4])
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
        #print ' Sending check data  to '
        #print S_HOST
        send_sock[i].connect((S_HOST, S_PORT))
        data = 'req=check:players_nick=' + str(players_nick) + '$'
        send_sock[i].send(data)
        i += 1
    pot_money = []
    pot_money.append(pot_investment[small_blind] + pot_investment[big_blind])
    side_pot = False

    # Game Starts now
    while(True):
        # Get number of players with no money
        no_of_zero_money_players = 0
        for i in range(NO_OF_PLAYERS):
            if players_money[i] <= 0:
                no_of_zero_money_players += 1
        # NO players to play with
        if (NO_OF_PLAYERS - no_of_zero_money_players) <= 1:
            break

        no_of_pots= 1
        # Will be chaged when pot life ends
        pot_players = []
        #live_players = []
        pot_players.append(live_players)
        last_raised_amt = small_blind_amt * 2
        last_raised_by = small_blind_amt * 2
        # Trying to fix a bug
        send_them_all('req=reset$') 
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
            if live_players[i] == 1 or live_players[i] ==2:
                threads.append(threading.Thread(target = send_data, args = (data,i,)))
                threads[-1].start() 
            print str(players_nick[i]) + ' ==> ' + str(cards[(i*2):((i*2)+2)])
            i += 1
        for t in threads:
            t.join()


        del threads
        threads = []
        i = 0
        # Sending Public Data
        #print 'sending data '
        while(i < NO_OF_PLAYERS):
            data = 'req=data:' + 'nop=' + str(NO_OF_PLAYERS) + ';live=' + str(live_players) + ';yourPos=' + str(i) + ";sb=" + str(small_blind) + ";current_player=" + str(current_player) + ";NO_OF_POTS=" + str(no_of_pots) + ";players_money=" + str(players_money) + ";pot_investment=" +str(pot_investment) + ";last_raised_amt=" + str(last_raised_amt) + ';pot_money=' + str(pot_money) + ';last_raised_by=' + str(last_raised_by) + '$'
            threads.append(threading.Thread(target = send_data, args = (data,i,)))
            threads[i].start()
            i += 1

        for t in threads:
            t.join()
        
        del threads
        threads = []
        round_cards = []
        # Rounds start now
        #print ' round  STARTS NOW>>>>>>>>>'
        for current_round in all_rounds:
            print 'round ' + current_round[0] + ' started '
            # ALL play
            current_rnd_pot = no_of_pots - 1
            if current_round[1] == 1:
                current_rnd_pot_amt = 0
            else:
                side_pot = False
                current_rnd_pot_amt = pot_money[current_rnd_pot]
                current_player = small_blind
                if current_round[1] == 2:   #flop
                    round_cards = cards[2*NO_OF_PLAYERS+1:2*NO_OF_PLAYERS+4]
                    send_them_all('req=data:flop_cards=' + str(round_cards) + '$')
                elif current_round[1] == 3:   #turn
                    round_cards = cards[2*NO_OF_PLAYERS+5]
                    send_them_all('req=data:turn_cards=' + str(round_cards) + '$')
                elif current_round[1] == 4:   #river
                    round_cards = cards[2*NO_OF_PLAYERS+7]
                    send_them_all('req=data:river_cards=' + str(round_cards) + '$')

            somebody_raised = False
            p_list = get_player_list(current_round[1])
            #print p_list
            #ALL play
            for player in p_list:
                if get_no_of_live_players() <= 1:
                    print 'Only one Player left'
                    break

                current_player = player
                send_them_all('req=data:current_player=' + str(current_player) + '$')
                #print ' in all play current_player = ' + str(current_player)

                t = threading.Thread(target = recv_data , args = ())
                t.start()
                t.join()
                #print 'curr_data_recvd after join is ' + thread_recvd_data.curr_data_recvd
                req_type = thread_recvd_data.curr_data_recvd.partition(':')[0].partition('=')[2]
                if req_type == 'raiseTO':
                    print str(current_player) + '  raised'
                    somebody_raised = True
                    last_raised = current_player
                    if last_raised_by < int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) - last_raised_amt:
                        last_raised_by = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) - last_raised_amt
                    if int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) == players_money[current_player] + pot_investment[current_player]:
                        live_players[current_player] = 2
#---Marked for confirmation
                    last_raised_amt = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) 
                    players_money[current_player] -= (last_raised_amt - pot_investment[current_player])
                    if side_pot:
                        pot_investment[current_player] = last_raised_amt
                        no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)
                    else:
                        pot_money[no_of_pots - 1] += (last_raised_amt - pot_investment[current_player])
                        pot_investment[current_player] = last_raised_amt
                        send_them_all('req=data:current_player=' + str(current_player) + ';last_raised_amt=' + str(last_raised_amt) + ';last_raised_by=' + str(last_raised_by) + ';players_money=' + str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + ';live=' + str(live_players) + '$')

                    current_player = get_next_player(current_player)
                    send_them_all('req=data:current_player=' + str(current_player) + ';last_raised_amt=' + str(last_raised_amt) + ';last_raised_by=' + str(last_raised_by) + ';players_money=' + str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + ';live=' + str(live_players) +'$')
                    break

                elif req_type == 'fold':
                    print str(current_player) + ' folded'
                    live_players[current_player] = 0
                    # Kick out of all pots code.
                    removeFromPots(current_player, pot_players)
                    print 'player ' + str(current_player) + ' removed '
                    print pot_players
                    send_them_all('req=data:live=' + str(live_players) + '$')

                elif req_type == 'call':
                    print str(current_player) + '  called'

                    # Everything is Good
                    if (last_raised_amt == int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2])):
                        if players_money[current_player] >= (last_raised_amt - players_money[current_player]):
                            players_money[current_player] -= (last_raised_amt - pot_investment[current_player])
                            pot_money[no_of_pots - 1] += last_raised_amt - pot_investment[current_player]
                            pot_investment[current_player] = last_raised_amt
                            if players_money[current_player] == 0:
                                live_players[current_player] = 2
                            if side_pot:
                                pot_investment[current_player] = last_raised_amt
                                no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)
                            else:
                                pot_money[no_of_pots - 1] += (last_raised_amt - pot_investment[current_player])
                                pot_investment[current_player] = last_raised_amt
                                send_them_all('req=data:players_money='+str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + '$')
                            send_them_all('req=data:players_money='+str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + '$')
                        else:
                            print 'player ',current_player,' has ',players_money[current_player],' money, req is ',last_raised_amt
                    
                    # Side pot Required
                    else:
                        side_pot = True
                        players_money[current_player] = 0
                        pot_investment[current_player] = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2])
                        live_players[current_player] = 2
                        no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)


            #print 'somebody_raised is ' + str(somebody_raised)
            # If somebody raised 
            # raise wala code
            if somebody_raised:
                #print 'current_player an last_raised are ' + str(current_player) + '  :::::  ' +  str(last_raised)

                while(current_player != last_raised): 
                    if get_no_of_live_players() <= 1:
                        print 'Only one Player left'
                        break

                    #print ' in raise play current_player = ' + str(current_player)
                    t = threading.Thread(target = recv_data , args = ())
                    t.start()
                    t.join()

                    req_type = thread_recvd_data.curr_data_recvd.partition(':')[0].partition('=')[2]
                    if req_type == 'raiseTO':
                        last_raised = current_player
                        #Everything is good
                        if last_raised_by < int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) - last_raised_amt:
                            last_raised_by = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) - last_raised_amt

                        # All in case
                        if int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) == players_money[current_player] + pot_investment[current_player]:
                            live_players[current_player] = 2

                        last_raised_amt = int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2]) 
                        players_money[current_player] -= (last_raised_amt - pot_investment[current_player])
                        #print '------IN Raise play (raiseTO) side_pot is : ' + str(side_pot)
                        if side_pot:
                            pot_investment[current_player] = last_raised_amt
                            no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)
                        else:
                            pot_money[no_of_pots - 1] += (last_raised_amt - pot_investment[current_player])
                            pot_investment[current_player] = last_raised_amt
                            send_them_all('req=data:current_player=' + str(current_player) + ';last_raised_amt=' + str(last_raised_amt) + ';last_raised_by=' + str(last_raised_by) + ';players_money=' + str(players_money) + ';pot_investment=' + str(pot_investment) + ';pot_money=' + str(pot_money) + ';live=' + str(live_players) + '$')

                    elif req_type == 'fold':
                        print str(current_player) + '  folded'
                        live_players[current_player] = 0
                        removeFromPots(current_player, pot_players)
                        #print 'player ' + str(current_player) + ' removed '
                        #print pot_players
                        send_them_all('req=data:live=' + str(live_players) + '$')

                    elif req_type == 'call':
                        print str(current_player) + '  called'
                        if (last_raised_amt == int(thread_recvd_data.curr_data_recvd.partition(':')[2].partition('=')[2])):
                            if players_money[current_player] + pot_investment[current_player] >= last_raised_amt:
                                players_money[current_player] -= (last_raised_amt - pot_investment[current_player])
                                if players_money[current_player] == 0:
                                    live_players[current_player] == 2

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
                            live_players[current_player] = 2
                            no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, current_rnd_pot_amt, current_rnd_pot)
                            
                    current_player = get_next_player(current_player)
                   
                    print '---------------END OF LOOP--------------------'
                    print 'current players is  => ',current_player 
                    print 'last_raised is  => ',last_raised
                    print 'players_money is => ',players_money
                    print 'pot_investment is => ',pot_investment
                    print '----------------------------------------------'
                     # Round ends Here
                    if current_player == last_raised:
                        break
                    send_them_all('req=data:current_player=' + str(current_player) + '$')

            # Reinit for next round
            for i in range(0, NO_OF_PLAYERS):
                pot_investment[i] = 0
            last_raised_amt = 0
            last_raised_by = small_blind_amt * 2
            send_them_all('req=data:pot_investment=' + str(pot_investment) + ';small_blind=' + str(small_blind) +';players_money=' + str(players_money) + ';last_raised_amt=' + str(last_raised_amt) + ';last_raised_by=' + str(last_raised_by) + '$')
            
            print '---------------End of round------------------------------------------------'
            print 'current players is  => ',current_player 
            print 'last_raised is  => ',last_raised
            print 'players_money is => ',players_money
            print 'pot_investment is => ',pot_investment
            print '---------------------------------------------------------------------------'
                
        print 'round ' + str(current_round) + ' ended'
        # Make showdown list. 
        showdown_list = []
        for player in live_players:
            if player == 1:
                showdown_list.append(1)
            elif player == 2:
                showdown_list.append(1)
            else:
                showdown_list.append(0)
        # Determine winner
        pot_winners = hand_evaluator.decide_winners(pot_players, cards, NO_OF_PLAYERS)
        print 'pot_winners ', pot_winners
        # Distribute pot money according to winner
        distributePotMoneyToWinners(pot_money, pot_winners)

        # Reinit  for next game
        side_pot = False
        # Players who have non-zero money will play
        for i in range(0, NO_OF_PLAYERS):
            if players_money[i] > 0:
                live_players[i]= 1
            else:
                live_players[i]= 0
        # Get new small blind
        small_blind = get_next_player(small_blind)
        big_blind = get_next_player(small_blind)

        # Check if small blind has enough amt to play and handle the situation accordingly
        if players_money[small_blind] < small_blind_amt:
            pot_investment[small_blind] = players_money[small_blind]
            side_pot = True
            live_players[small_blind] = 2
        else:
            pot_investment[small_blind] += small_blind_amt
        players_money[small_blind] -= pot_investment[small_blind]


        # Check if big blind has enough amt to play and handle accordingly
        if players_money[big_blind] < (small_blind_amt * 2):
            pot_investment[big_blind] = players_money[big_blind]
            side_pot = True
            live_players[big_blind] = 2
            no_of_pots = side_pot_handler(no_of_pots, pot_investment, pot_players, pot_money, 0, 0)
        else:
            pot_investment[big_blind] += (small_blind_amt * 2)
        players_money[big_blind] -= pot_investment[big_blind]

        pot_money = []
        pot_money.append(pot_investment[small_blind] + pot_investment[big_blind])


        send_them_all('req=data:pot_investment=' + str(pot_investment) + ';small_blind=' + str(small_blind) +';players_money=' + str(players_money) + '$')
        #send_them_all('req=data:showdown_list=' + str(showdown_list) + ';cards=' + cards + '$')
        print 'req=data:showdown_list=' + str(showdown_list) + ';cards=' + str(cards) + '$'

        # Print them all 
        print '-----------------------------------------------------------------------------------------------------'
        print '\tpot_investment : ' + str( pot_investment)
        print '\tplayers_money : ' + str(players_money)
        print '\tpot_players : ' + str(pot_players)
        print '\tlive_players : ' + str(live_players)
        print '------------------------------------------------------------------------------------------------------'
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
    pot_players.pop()

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
    print "pot players -> last",pot_players[-1]
    
    # How would they know if there were no papers? Send them all.
    send_them_all('req=data:live=' + str(live_players) + ";NO_OF_POTS=" + str(no_of_pots) + ';pot_money=' + str(pot_money) + ';players_money=' + str(players_money) + ';pot_investment=' + str(pot_investment) + ';last_raised_amt=' + str(last_raised_amt) + ';last_raised_by=' + str(last_raised_by) + '$')
    
    return no_of_pots

def removeFromPots(player,pot_players):
    for pot_livers in pot_players:
        pot_livers[player] = 0

def distributePotMoneyToWinners(pot_money, pot_winners):
    for i in range(len(pot_money)):
        for j in range(len(pot_winners[i])):
            players_money[pot_winners[i][j]] += pot_money[i]/len(pot_winners[i])
        for player in random.sample(pot_winners[i], pot_money[i]%len(pot_winners[i])):
            players_money[player] += 1
    send_them_all('req=data:players_money=' + str(players_money) + '$')



if __name__  ==  '__main__':
    main()
