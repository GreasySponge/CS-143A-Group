# Fill in the following information before submitting
# Group id: 2
# Members: Nathan Andrews, Drake Smith, Aditya Chakkai

import collections as c
import pathlib as p
import queue as q
import enum as e
import sys as sys

# PID is just an integer, but it is used to make it clear when a integer 
# is expected to be a valid PID.
PID = int

# This class represents the PCB of processes.
# It is only here for your convinience and can be modified however you 
# see fit.


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
            # Lower priority number = higher priority
            # Use PID as tiebreaker
            if self.priority == other.priority:
                return self.pid < other.pid
            return self.priority < other.priority
        return False

    def __le__(self, other):
        if isinstance(other, PCB):
            if self.priority == other.priority:
                return self.pid <= other.pid
            return self.priority <= other.priority
        return False

    def __gt__(self, other):
        if isinstance(other, PCB):
            if self.priority == other.priority:
                return self.pid > other.pid
            return self.priority > other.priority
        return False

    def __ge__(self, other):
        if isinstance(other, PCB):
            if self.priority == other.priority:
                return self.pid >= other.pid
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
# The simulator will create an instance of this object and use it to 
# respond to syscalls and interrupts.
# DO NOT modify the name of this class or remove it.


class Kernel:
    scheduling_algorithm: Scheduling_Algorithm
    ready_queue: c.deque[PCB]
    waiting_queue: c.deque[PCB]
    running: PCB
    idle_pcb: PCB
    priority_queue: q.PriorityQueue[PCB]
    exiting: bool

    # Multilevel scheduling variables
    background_queue: c.deque[PCB]
    foreground_queue: c.deque[PCB]
    max_ml_time: int
    ml_interrupt_counter: int
    current_level: str
    found_first_process: bool

    # Called before the simulation begins.
    # Use this method to initilize any variables you need throughout the 
    # simulation.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def __init__(self, scheduling_algorithm: str, logger):
        self.ready_queue = c.deque()
        self.waiting_queue = c.deque()
        self.idle_pcb = PCB(0, sys.maxsize, "Background")
        self.running = self.idle_pcb
        self.logger = logger
        self.foreground_queue = c.deque()
        self.background_queue = c.deque()


        # Multilevel scheduling initialization
        self.foreground_queue = c.deque()
        self.background_queue = c.deque()

        # Student Defined:
        self.scheduling_algorithm = Scheduling_Algorithm.from_string(
            scheduling_algorithm)
        self.priority_queue = q.PriorityQueue()
        self.exiting = False
        output_dir: p.Path = p.Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        self.interrupt_counter = 0
        
        # Multilevel scheduling variables
        self.max_ml_time = 200
        self.ml_interrupt_counter = 0
        self.current_level = "Foreground"
        self.found_first_process = False

        # Semaphore and Mutex storage
        self.semaphores = {}
        self.mutexes = {}
    
    def is_idle(self) -> bool:
        return self.running == self.idle_pcb

    def log_queue_ml(self):
        self.logger.log(f"lvl: {self.current_level}")
        self.logger.log(f"cur-q: {self.foreground_queue if self.current_level == 'Foreground'else self.background_queue}")

    def log_both_queues_ml(self):
        self.logger.log(f"fg-q: {self.foreground_queue}")
        self.logger.log(f"bg-q: {self.background_queue}")

    def log_interrupt(self):
        self.logger.log(f"lvl: {self.current_level}")
        self.logger.log(f"cur-proc: {self.running}") 
        self.logger.log(f"ml_interrupt_ctr: {self.ml_interrupt_counter}")

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # priority is the priority of new_process.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int, 
                            process_type: str) -> PID:
        new_pcb = PCB(new_process, priority, process_type)
        if not self.found_first_process:
            self.current_level = process_type
            self.found_first_process = True
        match self.scheduling_algorithm:
            case Scheduling_Algorithm.FIRST_COME_FIRST_SERVE:
                self.ready_queue.append(new_pcb)
                if self.is_idle():
                    return self.choose_next_process()
                else:
                    return self.running.pid
            case Scheduling_Algorithm.PRIORITY:
                if self.is_idle():
                    self.running = new_pcb
                    return self.running.pid
                # Only preempt if new process has STRICTLY higher priority (lower number)
                if new_pcb.priority < self.running.priority:
                    self.priority_queue.put(self.running)
                    self.running = new_pcb
                    return new_pcb.pid
                else:
                    # New process has lower or equal priority - add to queue
                    self.priority_queue.put(new_pcb)
                    return self.running.pid
            case Scheduling_Algorithm.ROUND_ROBIN:
                self.ready_queue.append(new_pcb)
                if self.is_idle():
                    return self.choose_next_process()
                else:
                    return self.running.pid
            case Scheduling_Algorithm.MULTI_LEVEL:
                # self.logger.log(f"Adding process {new_process} to {\
                #     'foreground' if process_type == 'Foreground' \
                #         else 'background'} queue.")
                if process_type == "Foreground":
                    self.foreground_queue.append(new_pcb)
                elif process_type == "Background":
                    self.background_queue.append(new_pcb)
                else:
                    raise ValueError(f"Improper process type {process_type}")
                
                if self.is_idle():
                    return self.choose_next_process()
                else:
                    return self.running.pid
                
            case _:
                raise ValueError(
                    "Unknown scheduling algorithm: " \
                        + str(self.scheduling_algorithm))

    # This method is triggered every time the current process performs an 
    # exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_exit(self) -> PID:
        self.exiting = True

        # Reset counters for multilevel scheduling when queue becomes empty
        if self.scheduling_algorithm == Scheduling_Algorithm.MULTI_LEVEL:
            if self.current_level == "Foreground" \
                and len(self.foreground_queue) == 0:
                
                self.ml_interrupt_counter = 0
                self.interrupt_counter = 0
            elif self.current_level == "Background" \
                and len(self.background_queue) == 0:
                
                self.ml_interrupt_counter = 0
                self.interrupt_counter = 0
        if not self.is_idle():
            return self.choose_next_process()
        return self.idle_pcb.pid

    # This method is triggered when the currently running process requests 
    # to change its priority.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_set_priority(self, new_priority: int) -> PID:
        self.exiting = False
        old_priority = self.running.priority
        self.running.priority = new_priority
        if (self.scheduling_algorithm == Scheduling_Algorithm.PRIORITY and
                not self.priority_queue.empty()):
            # Check if any process in queue now has higher priority
            top = self.priority_queue.queue[0]
            if top.priority < self.running.priority:
                self.priority_queue.put(self.running)
                self.running = self.priority_queue.get()
                return self.running.pid
        return self.running.pid

    def is_other_level_empty(self) -> bool:
        if self.current_level == "Foreground":
            return len(self.background_queue) == 0
        elif self.current_level == "Background":
            return len(self.foreground_queue) == 0
        return True

    def choose_next_process(self) -> PID:
        match self.scheduling_algorithm:
            case Scheduling_Algorithm.FIRST_COME_FIRST_SERVE:
                if len(self.ready_queue) == 0:
                    self.running = self.idle_pcb
                else:
                    self.running = self.ready_queue.popleft()
            case Scheduling_Algorithm.PRIORITY:
                if self.priority_queue.empty():
                    self.running = self.idle_pcb
                else:
                    self.running = self.priority_queue.get()
            case Scheduling_Algorithm.ROUND_ROBIN:
                self.interrupt_counter = 0
                if len(self.ready_queue) == 0:
                    self.running = self.idle_pcb
                else:
                    self.running = self.ready_queue.popleft()
            case Scheduling_Algorithm.MULTI_LEVEL:
                self.log_queue_ml()
                if self.current_level == "Foreground":
                    self.interrupt_counter = 0
                    if len(self.foreground_queue) == 0: 
                        if len(self.background_queue) == 0:
                            self.running = self.idle_pcb
                        else:
                            self.running = self.background_queue.popleft()
                    else:
                        self.running = self.foreground_queue.popleft()
                elif self.current_level == "Background":
                    if len(self.background_queue) == 0:
                        if len(self.foreground_queue) == 0:
                            self.running = self.idle_pcb
                        else:
                            self.running = self.foreground_queue.popleft()
                    else:
                        self.running = self.background_queue.popleft()  
                if self.running != self.idle_pcb:
                    if self.running.process_type != self.current_level:
                        self.interrupt_counter = 0 
                    self.current_level = self.running.process_type
                    
                self.exiting = False
                if self.running != self.idle_pcb:
                    if self.running.process_type != self.current_level:
                        self.interrupt_counter = 0
                    self.current_level = self.running.process_type

                self.exiting = False
        return self.running.pid

    # This method is triggered when the currently running process requests 
    # to initialize a new semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_init_semaphore(self, semaphore_id: int, initial_value: int):
        if semaphore_id not in self.semaphores:
            self.semaphores[semaphore_id] = {
                "value": initial_value,
                "waiting": []
            }

    # This method is triggered when the currently running process calls 
    # p() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_semaphore_p(self, semaphore_id: int) -> PID:
        semaphore = self.semaphores.get(semaphore_id)
        if semaphore is None:
            raise ValueError(f"Semaphore {semaphore_id} not initialized")

        # Decrement the semaphore
        semaphore["value"] -= 1

        # Only block if value becomes negative
        if semaphore["value"] < 0:
            # Block current process
            semaphore["waiting"].append(self.running)
            return self.choose_next_process()

        # Continue running if semaphore allows
        return self.running.pid

    # This method is triggered when the currently running process calls 
    # v() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_semaphore_v(self, semaphore_id: int) -> PID:
        semaphore = self.semaphores.get(semaphore_id)
        if semaphore is None:
            raise ValueError(f"Semaphore {semaphore_id} not initialized")

        # Increment the semaphore value
        semaphore["value"] += 1

        # Wake up a waiting process if any
        if semaphore["waiting"]:
            if self.scheduling_algorithm == Scheduling_Algorithm.PRIORITY:
                # Select highest priority process (lowest priority number, 
                # then lowest PID)
                selected = min(semaphore["waiting"],
                               key=lambda p: (p.priority, p.pid))
                semaphore["waiting"].remove(selected)
                # Check if we should preempt current process
                if selected.priority < self.running.priority:
                    self.priority_queue.put(self.running)
                    self.running = selected
                    return selected.pid
                else:
                    self.priority_queue.put(selected)
            else:  # FCFS or RR
                selected = min(semaphore["waiting"], key=lambda p: p.pid)
                semaphore["waiting"].remove(selected)
                self.ready_queue.append(selected)

        return self.running.pid

    # This method is triggered when the currently running process requests 
    # to initialize a new mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_init_mutex(self, mutex_id: int):
        if mutex_id not in self.mutexes:
            self.mutexes[mutex_id] = {
                "locked": False,
                "owner": None,
                "waiting": []
            }

        # This method is triggered when the currently running process 
        # calls lock() on an existing mutex.
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
        return self.choose_next_process()

    # This method is triggered when the currently running process calls 
    # unlock() on an existing mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_mutex_unlock(self, mutex_id: int) -> PID:
        mutex = self.mutexes.get(mutex_id)
        if mutex is None:
            raise ValueError(f"Mutex {mutex_id} not initialized")

        if mutex["owner"] != self.running.pid:
            raise PermissionError(f"Process {self.running.pid} cannot unlock mutex it does not own")

        # Unlock the mutex
        mutex["locked"] = False
        mutex["owner"] = None

        if mutex["waiting"]:
            # Pick a process to give the lock to
            if self.scheduling_algorithm == Scheduling_Algorithm.PRIORITY:
                selected = min(mutex["waiting"],
                               key=lambda p: (p.priority, p.pid))
                mutex["waiting"].remove(selected)
                mutex["locked"] = True
                mutex["owner"] = selected.pid
                # Check if we should preempt current process
                if selected.priority < self.running.priority:
                    self.priority_queue.put(self.running)
                    self.running = selected
                    return selected.pid
                else:
                    self.priority_queue.put(selected)
            else:  # FCFS or RR
                selected = min(mutex["waiting"], key=lambda p: p.pid)
                mutex["waiting"].remove(selected)
                mutex["locked"] = True
                mutex["owner"] = selected.pid
                self.ready_queue.append(selected)

        return self.running.pid

    def switch_levels(self):
        self.logger.log(f"Switching levels from {self.current_level} to {'Background' if self.current_level == 'Foreground' else 'Foreground'}")
        if self.current_level == "Foreground":
            self.interrupt_counter = 0
            if not self.exiting and self.running \
                != self.idle_pcb:
                
                self.logger.log(f"Moving process {self.running.pid} to foreground queue.")
                if self.running.process_type \
                    == "Foreground":
                    self.foreground_queue.append(\
                        self.running)
            self.current_level = "Background"
            self.ml_interrupt_counter = 0
        elif self.current_level == "Background":
            if not self.exiting and self.running \
                != self.idle_pcb:

                self.logger.log(f"Moving process {self.running.pid} to background queue.")
                if self.running.process_type \
                    == "Background":
                    self.background_queue.insert(\
                        0, self.running)
            self.current_level = "Foreground"
            self.ml_interrupt_counter = 0


    # This function represents the hardware timer interrupt.
    # It is triggered every 10 microseconds and is the only way a kernel 
    # can track passing time.
    # Do not use real time to track how much time has passed as time is 
    # simulated.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def timer_interrupt(self) -> PID:
        self.log_interrupt()
        # keeps an interrupt counter to track when to change processes
        self.exiting = False
        match self.scheduling_algorithm:
            case Scheduling_Algorithm.ROUND_ROBIN:
                self.interrupt_counter += 1
                if self.interrupt_counter == 4:
                    self.ready_queue.append(self.running)
                    return self.choose_next_process()

            case Scheduling_Algorithm.MULTI_LEVEL:
                self.ml_interrupt_counter += 1
                # if we have reached the max time for the current level, 
                # we need to switch levels
                if self.ml_interrupt_counter == 20:
                    self.ml_interrupt_counter = 0

                    # if the other level is not empty, we need 
                    # to switch levels
                    if not self.is_other_level_empty():
                        self.switch_levels()
                        self.log_both_queues_ml()
                        # context switch to the other level
                        # with the first process in that level
                        return self.choose_next_process()
                    # the other level is empty, so we commit to the 
                    # current level
                # its not time to context switch, we can just continue 
                # round robin style scheduling
                if self.current_level == "Foreground":
                    self.interrupt_counter += 1
                    if self.running != self.idle_pcb \
                        and self.interrupt_counter == 4:

                            self.interrupt_counter = 0
                            self.foreground_queue.append(self.running)
                            return self.choose_next_process()
                # FCFS doesn't require any extra actions during the 
                # timer_interrupt
                # self.logger.log(f"timer_interrupt: running={self.running \
                #                 }, level={self.current_level \
                #                 }, ic={self.interrupt_counter \
                #                 },ml_ic={self.ml_interrupt_counter}")
                # self.logger.log(f"Current foreground queue: {\
                #                 self.foreground_queue}")
                # self.logger.log(f"Current background queue: {\
                #                 self.background_queue}")
        return self.running.pid
