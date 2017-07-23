# octohook
Git Web Hook Tunnel for C2

# Install


```bash
# apt-get update && apt-get upgrade -y
# apt-get install python3-pip git -y
# pip install --upgrade pip
# pip install virtualenv
# virtualenv  -p python venv
# . venv/bin/activate
# git clone https://github.com/dsnezhkov/octohook
```
```bash
# pip install prompt_toolkit PyGithub bottle pygments pyaml delegator.py
```
or 

`pip install -r doc/requirements.txt`

# Setup
- Login as sevice GH account.
- Generate app teken as per:
    https://github.com/settings/tokens/new
- update git_app_token: '86c0ec38b90909c4fbb1cf7f4e20c8f7f451' in config/client.yml and config/server.yml
- set your agent ids on server and client
    Eg. agentid: 'b932e9f5'
- generate keys/server.pem 
    # ./utils/cr_cert.sh
- First client or server creates the repo 
    git_repo_name: 'rendezvous'

- Setup initial webhook(s):
    https://github.com/your-id/rendezvous/settings/hooks/new

    Set `Payload URL: https://IP-or-HOST:PORT/route/` where IP is the IP of your OC web service, PORT it listens on, and /route/ is the hook route
    specified in `hook_route: '/server/'` directive in configuration file.

    Set: `Content-type: application/json`
    " By default, we verify SSL certificates when delivering payloads. "  Disable for demo, enable in prod (letsencrypt)
    you can opt to receive all events but you may just 'Choose Let me select individual events.'  
    OC needs at a minimum: "Issue comment", "Issues". 
    Make sure you start your octohook server on the Payload URL above upon Webhook creation. IF set to "Active" "We will deliver event details when this hook is triggered." a ping registration request will be sent out to the OC server.

    Once you see "Green checkmark" in webhooks, you are registered. If not - check your params, and "redeliver" the ping. 

    Repeat setup for other webhooks if needed ( bidirectional RTM and swarm (future) )

## Start Server:
`python octohook.py ./config/server.yml`

## Start Client
`python octohook.py ./config/client.yml`


# TODO
- fix file put on python3
- open issue with delegator.p maintainer on .chain methon under python3

