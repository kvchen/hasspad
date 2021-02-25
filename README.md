# hasspad

A macropad interface for Home Assistant using the Pimoroni Keybow

## Installation

### Using Docker (Recommended)

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

The last thing you need to do is provision a config file. You can see the `example-config.yml` file at the root of this repository. Copy it and the `docker-compose.yml` file to the directory where you want to run the code, and run `docker-compose up`. You may need to modify `docker-compose.yml` with the correct bind path to your config file.

### Using pip

You can also just install the binary using `pip install hasspad`. To ensure it runs persistently across network issues and errors, you'll likely also want to write a systemd file.
