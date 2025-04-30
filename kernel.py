### Fill in the following information before submitting
# Group id: 2
# Members: Nathan Andrews, Drake Smith, Aditya Chakka

import collections as c
import pathlib as p
import queue as q
import enum as e
import sys as sys

# PID is just an integer, but it is used to make it clear when a integer is expected to be a valid PID.
PID = int

# This class represents the PCB of processes.
# It is only here for your convinience and can be modified however you see fit.
class PCB:
    pid: PID
    priority: int
    def __init__(self, pid: PID, priority: int):
        self.pid = pid
        self.priority = priority
    def __str__(self):
        return f"PCB(pid: {self.pid}, priority: {self.priority})"
    def __eq__(self, other):
        if isinstance(other, PCB):
            return self.pid == other.pid and self.priority == other.priority
        return False
    def __lt__(self, other):
        if isinstance(other, PCB):
            return self.priority < other.priority
        return False
    def __gt__(self, other):
        if isinstance(other, PCB):
            return self.priority > other.priority
        return False

@e.unique
class Scheduling_Algorithm(e.Enum):
    FCFS = "FCFS"
    PRIORITY = "Priority"

    def __str__(self):
        return self.name
    @staticmethod
    def from_string(s: str) -> "Scheduling_Algorithm":
        match s:
            case "FCFS":
                return Scheduling_Algorithm.FCFS
            case "Priority":
                return Scheduling_Algorithm.PRIORITY
            case _:
                raise ValueError(f"Unknown scheduling algorithm: {s}")

# This class represents the Kernel of the simulation.
# The simulator will create an instance of this object and use it to respond to syscalls and interrupts.
# DO NOT modify the name of this class or remove it.
class Kernel:
    scheduling_algorithm: Scheduling_Algorithm
    ready_queue: c.deque[PCB]
    waiting_queue: c.deque[PCB]
    running: PCB
    idle_pcb: PCB
    
    priority_queue: q.PriorityQueue[PCB]
    exiting: bool

    # Called before the simulation begins.
    # Use this method to initilize any variables you need throughout the simulation.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def __init__(self, scheduling_algorithm: str):
        # changed scheduling algorithm to enum
        self.scheduling_algorithm = Scheduling_Algorithm.from_string(scheduling_algorithm)
        self.ready_queue = c.deque()
        self.waiting_queue = c.deque()
        # changed PCB to have priority inside
        self.idle_pcb = PCB(0, sys.maxsize)
        self.running = self.idle_pcb

        # Student Defined:
        self.priority_queue = q.PriorityQueue()
        self.exiting = False
        directory: p.Path = p.Path("output")
        directory.mkdir(parents=True, exist_ok=True)
    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # priority is the priority of new_process.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int) -> PID:
        print(f"New process {new_process} with priority {priority} arrived.")
        match self.scheduling_algorithm:
            case Scheduling_Algorithm.FCFS:
                self.ready_queue.append(PCB(new_process, priority))
                if self.running == self.idle_pcb:
                    print("Idle process running, choosing new process.")
                    return self.choose_next_process()
                else:
                    print("Idle process not running, continuing process.")
                    return self.running.pid
            case Scheduling_Algorithm.PRIORITY:
                self.priority_queue.put(PCB(new_process, priority))
                self.exiting = False
                return self.choose_next_process()
    # This method is triggered every time the current process performs an exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_exit(self) -> PID:
        print(f"Process {str(self.running)} exited.")
        self.exiting = True
        return self.choose_next_process()

    # This method is triggered when the currently running process requests to change its priority.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_set_priority(self, new_priority: int) -> PID:
        print(f"Process {str(self.running)} set priority to {new_priority}")
        self.exiting = False
        self.running.priority = new_priority
        return self.choose_next_process()


    # This is where you can select the next process to run.
    # This method is not directly called by the simulator and is purely for your convinience.
    # Feel free to modify this method as you see fit.
    # It is not required to actually use this method but it is recommended.
    def choose_next_process(self) -> PID:
        print("Choosing next process to run.")
        if len(self.ready_queue) == 0 and len(self.priority_queue.queue) == 0:
            print("No processes in ready queue or priority queue, running idle.")
            return self.idle_pcb.pid
        match self.scheduling_algorithm:
            case Scheduling_Algorithm.FCFS:
                print("Choosing next process from ready queue.")
                print(f"rq: {self.ready_queue}")
                self.running = self.ready_queue.popleft()
            case Scheduling_Algorithm.PRIORITY:
                print("Choosing next process from priority queue.")
                print(f"pq: {self.priority_queue.queue}")
                if not self.exiting and self.running != self.idle_pcb:
                    self.priority_queue.put(self.running)
                self.running = self.priority_queue.get()
        print(f"Next process to run: {str(self.running)}")
        return self.running.pid

