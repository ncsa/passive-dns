#!/usr/bin/env python
import pcapy
import dns.message
import time, datetime
import gzip
import psyco
psyco.full()

OFFSET = 42
A = 1

def date(d):
    return datetime.datetime.fromtimestamp(d).strftime("%Y-%m-%d %H:%M:%S")

def get_ips(m):
    for a in m.answer:
        if a.rdtype != A: continue
        for i in a:
            yield i.to_text(), a.ttl

def get_query(m):
    query = m.question[0].to_text().split()[0]
    return query
        
class Statmaker:
    def __init__(self):
        self.ipnames = {}

    def __call__(self, header, data):

        ts, _ =  header.getts()
        try :
            m = dns.message.from_wire(data[OFFSET:])
        except:
            return
        query = get_query(m)

        ipn = self.ipnames

        for ip, ttl in get_ips(m):
            tup = (ip, query)
            if tup in ipn:
                r = ipn[tup]
                r.update({'last': ts, 'ttl': ttl})
            else:
                ipn[tup]={'first': ts, 'last': ts, 'ttl': ttl}

        
def parse(fn):
    s = Statmaker()
    pcap = pcapy.open_offline(fn)
    pcap.loop(0, s)

    return s

def report(fn, outfn):
    s = parse(fn)
    if outfn.endswith("gz"):
        o = gzip.open
    else:
        o = open
    f = o(outfn, 'w')

    for (ip, name), rec in s.ipnames.iteritems():
        f.write("%s %s %s %s %s\n" % (ip, name, rec['ttl'], date(rec['first']),date(rec['last'])))
    f.close()

if __name__ == "__main__":
    import sys
    inf = sys.argv[1]
    outf = "/dev/stdout"
    if len(sys.argv) > 2:
        outf = sys.argv[2]
    if outf == "auto":
        outf = inf.replace(".pcap",".txt.gz")
        if outf == inf:
            raise Exception("Same filename???")
    report(inf, outf)