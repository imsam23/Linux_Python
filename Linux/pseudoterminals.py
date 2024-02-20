import os
import pty
import sys

# Create a pseudoterminal pair (master and slave)
master, slave = pty.openpty()

# Launch a shell in the slave terminal
shell = "/bin/bash"
pid = os.fork()

if pid == 0:  # Child process (shell)
    os.dup2(slave, sys.stdin.fileno())
    os.dup2(slave, sys.stdout.fileno())
    os.dup2(slave, sys.stderr.fileno())
    os.execv(shell, [shell])

# Parent process (controlling process)
while True:
    try:
        user_input = input("Enter a command (q to quit): ")
        if user_input.lower() == "q":
            break
        os.write(master, (user_input + "\n").encode())
        output = os.read(master, 4096).decode()
        print(output)
    except EOFError:
        break

os.close(master)
os.close(slave)

# =============

x = {
    "adc_version": [
        "Cisco Web Usage Controls - Application Discovery and Control Data: 1693557522 (Fri Sep 01 08:55:20 2023)"
    ],
    "adc_apps": {
        "737280": {
            "possible_action": [
                "block",
                "monitor"
            ],
            "name": "Zucks",
            "cat_name": "Ad Publishing"
        },
        "1": {
            "possible_action": [
                "block",
                "monitor"
            ],
            "name": "1&1 IONOS Web Hosting",
            "cat_name": "Hosting Services"
        },
        "540676": {
            "possible_action": [
                "block",
                "monitor"
            ],
            "name": "Webkinz",
            "cat_name": "Games"
        }
    },
    "adc_categories": {
        "Marketing & Sales": {
            "possible_action": [
                "block",
                "monitor"
            ]
        },
        "Media": {
            "possible_action": [
                "block",
                "monitor"
            ]
        },
        "Travel": {
            "possible_action": [
                "block",
                "monitor"
            ]
        },
        "Human Resources": {
            "possible_action": [
                "block",
                "monitor"
            ]
        },
        "Service Management": {
            "possible_action": [
                "block",
                "monitor"
            ]
        }
    },
    "adc_activity_regexes": {
        "5000064": [
            "download\\.wetransfer\\.com\/.*"
        ],
        "5000065": [
            "photos\\.smugmug\\.com\/.*\/.*\/.*\/.*\/.*\/D\/.*-D\\..*",
            "photos\\.smugmug\\.com\/.*\/.*\/.*\/.*\/.*\/.*D\/.*D\\..*",
            "photos\\.smugmug\\.com\/photos\/.*\/.*\/.*\/D\/.*-D\\..*",
            "photos\\.smugmug\\.com\/photos\/.*\/.*\/.*\/.*D\/.*D\\..*",
            "secure\\.smugmug\\.com\/archive\/.*",
            "photos\\.smugmug\\.com\/Folder\/.*\/.*\/.*\/D\/.*-D\\..*",
            "www\\.smugmug\\.com\/api\/.*\/album\/.*!download",
            "api\\.smugmug\\.com\/api\/.*\/album\/.*!download"
        ],
        "5000077": [
            "i\\.instagram\\.com\/rupload_igphoto\/.*",
            ".*\\.instagram\\.com\/accounts\/web_change_profile_picture",
            "i\\.instagram\\.com\/rupload_igvideo\/.*"
        ],
        "5000078": [
            "www\\.linkedin\\.cn\/dms-uploads\/.*\/profile.*uploadedImage\/.*",
            "www\\.linkedin\\.com\/dms-uploads\/.*\/.*"
        ],
        "5000079": [
            "upload\\.twitter\\.com\/i\/media\/upload.*\\.json"
        ]},
    "adc_app_domains": {
        "737280": [
            "s.side3.zucks.net",
            "zimg.jp",
            "zucks.co.jp",
            "zucks.net"
        ],
        "540676": [
            "webkinz.com"
        ],
        "438273": [
            "admin.privy.com",
            "dashboard.privy.com",
            "privy.com",
            "privymktg.com"
        ],
        "11": [
            "4sharedapi.com",
            "4shared.com",
            "api.4sharedapi.com",
            "api.4shared.com",
            "e.4shared.com",
            "epomads2.4shared.com",
            "search.4shared.com",
            "static.4shared.com",
            "upload.4shared.com",
            "webdav.4shared.com"
        ],
        "901132": [
            "flowplay.com"
        ]}
}
