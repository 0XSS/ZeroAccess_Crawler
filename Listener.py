import socket
import sys
import random
import struct
import urllib2

def internet_on():
    try:
        urllib2.urlopen('https://www.google.com', timeout=1)
        return True
    except urllib2.URLError as err: 
        return False

def get_host_name():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("google.com",80))
	name = (s.getsockname()[0])
	s.close()
	return name

def L2B(dword):
	return struct.unpack(">I",struct.pack("<I",dword))[0]


def int2ip(addr):                                                               
    return socket.inet_ntoa(struct.pack("!I", addr))

rol = lambda val, r_bits, max_bits: \
    (val << r_bits%max_bits) & (2**max_bits-1) | \
    ((val & (2**max_bits-1)) >> (max_bits-(r_bits%max_bits)))
	

def _dword(s,i):
	a ="0x"+(s[i+3]).encode('hex')+s[i+2].encode('hex')+s[i+1].encode('hex')+s[i].encode('hex')
	result = int(a,16)
	return result
	
def decode_stream(data,key):
	k=struct.unpack(">I",key)[0]
	i=0
	s=''
	size=len(data)
	size>>=2
	while (size>0):
		tmp=_dword(data,i)
		s+=struct.pack("<I",tmp^k)
		k=rol(k,1,32)
		i=i+4
		size=size-1
	return s


def peer2data(peer_list):
	ip= ''
	for i in peer_list:
		ip+=socket.inet_aton(str(i[0]))
	return ip
	
			
def	peers_extract(decoded_packet):
	peer_list = []
	i=0x10
	peer_count = 0x10
	while peer_count > 0:
		a=[]
		a.append(int2ip(L2B(_dword(decoded_packet,i))))
		a.append(int2ip(L2B(_dword(decoded_packet,i+0x4))))
		peer_list.append(a)
		i+=0x8
		peer_count = peer_count -1
	
	return peer_list


	
def udp_listen(cok, server_address, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server_address = (server_address, port)
	print >>sys.stderr, '[+] Starting up on %s port %s' % server_address
	sock.bind(server_address)
	filename = 'peers_stored/peers.p'
	checker = 0
	count = 0
	peer_list = []
	while True:
		data=''
		print >>sys.stderr, '\nwaiting for incoming packet...'
		try:
			data, address = sock.recvfrom(4096)
			print >>sys.stderr, 'received %s bytes from %s' % (len(data), address)
			
			decoded = (decode_stream(data,'ftp2'))
			crc = _dword(decoded, 0x0)
			cmd = struct.pack(">I", _dword(decoded, 0x4)) 
			flag = _dword(decoded, 0x8)
			c = _dword(decoded, 0xc)
			if cmd == 'getL':
				print >> sys.stderr,'Received getL packet.'
			#send retL
				pass
			elif cmd == 'retL' and len(decoded) >= 848:
				print >> sys.stderr,'Received retL packet.'
				print >>sys.stderr, data
				peers_tmp = peers_extract(decoded)
				count+=1
				if count <=16:	
					for i in peers_tmp:
						peer_list.append(i)
					cmd, client = cok.recvfrom(1024)
					if str(cmd)=="new":
						try:
							cok.sendto(peer2data(peers_tmp), client)
						except socket.error, exc:
							print "Caught exception socket.error : %s" % exc	
						
	
				else:	
					peers1 = []
					for i in peer_list:
						peers1.append(str(i[0]))
					peers1 = list(set(peers1))
					if checker == 0:
						f = open(filename,'w')
						for ip in peers1:
							print >> f, ip
						f.close()
					else:
						peers2 = [line.rstrip('\n') for line in open(filename)]
						f = open(filename,'a')
						for ip in peers1:
							if not(ip in peers2):
								f.write(ip+'\n')
							else:
								pass
						f.close()	
					count=0
					checker = 1
					peer_list = []	
		
			else:
				print >> sys.stderr, 'Unknown command !!!'
		except socket.error, exc:
			print "Caught exception socket.error : %s" % exc	
		
		
		
	
			
		
if not(internet_on()):
	print >> sys.stderr, 'No internet connection !'
	sys.exit(0)
	
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 10000)
print >>sys.stderr, 'Listening for PORT on %s port %s...' % server_address
sock.bind(server_address)
# Wait for a connection
print >>sys.stderr, 'Waiting for a connection'
data, client_address = sock.recvfrom(4096)

try:
	if str(data)=="SYN":
		print >> sys.stderr, 'Received SYN. Sending confirmation...'
		sock.sendto("OK",client_address)
		host = get_host_name()
		port = int(client_address[1])
		udp_listen(sock, host, port)
	else:
		print >>sys.stderr, 'no/wrong data', client_address
		sock.sendto("NO",client_address)
finally:
	sock.close()



