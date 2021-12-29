#!/usr/bin/env python3
import traceback
import sys
import socket
import random
import time
import math
import sqlite3
import os
import configparser
import argparse
import queue
from datetime import datetime
W =     WHITE =     "\x0300"
K =     BLACK =     "\x0301"
B =     BLUE =      "\x0302"
G =     GREEN =     "\x0303"
R =     RED =       "\x0304"
BR =    BROWN =     "\x0305"
P =     PURPLE =    "\x0306"
O =     ORANGE =    "\x0307"
Y =     YELLOW =    "\x0308"
LG =    L_GREEN =   "\x0309"
C =     CYAN =      "\x0310"
LC =    L_CYAN =    "\x0311"
LB =    L_BLUE =    "\x0312"
PK =    PINK =      "\x0313"
GY =    GRAY =      "\x0314"
LGY =   L_GRAY =    "\x0315"
X =     CLEAR =     "\x03" # XXX non printing character or something here?

type_dict = {
    #           2X effective                                1/2 effective                                               0 effective
    "water":    (["ground", "rock", "fire"],                ["water", "grass"],                                         []),
    "grass":    (["ground", "rock", "water"],               ["flying", "poison", "bug", "fire", "grass", "dragon"],     []),
    "fire":     (["bug", "grass", "ice"],                   ["rock", "fire", "water", "dragon"],                        []),
    "electric": (["flying", "water"],                       ["grass", "electric", "dragon"],                            ["ground"]),
    "ground":   (["poison", "rock", "fire", "electric"],    ["bug", "grass"],                                           ["flying"]),
    "rock":     (["fire", "bug", "flying", "ice"],          ["fighting", "ground"],                                     []),
    "flying":   (["fighting", "bug", "grass"],              ["rock", "electric"],                                       []),
    "normal":   ([],                                        ["rock"],                                                   ["ghost"]),
    "psychic":  (["fighting", "poison"],                    ["psychic"],                                                []),
    "ghost":    (["ghost", "psychic"],                      [],                                                         ["normal"]),
    "dragon":   (["dragon"],                                [],                                                         []),
    "ice":      (["flying", "ground", "grass", "dragon"],   ["water", "ice", "fire"],                                   []),
    "bug":      (["grass", "psychic"],                      ["poison", "fighting", "flying", "ghost", "fire"],          []),
    "fighting": (["normal", "rock", "ice"],                 ["flying", "poison", "bug", "psychic"],                     ["ghost"]),
    "poison":   (["grass"],                                 ["poison", "ground", "rock", "bug"],                        []),
}
type_color_dict = {
    "electric": "08",
    "fire": "04",
    "water": "02",
    "grass": "09",
    "ground": "05",
    "rock": "14",
    "flying": "11",
    "normal": "00",
    "psychic": "13",
    "ghost": "06",
    "dragon": "12",
    "ice": "10",
    "bug": "15",
    "fighting": "03",
    "poison": "07"
    }


"""Notable changes from gen 1:
    Pokemon only have 1 type
    Type advantages use Generation 2 fixes (bug weak against poison, poison not strong against bug, 
                                                ghost strong against psychic, ice weak against fire)
    EVs aren't implemented (this may change)
    You can only fight a wild pokemon with one pokemon, no switching out.
    You can steal someone else's weakened wild pokemon if that wild pokemon won.
    No potions or pokecenter.  Pokemon heal slowly over time.
    No specific moves. Instead of implementing hundreds of moves, pokemon are to be viewed as more doing whatever they can to win
        sorta like a dog or cock fight, with no commands from the trainer. They all have a weak and strong normal attack and weak and strong special attack
    This means no status changes.  
    Instead of a single Special stat, uses Special Attack and Special Defense
"""

# water: blue
# grass: light green
# fire: light red
# electric: yellow
# ground: brown
# rock: grey
# flying: light cyan
# normal: white
# psychic: pink
# ghost: purple
# dragon: light blue
# ice: cyan
# bug: light gray
# fighting: white
# poison: green
starters = (
    "bulbasaur", 
    "squirtle",
    "charmander",
    "pikachu",
    "caterpie",
    "pidgey",
    "meowth",
    "nidoran_m",
    "nidoran_f",
    "abra",
    "gastly",
    "machop",
    "geodude",
    "dratini",
    "cubone",
    )

pokemon_dict = {
    # name              idx     type         rare,grth,bexp     hp  att def satt sdef spd      evolution    lvl
    "Bulbasaur":        (1,     "grass",        2,2,64,         (45, 49, 49,  65,  65, 45),  ("Ivysaur",     16),    8),
    "Ivysaur":          (2,     "grass",        2,2,141,        (60, 62, 63,  80,  80, 60),  ("Venusaur",     32),   16),
    "Venusaur":         (3,     "grass",        2,2,208,        (80, 82, 83, 100, 100, 80),  ("XXXXXXX",     0),     32),
    "Charmander":       (4,     "fire",         2,2,65,         (39, 52, 43, 60, 50, 65),  ("Charmeleon",     16),   8),
    "Charmeleon":        (5,     "fire",         2,2,142,        (58, 64, 58, 80, 65, 80),  ("Charizard",     36),   16),
    "Charizard":        (6,     "fire",         2,2,209,        (78, 84, 78, 109, 85, 100),  ("XXXXXXX",     0),     32),
    "Squirtle":         (7,     "water",        2,2,66,         (44, 48, 65, 50, 64, 43),  ("Wartortle",     16),    8),
    "Wartortle":        (8,     "water",        2,2,143,        (59, 63, 80, 65, 80, 58),  ("Blastoise",     36),    16),
    "Blastoise":        (9,     "water",        2,2,210,        (79, 83, 100, 85, 105, 78),  ("XXXXXXX",     0),     32),
    "Caterpie":         (10,     "bug",         0,1,53,         (45, 30, 35, 20, 20, 45),  ("Metapod",     7),       2),
    "Metapod":          (11,     "bug",         0,1,72,         (50, 20, 55, 25, 25, 30),  ("Butterfree",    10),    7),
    "Butterfree":       (12,     "bug",         1,1,160,        (60, 45, 50, 90, 80, 70),  ("XXXXXXX",     0),       10),
    "Weedle":           (13,     "bug",         0,1,52,         (40, 35, 30, 20, 20, 50),  ("Kakuna",     7),        2),
    "Kakuna":           (15,     "bug",         0,1,71,         (45, 25, 50, 25, 25, 35),  ("Beedrill",     10),     7),
    "Beedrill":         (15,     "bug",         1,1,159,        (65, 90, 40, 45, 80, 75),  ("XXXXXXX",     0),       10),
    "Pidgey":           (16,     "flying",      0,2,55,         (40, 45, 40, 35, 35, 56),  ("Pidgeotto",     18),    2),
    "Pidgeotto":        (17,     "flying",      1,2,113,        (63, 60, 55, 50, 50, 71),  ("Pidgeot",     36),      18),
    "Pidgeot":          (18,     "flying",      1,2,172,        (83, 80, 75, 70, 70, 101),  ("XXXXXXX",     0),      36),
    "Rattata":          (19,     "normal",      0,1,57,         (30, 56, 35, 25, 35, 72),  ("Raticate",     20),     2),
    "Raticate":         (20,     "normal",      1,1,116,        (55, 81, 60, 50, 70, 97),  ("XXXXXXX",     0),       20),
    "Spearow":          (21,     "flying",      0,1,58,         (40, 60, 30, 31, 31, 70),  ("Fearow",     20),       2),
    "Fearow":           (22,     "flying",      1,1,162,        (65, 90, 65, 61, 61, 100),  ("XXXXXXX",     0),      20),
    "Ekans":            (23,     "poison",      1,1,62,         (35, 60, 44, 40, 54, 55),  ("Arbok",     22),        3),
    "Arbok":            (24,     "poison",      1,1,147,        (60, 95, 69, 65, 79, 80),  ("XXXXXXX",     0),       22),
    "Pikachu":          (25,     "electric",    2,1,82,         (35, 55, 40, 50, 50, 90),  ("Raichu",     22),       8), # added
    "Raichu":           (26,     "electric",    2,1,122,        (60, 90, 55, 90, 80, 110),  ("XXXXXXX",     0),      22),
    "Sandshrew":        (27,     "ground",      1,1,93,         (50, 75, 85, 20, 30, 40),  ("Sandslash",     22),    4),
    "Sandslash":        (28,     "ground",      1,1,163,        (75, 100, 110, 45, 55, 65),  ("XXXXXXX",     0),     22),
    "Nidoran_f":        (29,     "poison",      0,2,59,         (55, 47, 52, 40, 40, 41),  ("Nidorina",     16),     3),
    "Nidorina":         (30,     "poison",      1,2,117,        (70, 62, 67, 55, 55, 56),  ("Nidoqueen",     35),    16), # added
    "Nidoqueen":        (31,     "poison",      1,2,194,        (90, 92, 87, 75, 85, 76),  ("XXXXXXX",     0),       35),
    "Nidoran_m":        (32,     "poison",      0,2,60,         (46, 57, 40, 40, 40, 50),  ("Nidorino",     16),     3),
    "Nidorino":         (33,     "poison",      1,2,118,        (61, 72, 57, 55, 55, 65),  ("Nidoking",     35),     16), # added
    "Nidoking":         (34,     "poison",      1,2,195,        (81, 102, 77, 85, 75, 85),  ("XXXXXXX",     0),      35),
    "Clefairy":         (35,     "normal",      2,0,68,         (70, 45, 48, 60, 65, 35),  ("Clefable",     30),     5), # added
    "Clefable":         (36,     "normal",      2,0,129,        (95, 70, 73, 95, 90, 60),  ("XXXXXXX",     0),       30),
    "Vulpix":           (37,     "fire",        1,1,63,         (38, 41, 40, 50, 65, 65),  ("Ninetails",     30),    5), # added
    "Ninetails":        (38,     "fire",        1,1,178,        (73, 76, 75, 81, 100, 100),  ("XXXXXXX",     0),     30),
    "Jigglypuff":       (39,     "normal",      2,0,76,         (115, 45, 20, 45, 25, 20),  ("Wigglytuff",     30),  5), # added
    "Wigglytuff":       (40,     "normal",      2,0,109,        (140, 70, 45, 85, 50, 45),  ("XXXXXXX",     0),      30),
    "Zubat":            (41,     "poison",      0,1,54,         (40,  45, 35, 30, 40, 55),  ("Golbat",     22),      5),
    "Golbat":           (42,     "poison",      1,1,171,        (75, 80, 70, 65, 75, 90),  ("XXXXXXX",     0),       22),
    "Oddish":           (43,     "grass",       0,2,78,         (45, 50, 55, 75, 65, 30),  ("Gloom",     21),        5),
    "Gloom":            (44,     "grass",       1,2,132,        (60, 65, 70, 85, 75, 40),  ("Vileplume",     40),    21), # added
    "Vileplume":        (45,     "grass",       1,2,184,        (75, 80, 85, 110, 90, 50),  ("XXXXXXX",     0),      40),
    "Paras":            (46,     "bug",         1,1,70,         (35, 70, 55, 45, 55, 25),  ("Parasect",     24),     5),
    "Parasect":         (47,     "bug",         1,1,128,        (60, 95, 80, 60, 80, 30),  ("XXXXXXX",     0),       24),
    "Venonat":          (48,     "bug",         1,1,75,         (60, 55, 50, 40, 55, 45),  ("Venomoth",     31),     5),
    "Venomoth":         (49,     "bug",         1,1,138,        (70, 65, 60, 90, 75, 90),  ("XXXXXXX",     0),       31),
    "Diglett":          (50,     "ground",      0,1,81,         (10, 55, 25, 35, 45, 95),  ("Dugtrio",     26),      6),
    "Dugtrio":          (51,     "ground",      1,1,153,        (35, 100, 50, 50, 70, 120),  ("XXXXXXX",     0),     26),
    "Meowth":           (52,     "normal",      1,1,69,         (40, 45, 35, 40, 40, 90),  ("Persian",     28),      8),
    "Persian":          (53,     "normal",      1,1,148,        (65, 70, 60, 65, 65, 115),  ("XXXXXXX",     0),      28),
    "Psyduck":          (54,     "psychic",       1,1,80,         (50, 52, 48, 65, 50, 55),  ("Golduck",     33),      10),
    "Golduck":          (55,     "psychic",       1,1,174,        (80, 82, 78, 95, 80, 85),  ("XXXXXXX",     0),       33),
    "Mankey":           (56,     "fighting",    1,1,74,         (40, 80, 35, 35, 45, 70),  ("Primeape",     28),     8),
    "Primeape":         (57,     "fighting",    1,1,149,        (65, 105, 60, 60, 70, 85),  ("XXXXXXX",     0),      28),
    "Growlithe":        (58,     "fire",        1,3,91,         (55, 70, 45, 70, 50, 60),  ("Arcanine",     30),     10), # added
    "Arcanine":         (59,     "fire",        1,3,213,        (90, 110, 80, 100, 80, 95),  ("XXXXXXX",     0),     30),
    "Poliwag":          (60,     "water",       1,2,77,         (40, 50, 40, 40, 40, 90),  ("Poliwhirl",     25),    8),
    "Poliwhirl":        (61,     "water",       1,2,131,        (65, 65, 65, 50, 50, 90),  ("Poliwrath",     40),    25), #added
    "Poliwrath":        (62,     "water",       1,2,185,        (90, 95, 95, 70, 90, 70),  ("XXXXXXX",     0),       40),
    "Abra":             (63,     "psychic",     1,2,73,         (25, 20, 15, 105, 55, 90),  ("Kadabra",     16),     8),
    "Kadabra":          (64,     "psychic",     1,2,145,        (40, 35, 30, 120, 70, 105),  ("Alakazam",     40),   16), #added
    "Alakazam":         (65,     "psychic",     2,2,186,        (55, 50, 45, 135, 95, 120),  ("XXXXXXX",     0),     40),
    "Machop":           (66,     "fighting",    1,2,88,         (70, 80, 50, 35, 35, 35),  ("Machoke",     28),      8),
    "Machoke":          (67,     "fighting",    1,2,146,        (80, 100, 70, 50, 60, 45),  ("Machamp",     40),     28), #added
    "Machamp":          (68,     "fighting",    2,2,193,        (90, 130, 80, 65, 85, 55),  ("XXXXXXX",     0),      40),
    "Bellsprout":       (69,     "grass",       1,2,84,         (50, 75, 35, 70, 30, 40),  ("Weepinbell",     21),   8),
    "Weepinbell":       (70,     "grass",       1,2,151,        (65, 90, 50, 85, 45, 55),  ("Victreebell",     40),  21), #added
    "Victreebel":       (71,     "grass",       2,2,191,        (80, 105, 65, 100, 70, 70),  ("XXXXXXX",     0),     40),
    "Tentacool":        (72,     "water",       1,3,105,        (40, 40, 35, 50, 100, 70),  ("Tentacruel",     30),  10),
    "Tentacruel":       (73,     "water",       1,3,205,        (80, 70, 65, 80, 120, 100),  ("XXXXXXX",     0),     30),
    "Geodude":          (74,     "rock",        1,2,86,         (40, 80, 100, 30, 30, 20),  ("Graveler",     25),    9),
    "Graveler":         (75,     "rock",        1,2,134,        (55, 95, 115, 45, 45, 35),  ("Golem",     45),       25), #added
    "Golem":            (76,     "rock",        2,2,177,        (80, 120, 130, 55, 65, 45),  ("XXXXXXX",     0),     45),
    "Ponyta":           (77,     "fire",        1,1,152,        (50, 85, 55, 65, 65, 90),  ("Rapidash",     40),     12),
    "Rapidash":         (78,     "fire",        1,1,192,        (65, 100, 70, 80, 80, 105),  ("XXXXXXX",     0),     40),
    "Slowpoke":         (79,     "water",       1,1,99,         (90, 65, 65, 40, 40, 15),  ("Slowbro",     37),      12),
    "Slowbro":          (80,     "water",       1,1,164,        (95, 75, 110, 100, 80, 30),  ("XXXXXXX",     0),     37),
    "Magnemite":        (81,     "electric",    1,1,89,         (25, 35, 70, 95, 55, 45),  ("Magneton",     30),     12),
    "Magneton":         (82,     "electric",    1,1,161,        (50, 60, 95, 120, 70, 70),  ("XXXXXXX",     0),      30),
    "Farfetch'd":       (83,     "flying",      2,1,94,         (52, 90, 55, 58, 62, 60),  ("XXXXXXX",     0),       12),
    "Doduo":            (84,     "flying",      1,1,96,         (35, 85, 45, 35, 35, 75),  ("Dodrio",     31),       12),
    "Dodrio":           (85,     "flying",      1,1,158,        (60, 110, 70, 60, 60, 110),  ("XXXXXXX",     0),     31),
    "Seel":             (86,     "water",       1,1,100,        (65, 45, 55, 45, 70, 45),  ("Dewgong",     34),      12),
    "Dewgong":          (87,     "water",       1,1,176,        (90, 70, 80, 70, 95, 70),  ("XXXXXXX",     0),       34),
    "Grimer":           (88,     "poison",      1,1,90,         (80, 80, 50, 40, 50, 25),  ("Muk",     38),          20),
    "Muk":              (89,     "poison",      1,1,157,        (105, 105, 75, 65, 100, 50),  ("XXXXXXX",     0),    38),
    "Shellder":         (90,     "water",       1,3,97,         (30, 65, 100, 45, 25, 40),  ("Cloyster",    30),     14), #added
    "Cloyster":         (91,     "water",       1,3,203,        (50, 95, 180, 85, 45, 70),  ("XXXXXXX",     0),      30),
    "Gastly":           (92,     "ghost",       1,2,95,         (30, 35, 30, 100, 35, 80),  ("Haunter",     25),     18),
    "Haunter":          (93,     "ghost",       1,2,126,        (45, 50, 45, 115, 55, 95),  ("Gengar",     50),      25), #added
    "Gengar":           (94,     "ghost",       2,2,190,        (60, 65, 60, 130, 75, 110),  ("XXXXXXX",     0),     50),
    "Onix":             (95,     "rock",        2,1,108,        (35, 45, 160, 30, 45, 70),  ("XXXXXXX",     0),      20),
    "Drowzee":          (96,     "psychic",     1,1,102,        (60, 48, 45, 43, 90, 42),  ("Hypno",     26),        16),
    "Hypno":            (97,     "psychic",     1,1,165,        (85, 73, 70, 73, 115, 67),  ("XXXXXXX",     0),      26),
    "Krabby":           (98,     "water",       1,1,115,        (30, 105, 90, 25, 25, 50),  ("Kingler",     28),     12),
    "Kingler":          (99,     "water",       1,1,206,        (55, 10, 115, 50, 50, 75),  ("XXXXXXX",     0),      28),
    "Voltorb":          (100,     "electric",   1,1,103,        (40, 30, 50, 55, 55, 100),  ("Electrode",     30),   16),
    "Electrode":        (101,     "electric",   1,1,150,        (60, 50, 70, 80, 80, 150),  ("XXXXXXX",     0),      30),
    "Exeggcute":        (102,     "grass",      2,3,98,         (60, 40, 80, 60, 45, 40),  ("Exeggutor",     40),    22), #added
    "Exeggutor":        (103,     "grass",      2,3,212,        (95, 95, 85, 125, 75, 55),  ("XXXXXXX",     0),      40),
    "Cubone":           (104,     "ground",     1,1,87,         (50, 50, 95, 40, 50, 35),  ("Marowak",     28),      13),
    "Marowak":          (105,     "ground",     1,1,124,        (60, 80, 110, 50, 80, 45),  ("XXXXXXX",     0),      28),
    "Hitmonlee":        (106,     "fighting",   2,1,139,        (50, 120, 53, 35, 110, 87),  ("XXXXXXX",     0),     25),
    "Hitmonchan":       (107,     "fighting",   2,1,140,        (50, 105, 79, 35, 110, 76),  ("XXXXXXX",     0),     25),
    "Lickitung":         (108,     "normal",     2,1,127,        (90, 55, 75, 60, 75, 30),  ("XXXXXXX",     0),       20),
    "Koffing":          (109,     "poison",     1,1,114,        (40, 65, 95, 60, 45, 35),  ("Weezing",     35),      20),
    "Weezing":          (110,     "poison",     1,1,173,        (65, 90, 120, 85, 70, 60),  ("XXXXXXX",     0),      35),
    "Rhyhorn":          (111,     "rock",       1,3,135,        (80, 85, 95, 30, 30, 25),  ("Rhydon",     42),       23),
    "Rhydon":           (112,     "rock",       1,3,204,        (105, 130, 120, 45, 45, 40),  ("XXXXXXX",     0),    42),
    "Chansey":          (113,     "normal",     2,0,255,        (250, 5, 5, 35, 105, 50),  ("XXXXXXX",     0),       25),
    "Tangela":          (114,     "grass",      1,1,166,        (65, 55, 115, 100, 40, 60),  ("XXXXXXX",     0),     18),
    "Kangaskhan":       (115,     "normal",     2,1,175,        (105, 95, 80, 40, 80, 90),  ("XXXXXXX",     0),      28),
    "Horsea":           (116,     "water",      1,1,83,         (30, 40, 70, 70, 25, 60),  ("Seadra",     32),       22),
    "Seadra":           (117,     "water",      1,1,155,        (55, 65, 95, 95, 45, 85),  ("XXXXXXX",     0),       32),
    "Goldeen":          (118,     "water",      1,1,111,        (45, 67, 60, 35, 50, 63),  ("Seaking",     33),      15),
    "Seaking":          (119,     "water",      1,1,170,        (80, 92, 65, 65, 80, 68),  ("XXXXXXX",     0),       33),
    "Staryu":           (120,     "water",      1,3,106,        (30, 45, 55, 70, 55, 85),  ("Starmie",     30),      15), #added
    "Starmie":          (121,     "water",      1,3,207,        (60, 75, 85, 100, 85, 115),  ("XXXXXXX",     0),     30),
    "Mr_mime":          (122,     "psychic",    2,1,136,        (40, 45, 65, 100, 120, 90),  ("XXXXXXX",     0),     25),
    "Scyther":         (123,     "bug",         2,1,187,        (70, 110, 80, 55, 80, 105),  ("XXXXXXX",     0),     30),
    "Jynx":             (124,     "psychic",    2,1,137,        (65, 50, 35, 15, 95, 95),  ("XXXXXXX",     0),       30),
    "Electabuzz":        (125,     "electric",  2,1,156,        (65, 83, 57, 95, 85, 105),  ("XXXXXXX",     0),      30),
    "Magmar":           (126,     "fire",       2,1,167,        (65, 95, 57, 100, 85, 93),  ("XXXXXXX",     0),      30),
    "Pinsir":           (127,     "bug",        2,3,200,        (65, 125, 100, 55, 70, 85),  ("XXXXXXX",     0),     30),
    "Tauros":           (128,     "normal",     2,3,211,        (75, 100, 95, 40, 80, 110),  ("XXXXXXX",     0),     30),
    "Magikarp":         (129,     "water",      1,3,20,         (20, 10, 55, 15, 20, 80),  ("Gyarados",     20),     4),
    "Gyarados":         (130,     "water",      2,3,214,        (95, 125, 79, 60, 100, 81),  ("XXXXXXX",     0),     20),
    "Lapras":           (131,     "water",      2,3,219,        (130, 85, 80, 85, 95, 60),  ("XXXXXXX",     0),      30),
    "Ditto":            (132,     "normal",     2,1,61,         (48, 48, 48, 48, 48, 48),  ("XXXXXXX",     0),       20),
    "Eevee":            (133,     "normal",     2,1,92,         (55, 55, 50, 45, 65, 55),  ("Vaporeon",     30),     15), #added
    "Vaporeon":         (134,     "grass",      2,1,196,        (130, 65, 60, 110, 95, 65),  ("XXXXXXX",     0),     30),
    "Jolteon":          (135,     "electric",   2,1,197,        (65, 65, 60, 110, 95, 130),  ("XXXXXXX",     0),     30),
    "Flareon":          (136,     "fire",       2,1,198,        (65, 130, 60, 95, 110, 65),  ("XXXXXXX",     0),     30),
    "Porygon":          (137,     "normal",     2,1,130,        (65, 60, 70, 85, 75, 40),  ("XXXXXXX",     0),       25),
    "Omanyte":          (138,     "water",      2,1,120,        (35, 40, 100, 90, 55, 35),  ("Omastar",     40),     25),
    "Omastar":          (139,     "water",      2,1,199,        (70, 60, 125, 115, 70, 55),  ("XXXXXXX",     0),     40),
    "Kabuto":           (140,     "water",      2,1,119,        (30, 80, 90, 55, 45, 55),  ("Kabutops",     40),     25),
    "Kabutops":         (141,     "water",      2,1,201,        (60, 115, 105, 65, 70, 80),  ("XXXXXXX",     0),     40),
    "Aerodactyl":       (142,     "flying",     2,3,202,        (80, 105, 65, 60, 75, 130),  ("XXXXXXX",     0),     30),
    "Snorlax":          (143,     "normal",     2,3,154,        (160, 110, 65, 65, 110, 30),  ("XXXXXXX",     0),    30),
    "Articuno":         (144,     "flying",     3,3,215,        (90, 85, 100, 95, 125, 85),  ("XXXXXXX",     0),     30),
    "Zapdos":           (145,     "electric",   3,3,216,        (90, 90, 85, 125, 90, 100),  ("XXXXXXX",     0),     50),
    "Moltres":          (146,     "flying",     3,3,217,        (90, 100, 90, 125, 85, 90),  ("XXXXXXX",     0),     50),
    "Dratini":          (147,     "dragon",     2,3,67,         (41, 64, 45, 50, 50, 50),  ("Dragonair",     30),    20),
    "Dragonair":        (148,     "dragon",     2,3,144,        (61, 84, 65, 70, 70, 70),  ("Dragonite",     55),    30),
    "Dragonite":        (149,     "dragon",     2,3,218,        (91, 135, 95, 100, 100, 80),  ("XXXXXXX",     0),    55),
    "Mewtwo":           (150,     "psychic",    3,3,220,        (106, 110, 90, 154, 90, 130),  ("XXXXXXX",     0),   70),
    "Mew":              (151,     "psychic",    3,2,64,         (100, 100, 100, 100, 100, 100),  ("XXXXXXX",     0), 50),
    }
slow_medium_levels = [0] # original formula has a negative
    # which caused an integer underflow.  Just set it to 0.

for n in range(2, 101):
    exp = (6/5)*n**3 - 15 * n**2 + 100*n - 140
    slow_medium_levels.append(exp)

def get_level_from_exp_slow_medium(exp):
    L = 0
    for n in slow_medium_levels:
        if n > exp:
            return L
            break
        L += 1
    return L


tiers = {0: [], 1: [], 2: [], 3: []}
a = []
lowest_levels = {}
common = []
average = []
rare = []
legendary = []

for p in pokemon_dict.keys():
    lowest_levels[p] = 0

for p, k in pokemon_dict.items():
    evolution_data = k[6]
    lowest_level = k[7]
    if evolution_data[0] != "XXXXXXXX":
#        lowest_levels[evolution_data[0]] = evolution_data[1]
        lowest_levels[p] = lowest_level
    rarity = k[2]

    if rarity == 0:
        common.append(p)
    elif rarity == 1:
        average.append(p)
    elif rarity == 2:
        rare.append(p)
    else:
        legendary.append(p)
    stats = k[5]
    total = sum(stats)
    mean = int(total / 6)
    a.append((p, mean))
    if mean < 50:
        tiers[0].append(p)
    elif mean < 70:
        tiers[1].append(p)
    elif mean < 90:
        tiers[2].append(p)
    else:
        tiers[3].append(p)
        
#s = sorted(a, key=lambda x: x[1])

class Channel(object):
    def __init__(self, game, name, encounter_info):
        self.game = game
        encounter_type = encounter_info[0]
        self.encounter_type = encounter_type
        self.challenge = None
        if encounter_type == "time":
            self.min_time = encounter_info[1]
            self.max_time = encounter_info[2]
            self.get_next_encounter_time()
        elif encounter_type == "message":
            self.min_message = encounter_info[1]
            self.max_message = encounter_info[2]
            self.get_next_encounter_message()
        self.name = name
        self.current_privmsg = 0
        self.fainted_pokemon = None
        self.wild_pokemon = None
        #time for pokemon to leave
        self.wild_pokemon_time = 0
        self.active_players = set()
        self.ignore_players = False

    def is_encounter_time(self):
        if self.encounter_type == "time":
            if int(time.time()) >= self.next_wild_time:
                return True
            return False
        elif self.encounter_type == "message":
            if self.current_privmsg >= self.next_encounter_message:
                return True
            return False

    def get_next_encounter_message(self):
        self.next_encounter_message = random.randrange(self.min_message, self.max_message)

    def get_next_encounter_time(self):
        self.next_wild_time = int(time.time()) + random.randrange(self.min_time, self.max_time)

    def reset_next_wild(self):
        self.current_privmsg = 0
        if self.encounter_type == "time":
            self.get_next_encounter_time()
        else:
            self.get_next_encounter_message()
        self.active_players = set()

    def increment_privmsg(self, nick):
        player = self.game.get_player(nick) 
        if player:
            self.active_players.add(player)
        self.current_privmsg += 1
        
    def make_next_wild_pokemon(self):
        boxes = []
        players = self.active_players
        if self.ignore_players or not self.active_players:
            players = self.game.players
        for p in self.active_players:
            for pkmn in p.party:
                boxes.append(pkmn.level)
        if not boxes:
            boxes = [5]
        higher_pokemon = random.randrange(100)
        # randomly select one of the levels of the three highest pokemon and make a tougher pokemon than those
        #if higher_pokemon >= 95 and len(boxes) > 6: #TODO: fix
        if higher_pokemon >= 100 and len(boxes) > 6: #XXX disabling because paine was complaining, may re-enable with lure
            three_highest = list(reversed(sorted(boxes)))[:3]
            level = random.choice(three_highest) + random.randrange(5, 15)
        else:
            which_box = random.choice(boxes)
            level = which_box + random.randrange(-5, 5)
        level = max(2, level)
        level = min(100, level)
       # Rareness:
       # 0: 40% - Common Technically less rare but there are fewer in thsi category, making each species more common
       # 1: 50% - Average rareness
       # 2: 9% -  Rare
       # 3: 1% - Legendary
        while True:
            random_num = random.randrange(100)
            if random_num < 40:
                species = random.choice(common)
            elif random_num < 90:
                species = random.choice(average)
            elif random_num < 99:
                species = random.choice(rare)
            else:
                species = random.choice(legendary)
            # so we don't get level 2 charizards
            if lowest_levels[species] > level:
                continue
            # so we don't get level 100 charmanders
            evolution_level = pokemon_dict[species][6][1]
            if evolution_level != 0 and evolution_level <= level:
                continue
            else: break
        pokemon = Pokemon(species, level)
        return pokemon

    def __repr__(self):
        return self.name

class BadChanCommand(Exception):
    def __init__(self, channel, text):
        self.channel = channel
        self.text = text

class BadPrivMsgCommand(Exception):
    def __init__(self, nick, text):
        self.text = text
        self.nick = nick

class Player(object):
    def __init__(self, name):
        self.name = name
        self.party = []
        self.stored = []
        #TODO: store in database
        self.recently_swapped = queue.Queue(10)
        #TODO recreate player with potions and pokeballs
        self.potions = 5
        # TODO: set message preference in database
        self.message_preference = "privmsg"

    def get_queue_contents(self):
        removed = []
        while not self.recently_swapped.empty():
            retrieved = self.recently_swapped.get()
            removed.append(retrieved)
        for r in removed:
            self.recently_swapped.put(r)
        return removed

    def add_to_queue(self, pokemon):
        contents = self.get_queue_contents()
        # Don't want to put the same pokemon in twice.
        if pokemon in contents:
            return False
        if self.recently_swapped.full():
            self.recently_swapped().get()
        self.recently_swapped.put(pokemon)

    def show_queue(self):
        recent_swap_string = ""
        contents = self.get_queue_contents()
        for pkmn in contents:
            recent_swap_string += f" {pkmn.container_label}:{pkmn}"
        return recent_swap_string.strip()
#        removed = []
#        while not self.recently_swapped.empty():
#            retrieved = self.recently_swapped.get()
#            removed.append(retrieved)
#            recent_swap_string += f" {retrieved.container_label}:{retrieved}"
#        for r in removed:
#            self.recently_swapped.put(r)
        

        return recent_swap_string
    def increment_potions(self):
        self.potions += 1
        self.potions = min(5, self.potions)

    def get_container_label(self, pokemon):
        for e, p in enumerate(self.party):
            if p == pokemon:
                return "ABCDEF"[e]
        for e, p in enumerate(self.stored):
            if p == pokemon:
                return str(e)
        return None

    def add_pokemon(self, pokemon):
        if len(self.party) < 6:
            self.party.append(pokemon)
        else:
            self.stored.append(pokemon)

class Pokemon(object):
    def __init__(self, species, level):
        self.level = level
        self.name = species
        self.get_stats()
        # This is just random.  I'm not going to implement a faithful attack system.
        self.moves = [("attack", 40), ("attack", 80), ("special attack", 40), ("special attack", 80), ("lower defense")]
        self.captured = False
        self.exp = 0
        self.get_experience()
        self.ev = 0 #TODO: study how EVs work, might not bother though
        self.health_iv = random.randrange(32)
        self.attack_iv = random.randrange(32)
        self.defense_iv = random.randrange(32)
        self.sattack_iv = random.randrange(32)
        self.sdefense_iv = random.randrange(32)
        self.speed_iv = random.randrange(32)
        self.health_ev = 0
        self.attack_ev = 0
        self.defense_ev = 0
        self.sattack_ev = 0
        self.sdefense_ev = 0
        self.speed_ev = 0
        self.times_evolved = 0
        self.hp()
        self._hp = self.max_hp
        self.attack()
        self.defense()
        self.special_attack()
        self.special_defense()
        self.speed()
        self.defeated_by = None
        # 0: don't evolve 1: evolve as normal 2: jolteon 3: flareon 4: vaporeon
        self.evolve_setting = 1
        if self.name.capitalize() == "Eevee":
            self.evolve_setting = 0

    def get_stats(self):
        self.stats = pokemon_dict[self.name.capitalize()]
        self.pokemon_index = self.stats[0]
        self.type = self.stats[1]
        self.rarity = self.stats[2]
        self.growth_rate = self.stats[3]
        self.base_experience_value = self.stats[4]
        self.base_hp, self.base_att, self.base_def, self.base_satt, self.base_sdef, self.base_spd = self.stats[5]
        self.evolution, self.evolution_level  = self.stats[6]
        self.lowest_level = self.stats[7]

    def get_experience(self, level=None):
        if not level:
            level = self.level
            update = True
        else:
            update = False
        if self.growth_rate == 0:
            exp = (5 * level ** 3)/4
        elif self.growth_rate == 1:
            exp = (6/5)*level**3 - 15 * level**2 + 100 * level - 140
        elif self.growth_rate == 2:
            exp = level**3
        elif self.growth_rate == 3:
            exp = (4 * level**3)/5
        if update:
            self.exp = int(exp)
        return int(exp)

    def gain_ev(self, loser):
        # TODO: set max for these
        self.health_ev += loser.base_hp
        self.attack_ev += loser.base_att
        self.defense_ev += loser.base_def
        self.sattack_ev += loser.base_satt
        self.sdefense_ev += loser.base_sdef
        self.speed_ev += loser.base_spd
        
    def get_pokemon_identifier(self):
        """Creates a more interesting pokemon ID number than counting up from 0. Only useful for the player,
        not for the actual mechanics of the game."""
        return str(hash( str(self.index) ) %10000).zfill(4)

    def gain_experience(self, loser):
        a = 1.5 if self.captured else 1
        t = 1 # 1.5 if pokemon was traded
        b = 1 # base experience yield of fainted species-was this used generation 1?
        b = loser.base_experience_value
        e = 1 # lucky egg
        L = loser.level
        p = 1 # exp point power
        f = 1 # Affection
        v = 1 # only relevant for gen 6+
        s = 1 # number of pokemon who fought in battle (diff if expall)
        exp_change = int((a * t * b * e * L * p * f * v)/ (7 * s))
        self.exp += exp_change
        return exp_change

    def evolve(self):
        evolve_dict = {2: "Jolteon", 3: "Vaporeon", 4: "Flareon"}
        if self.evolve_setting in evolve_dict.keys():
            self.name = evolve_dict[self.evolve_setting]
        else:
            self.name = self.evolution
        self.get_stats()
        self._hp = self.max_hp
        self.times_evolved += 1

        
    def check_level(self, check_evolve=True):
        if self.growth_rate == 3: # fast
            level = round(((5*self.exp)/4)**(1/3))
        elif self.growth_rate == 2:
            level = round(self.exp**(1/3))
        elif self.growth_rate == 1:
            # I skipped "solving cubic function" day at school
            level = get_level_from_exp_slow_medium(self.exp)
        elif self.growth_rate == 0:
            n = ((4 * self.exp)/5) ** (1/3)
            level = round(n)
        if level == 0:
            level = 1
            self.level = 1
        if level != self.level:
            self.level = level
            self.hp()
            self.attack()
            self.defense()
            self.special_attack()
            self.special_defense()
            self.speed()
            if self.level >= self.evolution_level and self.evolution != "XXXXXXX" and self.evolve_setting != 0 and check_evolve:
                self.evolve()
            return level
        else:
            return False
    #TODO: handle evolution in SQL

    def hp_to_percent(self):
        return int(self._hp / self.max_hp * 100)

    def hp(self):
        self.max_hp = round((((self.base_hp + self.health_iv) * 2 + round(math.sqrt(self.health_ev)/4)) * self.level)/100) + self.level + 10

    def attack(self):
        self._attack = round((((self.base_att + self.attack_iv) * 2 + round(math.sqrt(self.attack_ev)/4)) * self.level)/100) + 5

    def defense(self):
        self._defense = round((((self.base_def + self.defense_iv) * 2 + round(math.sqrt(self.defense_ev)/4)) * self.level)/100) + 5

    def special_attack(self):
        self._sattack = round((((self.base_satt + self.sattack_iv) * 2 + round(math.sqrt(self.sattack_ev)/4)) * self.level)/100) + 5

    def special_defense(self):
        self._sdefense = round((((self.base_sdef + self.sdefense_iv) * 2 + round(math.sqrt(self.sdefense_ev)/4)) * self.level)/100) + 5

    def speed(self):
        self._speed = round((((self.base_spd + self.speed_iv) * 2 + round(math.sqrt(self.speed_ev)/4)) * self.level)/100) + 5

    def increase_health_five_percent(self):
        current_hp = self._hp
        five_percent = max(1, self.max_hp / 20)
        new_hp = current_hp + five_percent
        new_hp = min(self.max_hp, new_hp)
        self._hp = new_hp

    def __repr__(self):
        hp_percent = self.hp_to_percent()
        if hp_percent > 66:
            hp_color = ""
        elif hp_percent > 33:
            hp_color = "\x0308"
        else:
            hp_color = "\x0304"
#        color_dict = {"electric": "08", "fire": "04", "water": "02", "grass": "09", "ground": "05", "rock": "14", 
#            "flying": "11", "normal": "00", "psychic": "13", "ghost": "06", "dragon": "12", "ice": "10", "bug": "15", "fighting": "03", "poison": "07"}
        return f"\x03{type_color_dict[self.type]}{self.name}\x03-{hp_color}{self.level}\x03"


class ReconstructedPokemon(Pokemon):
    def __init__(self, index, species, trainer, container_label, exp, hp, health_iv, attack_iv, defense_iv, sattack_iv, sdefense_iv, speed_iv, health_ev, attack_ev, defense_ev, sattack_ev, sdefense_ev, speed_ev, times_evolved, evolve_setting):
        self.container_label = container_label
        self.index = index
        self.name = species
        self.player = trainer
        self.exp = exp
        self._hp = hp
        #XXX set SQL for evolve setting
        self.evolve_setting = evolve_setting
#        if self.name.capitalize() == "Eevee":
#            self.evolve_setting = 0
        self.health_iv = health_iv
        self.attack_iv = attack_iv
        self.defense_iv = defense_iv
        self.sattack_iv = sattack_iv
        self.sdefense_iv = sdefense_iv
        self.speed_iv = speed_iv
        self.health_ev = health_ev
        self.attack_ev = attack_ev
        self.defense_ev = defense_ev
        self.sattack_ev = sattack_ev
        self.sdefense_ev = sdefense_ev
        self.speed_ev = speed_ev
        self.times_evolved = times_evolved
        self.get_stats()
        self.captured = True
        # This is just random.  I'm not going to implement a faithful attack system.
        self.moves = [("attack", 40), ("attack", 80), ("special attack", 40), ("special attack", 80), ("lower defense")]
        self.level = 1
        self.check_level(check_evolve=False)
        self.get_experience()
        self.hp()
        self.attack()
        self.defense()
        self.special_attack()
        self.special_defense()
        self.speed()
        self.defeated_by = None

class Client(object):
    #TODO: QUIT messages, handling timeouts
    def __init__(self, socket, config):
        print("creating Client")
        self.socket = socket
        self.now = int(time.time())
        self.next_pokemon_appearance = None
        self.players = []
        self.channels = []
        self.parse_config(config)
        self.client_ready = False

        if not os.path.exists(self.db_file):
            self.create_database()
        self.create_database()
        self.players = self.sql_get_trainers()
        for p in self.players:
            self.reconstruct_pokemon(p)

    def parse_config(self, config):
        sections = config.sections()
        if len(sections) < 1:
            raise Exception("need more sections")
        main = sections[0]
        self.nick = config[main]["nick"]
        self.db_file = config[main]["db_file"]

        for name in sections[1:]:
            section = config[name]
            encounter_type = config[name]["encounter_type"]
            if encounter_type == "time":
                min_time = int(config[name].get("min_time"))
                max_time = int(config[name].get("max_time"))
                channel = Channel(self, name, (encounter_type, min_time, max_time))
                self.channels.append(channel)

            elif encounter_type == "message":
                minimum = int(config[name].get("min_msg"))
                maximum = int(config[name].get("max_msg"))
                channel = Channel(self, name, (encounter_type, minimum, maximum))
                self.channels.append(channel)

            else:
                raise Exception("encounter_type not set to 'time' or 'message'")
        
    def reconstruct_pokemon(self, player):
        self.cur.execute("""SELECT * FROM pokemon WHERE trainer = ?""", (player.index,))
        results = self.cur.fetchall()
        all_pokemon = []
        for r in results:
            pokemon = ReconstructedPokemon(*r)
            all_pokemon.append(pokemon)
        sorted_pokemon = sorted(all_pokemon, key= lambda x: x.container_label)
        party_pokemon = filter(lambda x: x.container_label.upper() in "ABCDEF", sorted_pokemon)
        pc_pokemon = filter(lambda x: x.container_label.isdigit(), sorted_pokemon)
        for p in party_pokemon:
            player.party.append(p)
        for p in pc_pokemon:
            player.stored.append(p)

    def connect(self):
        self.send(f"USER {self.nick} sean sean sean")
        self.send(f"NICK {self.nick}")

    def join(self, channel):
        message = f"JOIN {channel}"
        print(message)
        self.send(message)
    
    def send(self, message):
        message += "\r\n"
        to_send_back = bytes(message.encode("utf-8")) 
        print(to_send_back)
        self.socket.send(to_send_back)

    def send_to(self, recipient, message):
        IRC_cmd = "PRIVMSG"
        if type(recipient) is str:
            possible_player = self.get_player(recipient)
            if possible_player:
                recipient = possible_player
                
        if type(recipient) is Player:
            if recipient.message_preference == "notice":
                IRC_cmd = "NOTICE"
            recipient = recipient.name
        length = len(message)
        num_messages = int(math.ceil(length/400))
        for n in range(num_messages):
            submessage = message[n*400:(n+1)*400] # max length IRC is 512 cf. rfc1459
            self.send(f"{IRC_cmd} {recipient} :{submessage}")

    def handle_ping(self, data):
        self.send(f"PONG {data[1]}")

    @property
    def player_list(self):
        return [p.name for p in self.players]

    def handle_privmsg(self, data):
        nick = data[0].partition("!")[0]
        recipient = data[2]
        channel = None
        for c in self.channels:
            if recipient == c.name:
                channel = c
                break

        if channel:
            channel.increment_privmsg(nick)
        message = " ".join(data[3:])
        message = message.lstrip(":").lower()

        split = message.split()
        player_cmd = split[0]

        if player_cmd == "#starter":
            self.parse_starter(nick, split)
        if player_cmd == "#go" and channel:
            self.parse_go(channel, nick, split)
        elif player_cmd == "#debugheal" and test: #XXX
            self.parse_debugheal(nick)
        elif player_cmd == "#heal":
            self.parse_heal(nick, split)
        elif player_cmd == "#team":
            self.parse_team(nick, channel, split)
        elif player_cmd == "#examine":
            self.parse_examine(nick, split)
        elif player_cmd == "#pc":
            self.parse_pc(nick, split)
        elif player_cmd == "#swap":
            self.parse_swap(nick, split)
        elif player_cmd == "#repel" and channel:
            self.parse_repel(channel.name, nick)
        elif player_cmd == "#commands":
            self.parse_commands(nick)
        elif player_cmd == "#release":
            self.parse_release(nick, split)
        elif player_cmd == "#catch" and channel:
            self.parse_catch(channel, nick)
        elif player_cmd == "#test":
            self.parse_test(nick)
        elif player_cmd == "#pokecount":
            self.parse_pokecount(nick)
        elif player_cmd == "#pokedex":
            self.parse_pokedex(nick, split)
        elif player_cmd == "#challenge":
            self.parse_challenge(channel, nick, split)
        elif player_cmd == "#challenge-accept":
            self.parse_challenge_accept(channel, nick, split)
        elif player_cmd == "#challenge-decline":
            self.parse_challenge_decline(channel, nick)
        elif player_cmd == "#pokefind":
            self.parse_pokefind(nick, split)
        elif player_cmd == "#set-evolve":
            self.parse_set_evolve(nick, split)

    def parse_set_evolve(self, nick, command):
        eeveelutions = ["Jolteon", "Vaporeon", "Flareon"]
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        if len(command) < 3:
           raise BadPrivMsgCommand(nick, f"Syntax: #set-evolve <pokemon_label> <setting>. Setting can be Off, On, or if Eevee: Jolteon, Vaporeon, Flareon")
        _, _, pokemon = self.get_pokemon(command[1], player)
        #return index, which_container, pokemon
        setting = command[2]
        if setting.lower() in ["off", "false", "no"]:
            pokemon.evolve_setting = 0
        elif setting.lower() in ["on", "true", "yes"]:
            if pokemon.name.capitalize() == "Eevee":
                raise BadPrivMsgCommand(nick, "#set-evolve: the only valid settings for Eevee are Off, 'Jolteon', 'Vaporeon', and 'Flareon'")
            pokemon.evolve_setting = 1
        elif setting.capitalize() in eeveelutions:
            print("is in eeveelutions")
            if pokemon.name.capitalize() == "Eevee":
                print("is eevee")
                pokemon.evolve_setting = eeveelutions.index(setting.capitalize()) + 2
                print(pokemon.evolve_setting)
            else:
                print("is not eevee")
                raise BadPrivMsgCommand(nick, "#set-evolve: You can only set 'Jolteon', 'Vaporeon' and 'Flareon' for Eevee.")
        
        
        #self.evolve_setting = 1
        self.sql_change_evolve_setting(pokemon.index, pokemon.evolve_setting)

        
    #def get_pokemon(self, which_pokemon, player, has_to_be="Neither"):
            
    def sql_change_evolve_setting(self, pokemon_index, setting):
        self.cur.execute("""UPDATE pokemon SET evolve_setting = ? WHERE pokemon_id =?""", (setting, pokemon_index))
        self.con.commit()
        
        #self.cur.execute("""UPDATE pokemon SET container_label = ? WHERE pokemon_id = ?""", (container_label, pokemon_id))
    def parse_pokefind(self, nick, command):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        if len(command) < 2:
            raise BadPrivMsgCommand(nick, f"Syntax: #pokefind <species name>")
        search_term = command[1].capitalize()
        if search_term not in pokemon_dict.keys():
            raise BadPrivMsgCommand(nick, f"There is no pokemon species with the name '{search_term}'")
        party_string = ""
        for pokemon in player.party:
            if pokemon.name.capitalize() == search_term:
                party_string += f" {pokemon.container_label}:{pokemon}#{pokemon.get_pokemon_identifier()}"
        team_string = ""
        for pokemon in player.stored:
            if pokemon.name.capitalize() == search_term:
                party_string += f" {pokemon.container_label}:{pokemon}#{pokemon.get_pokemon_identifier()}"
        both = f"{party_string} {team_string}".strip()
        if not both:
            self.send_to(player, f"Sorry, you don't have any {search_term}")
        else:
            self.send_to(player, both)

            
            
            

    def parse_challenge_accept(self, channel, nick, split):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player2 = self.get_player(nick)
        if not channel.challenge or player2 != channel.challenge["challenged"]:
            raise BadPrivMsgCommand(nick, f"You weren't challenged to a trainer battle in {channel.name}!")
        if channel.challenge["phase"] != "prebattle":
            raise BadPrivMsgCommand(nick, "The challenge has already been accepted!")
        challenged_party = self.get_challenge_party(player2, split)
        #challenge_party = player2.party #TODO: select a subset
        average = int(sum([p.level for p in challenged_party])/len(challenged_party))

        channel.challenge["challenged_party"] = challenged_party
        channel.challenge["phase"] = "first_turn"
        channel.challenge["timeout"] = int(time.time()) + 60
        player1 = channel.challenge["challenger"]
        print(challenged_party)
        self.send_to(channel.name, f"{BLUE}{nick}{CLEAR} has accepted the challenge with a team of {GREEN}{len(challenged_party)}{CLEAR} (average level: {GREEN}{average}{CLEAR}). {RED}{player1.name}{CLEAR} has {GREEN}60{CLEAR} seconds to send out the first pokemon with {GRAY}#go{CLEAR}.")

    def parse_challenge_decline(self, channel, nick):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player2 = self.get_player(nick)
        challenger = channel.challenge["challenger"]
        challenged = channel.challenge["challenged"]
        
        if not channel.challenge or player2 not in [challenger, challenged]:
            raise BadPrivMsgCommand(nick, f"You weren't challenged to a trainer battle in {channel.name}!")

        if channel.challenge["phase"] != "prebattle" and player2 == challenged:
            raise BadPrivMsgCommand(nick, "The challenge has already been accepted!")
        if channel.challenge["phase"] == "first_turn" and player2 == challenger:
            message = f"{RED}{challenger.name}{CLEAR} has rejected {BLUE}{challenged.name}{CLEAR}'s counter-challenge."
        else: 
            message = f"{BLUE}{nick}{CLEAR} has rejected {RED}{challenger.name}{CLEAR}'s challenge." 
    
        self.send_to(channel.name, message)
        #self.send_to(channel.name, f"{BLUE}{nick}{CLEAR} has rejected {RED}{channel.challenge['challenger'].name}{CLEAR}'s challenge.") 
        channel.challenge = None
        
    def get_challenge_party(self, player, split):
        challenge_party = set()
        if len(split) > 2:
            for arg in split[2:]:
                _, _, pokemon = self.get_pokemon(arg, player, "party")
                if pokemon._hp > 0:
                    challenge_party.add(pokemon)
                    print(f"{pokemon} added")
        if not challenge_party:
            challenge_party = player.party
        return challenge_party

    def parse_challenge(self, channel, nick, split):
        if len(split) < 2:
            raise BadPrivMsgCommand(nick, "Syntax: #challenge <player>")
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        nick2 = split[1]
        if nick2 not in self.player_list:
            raise BadChanCommand(channel.name, f"{nick2} is not a valid player")
        if channel.challenge:
            raise BadChanCommand(channel.name, f"There is already a battle challenge in this channel")
        player2 = self.get_player(nick2)
        if player == player2:
            raise BadChanCommand(channel.name, f"You can't challenge yourself!")
        challenger_party = self.get_challenge_party(player, split)
        
        print(challenger_party)
        #first_idx, first_container, first_pokemon = self.get_pokemon(first_pokemon, player, first_has_to_be)

        timeout = 180
        channel.challenge = {"challenger": player, "challenged": player2, "pokemon1": None, "pokemon2": None, "timeout": int(time.time()) + timeout, "phase": "prebattle", "challenger_party": challenger_party}
        #challenge_party = player.party #TODO: select a subset
        average = int(sum([p.level for p in challenger_party])/len(challenger_party))
        self.send_to(channel.name, f"{RED}{nick}{CLEAR} challenges {BLUE}{nick2}{CLEAR} to a battle with a team of {GREEN}{len(challenger_party)}{CLEAR} (average level: {GREEN}{average}{GREEN}{CLEAR}). {BLUE}{nick2}{CLEAR} has {GREEN}{timeout}{CLEAR} seconds to {GRAY}#challenge-accept{CLEAR} or {GRAY}#challenge-decline{CLEAR}.")

        
    
    def parse_pokedex(self, nick, command):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        if not len(command) >= 2:
            raise BadPrivMsgCommand(nick, f"Syntax: #pokedex <pokemon_species>")
        which_pokemon = command[1].lower().capitalize()
        pokemon_values = pokemon_dict.get(which_pokemon)
        if not pokemon_values:
            raise BadPrivMsgCommand(nick, f"Non existent pokemon: {which_pokemon}")
        idx, pkmn_type, rarity, growth, base_exp, stats, evolution, min_level = pokemon_values
        hp, att, _def, satt, sdef, spd = stats
        o = "\x0307" # orange
        g = "\x0309" # light green
        c = "\x0311" # cyan
        n = "\x0300"
        type_color = "\x03" + f"{type_color_dict[pkmn_type]}"
        growth_rate_text = {0: "fast", 1: "medium-fast", 2: "medium-slow", 3: "slow"}[growth]
        rarity_text = {0: "common", 1: "average", 2: "rare", 3: "legendary"}[rarity]
        string =  f"#{idx}: {type_color}{which_pokemon}[{pkmn_type}] {g}Rarity{n}:{rarity_text} {g}lowest_level:{min_level} "
        string += f"{c}growth_rate{n}:{growth_rate_text} {o}base_exp{n}:{base_exp} {o}base_hp{n}:{hp} {o}base_att{n}:{att} "
        string += f"{o}base_def{n}:{_def} {o}base_spec_att{n}:{satt} {o}base_spec_def{n}:{sdef} {o}base_speed{n}:{spd} "
        if evolution[0] != "XXXXXXX":
            string += f". Evolves into {evolution[0]} at level {evolution[1]}."
        self.send_to(nick, string)

    def count_pokemon(self, player):
        
        self.cur.execute("SELECT * FROM pokemon WHERE trainer = ?", (player.index,))
        results = self.cur.fetchall()
        print(results)
        ever_owned = set()
        for i in results:
            name = i[1].lower().capitalize()
            times_evolved = i[18]
            prevs = []
            known_about = [name]
            while times_evolved > 0:
                for k in list(reversed(pokemon_dict.keys())):
                    possible_preevolve = k
                    data = pokemon_dict[k]
                    evolution = data[6]
                    if evolution[0].lower().capitalize() in known_about:
                        known_about.append(possible_preevolve.lower().capitalize())
                        
                        prevs.append(possible_preevolve)
                        ever_owned.add(possible_preevolve)
                        times_evolved -= 1

            ever_owned.add(name)
        amount = len(ever_owned)
        return ever_owned
    def parse_pokecount(self, nick):
        abbreviations =  "BLB IVY VNS CHM CHE CHZ SQU WAR BLA CAT MPD BFR WDL KAK BDR " 
        abbreviations += "PGY PGO PGT RTA RTC SPW FRW EKS ARB PIK RAI SRW SSL NDM NDO "
        abbreviations += "NDK NDF NDA NDQ CLF CFB VPX NTS JPF WTF ZUB GOL ODD GLM VLP "
        abbreviations += "PRS PST VNT VMT DLT DTR MTH PRS PSD GLD MKY PRI GRW ARC PWG "
        abbreviations += "PWL PWT ABR KDB ALA MCH MCK MCP BSP WPB VTB TCL TCR GEO GRV "
        abbreviations += "GLM PNY RPD SLP SLB MGN MGT FFD DDU DDR SEL DWG GRM MUK SHL "
        abbreviations += "CLY GAS HNT GEN ONX DRZ HYP KRB KNG VLT ELE EXC EXT CUB MWK "
        abbreviations += "HML HMC LIK KOF WEZ RHH RHD CHS TNG KGK HRS SEA GLD SKG SYU "
        abbreviations += "SME MIM SCY JYX EBZ MAG PNS TRS MKP GRD LAP DIT EVE VPR JLT "
        abbreviations += "FLR PRG OMY OMS KAB KAT AER SLX ART ZAP MOL DTI DNR DNT MWT MEW"
        abbreviations = abbreviations.split()

        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        
        ever_owned = self.count_pokemon(player)
        count_string = f"You have caught {len(ever_owned)}/151 pokemon! "
        for e, pokemon_name in enumerate(pokemon_dict.keys()):
            this_abbreviation = abbreviations[e]
            if pokemon_name.lower().capitalize() not in ever_owned:
                this_abbreviation = this_abbreviation.lower()
            else:
                this_abbreviation = f"\x0310{this_abbreviation}\x03"
            count_string += this_abbreviation + " "
        self.send_to(nick, count_string)
                
    def parse_catch(self, channel, nick):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        if channel.fainted_pokemon:
            if channel.fainted_pokemon.defeated_by != player:
                raise BadPrivMsgCommand(nick, f"{nick}: Only the player who defeated {channel.fainted_pokemon} may catch it! ")
            else:
                player.add_pokemon(channel.fainted_pokemon)
                channel.fainted_pokemon.captured = True
                container_label = player.get_container_label(channel.fainted_pokemon)
                channel.fainted_pokemon.container_label = container_label
                before = len(self.count_pokemon(player))
                pokemon_id = self.sql_add_pokemon(channel.fainted_pokemon, player)
                channel.fainted_pokemon.index = pokemon_id
                self.sql_update_pokemon(channel.fainted_pokemon)
                after = len(self.count_pokemon(player))
                message = f"{nick} caught the {channel.fainted_pokemon}."
                print("before, after")
                print(before, after)
                if before != after:
                    print(before, after)

                    message += f" {nick} has caught {after}/151 pokemon!"
                self.send_to(channel.name, message)
#                self.send_to(channel.name, f"{nick} caught the {channel.fainted_pokemon}. {nick} now caught {self.count_pokemon(player)} pokemon!")
                channel.fainted_pokemon = None
        else:
            raise BadPrivMsgCommand(nick, f"{nick}: There is no pokemon to catch.  Are you confused?")

    def parse_release(self, nick, command):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        self.check_if_in_trainer_battle(player)
        if len(command) != 3:
            raise BadPrivMsgCommand(nick, f"{nick}: Syntax: #release <location_id> <pokemon_name> .  e.g. '#release D pidgey' if in party or '#release 5 rattata' if in PC")
        location_id = command[1]
        pokemon_name = command[2]
        if not location_id.isdigit() and not location_id.lower() in "abcdef":
            raise BadPrivMsgCommand(nick, f"{nick}: Syntax: #release <location_id> <pokemon_name> .  e.g. '#release D pidgey' if in party or '#release 5 rattata' if in PC")

        if location_id.isdigit():
            index = int(location_id)
            container = player.stored
        elif location_id.lower() in "abcdef":
            index = "abcdef".index(location_id.lower())
            container = player.party
        else:
            raise BadPrivMsgCommand(nick, f"{nick}: Syntax: #release <location_id> <pokemon_name> .  e.g. '#release D pidgey' if in party or '#release 5 rattata' if in PC")
        try:
            idx, _, pokemon = self.get_pokemon(location_id, player, has_to_be = "party" if container == player.party else "PC")
        except IndexError:
            raise BadPrivMsgCommand(nick, f"{nick}: You have no pokemon under the location ID of {location_id}. Please check #team and #PC")
        if pokemon.name.lower() != pokemon_name.lower():
            raise BadPrivMsgCommand(nick, f"{nick}: There is no pokemon of the name {pokemon_name} under the location ID of {location_id}. Please check #team and #PC")
        else:
            if len(container) == 1 and container == player.party:
                raise BadPrivMsgCommand(nick, f"You can not release the only pokemon in your party.")
            self.send_to(nick, f"{nick} released {pokemon} into the wilderness.  Good luck, {pokemon}!")
            self.sql_change_container_label(pokemon.index, "X") # "X" means released into the wild
            container.remove(pokemon)
            del pokemon
            
         

    def parse_repel(self, channel, nick):
        self.repelling = True
        self.send_to(channel, f"{nick} set a repel.  Pokemon won't appear for another half hour.")

    def parse_commands(self, nick):
        self.send_to(nick, "#starter #go #examine #team #pc #swap #repel #release #catch #commands #pokecount #pokedex #challenge #challenge-accept #challenge-decline #pokefind #set-evolve") #TODO: pokedex

    def parse_test(self, nick):
        raise BadPrivMsgCommand(nick, "This is a test")

    def find_which_pokemon(self, label, container):
        pokemon = None
        label = label.lower()
        if label.isdigit():
            which_pokemon = int(label)
            if 0 <= which_pokemon < len(container):
                pokemon = container[which_pokemon]
        else:
            for p in container:
                if p.name.lower() == label:
                    pokemon = p
        return pokemon

    def check_if_in_trainer_battle(self, player):

        for c in self.channels:
            if c.challenge:
                if player in (c.challenge["challenger"], c.challenge["challenged"]) and c.challenge["phase"] != "prebattle":
                    raise BadPrivMsgCommand(player.name, f"You can not swap pokemon while in a trainer battle!")

    def sql_change_container_label(self, pokemon_id, container_label):
        self.cur.execute("""UPDATE pokemon SET container_label = ? WHERE pokemon_id = ?""", (container_label, pokemon_id))
        self.con.commit()

    def parse_swap(self, nick, command):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        self.check_if_in_trainer_battle(player)
        if len(command) != 3:
            raise BadPrivMsgCommand(nick, f"{nick}: Syntax: #swap <party_pokemon> <PC_pokemon>")
        first_pokemon = command[1].lower()
        second_pokemon = command[2].lower()
        first_has_to_be = "Neither"
        second_has_to_be = "Neither"
        if not first_pokemon.isdigit() and not first_pokemon.lower() in "abcdef":
            first_has_to_be = "party"
        if not second_pokemon.isdigit() and not second_pokemon.lower() in "abcdef":
            second_has_to_be = "PC"
        first_idx, first_container, first_pokemon = self.get_pokemon(first_pokemon, player, first_has_to_be)
        second_idx, second_container, second_pokemon = self.get_pokemon(second_pokemon, player, second_has_to_be)
        first_container[first_idx] = second_pokemon
        second_container[second_idx] = first_pokemon
        message = f"{nick} swapped {first_pokemon} with {second_pokemon}"
        container_label_1 = player.get_container_label(first_pokemon)
        container_label_2 = player.get_container_label(second_pokemon)
        first_pokemon.container_label = container_label_1
        second_pokemon.container_label = container_label_2
        
        self.sql_change_container_label(first_pokemon.index, container_label_1)
        self.sql_change_container_label(second_pokemon.index, container_label_2)
        if first_container != second_container:
        #    if first_container == player.stored:
                player.add_to_queue(second_pokemon)
        #    else:
                player.add_to_queue(first_pokemon)
        self.send_to(nick, message)

    def parse_pc(self, nick, command):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        amount_to_show = 20
        player = self.get_player(nick)
        message = ""
        if len(command) == 2 and command[1].isdigit():
            beginning = max(0, min(len(player.stored)-amount_to_show, int(command[1])))
        else:
            beginning = max(0, len(player.stored)-amount_to_show)
        print(beginning)
        for i in range(beginning, min(beginning+amount_to_show, len(player.stored))):
            print(i)
#            if i >= len(player.stored)-1:
#                break
            message += f"{i}:{player.stored[i]} "
            print(message)
#        for num, pokemon in enumerate(player.stored):
#            message += f"{num}:{pokemon} "
    
        recently_swapped_string = player.show_queue()
        self.send_to(nick, message)
        if recently_swapped_string:
            self.send_to(nick, f"Recently swapped: {recently_swapped_string}")

    def parse_examine(self, nick, command):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        if len(command) < 2:
            raise BadPrivMsgCommand(nick, f"{nick}: Syntax: #examine <pokemon>")
        player = self.get_player(nick)
        index, container, pkmn = self.get_pokemon(command[1].lower(), player)
        ID = pkmn.get_pokemon_identifier()
        exp_to_next_level = pkmn.get_experience(pkmn.level+1) - pkmn.exp
        ev_setting_dict = {0: "No", 1: "Yes", 2: "into Jolteon", 3: "into Vaporeon", 4: "into Flareon"}
        will_evolve = ev_setting_dict[pkmn.evolve_setting]
        print(pkmn.evolve_setting)
        print(will_evolve)
        if will_evolve != "No" and not pkmn.evolution != "XXXXXXX":
            will_evolve = "No"
        if pkmn.level == 100:
            exp_to_next_level = "N/A"

        growth_dict = {0: "slow", 1: "medium-slow", 2: "medium-fast", 3: "fast"}
        message = f"{pkmn.name} \x0300ID\x03:{ID} \x0300Lvl\x03:{pkmn.level} \x0300EXP\x03:{pkmn.exp} \x0300HP\x03:{pkmn._hp} \x0300MaxHP\x03:{pkmn.max_hp} \x0300Health\x03:{int(pkmn._hp/pkmn.max_hp*100)}% "
        message += f"\x0304Att\x03:{pkmn._attack} \x0304Def\x03:{pkmn._defense} \x0304SAtt\x03:{pkmn._sattack} \x0304SDef\x03:{pkmn._sdefense} \x0304Spd\x03:{pkmn._speed} "
        message += f"\x0302h_iv\x03:{pkmn.health_iv} \x0302a_iv\x03:{pkmn.attack_iv} \x0302d_iv\x03:{pkmn.defense_iv} \x0302sa_iv\x03:{pkmn.sattack_iv} \x0302sd_iv\x03:{pkmn.sdefense_iv} \x0302spd_iv\x03:{pkmn.speed_iv} "
        message += f"\x0303h_ev\x03:{pkmn.health_ev} \x0303a_ev\x03:{pkmn.attack_ev} \x0303d_ev\x03:{pkmn.defense_ev} \x0303sa_ev\x03:{pkmn.sattack_ev} \x0303sd_ev\x03:{pkmn.sdefense_ev} \x0303spd_ev\x03:{pkmn.speed_ev} "
        message += f"\x0308GrowthRate\x03:{growth_dict[pkmn.growth_rate]} \x0308ExpToNextLevel\x03:{exp_to_next_level}\x03 \x0308Will_evolve\x03:{will_evolve}"
        self.send_to(nick, message)

    def heal_pokemon(self, pokemon):
        pokemon._hp = pokemon.max_hp
        self.sql_update_health(pokemon)

    def parse_heal(self, nick, command):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        if len(command) < 2:
            raise BadPrivMsgCommand(nick, f"Syntax: #heal <pokemon_label>")
        player = self.get_player(nick)
        index, container, pokemon = self.get_pokemon(command[1].lower(), player, has_to_be="party")
        
        if player.potions > 0:
            self.heal_pokemon(pokemon)
            player.potions -= 1
            self.send_to(nick, f"You've healed {pokemon} to full health!  You now have {player.potions} potion(s).")
        else:
            raise BadPrivMsgCommand(nick, "You do not have any potions left!")


            
        
    def parse_debugheal(self, nick):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        for pokemon in player.party:
            pokemon._hp = pokemon.max_hp
            self.sql_update_health(pokemon)
        self.send_to(nick, "You've healed all the pokemon in your party")

    def parse_team(self, nick, channel, split):
        if nick not in self.player_list:
            raise BadPrivMsgCommand(nick, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")

        player = self.get_player(nick)
        if len(split) >= 2 and  split[1].lower() == "show" and channel:
            dest = channel.name
        else:
            dest = nick

        letters = "ABCDEF"
        self.send_to(dest, f"{nick}'s team: {', '.join([f'{letters[L]}:{p}|{int(p._hp/p.max_hp*100)}%' for L, p in enumerate(player.party)])}")

    def battle(self, poke1, poke2):
        # randomness in case they have the same speed
        fighters = [poke1, poke2]
        random.shuffle(fighters)
        sorted_fighters = sorted(fighters, key=lambda x: x._speed)
        sorted_fighters = list(reversed(sorted_fighters))
        i = 0
        loser = None
        while True:
            for poke in (poke1, poke2):
                if poke._hp <= 0:
                    loser = poke
                    break
            if loser:
                break
            attacker = sorted_fighters[i%2]
            defender = sorted_fighters[(i+1)%2]
            move = random.choice(attacker.moves[:4])
            self.do_damage(attacker, defender, move)
            i += 1
        return loser


    def do_damage(self, attacker, defender, move):
        type_effectiveness = 1
        double, half, none = type_dict[attacker.type]
        if defender.type in double:
            type_effectiveness = 2
        elif defender.type in half:
            type_effectiveness = 0.5
        elif defender.type in none:
            type_effectiveness = 0
        move_type, power = move
        stab = 1 # the "same type attack bonus"
        if attacker.type == defender.type:
            stab = 1.5
        if move_type == "attack":
            attack = attacker._attack
            defense = defender._defense
        else:
            attack = attacker._sattack
            defense = defender._sdefense
        random_multiplier = random.randrange(85, 100) / 100
        damage = int(((((2 * attacker.level) / 5 + 2) * power * (attack/defense))/50 + 2) * random_multiplier * stab * type_effectiveness)
        damage = max(1, damage)
        defender._hp -= damage
        defender._hp = max(defender._hp, 0)

    def get_player(self, nick):
        for p in self.players:
            if nick.lower() == p.name.lower():
                player = p
                return player
        return False

    def get_pokemon(self, which_pokemon, player, has_to_be="Neither"):
        pokemon = None
        nick = player.name
        if which_pokemon.upper() in "ABCDEF":
            if has_to_be == "PC":
                raise BadPrivMsgCommand(nick, f"PC pokemon are referred to by numerical numbers [0-...]")
            elif has_to_be in ("party_no_label", "challenge_team_no_label"):
                raise BadPrivMsgCommand(nick, f"Can't refer to pokemon by label. Use full name instead.")
            which_pokemon = "ABCDEF".index(which_pokemon.upper())
            which_container = player.party
            try:
                pokemon = which_container[which_pokemon]
            except:
                raise BadPrivMsgCommand(nick, f"You do not have that many pokemon in your PC")
            index = which_pokemon

        
        elif which_pokemon.isdigit():
            if has_to_be == "party":
                raise BadPrivMsgCommand(nick, f"Party pokemon are referred to by letters [A-Z]")
            if has_to_be in  ("party_no_label", "challenge_team_no_label"):
                raise BadPrivMsgCommand(nick, f"Can't refer to pokemon by label.  Use full name instead.")
            which_container = player.stored
            which_pokemon = int(which_pokemon)
            try:
                pokemon = which_container[which_pokemon]
            except:
                raise BadPrivMsgCommand(nick, f"You do not have that many pokemon in your PC")
            index = which_pokemon
        else:
            if has_to_be == "PC":
                which_container = player.stored
            # the subset of a team for a trainer battle
            elif has_to_be == "challenge_team_no_label":
                for c in self.channels:
                    challenge = c.challenge
                    if not challenge:
                        raise BadPrivMsgCommand("ctnl: This text shouldn't show.  Tell sean if it does.")
                    challenger, challenged = challenge["challenger"], challenge["challenged"]
                    if nick == challenger.name:
                        which_container = challenge["challenger_party"]
                    elif nick == challenged.name:
                        which_container = challenge["challenged_party"]


            else:
                which_container = player.party
            index = 0
            for poke in which_container:
                if which_pokemon.lower() == poke.name.lower():
                    pokemon = poke
                    break
                index += 1
        if not pokemon:
            raise BadPrivMsgCommand(player.name, f"That is not a valid pokemon")
        return index, which_container, pokemon

    def sql_evolve(self, pokemon):
        self.cur.execute("""UPDATE pokemon SET species = ?, hp = ?, times_evolved = ? WHERE pokemon_id = ?""", (pokemon.name.capitalize(), pokemon._hp, pokemon.times_evolved, pokemon.index))
        self.con.commit()

    def parse_go(self, channel, nick, command):
        if nick not in self.player_list:
            raise BadChanCommand(channel.name, f"{nick}: You have to choose a starter pokemon first with the command #starter <pokemon>")
        player = self.get_player(nick)
        if channel.challenge:
            contestants = (channel.challenge["challenger"], channel.challenge["challenged"])
        if not channel.challenge or player not in contestants:
            if not channel.wild_pokemon:
                raise BadChanCommand(channel.name, "There is no pokemon there!")

        if len(command) < 2:
            raise BadChanCommand(channel.name, f"Syntax: #go <pokemon>")
        which_pokemon = command[1].lower()
        index, container, pokemon = self.get_pokemon(which_pokemon, player, has_to_be="party_no_label")
        if pokemon._hp <= 0:
            raise BadChanCommand(channel.name, f"{pokemon} has fainted and can't fight!")

        if channel.challenge and player in contestants:
            index, container, pokemon = self.get_pokemon(which_pokemon, player, has_to_be="challenge_team_no_label")
            if contestants.index(player) == 0:
                channel.challenge["pokemon1"] = pokemon
                if channel.challenge["phase"] == "first_turn":
                    channel.challenge["phase"] = "battle"
                    channel.challenge["timeout"] = int(time.time()) + 40
            else:
                channel.challenge["pokemon2"] = pokemon
            if all((channel.challenge["pokemon1"], channel.challenge["pokemon2"])):
                pokemon1 = channel.challenge["pokemon1"]
                pokemon2 = channel.challenge["pokemon2"]
                loser = self.battle(pokemon1, pokemon2)
                if loser == pokemon1:
                    losing_trainer = channel.challenge["challenger"]
                    winning_trainer = channel.challenge["challenged"]
                    channel.challenge["pokemon1"] = None
                else:
                    losing_trainer = channel.challenge["challenged"]
                    winning_trainer = channel.challenge["challenger"]
                    channel.challenge["pokemon2"] = None

                message = self.post_battle(channel, pokemon1, pokemon2, "challenge", winning_trainer)
                if not any([p._hp for p in losing_trainer.party]):
                    message += f"{losing_trainer.name} has no more usable pokemon!  They have lost the battle. Congratulations {winning_trainer.name}!"
                    channel.challenge = None
                    
                self.send_to(channel.name, message)
            else:
                self.send_to(channel.name, f"waiting for other player")
            if channel.challenge:
                channel.challenge["timeout"] = int(time.time()) + 40
            return
            
        loser = self.battle(pokemon, channel.wild_pokemon)
        if loser != pokemon:
            message = self.post_battle(channel, pokemon, channel.wild_pokemon, "wild", player)
        else:
            message = f"{nick}'s {pokemon} lost the battle! {channel.wild_pokemon}'s health: {channel.wild_pokemon.hp_to_percent()}%"
        self.send_to(channel.name, message)
        return

    def post_battle(self, channel, pokemon1, pokemon2, battle_type, winning_trainer):
        winner = pokemon1
        loser = pokemon2
        if pokemon1._hp == 0:
            winner = pokemon2
            loser = pokemon1
        exp = winner.gain_experience(loser)
        print(f"EXP IS NOW {exp} {winner.exp}")
        winner.gain_ev(loser)
        winner_before_str = str(winner)
        before_name = winner.name
        level = winner.check_level()
        self.sql_update_pokemon(winner)
        nick = winning_trainer.name
        message = f"{nick}'s {winner_before_str} defeated the {loser}. {winner_before_str} gained {exp} EXP and is at {winner.hp_to_percent()}% health. "

        if level:
            winner.level = level
            message += f"{winner_before_str} is now level {winner.level}. "
            if winner.name != before_name:

                message += f"{before_name} evolved into {winner.name}!"
                self.sql_evolve(winner)
        if battle_type == "wild":
            channel.current_privmsg = 0
            channel.wild_pokemon = None
            channel.reset_next_wild()
            channel.fainted_pokemon = loser
            loser.defeated_by = winning_trainer
        else:
            challenger = channel.challenge["challenger"]
            challenger_alive = list(filter(lambda pkmn: pkmn._hp > 0, challenger.party))
            challenger_dead = list(filter(lambda pkmn: pkmn._hp <= 0, challenger.party))
            challenger_string = f"{RED}{challenger.name}{CLEAR}: [{GREEN}{'o' * len(challenger_alive)}{RED}{'#' * len(challenger_dead)}{CLEAR}]"

            challenged = channel.challenge["challenged"]
            challenged_alive = list(filter(lambda pkmn: pkmn._hp > 0, challenged.party))
            challenged_dead = list(filter(lambda pkmn: pkmn._hp <= 0, challenged.party))
            challenged_string = f"{BLUE}{challenged.name}{CLEAR}: [{GREEN}{'o' * len(challenged_alive)}{RED}{'#' * len(challenged_dead)}{CLEAR}]"

            message = challenger_string + " " + challenged_string + message
            self.sql_update_health(loser)
        self.sql_update_health(winner)
        return message


        
                
    def parse_starter(self, nick, command):
        f_starters = " ".join(starters)
        if nick in self.player_list:
            raise BadPrivMsgCommand(nick, "You already chose a starter")
        if len(command) != 2:
            raise BadPrivMsgCommand(nick, f"Syntax: #starter <pokemon_name> .  Available: {f_starters}")
        if command[1] not in starters:
            raise BadPrivMsgCommand(nick, f"That is not an available starter pokemon. Available: {f_starters}")
        player = Player(nick)
        index = self.sql_add_trainer(player.name)
        player.index = index
        starter = Pokemon(command[1], 5)
        starter.captured = True
        starter.container_label = "A"
        index = self.sql_add_pokemon(starter, player)
        starter.index = index
        player.add_pokemon(starter)
        self.players.append(player)
        self.send_to(nick, f"Congratulations, your first pokemon is {starter}!")
    
    def sql_add_pokemon(self, pokemon, player):
        species = pokemon.name 
        trainer = player.index
        container_label = pokemon.container_label
        experience = pokemon.exp
        hp = pokemon._hp
        health_iv = pokemon.health_iv
        attack_iv = pokemon.attack_iv
        defense_iv = pokemon.defense_iv
        sattack_iv = pokemon.sattack_iv
        sdefense_iv = pokemon.sdefense_iv
        speed_iv = pokemon.speed_iv
        health_ev = pokemon.health_ev
        attack_ev = pokemon.attack_ev
        defense_ev = pokemon.defense_ev
        sattack_ev = pokemon.sattack_ev
        sdefense_ev = pokemon.sdefense_ev
        speed_ev = pokemon.speed_ev
        times_evolved = pokemon.times_evolved
        evolve_setting = pokemon.evolve_setting
        self.cur.execute("""INSERT INTO pokemon (species, trainer, container_label, experience, hp, health_iv, attack_iv, defense_iv, sattack_iv, sdefense_iv, speed_iv, health_ev, attack_ev, defense_ev, sattack_ev, sdefense_ev, speed_ev, times_evolved, evolve_setting) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (species, trainer, container_label, experience, hp, health_iv, attack_iv, defense_iv, sattack_iv, sdefense_iv, speed_iv, health_ev, attack_ev, defense_ev, sattack_ev, sdefense_ev, speed_ev, times_evolved, evolve_setting))
        self.con.commit()
        self.cur.execute("""SELECT pokemon_id FROM pokemon ORDER BY pokemon_id DESC LIMIT 1;""")
        results = self.cur.fetchall()
        answer = results[0][0]
        return answer

    def sql_update_pokemon(self, pokemon):
        args = (pokemon.exp, pokemon._hp, pokemon.health_iv, pokemon.attack_iv, pokemon.defense_iv, pokemon.sattack_iv, pokemon.sdefense_iv, pokemon.speed_iv, pokemon.health_ev, pokemon.attack_ev, pokemon.defense_ev, pokemon.sattack_ev, pokemon.sdefense_ev, pokemon.speed_ev, pokemon.index)
        self.cur.execute("""UPDATE pokemon SET experience = ?, hp = ?, health_iv = ?, attack_iv = ?, defense_iv = ?, sattack_iv = ?, sdefense_iv = ?, speed_iv = ?, health_ev = ?, attack_ev = ?, defense_ev = ?, sattack_ev = ?, sdefense_ev = ?, speed_ev = ? WHERE pokemon_id = ? """, args)
        self.con.commit()

    def post_registration(self):
        print("Connected to network.")
        for c in self.channels:
            self.join(c.name)
        self.client_ready = True


    def sql_update_health(self, pokemon):
        self.cur.execute("""UPDATE pokemon SET hp = ? WHERE pokemon_id = ?""", (pokemon._hp, pokemon.index))
        self.con.commit()
        
    def update_health_all(self):
        in_battles = set()
        for c in self.channels:
            if c.challenge and c.challenge["phase"] != "prebattle":
                in_battles.add(c.challenge["challenger"])
                in_battles.add(c.challenge["challenged"])
        for player in self.players:
            if player in in_battles:
                continue
            for pokemon in player.party + player.stored:
                before = pokemon._hp
                pokemon.increase_health_five_percent()
                if before != pokemon._hp:
                    self.sql_update_health(pokemon)

    def check_connection(self):
        self.send(f"PING {self.channels[0].name}")
        self.ping_sent = True

    def handle_pong(self):
        self.pong_received = True

    def reconnect_loop(self):
        is_connected = False
        time.sleep(1)
        i = 0
        while i <= 6:
            try:
                print(f"checking connection #{i}")
                self.check_connection()
                is_connected = True
                break
            except BlockingIOError as e:
                print(f"check #{i} failed")
                self.is_connected = False
                time.sleep(30)
            i += 1
        return is_connected

    def give_out_potions(self):
        for p in self.players:
            p.increment_potions
    def loop(self):
        self.is_connected = True
        self.repelling = False
        self.wild_pokemon = None
        self.fainted_pokemon = None
        wild_pokemon_time = None
        current_time = int(time.time())
        next_heal_time = current_time + 180
        next_check_connection_time = current_time + 25
        next_check_connection_time_2 = next_check_connection_time + 5
        self.ping_sent = False
        self.pong_received = False
        potion_time = 14400
        next_free_potion = current_time + potion_time
        gave_potion = True
        while self.is_connected:
            time.sleep(0.001)
            self.current_time = int(time.time())
            if self.current_time >= next_check_connection_time:
                if not self.ping_sent:
                    self.check_connection()
                elif self.current_time >= next_check_connection_time_2:
                    if not self.pong_received:
                        self.is_connected = False
                        break
                    else:
                        self.ping_sent = False
                        self.pong_received = False
                        next_check_connection_time = self.current_time + 25
                        next_check_connection_time_2 = self.current_time + 30

            if self.current_time % (60*60*4) == 0:
                if not gave_potion:
                    self.give_out_potions()
                    gave_potion = True
                else:
                    gave_potion = False

                
            data_received = False
            try:
                data = self.socket.recv(1024)
                data = data.decode("utf-8")
                data_received = True
                if not data:
                    pass
            except UnicodeDecodeError:
                pass
            except BlockingIOError:
                pass
            except Exception as e:
                print(e)

            if data_received:
                data = data.lstrip(":")
                data = data.split()
                if not data:
                    continue
                first_arg = data[0]
                try:
                    second_arg = data[1]
                except: continue
                
                if first_arg.lower() == "ping":
                    self.handle_ping(data)
                elif second_arg and second_arg.lower() == "pong":
                    self.handle_pong()
                elif second_arg and second_arg.lower() == "001":
                    self.post_registration()
                elif second_arg and second_arg.lower() == "privmsg":
                    try:
                        self.handle_privmsg(data)
                    except BadChanCommand as e:
                        self.send_to(e.channel, e.text)
                    except BadPrivMsgCommand as e:
                        nick = e.nick
                        self.send_to(nick, e.text)
                    except Exception as e:
                        exception_type, exception_object, exception_traceback = sys.exc_info()
                        line_number = exception_traceback.tb_lineno
                        print(exception_type, exception_object, exception_traceback)
                        print(line_number)
                        print(e)
                        print(traceback.format_exc())
                        pass
            if not self.client_ready:
                continue
            if self.current_time >= next_heal_time:
                self.update_health_all()
                next_heal_time = self.current_time + 180
            
            for c in self.channels:
                #TODO: make sure that players cant swap or receive potions during battle
                if c.challenge:
                    if self.current_time >= c.challenge["timeout"]:
                        if c.challenge["phase"] == "prebattle":
                            self.send_to(c.name, f"{c.challenge['challenged'].name} didn't respond in time, and the challenge expired")
                            c.challenge = None
                        elif c.challenge["phase"] == "first_turn":
                            self.send_to(c.name, f"{c.challenge['challenger'].name} didn't respond in time, and has forfeited the match.")
                            c.challenge = None
                        elif c.challenge["phase"] == "battle":
                            loser = c.challenge["challenged"]
                            if not c.challenge["pokemon1"]:
                                loser = c.challenge["challenger"]
                            
                            self.send_to(c.name, f"{loser.name} didn't send out a pokemon in time, and has forefeited the match.")
                            c.challenge = None


                # if it's time for the pokemon to show up, send it out
                if c.is_encounter_time() and not c.wild_pokemon:
                    c.fainted_pokemon = None
                    c.wild_pokemon = c.make_next_wild_pokemon()
                    c.wild_pokemon_time = int(time.time()) + 600
                    self.send_to(c.name, f"A wild {c.wild_pokemon} appeared!")

                #if it's time for the pokemon to wander off
                if self.current_time >= c.wild_pokemon_time and c.wild_pokemon:# and c.current_privmsg > 0:
                    pokemon_type = c.wild_pokemon.type

                    self.send_to(c.name, f"The wild {c.wild_pokemon} wandered off.")
                    del c.wild_pokemon
                    c.wild_pokemon = None
                    c.reset_next_wild()
                    

    def create_database(self):
        self.con = sqlite3.connect(self.db_file)
        self.con.execute("PRAGMA foreign_keys = 1")
        self.cur = self.con.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS trainers (trainer_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, nick TEXT NOT NULL UNIQUE)""")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS pokemon (pokemon_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, species TEXT NOT NULL, trainer INTEGER, container_label TEXT,  experience INTEGER, hp INTEGER, health_iv INTEGER, attack_iv INTEGER, defense_iv INTEGER, sattack_iv INTEGER, sdefense_iv INTEGER, speed_iv INTEGER, health_ev INTEGER, attack_ev INTEGER, defense_ev INTEGER, sattack_ev INTEGER, sdefense_ev INTEGER, speed_ev INTEGER, times_evolved INTEGER DEFAULT 0, evolve_setting INTEGER DEFAULT 1, FOREIGN KEY (trainer) REFERENCES trainers(trainer_id))""")
        self.con.commit()

    def sql_add_trainer(self, nick):
        self.cur.execute(f"INSERT INTO trainers (nick) VALUES (?)", (nick,))
        self.con.commit()
        self.cur.execute(f"SELECT * FROM trainers ORDER BY trainer_id DESC LIMIT 1;")
        last_one = self.cur.fetchall()[0][0]
        return last_one

    def sql_get_trainers(self):
        self.cur.execute("SELECT * FROM trainers")
        all_trainers_data = self.cur.fetchall()
        all_trainers = []
        for trainer in all_trainers_data:
            index = trainer[0]
            nick = trainer[1]
            player = Player(nick)
            player.index = index
            all_trainers.append(player)
        return all_trainers

parser = argparse.ArgumentParser(description="A CLI parser for pokebot")
parser.add_argument("config", help="Which config file to use")
args = parser.parse_args()
conf_file = args.config
config = configparser.ConfigParser()
config.read(conf_file)
def connect():
    HOST = config["SETTINGS"]["host"]
    PORT = int(config["SETTINGS"]["port"])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        a = s.connect((HOST, PORT))
        s.setblocking(False)
        client = Client(s, config)
        time.sleep(0.2)
        client.connect()
        client.loop()
        
while True:
    connect()
    print("Disconnected. Will try again in five minutes")
    time.sleep(5*60)
