#!/bin/sh

echo "To exit screen session press [ctrl]+[a]+[d]"
read -p "Press return key to attach to session..." tmpVar

screen -d -r "cs-discordbot"
