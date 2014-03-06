#!/usr/bin/python2.7
import itertools
import time
import random
import sys

#Global data
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


# utility functions
def cmp_cards(a, b):
    return cmp(ORDER_LOOKUP[a], ORDER_LOOKUP[b])
def cmp_tuples(a, b):
    n1 = len(a)
    n2 = len(b)
    if n1 != n2:
        return cmp(n1, n2)
    return cmp(a, b)
def suit(card):
    return card[1]
def suit_int(card):
    return SUIT_LOOKUP[card[1]]
def rank(card):
    return card[0]
def rank_int(card):
    return RANK_LOOKUP[card[0]]
def card_int(card):
    s = 1 << suit_int(card)
    r = rank_int(card)
    c = (s << 4) | r
    return c

#Tested
def rank_count(cards):
    result = {}
    for card in cards:
        r = rank_int(card)
        result[r] = result.get(r, 0) + 1
    return result
#Tested
def get_ranks(counts):
    values = [(count, rank) for rank, count in counts.iteritems()]
    values.sort(reverse=True)
    values = [n[1] for n in values]
    return values

#Tested
def is_full_house(cards, counts=None):
    isThree, isTwo = False, False
    counts = counts or rank_count(cards)
    for rank, count in counts.iteritems():
        if not isThree and count == 3:
            isThree = True
            continue
        if not isTwo and count >= 2:
            isTwo = True
    return isThree and isTwo

def is_flush(cards):
    suit_map = [[0, []], [0, []], [0, []], [0, []]]
    for card in cards:
        s = suit_int(card)
        suit_map[s][0] += 1
        suit_map[s][1].append(card)
    flush_suit = -1
    for i in range(len(suit_map)):
        if len(suit_map[i][1])>=5:
            flush_suit = i
    if flush_suit!= -1:
        return (True, suit_map[flush_suit][1])
    else:
        return (False, -1)


#Tested
def is_straight(cards):
    card_map = [0]*13
    for card in cards:
        r = rank_int(card)
        card_map[r] = 1
    straight_size = 0
    straight_pos = -1
    if card_map[12]==1:
        straight_size = 1
        for i in range(4):
            if card_map[i] == 1:
                straight_size += 1
                if straight_size >= 5:
                    straight_pos = i
            else:
                straight_size = 0
    straight_size = 0
    for i in range(len(card_map)):
        if card_map[i] == 1:
            straight_size += 1
            if straight_size >= 5:
                straight_pos = i
        else:
            straight_size = 0
    if straight_pos >= 3:
        return (True, straight_pos)
    else:
        return (False, -1)
        

#Tested
def is_four(cards, counts=None):
    counts = counts or rank_count(cards)
    for rank, count in counts.iteritems():
        if count == 4:
            return True
    return False

#Tested
def is_three(cards, counts=None):
    counts = counts or rank_count(cards)
    for rank, count in counts.iteritems():
        if count == 3:
            return True
    return False
#Tested
def is_two_pair(cards, counts=None):
    pairs = 0
    counts = counts or rank_count(cards)
    for rank, count in counts.iteritems():
        if count == 2:
            pairs += 1
    return pairs >= 2
#Tested
def is_pair(cards, counts=None):
    counts = counts or rank_count(cards)
    for rank, count in counts.iteritems():
        if count == 2:
            return True
    return False


def get_straight_rank(cards):
    top = rank_int(cards[-1])
    bottom = rank_int(cards[0])
    if top == 12 and bottom == 0:
        return 3
    return top
def evaluate_hand(cards):
    flush, flush_cards = is_flush(cards)
    if flush:
        straight, straight_card = is_straight(flush_cards)
    else:
        straight, straight_card = is_straight(cards)
    counts = rank_count(cards)
    ranks = get_ranks(counts)
    value = 0
    '''
    if straight:
        ranks = [get_straight_rank(cards)]
    '''
    if flush and straight:
        value = 9
        ranks = [straight_card]
    elif is_four(cards):
        value = 8
        ranks = ranks[:1] + [max(ranks[1:])]
        ranks = ranks[:2]
    elif is_full_house(cards):
        value = 7
        ranks = ranks[:2]
    elif flush:
        value = 6
        ranks = [rank_int(max([c[0] for c in flush_cards]))]
    elif straight:
        value = 5
        ranks = [straight_card]
    elif is_three(cards, counts):
        value = 4
        ranks = ranks[:3]
    elif is_two_pair(cards, counts):
        value = 3
        ranks = ranks[:2] + [max(ranks[2:])]
        ranks = ranks[:3]
    elif is_pair(cards, counts):
        value = 2
        ranks = ranks[:4]
    else:
        value = 1
    ranks.insert(0, value)
    return ranks


def main():
    cards = random.sample(DECK, 7)
    #cards = ['7d', 'Kh', '8h', 'Ks', '8s', '8c', '8d']
    print cards
    print evaluate_hand(cards)
    
    from time import time
    t1 = time()
    print 'Generating stats'
    values = [0]*10
    for i in xrange(1000000):
        cards = random.sample(DECK, 5)
        values[evaluate_hand(cards)[0]] += 1    
    print values
    print 'Time elapsed' + str(time()-t1)

    
if __name__  ==  '__main__':
    main()
