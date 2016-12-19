import socket
import sys
import struct
import zlib		
import random
import time
import platform
import urllib2
import os
#===============Utils======================================#	
rol = lambda val, r_bits, max_bits: \
    (val << r_bits%max_bits) & (2**max_bits-1) | \
    ((val & (2**max_bits-1)) >> (max_bits-(r_bits%max_bits)))
 
def L2B(dword):
	return struct.unpack(">I",struct.pack("<I",dword))[0]
	
def ip2int(addr):                                                               
    return struct.unpack("!I", socket.inet_aton(addr))[0]                       

def int2ip(addr):                                                               
    return socket.inet_ntoa(struct.pack("!I", addr))
	
def is_os_64bit():
	return platform.machine().endswith('64')

def _dword(s,i):
	a ="0x"+(s[i+3]).encode('hex')+s[i+2].encode('hex')+s[i+1].encode('hex')+s[i].encode('hex')
	result = int(a,16)
	return result

#======GLOBAL VARs=========================================#
	
backup_rand = 0
port = 0
new_peers = 'peers_stored/peers.p'
if not(is_os_64bit()):		
	port = 16470
	peer_file = 's64'
else:
	port = 16471
	peer_file = 's32'
	
def internet_on():
    try:
        urllib2.urlopen('https://www.google.com', timeout=1)
        return True
    except urllib2.URLError as err: 
        return False

	
def data2peer(data):
	peer_list = []
	count = len(data) >> 2
	i=0
	while count > 0:
		peer_list.append(int2ip(L2B(_dword(data,i))))
		i+=0x4
		count = count - 1
	return peer_list

	
def build_getL_packet(key,flag):
	cmd='getL'
	crc = struct.pack("<I",0)
	cmd = struct.pack("<I",(struct.unpack(">I",cmd)[0]))
	flg = struct.pack("<I",flag)
	rand = struct.pack("<I",int(random.random()*0xffffffff)&0x3ff)
	backup_rand = rand
	Init_packet = crc+cmd+flg+rand
	crc = struct.pack("<I",zlib.crc32(Init_packet,0)&0xffffffff)
	raw_packet = crc+cmd+flg+rand
	i=0
	k=struct.unpack(">I",key)[0]
	final_packet=''
	while (i<16):
		tmp =_dword(raw_packet,i)
		final_packet+=struct.pack("<I",tmp^k)
		k=rol(k,1,32)
		i=i+4
	return final_packet
	
	
def load_bootstrap_peers(file):
	f=open(file,'rb')
	f.seek(0,2) #jump to end of file
	fsize = f.tell() #get file size
	f.seek(0,0) #jump back
	peer_list =[]
	while f.tell() < fsize:
		peer_list.append(str(int2ip(struct.unpack(">I", f.read(4))[0])))
		f.read(4)
	f.close()
	return peer_list

def load_new_peers(file):
	peers = [line.rstrip('\n') for line in open(file)]
	return peers

#=================================================================================================#
	

	
def send_getL(socket, ipaddr, port, getL_packet):
	server_address = (ipaddr, port)
	try:
		print "Sending getL packet to %s:%s" %(ipaddr,port)
		sent = socket.sendto(getL_packet, server_address)
	except:
		print >>sys.stderr, '\nSend Failed!!!'

		

def m():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	
	sock.settimeout(10)
	flag=0
	key = 'ftp2'
	getL_packet = (build_getL_packet(key, flag))
	print "getL packet: "+ (getL_packet.encode('hex'))
	if os.path.isfile(new_peers):
		peer_list = load_new_peers(new_peers)
		print >> sys.stderr, 'peers.p exists, loading peers.p instead of %s...' %peer_file
		time.sleep(1)
	else:
		print >> sys.stderr, 'Loading peer list: %s...' %peer_file
		peer_list =  load_bootstrap_peers(peer_file)
		time.sleep(1)
	server_address = ('localhost', 10000)
    # Send data
	data=''
	message = "SYN"
	try:
		print >>sys.stderr, 'sending "%s"' % message
		sent = sock.sendto(message, server_address)
		# Receive response
		print >>sys.stderr, 'waiting for confirmation...'
		data, server = sock.recvfrom(4096)
		if data:
			print >>sys.stderr, 'received "%s"' % data
	except socket.error, ecx:
		print "Caught exception socket.error : %s" % ecx	
		sock.close()
		
	if str(data)=="OK":
		print >>sys.stderr, 'Sending getL...'
		while peer_list:
			for i in peer_list:
				send_getL(sock, i, port, getL_packet)
				#time.sleep(0.1)
				peer_list = list(filter(lambda x: x!= i , peer_list))
				if peer_list == []:
					#while peer_list == []:
					cock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	
					cock.settimeout(10)
					message = "new"
					try:
						print >>sys.stderr, 'sending request : "%s"' % message
						sent = cock.sendto(message, server_address)
						# Receive response
						print >>sys.stderr, 'waiting for new peers...'
						data, server = cock.recvfrom(4096)
						cock.close()
						if data:
							print >>sys.stderr, 'received new peers...'
							peer_list = data2peer(data)
							getL_packet = (build_getL_packet(key, flag))
					except socket.timeout, ecx:
						print "Time out exception : %s" % ecx	
						print "Load new peers from file : %s\n" % new_peers
						peer_list = load_new_peers(new_peers)
						getL_packet = (build_getL_packet(key, flag))
						cock.close()
					except socket.error, ecx:
						print "Caught exception socket.error : %s" % ecx	
						cock.close()
					time.sleep(0.1)
					continue
	else:
		print >>sys.stderr, 'Closing...'
		sock.close()

if not(internet_on()):
	print >> sys.stderr, 'No internet connection !'
	sys.exit(0)

m()
