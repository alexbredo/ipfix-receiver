ipfix-receiver
==============

Project's website: www.ipfix-receiver.de (= www.ipfix-collector.de)

IPFIX Receiver and Conversation-Aggregator (Proof-of-Conzept)

Features:
 * Receives IPFIX (Netflow v10) & Netflow v5 is now processed too (new).
 * Processing up to 3000 flows/s or 1,1 GBit/s were possible with my hardware
 * Lookup protocol names
 * calculate flow duration (with bugfix for Extreme Networks IPFIX Implementation Error)
 * lookup network location (by subnet)
 * aggregates flows to conversations (ratio 1:4+; with integrated flow caching)
 * lookup hostnames (with integrated DNS caching)
 * print to screen
 * save to file or elasticsearch
 * **NEW**: Simple IDS-functions for conversations security evaluation (trust, blacklists, port reputation)
 * Tested for Windows + Linux

Dependencies:
 * urllib

Usage:
```bash
# Generate Config
python3 ipfix_receiver.py -d config.xml
# Run
python3 ipfix_receiver.py
```

TODO: 
 * reuse my common-modules in site-packages(3) and remove duplicates
 * implement horizonal scale-out
 * cleanup
 
Contribution welcome.

All rights reserved.
(c) 2014 by Alexander Bredo
