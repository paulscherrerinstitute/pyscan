from bsread import source
import argparse

parser = argparse.ArgumentParser(description='Sqare root calculator')
parser.add_argument('channel_name', type=str)
parser.add_argument('n_messages', type=int)

args = parser.parse_args()
print("Connecting to channel: ", args.channel_name)
print("Printing number of messages: ", args.n_messages)

with source(channels=[args.channel_name], receive_timeout=1000) as stream:
    for _ in range(args.n_messages):

        message = stream.receive()

        if message is None:
            print("No data in 1 second")
        else:
            print(message.data.data[args.channel_name].value)