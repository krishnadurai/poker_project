#!/usr/bin/python2.7
import itertools
import sys
import time
from socket import *
import random
import hand_evaluator

# Variable Initialisation
NO_OF_PLAYERS = 1

INITIAL_MONEY = 1000

MINIMUM_RAISE = 1

small_blind=random.randint(0, NO_OF_PLAYERS-1);

players_money = []
for i in range(0, NO_OF_PLAYERS):
    players_money.append(INITIAL_MONEY)

live_players = ""
for i in range(0, NO_OF_PLAYERS):
    live_players += "1"

current_round = 0

current_player = small_blind

pot_investment = [0] * NO_OF_PLAYERS

pot_investment[small_blind] = 1

big_blind = (small_blind + 1) % NO_OF_PLAYERS

pot_investment[big_blind] = 2


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

# Main
def main():
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    HOST = ''
    PORT = 11717
    s.bind((HOST, PORT))
    ip_array = []
    print 'OK ready for connection'
    while(1):
        s.listen(1)
        conn, addr = s.accept()
        try:
            data = conn.recv(1024)
            if data == 'req':
                print addr[0]
                ip_array.append(addr[0])
                conn.close()
        except:
            print 'we are unable to receive data from client or bad request'
        if(len(ip_array) == NO_OF_PLAYERS):
            break
    s.close()
    time.sleep(1)
    print ' Sending cards to players'
    cards = random.sample(DECK, 2 * NO_OF_PLAYERS + 8)
    i = 0
    sock=[]
    while(i < NO_OF_PLAYERS):
        HOST = ip_array[i]
        PORT = 11716
        sock.append(socket(AF_INET, SOCK_STREAM))
        print 'Sending cards to '
        print HOST
        sock[i].connect((HOST, PORT))
        data = 'req=cards:' + cards[i * 2] + "," + cards[i * 2 + 1]
        sock[i].send(data)
        i += 1
        print 'cards sent to '
        print HOST
    i = 0
    """print 'sending data '
    time.sleep(3)
    while(i < NO_OF_PLAYERS):
        data = 'req=data:' + 'nop=' + str(NO_OF_PLAYERS) + ',live=' + live_players + ',yourPos=' + str(i) + ",sb=" + str(small_blind)
        sock[i].send(data)
        i += 1
    """
if __name__  ==  '__main__':
    main()
