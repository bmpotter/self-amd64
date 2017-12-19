<img src="https://avatars0.githubusercontent.com/u/23140100?s=200&v=4" width="150">

# self-amd64
Watson-Intu Self Docker container build for x86 (amd64) 
Requires sound card, mic, speaker (or headphones), and camera (webcam preferred)

<img src="https://assets.logitech.com/assets/55372/webcam-c270-gallery.png" width="120">   +  <img src="https://images-na.ssl-images-amazon.com/images/I/71yMKM1VW2L._SL1500_.jpg" width="120">   +   <img src="https://www.sabrent.com/uploads/AU-MMSA-Main.jpg" width="120">

### Build
    docker build --squash --build-arg "mode=dev" -f Dockerfile.x86 -t openhorizon/amd64-x86-intu-self:edge .
(omit "--squash" if you're not using docker experimental features)

### Pull Docker image from openhorizon public repo
    docker pull openhorizon/amd64-x86-intu-self:edge     # approx 5GB

### Run
0. Clone this repo, and cd to the ./config directory. Use bootstrap-example.json as a starting point
1. Set up an IBM account with credentials for Watson services, according to this [guide](https://github.com/open-horizon/self-amd64/wiki/Register-for-Watson-Cloud-Services)
2. Copy your Watson services credential pwds/URLs into bootstrap-example.json, save as bootstrap.json.
3. On your x86 system, run `aplay -l` and `arecord -l`, identify the integer number of your sound card.  Edit the alsa.conf file with these values. Save the file.
4. Run Self in a container, linking your current config files:

    `docker run -it --rm --privileged -p 9443:9443 -v $PWD:/config self-test-edge-x86 /bin/bash -c "ln -s -f /config/bootstrap.json bin/linux/etc/shared/; ln -s -f /config/alsa.conf /usr/share/alsa/alsa.conf; ./bin/linux/run_self.sh"`
    
5. When Self starts, it will verbally greet you. You can browse to `http://localhost:9443/www/dashboard#/` to see the Self dashboard.  (substitute your TX2's IP address in place of "localhost" to visit the UI from another computer on LAN)
