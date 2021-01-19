# hasspad

A macropad interface for Home Assistant using the Pimoroni Keybow

## Installation

First, provision the device. Flash `raspios` and ensure `ssh` and WiFi access are enabled.
This can be done by writing a blank `ssh` file and a `wpa_supplicant.conf` file to the BOOT mount.

Once you are able to login to the device, perform some basic setup to set the hostname and enable SPI:

```
sudo raspi-config nonint do_hostname hasspad
sudo raspi-config nonint do_spi 1
sudo reboot
```

Install `docker` and `docker-compose`:

```
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker pi

sudo apt-get install -y libffi-dev libssl-dev python3 python3-pip
sudo pip3 install docker-compose
```

The last thing you need to do is ensure environment variables are set that are used to authenticate with Home Assistant.
You can also pass these in as flags or modify `docker-compose.yml`:

```
export HASSPAD_URI="ws://homeassistant.local:8123/api/websocket"
export HASSPAD_ACCESS_TOKEN="abcd"
```

Finally, just run `docker-compose up`.
