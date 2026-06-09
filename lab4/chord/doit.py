""" 
Chord Application
- defines a DummyChordClient implementation
- sets up a ring of chord_node instances
- Starts up a DummyChordClient
- nodes and client run in separate processes
- multiprocessing should work on unix and windows
"""

import logging
import sys
import multiprocessing as mp
import random

import chordnode as chord_node
import constChord
from context import lab_channel, lab_logging

lab_logging.setup(stream_level=logging.INFO)


class DummyChordClient:
    """A dummy client template with the channel boilerplate"""

    def __init__(self, channel):
        self.channel = channel
        self.node_id = channel.join('client')

    def enter(self):
        self.channel.bind(self.node_id)

    def run(self):
        m = self.channel.n_bits
        search_key = random.randint(0, (2**m) - 1)

        # 2. Liste aller aktiven Knoten aus Redis holen
        nodes = list(self.channel.channel.smembers('node'))
        
        # 3. Zufälligen Startknoten auswählen und SAUBER decodieren (aus b'4' wird '4')
        raw_node = random.choice(nodes)
        start_node = raw_node.decode('utf-8') if isinstance(raw_node, bytes) else str(raw_node)

        print(f"\n[Client] Starte Suche nach Key {search_key} über Einstiegsknoten {int(start_node):04n}...")

        # 4. Suchanfrage (LOOKUP_REQ) an den Startknoten senden
        # - [start_node] ist eine Liste mit Strings
        # - (constChord.LOOKUP_REQ, search_key, self.node_id) ist EIN Tupel
        self.channel.send_to([start_node], (constChord.LOOKUP_REQ, search_key, self.node_id))

        # 5. Auf das endrekursive Ergebnis warten
        message = self.channel.receive_from_any()
        sender = message[0]
        response = message[1]

        # 6. Ergebnis auswerten und Erfolgsmeldung ausgeben
        if response[0] == constChord.LOOKUP_REP:
            found_node = response[1]
            print(f"[Client] ERFOLG! Knoten {found_node:04n} ist zuständig für den Key {search_key}.\n")

        # 7. System ordnungsgemäß herunterfahren (Multicast STOP an alle Knoten)
        # Auch hier müssen wir sicherstellen, dass die Byte-Objekte aus Redis decodiert werden!
        self.channel.send_to(  
            {i.decode('utf-8') if isinstance(i, bytes) else str(i) for i in nodes},
            constChord.STOP
        )




def create_and_run(num_bits, node_class, enter_bar, run_bar):
    """
    Create and run a node (server or client role)
    :param num_bits: address range of the channel
    :param node_class: class of node
    :param enter_bar: barrier syncing channel population 
    :param run_bar: barrier syncing node creation
    """
    chan = lab_channel.Channel(n_bits=num_bits)
    node = node_class(chan)
    enter_bar.wait()  # wait for all nodes to join the channel
    node.enter()  # do what is needed to enter the ring
    run_bar.wait()  # wait for all nodes to finish entering
    node.run()  # start operating the node


if __name__ == "__main__":  # if script is started from command line
    m = 6  # Number of bits for linear names
    n = 8  # Number of nodes in the chord ring

    # Check for command line parameters m, n.
    if len(sys.argv) > 2:
        m = int(sys.argv[1])
        n = int(sys.argv[2])

    # Flush communication channel
    chan = lab_channel.Channel()
    chan.channel.flushall()

    # we need to spawn processes for support of windows
    mp.set_start_method('spawn')

    # create barriers to synchronize bootstrapping
    bar1 = mp.Barrier(n+1)  # Wait for channel population to complete
    bar2 = mp.Barrier(n+1)  # Wait for ring construction to complete

    # start n chord nodes in separate processes
    children = []
    for i in range(n):
        nodeproc = mp.Process(
            target=create_and_run,
            name="ChordNode-" + str(i),
            args=(m, chord_node.ChordNode, bar1, bar2))
        children.append(nodeproc)
        nodeproc.start()

    # spawn client proc and wait for it to finish
    clientproc = mp.Process(
        target=create_and_run,
        name="ChordClient",
        args=(m, DummyChordClient, bar1, bar2))
    clientproc.start()
    clientproc.join()

    # wait for node processes to finish
    for nodeproc in children:
        nodeproc.join()
