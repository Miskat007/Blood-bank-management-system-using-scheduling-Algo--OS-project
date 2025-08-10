from datetime import datetime, timedelta
from colorama import init, Fore, Style
import hashlib
import os
import time
import json
from tabulate import tabulate

# Initialize colorama
init()

# Helper functions
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print(Fore.RED + Style.BRIGHT + "*** Blood Bank Management System ***" + Style.RESET_ALL)

def loading_animation():
    for _ in range(3):
        print(Fore.YELLOW + ".", end="", flush=True)
        time.sleep(0.5)
    print(Style.RESET_ALL)

# Donor class
class Donor:
    def __init__(self):
        self.donors = {}
        self.load_donors()

    def load_donors(self):
        try:
            with open('donors.json', 'r') as file:
                self.donors = json.load(file)
        except FileNotFoundError:
            self.donors = {}

    def save_donors(self):
        with open('donors.json', 'w') as file:
            json.dump(self.donors, file)

    def register(self, username, password):
        if username in self.donors:
            print(Fore.RED + "❌ Username already exists!" + Style.RESET_ALL)
            return False
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.donors[username] = hashed_password
        self.save_donors()
        print(Fore.GREEN + f"✅ Donor {username} registered successfully!" + Style.RESET_ALL)
        return True

# Admin class
class Admin:
    def __init__(self):
        self.admins = {'admin': hashlib.sha256('admin123'.encode()).hexdigest()}
        self.logged_in = False
        self.current_user = None
        self.audit_log = []

    def login(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if username in self.admins and self.admins[username] == hashed_password:
            self.logged_in = True
            self.current_user = username
            self.log_action(f"Admin {username} logged in")
            return True
        return False

    def log_action(self, action):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.audit_log.append(f"{timestamp}: {action}")

# Memory management class
class MemoryManager:
    def __init__(self):
        self.total_capacity = 1000
        self.storage_blocks = []
        self.initialize_storage()

    def initialize_storage(self):
        block_size = 100
        for i in range(0, self.total_capacity, block_size):
            self.storage_blocks.append({
                'id': len(self.storage_blocks),
                'size': block_size,
                'used': 0,
                'blood_type': None,
                'entry_date': None,
                'expiry_date': None
            })

    def allocate_memory(self, blood_type, units):
        best_block = None
        min_waste = float('inf')

        for block in self.storage_blocks:
            if block['blood_type'] is None:
                waste = block['size'] - units
                if waste >= 0 and waste < min_waste:
                    min_waste = waste
                    best_block = block

        if best_block:
            best_block['blood_type'] = blood_type
            best_block['used'] = units
            best_block['entry_date'] = datetime.now()
            best_block['expiry_date'] = datetime.now() + timedelta(days=30)
            return True
        return False

    def deallocate_memory(self, blood_type, units):
        for block in self.storage_blocks:
            if block['blood_type'] == blood_type and block['used'] >= units:
                block['used'] -= units
                if block['used'] == 0:
                    block['blood_type'] = None
                    block['entry_date'] = None
                    block['expiry_date'] = None
                return True
        return False

    def get_memory_status(self):
        used_space = sum(block['used'] for block in self.storage_blocks)
        return {
            'total': self.total_capacity,
            'used': used_space,
            'available': self.total_capacity - used_space,
        }

# Blood inventory class
class BloodInventory:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.blood_stock = {
            'A+': {'units': 0, 'expiry': None},
            'A-': {'units': 0, 'expiry': None},
            'B+': {'units': 0, 'expiry': None},
            'B-': {'units': 0, 'expiry': None},
            'AB+': {'units': 0, 'expiry': None},
            'AB-': {'units': 0, 'expiry': None},
            'O+': {'units': 0, 'expiry': None},
            'O-': {'units': 0, 'expiry': None},
        }

    def donate_blood(self, blood_type, units):
        if blood_type not in self.blood_stock:
            print(Fore.RED + "❌ Invalid blood type!" + Style.RESET_ALL)
            return False
        if units <= 0:
            print(Fore.RED + "❌ Units must be positive!" + Style.RESET_ALL)
            return False
        if self.memory_manager.allocate_memory(blood_type, units):
            expiry_date = datetime.now() + timedelta(days=30)
            self.blood_stock[blood_type]['units'] += units
            self.blood_stock[blood_type]['expiry'] = expiry_date
            print(Fore.GREEN + f"✅ Success! {units} units of {blood_type} added to stock (Expiry: {expiry_date})." + Style.RESET_ALL)
            return True
        else:
            print(Fore.RED + "❌ Storage capacity full!" + Style.RESET_ALL)
            return False

    def request_blood(self, blood_type, units):
        if blood_type not in self.blood_stock:
            print(Fore.RED + "❌ Invalid blood type!" + Style.RESET_ALL)
            return False
        if units <= 0:
            print(Fore.RED + "❌ Units must be positive!" + Style.RESET_ALL)
            return False
        if self.blood_stock[blood_type]['units'] >= units:
            if self.memory_manager.deallocate_memory(blood_type, units):
                self.blood_stock[blood_type]['units'] -= units
                if self.blood_stock[blood_type]['units'] == 0:
                    self.blood_stock[blood_type]['expiry'] = None
                print(Fore.GREEN + f"✅ Success! {units} units of {blood_type} dispensed." + Style.RESET_ALL)
                return True
            else:
                print(Fore.RED + "❌ Memory deallocation failed!" + Style.RESET_ALL)
                return False
        else:
            print(Fore.RED + f"❌ Insufficient stock for {blood_type}! Available: {self.blood_stock[blood_type]['units']} units" + Style.RESET_ALL)
            return False

    def view_stock(self):
        print(Fore.CYAN + "\n🩸 Blood Stock:" + Style.RESET_ALL)
        table = [[bt, details['units'], details['expiry'] if details['expiry'] else "N/A"] 
                 for bt, details in self.blood_stock.items()]
        print(tabulate(table, headers=["Blood Type", "Units", "Expiry"], tablefmt="grid"))

# Scheduler class
class Scheduler:
    def __init__(self, inventory):
        self.requests = []
        self.inventory = inventory
        self.time_quantum = 10  # Seconds per time slice for Round Robin

    def add_request(self, request):
        self.requests.append(request)
        print(Fore.GREEN + f"✅ Request {request['id']} for {request['blood_type']} ({request['units']} units, Priority: {request['priority']}) added." + Style.RESET_ALL)

    def process_round_robin(self):
        print(Fore.CYAN + "\nProcessing Requests (Round Robin, Time Quantum: 10s):" + Style.RESET_ALL)
        if not self.requests:
            print(Fore.YELLOW + "No requests to process." + Style.RESET_ALL)
            return
        processed = []
        current_time = 0
        while self.requests:
            request = self.requests.pop(0)
            units = request['units']
            blood_type = request['blood_type']
            units_to_process = min(units, self.time_quantum)
            print(f"[Time {current_time}s] Processing request {request['id']} for {blood_type} ({units_to_process}/{units} units)")
            if self.inventory.request_blood(blood_type, units_to_process):
                if units > units_to_process:
                    self.requests.append({
                        'id': request['id'],
                        'blood_type': blood_type,
                        'units': units - units_to_process,
                        'priority': request['priority']
                    })
                processed.append((request['id'], units_to_process, blood_type))
            else:
                self.requests.append(request)  # Re-queue if failed
            current_time += self.time_quantum
        return processed

    def process_priority(self):
        print(Fore.CYAN + "\nProcessing Requests (Priority):" + Style.RESET_ALL)
        if not self.requests:
            print(Fore.YELLOW + "No requests to process." + Style.RESET_ALL)
            return
        # Create a copy to avoid modifying the original list during sorting
        requests_copy = self.requests.copy()
        requests_copy.sort(key=lambda x: x['priority'], reverse=True)
        processed = []
        print(f"Initial Request Queue: {[req['id'] for req in requests_copy]} (Priorities: {[req['priority'] for req in requests_copy]})")
        for request in requests_copy:
            print(f"Processing request {request['id']} for {request['blood_type']} ({request['units']} units, Priority: {request['priority']})")
            if self.inventory.request_blood(request['blood_type'], request['units']):
                processed.append((request['id'], request['units'], request['blood_type']))
            else:
                print(Fore.RED + f"❌ Failed to process request {request['id']} due to insufficient stock." + Style.RESET_ALL)
        print(f"Processed Requests: {[pid for pid, _, _ in processed]}")
        return processed

# Banker's Algorithm class
class BankersAlgorithm:
    def __init__(self, total_resources, blood_types):
        self.total_resources = total_resources
        self.available = total_resources.copy()
        self.blood_types = blood_types
        self.allocations = []
        self.max_demands = []
        self.processes = []

    def add_process(self, max_demand, allocation, process_id):
        self.max_demands.append(max_demand)
        self.allocations.append(allocation)
        self.processes.append(process_id)
        for i in range(len(self.available)):
            self.available[i] -= allocation[i]

    def is_safe(self):
        work = self.available[:]
        finish = [False] * len(self.allocations)
        sequence = []

        while len(sequence) < len(self.allocations):
            found = False
            for i in range(len(self.allocations)):
                if not finish[i]:
                    if all(self.max_demands[i][j] - self.allocations[i][j] <= work[j] for j in range(len(work))):
                        sequence.append(i)
                        finish[i] = True
                        for j in range(len(work)):
                            work[j] += self.allocations[i][j]
                        found = True
                        break
            if not found:
                return False, []
        return True, sequence

    def get_state(self):
        table = []
        for i, (max_d, alloc, proc_id) in enumerate(zip(self.max_demands, self.allocations, self.processes)):
            need = [max_d[j] - alloc[j] for j in range(len(max_d))]
            table.append([proc_id] + alloc + max_d + need)
        headers = ["Request ID"] + [f"Alloc {bt}" for bt in self.blood_types] + \
                  [f"Max {bt}" for bt in self.blood_types] + [f"Need {bt}" for bt in self.blood_types]
        return table, headers

# Visualizer class
class Visualizer:
    def __init__(self, inventory, scheduler, blood_types):
        self.inventory = inventory
        self.scheduler = scheduler
        self.blood_types = blood_types

    def visualize_bankers(self):
        print(Fore.CYAN + "\n=== Banker's Algorithm State ===" + Style.RESET_ALL)
        total_resources = [self.inventory.blood_stock[bt]['units'] for bt in self.blood_types]
        bankers = BankersAlgorithm(total_resources, self.blood_types)
        for req in self.scheduler.requests:
            max_demand = [0] * len(self.blood_types)
            allocation = [0] * len(self.blood_types)
            idx = self.blood_types.index(req['blood_type'])
            max_demand[idx] = req['units']
            bankers.add_process(max_demand, allocation, req['id'])
        safe, sequence = bankers.is_safe()
        table, headers = bankers.get_state()
        print("Resource Allocation Table:")
        print(tabulate(table, headers=headers, tablefmt="grid"))
        print("\nAvailable Resources:")
        available_table = [[bt, qty] for bt, qty in zip(self.blood_types, bankers.available)]
        print(tabulate(available_table, headers=["Blood Type", "Available"], tablefmt="grid"))
        if safe:
            print(Fore.GREEN + f"\n✅ Safe State! Sequence: {[bankers.processes[i] for i in sequence]}" + Style.RESET_ALL)
        else:
            print(Fore.RED + "\n❌ Unsafe State!" + Style.RESET_ALL)

    def visualize_priority(self):
        print(Fore.CYAN + "\n=== Priority Scheduling Queue ===" + Style.RESET_ALL)
        if not self.scheduler.requests:
            print(Fore.YELLOW + "No requests in queue." + Style.RESET_ALL)
            return
        sorted_requests = sorted(self.scheduler.requests, key=lambda x: x['priority'], reverse=True)
        table = [[req['id'], req['blood_type'], req['units'], req['priority']] 
                 for req in sorted_requests]
        print(tabulate(table, headers=["Request ID", "Blood Type", "Units", "Priority"], tablefmt="grid"))
        print("\nStock After Processing:")
        temp_requests = self.scheduler.requests.copy()
        self.scheduler.requests = sorted_requests
        processed = self.scheduler.process_priority()
        self.scheduler.requests = temp_requests
        stock_table = [[bt, self.inventory.blood_stock[bt]['units']] 
                       for bt in self.blood_types]
        print(tabulate(stock_table, headers=["Blood Type", "Units"], tablefmt="grid"))

    def visualize_round_robin(self):
        print(Fore.CYAN + "\n=== Round Robin Queue (Quantum: 10s) ===" + Style.RESET_ALL)
        if not self.scheduler.requests:
            print(Fore.YELLOW + "No requests in queue." + Style.RESET_ALL)
            return
        table = [[req['id'], req['blood_type'], req['units'], req['priority']] 
                 for req in self.scheduler.requests]
        print(tabulate(table, headers=["Request ID", "Blood Type", "Units", "Priority"], tablefmt="grid"))
        print("\nStock After Processing:")
        temp_requests = self.scheduler.requests.copy()
        processed = self.scheduler.process_round_robin()
        self.scheduler.requests = temp_requests
        stock_table = [[bt, self.inventory.blood_stock[bt]['units']] 
                       for bt in self.blood_types]
        print(tabulate(stock_table, headers=["Blood Type", "Units"], tablefmt="grid"))
        if processed:
            print("\nProcessed Requests:")
            proc_table = [[pid, units, bt] for pid, units, bt in processed]
            print(tabulate(proc_table, headers=["Request ID", "Units Processed", "Blood Type"], tablefmt="grid"))

# Main function
def main():
    admin_system = Admin()
    memory_manager = MemoryManager()
    inventory = BloodInventory(memory_manager)
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    scheduler = Scheduler(inventory)
    visualizer = Visualizer(inventory, scheduler, blood_types)

    while True:
        clear_screen()
        print_banner()

        print(Fore.CYAN + """
        1️⃣ View Blood Stock
        2️⃣ Donate Blood
        3️⃣ Register Donor
        4️⃣ Request Blood
        5️⃣ Admin Login
        6️⃣ Exit
        """ + Style.RESET_ALL)

        choice = input(Fore.YELLOW + "Enter your choice: " + Style.RESET_ALL)

        if choice == '1':
            inventory.view_stock()
        elif choice == '2':
            try:
                blood_type = input("Enter blood type (e.g., A+, O-): ").strip().upper()
                units = int(input("Enter number of units: "))
                inventory.donate_blood(blood_type, units)
            except ValueError:
                print(Fore.RED + "❌ Invalid input! Units must be a number." + Style.RESET_ALL)
        elif choice == '3':
            print(Fore.CYAN + "\n=== Donor Registration ===" + Style.RESET_ALL)
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            donor_system = Donor()
            donor_system.register(username, password)
        elif choice == '4':
            try:
                print(Fore.YELLOW + "Adding blood request..." + Style.RESET_ALL)
                blood_type = input("Enter blood type (e.g., A+, O-): ").strip().upper()
                units = int(input("Enter number of units: "))
                priority = int(input("Enter priority (1-10): "))
                if priority < 1 or priority > 10:
                    print(Fore.RED + "❌ Priority must be between 1 and 10!" + Style.RESET_ALL)
                else:
                    scheduler.add_request({'id': len(scheduler.requests) + 1, 'blood_type': blood_type, 'units': units, 'priority': priority})
            except ValueError:
                print(Fore.RED + "❌ Invalid input! Units and priority must be numbers." + Style.RESET_ALL)
        elif choice == '5':
            username = input("Enter admin username: ")
            password = input("Enter admin password: ")
            if admin_system.login(username, password):
                print(Fore.GREEN + "✅ Login successful!" + Style.RESET_ALL)
                while True:
                    print(Fore.CYAN + """
                    Admin Menu:
                    1. Process Requests (Round Robin)
                    2. Process Requests (Priority)
                    3. View Memory Status
                    4. Run Banker's Algorithm
                    5. Logout
                    6. Visualize Algorithms
                    """ + Style.RESET_ALL)
                    admin_choice = input(Fore.YELLOW + "Enter your choice: " + Style.RESET_ALL)
                    if admin_choice == '1':
                        scheduler.process_round_robin()
                    elif admin_choice == '2':
                        scheduler.process_priority()
                    elif admin_choice == '3':
                        memory_status = memory_manager.get_memory_status()
                        print(f"Memory Status: {memory_status}")
                    elif admin_choice == '4':
                        print(Fore.YELLOW + "Running Banker's Algorithm..." + Style.RESET_ALL)
                        total_resources = [inventory.blood_stock[bt]['units'] for bt in blood_types]
                        bankers = BankersAlgorithm(total_resources, blood_types)
                        for req in scheduler.requests:
                            max_demand = [0] * len(blood_types)
                            allocation = [0] * len(blood_types)
                            idx = blood_types.index(req['blood_type'])
                            max_demand[idx] = req['units']
                            bankers.add_process(max_demand, allocation, req['id'])
                        safe, sequence = bankers.is_safe()
                        if safe:
                            print(Fore.GREEN + f"✅ System is in a safe state! Sequence: {[bankers.processes[i] for i in sequence]}" + Style.RESET_ALL)
                        else:
                            print(Fore.RED + "❌ System is not in a safe state!" + Style.RESET_ALL)
                    elif admin_choice == '5':
                        print(Fore.YELLOW + "Logging out..." + Style.RESET_ALL)
                        break
                    elif admin_choice == '6':
                        print(Fore.CYAN + "\n=== Algorithm Visualizations ===" + Style.RESET_ALL)
                        visualizer.visualize_bankers()
                        visualizer.visualize_priority()
                        visualizer.visualize_round_robin()
                    else:
                        print(Fore.RED + "❌ Invalid choice!" + Style.RESET_ALL)
            else:
                print(Fore.RED + "❌ Invalid credentials!" + Style.RESET_ALL)
        elif choice == '6':
            print(Fore.YELLOW + "Exiting..." + Style.RESET_ALL)
            break
        else:
            print(Fore.RED + "❌ Invalid choice!" + Style.RESET_ALL)

        input(Fore.YELLOW + "\nPress Enter to continue..." + Style.RESET_ALL)

if __name__ == "__main__":
    main()