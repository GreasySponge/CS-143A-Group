# Fill in the following information before submitting
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
    process_type: str

    def __init__(self, pid: PID, priority: int, process_type: str):
        self.pid = pid
        self.priority = priority
        self.process_type = process_type

    def __str__(self):
        return f"PCB(pid: {self.pid}, priority: {self.priority}, process_type: {self.process_type})"

    def __eq__(self, other):
        if isinstance(other, PCB):
            return self.pid == other.pid and self.priority == other.priority
        return False

    def __lt__(self, other):
        if isinstance(other, PCB):
            return self.priority < other.priority
        return False

    def __le__(self, other):
        if isinstance(other, PCB):
            return self.priority <= other.priority
        return False

    def __gt__(self, other):
        if isinstance(other, PCB):
            return self.priority > other.priority
        return False

    def __ge__(self, other):
        if isinstance(other, PCB):
            return self.priority >= other.priority
        return False

    def __repr__(self) -> str:
        return str(self)


@e.unique
class Scheduling_Algorithm(e.Enum):
    FIRST_COME_FIRST_SERVE = "FIRST_COME_FIRST_SERVE"
    PRIORITY = "Priority"
    ROUND_ROBIN = "Round-Robin"
    MULTI_LEVEL = "Multi-Level"

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s: str) -> "Scheduling_Algorithm":
        match s:
            case "FCFS":
                return Scheduling_Algorithm.FIRST_COME_FIRST_SERVE
            case "Priority":
                return Scheduling_Algorithm.PRIORITY
            case "RR":
                return Scheduling_Algorithm.ROUND_ROBIN
            case "Multilevel":
                return Scheduling_Algorithm.MULTI_LEVEL
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
    def __init__(self, scheduling_algorithm: str, logger):
        self.ready_queue = c.deque()
        self.waiting_queue = c.deque()
        self.idle_pcb = PCB(0, sys.maxsize, "Background")
        self.running = self.idle_pcb
        self.logger = logger

        # Student Defined:
        self.scheduling_algorithm = Scheduling_Algorithm.from_string(
            scheduling_algorithm)
        self.priority_queue = q.PriorityQueue()
        self.exiting = False
        output_dir: p.Path = p.Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        self.interrupt_counter = 0

        self.semaphores = {}
        self.mutexes = {}

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # priority is the priority of new_process.
    # DO NOT rename or delete this method. DO NOT change its arguments.

    def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
        # self.logger.log(f"New process {new_process} with priority {priority} arrived.")
        new_pcb = PCB(new_process, priority, process_type)
        match self.scheduling_algorithm:
            case Scheduling_Algorithm.FIRST_COME_FIRST_SERVE:
                # self.logger.log(f"Adding process {new_process} to ready queue.")
                self.ready_queue.append(new_pcb)
                if self.is_idle():
                    # self.logger.log("Idle process running, choosing new process.")
                    return self.choose_next_process()
                else:
                    # self.logger.log("Idle process not running, continuing process.")
                    return self.running.pid

            case Scheduling_Algorithm.PRIORITY:
                if priority < self.running.priority:
                    # self.logger.log(f"new process {new_process} has higher priority than running process {self.running}, running new process.")
                    self.priority_queue.put(self.running)
                    self.running = new_pcb
                else:
                    self.priority_queue.put(new_pcb)
                return self.running.pid

            case Scheduling_Algorithm.ROUND_ROBIN:
                # self.logger.log(f"Adding process {new_process} to ready queue.")
                self.ready_queue.append(new_pcb)
                if self.is_idle():
                    # self.logger.log("Idle process running, choosing new process.")
                    return self.choose_next_process()
                else:
                    # self.logger.log("Idle process not running, continuing process.")
                    return self.running.pid
            case _:
                raise ValueError(
                    "Unknown scheduling algorithm: " + str(self.scheduling_algorithm))

    # This method is triggered every time the current process performs an exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.

    def syscall_exit(self) -> PID:
        # self.logger.log(f"Process {str(self.running)} exited.")
        self.exiting = True
        if not self.is_idle():
            return self.choose_next_process()
        return self.idle_pcb.pid

    # This method is triggered when the currently running process requests to change its priority.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    # def syscall_set_priority(self, new_priority: int) -> PID:
    #     # self.logger.log(f"Process {str(self.running)} set priority to {new_priority}")
    #     self.exiting = False
    #     self.running.priority = new_priority
    #     if self.priority_queue.queue[0].priority < self.running.priority:
    #         # self.logger.log(f"Process {str(self.running)} has lower priority than process {self.priority_queue.queue[0]}")
    #         self.priority_queue.put(self.running)
    #         self.running = self.priority_queue.get()
    #     return self.running.pid
    def syscall_set_priority(self, new_priority: int) -> PID:
        self.exiting = False
        self.running.priority = new_priority

        # ✅ Only check top of priority queue if it's non-empty
        if (self.scheduling_algorithm == Scheduling_Algorithm.PRIORITY and
                not self.priority_queue.empty()):
            top = self.priority_queue.queue[0]
            if top.priority < self.running.priority:
                self.priority_queue.put(self.running)
                self.running = self.priority_queue.get()

        return self.running.pid

    def choose_next_process(self) -> PID:
        # self.logger.log("Choosing next process to run.")
        match self.scheduling_algorithm:
            case Scheduling_Algorithm.FIRST_COME_FIRST_SERVE:
                if len(self.ready_queue) == 0:
                    # self.logger.log("No processes in ready queue, running idle.")
                    self.running = self.idle_pcb
                else:
                    # self.logger.log("choosing from ready queue.")
                    # self.logger.log(f"rq: {self.ready_queue}")
                    self.running = self.ready_queue.popleft()

            case Scheduling_Algorithm.PRIORITY:
                if self.priority_queue.empty():
                    # self.logger.log("No processes in priority queue, running idle.")
                    self.running = self.idle_pcb
                else:
                    # self.logger.log("choosing from priority queue.")
                    # self.logger.log(f"pq: {self.priority_queue.queue}")
                    # self.logger.log(f"choosing {self.priority_queue.queue[0]}")
                    self.running = self.priority_queue.get()

            case Scheduling_Algorithm.ROUND_ROBIN:
                self.interrupt_counter = 0
                if len(self.ready_queue) == 0:
                    # self.logger.log("No processes in ready queue, running idle.")
                    self.running = self.idle_pcb
                else:
                    # self.logger.log("choosing from ready queue.")
                    # self.logger.log(f"rq: {self.ready_queue}")
                    self.running = self.ready_queue.popleft()

        return self.running.pid

    def is_idle(self) -> bool:
        return self.running == self.idle_pcb

    # This method is triggered when the currently running process requests to initialize a new semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_init_semaphore(self, semaphore_id: int, initial_value: int):
        if semaphore_id not in self.semaphores:
            self.semaphores[semaphore_id] = {
                "value": initial_value,
                "waiting": []
            }

    # This method is triggered when the currently running process calls p() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_semaphore_p(self, semaphore_id: int) -> PID:
        semaphore = self.semaphores.get(semaphore_id)
        if semaphore is None:
            raise ValueError(f"Semaphore {semaphore_id} not initialized")

        semaphore["value"] -= 1

        if semaphore["value"] < 0:
            semaphore["waiting"].append(self.running)

            if self.scheduling_algorithm == Scheduling_Algorithm.FIRST_COME_FIRST_SERVE:
                return self.choose_next_process()

            return self.choose_next_process()

        return self.running.pid

    # This method is triggered when the currently running process calls v() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.

    def syscall_semaphore_v(self, semaphore_id: int) -> PID:
        semaphore = self.semaphores.get(semaphore_id)
        if semaphore is None:
            raise ValueError(f"Semaphore {semaphore_id} not initialized")

        # Increment the semaphore value
        semaphore["value"] += 1

        if semaphore["waiting"]:
            # Unblock the appropriate process based on scheduling policy
            if self.scheduling_algorithm == Scheduling_Algorithm.PRIORITY:
                selected = min(semaphore["waiting"],
                               key=lambda p: (p.priority, p.pid))
                self.priority_queue.put(selected)
            else:  # FCFS or RR
                selected = min(semaphore["waiting"], key=lambda p: p.pid)
                self.ready_queue.append(selected)

            # Remove from waitlist after adding back to queue
            semaphore["waiting"].remove(selected)

        # Do not preempt — continue running current process
        return self.running.pid

    # This method is triggered when the currently running process requests to initialize a new mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.

    def syscall_init_mutex(self, mutex_id: int):
        if mutex_id not in self.mutexes:
            self.mutexes[mutex_id] = {
                "locked": False,
                "owner": None,
                "waiting": []
            }

    # This method is triggered when the currently running process calls lock() on an existing mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_mutex_lock(self, mutex_id: int) -> PID:
        mutex = self.mutexes.get(mutex_id)
        if mutex is None:
            raise ValueError(f"Mutex {mutex_id} not initialized")

        if not mutex["locked"]:
            # Lock is free — this process gets it
            mutex["locked"] = True
            mutex["owner"] = self.running.pid
            return self.running.pid

        # Mutex is taken — block this process
        mutex["waiting"].append(self.running)

        # FCFS: do not preempt
        if self.scheduling_algorithm == Scheduling_Algorithm.FIRST_COME_FIRST_SERVE:
            self.running = self.choose_next_process()
            return self.running.pid

        # RR or Priority — switch to next process
        return self.choose_next_process()

    # This method is triggered when the currently running process calls unlock() on an existing mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.

    def syscall_mutex_unlock(self, mutex_id: int) -> PID:
        mutex = self.mutexes.get(mutex_id)
        if mutex is None:
            raise ValueError(f"Mutex {mutex_id} not initialized")

        if mutex["owner"] != self.running.pid:
            raise PermissionError(
                f"Process {self.running.pid} cannot unlock mutex it does not own")

        # Unlock the mutex
        mutex["locked"] = False
        mutex["owner"] = None

        if mutex["waiting"]:
            # Pick a process to give the lock to
            if self.scheduling_algorithm == Scheduling_Algorithm.PRIORITY:
                selected = min(mutex["waiting"],
                               key=lambda p: (p.priority, p.pid))
            else:
                selected = min(mutex["waiting"], key=lambda p: p.pid)

            mutex["waiting"].remove(selected)
            mutex["locked"] = True
            mutex["owner"] = selected.pid

            # Add it back to the correct queue
            if self.scheduling_algorithm == Scheduling_Algorithm.PRIORITY:
                self.priority_queue.put(selected)
            else:
                self.ready_queue.append(selected)

        return self.running.pid

    # This function represents the hardware timer interrupt.
    # It is triggered every 10 microseconds and is the only way a kernel can track passing time.
    # Do not use real time to track how much time has passed as time is simulated.
    # DO NOT rename or delete this method. DO NOT change its arguments.

    def timer_interrupt(self) -> PID:
        # keeps an interrupt counter to track when to change processes
        # self.logger.log("timer interrupt")
        self.interrupt_counter += 1
        if self.interrupt_counter == 4:
            self.ready_queue.append(self.running)
            self.choose_next_process()
        return self.running.pid
