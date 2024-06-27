# Travel Raspberry Pi Router
Based on https://www.raspberrypi.com/tutorials/host-a-hotel-wifi-hotspot/

It's mainly for connecting to public Wifi like at Hotels where you need to connect multiple devices and/or family member devices to the network and don't want to have to "authorize" all of them. Most places have timeouts on the portal authentication and require you to login multiple times a day. 

This is just the web app (Flask) that allows you to connect to new sites and minimal control over the pi. I'm working on an ansible playbook to configure the entire pi from scratch and might add it to this repository in the future.

P.S. Most of the code is written by ChatGPT with a lot of arguing and tweaking from me
P.P.S. I've also added a local Plex server to my Pi with a copy of all my movies, hence the hostname in the screenshots.

## Requirements

- Raspberry Pi OS (preferably lite)
- Install python3-flask
```
sudo apt install python3-flask
```
- Setup main wifi hotspot in Network Manager
```
sudo nmcli device wifi hotspot ssid <you SSID here> password <your wifi password here> ifname wlan0
sudo nmcli connection modify $(nmcli con show Hotspot|awk '/uuid/ {print $2}') connection.autoconnect yes connection.autoconnect-priority 100
```
- Set the local DNS so you can access the pi locally by hostname.local
```
echo "address=/.local/10.42.0.1" |sudo tee -a /etc/NetworkManager/dnsmasq-shared.d/hosts.conf
```
<img src="https://github.com/leftyfb/travel-pi/assets/3206263/de644a36-52d2-4ba9-bf7b-3ea9b1a62c80" width="500">
<img src="https://github.com/leftyfb/travel-pi/assets/3206263/c36dacd9-3dd3-4f09-9c2d-24d2ed663031" width="500">
<img src="https://github.com/leftyfb/travel-pi/assets/3206263/83d20e62-7847-4824-8fb7-67b7633eab79" width="500">
