# ZeroAccess_Crawler
A simple tool to crawl peers from ZeroAccess p2p network.
 ## Usage Instructions
 - Firstly Run python Listen.py <-- This will create a UDP socket to receive new peers from retL packet before sending them to the client (getL_sender)
 - Run python getL_sender.py <--- it simply sends getL packets to other peers (both from bootstrap list and new peers list received from Listener)
 - Peers will be saved in "peers_stored/peers.p"
