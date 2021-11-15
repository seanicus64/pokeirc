Pokemon Bot for IRC
Overview:
===
A bot to play pokemon on IRC.  You can catch, train, and battle pokemon.  This is based off generation 1 with a few changes to simplify and update. 


Dependencies:
====
* Python3

Python dependencies:
---
* sqlite3
* configparser
* argparse

Configuration:
====
1. `cp example.conf pokemon.conf`
2. Change the values according to your bot
3. Make sure you set the nick, the "db_file" 

How to Play:
===
Every once in a wild a wild pokemon will show up in the channel. Send out one of your pokemon to fight it, and then maybe catch it.
First you must register.  To do this, choose a starter pokemon with the #starter command.  The available starters are:
* bulbasaur
* squirtle
* charmander
* pikachu
* caterpie
* pidgey
* meowth
* nidoran\_m
* nidoran\_f
* abra
* gastly
* machop
* geodude
* dratini
* cubone

`#starter <pokemon_type>`

After you choose your starter, you are ready to go.  Pokemon will pop up with a message looking like
`* A wild Ratata_2 appeared! *`.  The `_2` represents that the Ratata is at level 2, but your level 5 pokemon should be able to fight it.
Type `#go <pokemon>` to fight it, where `<pokemon>` is the name of your pokemon.
If your pokemon loses, you can send out another pokemon to finish it off, or someone else can jump in and defeat the pokemon.  
Whoever defeats the pokemon has the ability to catch it, simply by using the one word command `#catch`.  Pokemon can only be caught after they're fainted.
After the pokemon is caught, it will go into your team, or if your team already has six pokemon, it will be transferred to your PC.
Whatever pokemon defeats the opponent will gain experience at rates similar to the game.
Your pokemon will heal at a consistent rate proportional to the level of HP they have; all pokemon will be fully healed after 1 hour since the battle.

Commands:
===
* `#starter <pokemon_species>`: chooses your starter pokemon
* `#go <pokemon species>`: sends out the pokemon of your choice against the enemy. If you have multiple pokemon of the same species, it will send out the highest in your team.
* `#catch`: Catch the pokemon
* `#team`: Shows your team.  Before each member of your team is a letter from A to F.  These labels are used for swapping pokemon from your team to your PC.
* `#team show`: Shows your team to the channel where you sent this command.  By default, `#team` sends you the list in PM.
* `#pc`: Shows all the pokemon in your PC. The number before each pokemon is a label which is used for swapping between your PC to your team.
* `#examine <pokemon_name or pokemon_label>`: Shows the stats of your pokemon.  See the Stats discussion for more information.
* `#swap <pokemon1> <pokemon2>`: Swaps your pokemon from the first position to another.  The arguments can be pokemon names or labels.  For example, #swap 3 B swaps the pokemon in the third slot in your PC with the second pokemon in your party.
* `#release <pokemon_label> <pokemon_name>`: Releases your pokemon into the wild.  `<pokemon_label>` is necessary to prevent you from making mistakes.
* `#heal <pokemon_name>`: Heals one of your pokemon with a potion.  You only get 5 potions a day: use them wisely.
* `#pokecount`: Tells you how many pokemon you've caught as well as a list of the ones you have and haven't caught.  For simplicity each pokemon's name is reduced to 3 characters, but they are in the order as the gen1 pokedex.
* `#commands`: Shows a brief summary of these commands
