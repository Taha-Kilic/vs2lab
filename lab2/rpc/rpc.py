import constRPC
import threading
import time

from context import lab_channel


class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


class Client:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None
        self._result_threads = []

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')

    def stop(self):
        for thread in self._result_threads:
            thread.join()
        self.chan.leave('client')

    def append(self, data, db_list, callback=None):
        assert isinstance(db_list, DBList)
        msglst = (constRPC.APPEND, data, db_list)  # message payload
        self.chan.send_to(self.server, msglst)  # send msg to server
        
        ack_msg = self.chan.receive_from(self.server)  # wait for response
        print("[Client] hat ACK erhalten - mache nun andere sachen weiter...")

        if callback:
            result_thread = threading.Thread(target=self.wait_for_result, args=(callback,))
            result_thread.daemon = True
            result_thread.start()
            self._result_threads.append(result_thread)

    def wait_for_result(self, callback):
        print("[Client] warte nebenbei auf Ergebnis...")
        result = self.chan.receive_from(self.server)  # wait for response
        sender, result_data = result

        callback(result_data)


class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)  # - Make sure we have a list
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)
        while True:
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request
            if msgreq is not None:
                client = msgreq[0]  # see who is the caller
                msgrpc = msgreq[1]  # fetch call & parameters
                
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested
                    data = msgrpc[1]
                    db_list = msgrpc[2]

                    print("[Server] sende ACK zurück an Client")
                    self.chan.send_to({client}, constRPC.ACK)  # send ACK back to client

                    print("[Server] bearbeite Anfrage...")
                    time.sleep(10)

                    result = self.append(data, db_list)
                    print("[Server] sende Ergebnis zurück an Client")
                    self.chan.send_to({client}, result)  # send result back to client


                else:
                    pass  # unsupported request, simply ignore
