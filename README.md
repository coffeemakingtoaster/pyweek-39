# Flow - Pyweek 39

This is our entry for the pyweek 39 with the topic downstream.

Battle it out with your sword against either a bot (offline) or against other players online.

## Controls

| Key          | Action       |
|-------------|-------------|
| WASD        | Move        |
| Left Mouse  | Sweep       |
| Right Mouse | Block       |
| Shift       | Stab/Dash   |
| Space       | Jump        |

## Online Play

When playing online, keep in mind that there aren't many players. You may want to queue at the same time as a friend. The matchmaking system does not use an MMR system but instead matches players as quickly as possible.

You can edit and persist your username in the settings. :)

To change the network configuration (e.g., switching to a self-hosted server), edit `./game/const/networking.py`. (Host and whether or not to use ssl when connecting)

**Note:** Our resources are limited. We will be hosting the game server for a while, but there will only be an EU instance. You can still play from other parts of the world, but you may experience latency issues.

## Game

Install the requirements

```sh
python3 -m pip install -r requirements.txt
```

Run the game 

```sh
python3 ./run_game.py
```

## Server

Honestly it's easiest to just start the docker compose :)

```sh
docker-compose up -d
```

For development just install the additional server requirements

```sh
python3 -m pip install -r server/requirements.txt
```

Run the server

```sh
python3 ./run_server.py
```

