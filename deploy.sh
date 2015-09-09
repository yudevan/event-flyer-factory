#!/bin/bash
ssh uwsgi@flyers.forbernie.com /bin/bash << EOF
    source /uwsgi/envs/event-flyer-factory/bin/activate
    cd /uwsgi/apps/event-flyer-factory
    git pull
    pip install -r requirements.txt
    touch /uwsgi/emperor/event-flyer-factory.ini
EOF

