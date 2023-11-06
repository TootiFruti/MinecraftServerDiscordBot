import time
from pyngrok import ngrok, conf
from datetime import datetime
import subprocess
import threading
import discord
from mcrcon import MCRcon


#  retrieving information from bot_properties.txt

try:
    with open("./MinecraftServerDiscordBot/bot_properties.txt", "r") as f:
        data = f.readlines()
        ngrok_data = data[0]
        ngrok_data = eval(ngrok_data[8:len(ngrok_data)-1])

        server_data = data[1]
        server_data = eval(server_data[19:len(server_data) - 1])

        discord_op = data[2]
        discord_op = eval(discord_op[13:len(discord_op)-1])

        bot_name = data[3][11:len(data[3])-1]

        discord_prop = eval(data[4][10:len(data[4])-1])
        f.close()

except Exception as e:
    print("something's not right with bot_properties.txt file. Check bot_log/logs.log for more information.\nQuiting...")
    with open("./MinecraftServerDiscordBot/bot_log/logs.log", "a+") as f:
        log = f"{datetime.now()} : {e}\n"
        f.writelines(log)

    exit()


# ngrok
conf.get_default().ngrok_version = "v2"
conf.get_default().region = ngrok_data[1]
ngrok.set_auth_token(ngrok_data[0])
ngrok_server = ngrok.connect("25565", "tcp")
server_ip = str(ngrok_server).split(" ")[1]
server_ip = server_ip[7:len(server_ip)-1]

# text
msg_template = f"""
----------{bot_name} BOT--------------
"""
help_cmds = f"""
----------{bot_name} BOT--------------
Commannds
/ip          to get the latest/current IP of the server
/ping    to ping the bot. Used for checking whether the bot is online.
/server status  to check whether server is running or not.
/server start   to start server
"""

# discord conf
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# server mc
isServerRunning = [0]


def start_mc_server(isServerRunning):
    server = subprocess.Popen(server_data[0], shell=True)
    time.sleep(16)
    isServerRunning[0] = 1
    return server


server = start_mc_server(isServerRunning)


def run_cmd(server, cmd):
    with MCRcon('localhost', server_data[1]) as mcr:
        print('logged in')
        output = mcr.command(cmd)
        return output


def status(isServerRunning):
    if isServerRunning[0] == 1:
        print("Server is running")
    else:
        print("Server is not running")


def stop_server(server, isServerRunning):
    print('stopping server')
    run_cmd(server, "stop")
    isServerRunning[0] = 0
    print('server stopped')


def logs_bot(txt, author):
    log = f"{datetime.now()} {author} : {txt}\n "
    with open("./MinecraftServerDiscordBot/bot_log/logs.log", "a+") as f:
        f.writelines(log)
        f.close


def cmd_promot(server, isServerRunning):
    while True:
        try:
            time.sleep(1)
            cmd = input('>>> ')
            if cmd:
                if cmd == 'start':
                    if isServerRunning == 0:
                        server = start_mc_server(isServerRunning)
                    else:
                        print(isServerRunning)
                        print('server is already running')
                elif cmd == 'stop-server':
                    stop_server(server, isServerRunning)
                elif cmd == 'status':
                    status(isServerRunning)
                elif cmd == '?':
                    print('basic cmds;\n1. start\n2.stop-server\n3. status')
                elif cmd == 'exit':

                    if isServerRunning[0] == 0:
                        exit()
                    else:
                        print('stopping minecraft server...')
                        stop_server(server, isServerRunning)
                        print('stopped server..')
                        exit()
                else:
                    run_cmd(server, cmd)
        except Exception as e:
            print(f"something went wrong..\n{e}")


@client.event
async def on_ready():
    print("logged in as {0.user}".format(client))
    channel = client.get_channel(discord_prop[0])
    await channel.send(f"{msg_template}Joined the server!\n{bot_name}online...\n")


@client.event
async def on_message(message):
    global server
    global isServerRunning
    global ngrok_server
    global server_ip
    if message.author == client.user:
        pass
    elif message.content.startswith("/help"):
        print(
            f"discord bot {datetime.now()} : {message.author} triggered /help")
        await message.channel.send(help_cmds)

    elif message.content.startswith("/ip"):
        print(f"discord bot {datetime.now()} : {message.author} triggered /ip")
        msg_sent = f"{msg_template}Server IP : {server_ip}\n"
        await message.channel.send(msg_sent)
    elif message.content.startswith("/ping"):
        print(
            f"discord bot {datetime.now()} : {message.author} triggered /pingbot")
        msg_sent = f"{msg_template}Pong!\n"
        await message.channel.send(msg_sent)
    elif message.content.startswith('/server status'):
        if isServerRunning[0] == 1:
            players = run_cmd(server, 'list')
            msg = f'{msg_template}server is running\n{players}.'
            await message.channel.send(msg)
            logs_bot('/server stauts', str(message.author))
        else:
            msg = f'{msg_template}server is not running.'
            await message.channel.send(msg)
    elif message.content.startswith('/server start'):
        if isServerRunning[0] == 1:
            await message.channel.send(f"{msg_template}server is already online.")
        else:
            await message.channel.send(f"{msg_template}Starting the server...Please wait for the confirmation")
            server = start_mc_server(isServerRunning)
            time.sleep(15)
            await message.channel.send(f"{msg_template}Server is online now.")
            logs_bot('started the server', str(message.author))

    elif message.content.startswith('/server cmdres'):
        try:

            if str(message.author) in discord_op:
                cmd = str(message.content)[15:]
                await message.channel.send(f'{msg_template}running cmd: {cmd}')
                output = run_cmd(server, cmd)
                print(output)
                await message.channel.send(f'cmd executed.\noutput of cmd:\n{output}')
                logs_bot(output, str(message.author))
            else:
                msg = f"{msg_template}{message.author}. you dont have permission."
                await message.channel.send(msg)
        except Exception as e:
            print(e)
            logs_bot(e, str(message.author))
            await message.channel.send(f"{msg_template}something went wrong while executing {str(message.content)[12:]}")
    elif message.content.startswith('/server cmd'):
        try:

            if str(message.author) in discord_op:
                cmd = str(message.content)[12:]
                await message.channel.send(f'{msg_template}running cmd: {cmd}')
                output = run_cmd(server, cmd)
                print(output)
                await message.channel.send('cmd executed.')
                logs_bot(output, str(message.author))
            else:
                msg = f"{msg_template}{message.author}. you dont have permission."
                await message.channel.send(msg)
        except Exception as e:
            print(e)
            await message.channel.send(f"{msg_template}something went wrong while executing {str(message.content)[12:]}")

    elif message.content.startswith('/server stop now'):
        author = str(message.author)
        if author in discord_op:
            if isServerRunning[0] == 1:
                await message.channel.send('shutting down the server now.')
                run_cmd(server, f"say shutting down server....")
                stop_server(server, isServerRunning)
                await message.channel.send(f"server shutdown successfully.")
                logs_bot('shut down server', str(message.author))

            else:
                await message.channel.send(f"server is already down")

        else:
            msg = f"{msg_template}{message.author}. you dont have permission."
            await message.channel.send(msg)

    elif message.content.startswith('/server stop'):
        author = str(message.author).replace(" ", "")
        if author in discord_op:
            if isServerRunning[0] == 1:
                await message.channel.send('shutting down the server in 1 min....')
                run_cmd(server, "say shutting down server in 1 minute.")
                time.sleep(30)
                await message.channel.send('shutting down the server in 30 seonds....')
                run_cmd(server, "say shutting down server in 30 seconds....")
                time.sleep(10)
                for i in range(9):
                    await message.channel.send(f'shutting down the server in {10-i} seonds....')
                    run_cmd(
                        server, f"say shutting down server in {10-i} seconds....")
                    time.sleep(1)
                await message.channel.send('shutting down the server...')
                run_cmd(server, f"say shutting down server....")
                stop_server(server, isServerRunning)
                await message.channel.send(f"server shutdown successfully.")
                logs_bot('shutdown server', str(message.author))
            else:
                await message.channel.send(f"server is already down")

        else:
            msg = f"{msg_template}{message.author}. you dont have permission."
            await message.channel.send(msg)

    elif message.content.startswith("/"):
        print(f"discord bot {datetime.now()} : {message.author} triggered /")
        msg_sent = f"{msg_template}No such command. Use /help to get info.\n"
        await message.channel.send(msg_sent)


@ client.event
async def close():
    channel = client.get_channel(discord_prop[0])
    await channel.send(f"{msg_template}{bot_name} going offline...\n")

# main
threading.Thread(target=cmd_promot, args=(server, isServerRunning)).start()
client.run(discord_prop[1])
