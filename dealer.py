#!/usr/bin/python2.7
import itertools
import sys
import time
from socket import *
import random
import hand_evaluator
import threading
import thread 

# Variable Initialisation
NO_OF_PLAYERS = 2

INITIAL_MONEY = 1000

MINIMUM_RAISE = 1

small_blind=random.randint(0, NO_OF_PLAYERS-1);


# Money in players hand
players_money = []
for i in range(0, NO_OF_PLAYERS):
    players_money.append(INITIAL_MONEY)


# Players involved in currently
live_players = ""
for i in range(0, NO_OF_PLAYERS):
    live_players += "1"


NO_OF_POTS = 1

# players in the current pot
pot_money = [0] * 8

# Will be chaged when pot life ends
pot_players = []
current_round = 0


# Player investment in round
pot_investment = [0] * NO_OF_PLAYERS
pot_investment[small_blind] = 1
big_blind = (small_blind + 1) % NO_OF_PLAYERS
pot_investment[big_blind] = 2
current_player = (big_blind + 1 ) % NO_OF_PLAYERS
#current_player = 2
# Player who raised last
last_raised = big_blind
last_raised_amt = pot_investment[big_blind]

# data
SUITS = ('c', 'd', 'h', 's')
RANKS = ('2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')

#DECK stores all cards
DECK = tuple(''.join(card) for card in itertools.product(RANKS,SUITS))
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
        except:
            print 'wtf'

# Send Data func
def send_data(data,i):
    try:
        send_sock[i].send(data)
    except:
        print 'wtf'

# Main
send_sock=[]
recv_conn = []
def main():
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

# Check conn
    i = 0
    S_PORT = 11716
    while(i < NO_OF_PLAYERS):
        S_HOST = ip_array[i]
        send_sock.append(socket(AF_INET, SOCK_STREAM))
        print ' Sending check data  to '
        print S_HOST
        send_sock[i].connect((S_HOST, S_PORT))
        data = 'req=check'
        send_sock[i].send(data)
        i += 1

    while(True):
        time.sleep(1)
        i = 0
        # Sending details 
        while(i < NO_OF_PLAYERS):
            print ' Sending initial data  to '
            print S_HOST
            data = 'req=init:' +  'nop=' + str(NO_OF_PLAYERS) + ';yourPos=' + str(i) + ";sb=" + str(small_blind) + ";players_money=" + str(players_money) 
            thread.start_new_thread(send_data, (data,i,))
            i += 1
            print 'initial data sent to '
            print S_HOST

#Sending card
        time.sleep(1)
        i = 0
        print ' Sending cards to players'
        cards = random.sample(DECK, 2 * NO_OF_PLAYERS + 8)
        while(i < NO_OF_PLAYERS):
            data = 'req=cards:' + cards[i * 2] + "," + cards[i * 2 + 1]
            thread.start_new_thread(send_data, (data,i,))
            i += 1

        i = 0
        print 'sending data '
        time.sleep(1)
        while(i < NO_OF_PLAYERS):
            data = 'req=data:' + 'nop=' + str(NO_OF_PLAYERS) + ';live=' + live_players + ';yourPos=' + str(i) + ";sb=" + str(small_blind) + ";current_player=" + str(current_player) + ";NO_OF_POTS=" + str(NO_OF_POTS) + ";last_raised=" + str(last_raised) + ";players_money=" + str(players_money) + ";pot_investment=" +str(pot_investment) + ";last_raised_amt=" + str(last_raised_amt)
            thread.start_new_thread(send_data, (data,i,))
            i += 1
        while(current_player != last_raised): 
            t = threading.Thread(target = recv_data , args = ())
            t.start()
            t.join()
        
        sys.exit()
if __name__  ==  '__main__':
    main()
