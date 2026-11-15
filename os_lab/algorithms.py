
def parse_processes(raw_text):
    """Parse one process per line: PID, arrival time, burst time, priority."""
    processes = []

    for line_number, line in enumerate(raw_text.strip().splitlines(), start=1):
        if not line.strip():
            continue

        parts = [part.strip() for part in line.split(",")]

        if len(parts) != 4:
            raise ValueError(
                f"Line {line_number}: enter PID, arrival, burst, priority."
            )

        pid = parts[0]

        if not pid:
            raise ValueError(f"Line {line_number}: process ID is required.")

        try:
            arrival = int(parts[1])
            burst = int(parts[2])
            priority = int(parts[3])
        except ValueError:
            raise ValueError(
                f"Line {line_number}: arrival, burst and priority must be integers."
            )

        if arrival < 0 or burst <= 0:
            raise ValueError(
                f"Line {line_number}: arrival must be 0 or greater and burst must be positive."
            )

        if any(p["pid"] == pid for p in processes):
            raise ValueError(f"Duplicate process ID: {pid}")

        processes.append({
            "pid": pid,
            "arrival": arrival,
            "burst": burst,
            "priority": priority,
        })

    if not processes:
        raise ValueError("Enter at least one process.")

    if len(processes) > 20:
        raise ValueError("A maximum of 20 processes is allowed.")

    return processes


def cpu_scheduling(processes, algorithm, quantum=2):
    """Run a non-preemptive scheduler or Round Robin."""
    remaining = {p["pid"]: p["burst"] for p in processes}
    first_start = {}
    completion = {}
    gantt = []
    current_time = 0

    if algorithm == "RR":
        if quantum <= 0:
            raise ValueError("Time quantum must be greater than zero.")

        ordered = sorted(processes, key=lambda p: (p["arrival"], p["pid"]))
        ready = []
        index = 0

        while len(completion) < len(processes):
            while index < len(ordered) and ordered[index]["arrival"] <= current_time:
                ready.append(ordered[index])
                index += 1

            if not ready:
                next_arrival = ordered[index]["arrival"]
                if current_time < next_arrival:
                    gantt.append({
                        "pid": "Idle",
                        "start": current_time,
                        "end": next_arrival,
                    })
                    current_time = next_arrival
                continue

            process = ready.pop(0)
            pid = process["pid"]

            if pid not in first_start:
                first_start[pid] = current_time

            run_time = min(quantum, remaining[pid])
            start = current_time
            current_time += run_time
            remaining[pid] -= run_time

            gantt.append({
                "pid": pid,
                "start": start,
                "end": current_time,
            })

            while index < len(ordered) and ordered[index]["arrival"] <= current_time:
                ready.append(ordered[index])
                index += 1

            if remaining[pid] > 0:
                ready.append(process)
            else:
                completion[pid] = current_time

    else:
        pending = list(processes)

        while pending:
            available = [
                p for p in pending if p["arrival"] <= current_time
            ]

            if not available:
                next_arrival = min(p["arrival"] for p in pending)

                if current_time < next_arrival:
                    gantt.append({
                        "pid": "Idle",
                        "start": current_time,
                        "end": next_arrival,
                    })

                current_time = next_arrival
                available = [
                    p for p in pending if p["arrival"] <= current_time
                ]

            if algorithm == "FCFS":
                process = min(available, key=lambda p: (p["arrival"], processes.index(p)))
            elif algorithm == "SJF":
                process = min(
                    available,
                    key=lambda p: (p["burst"], p["arrival"], processes.index(p))
                )
            elif algorithm == "PRIORITY":
                process = min(
                    available,
                    key=lambda p: (p["priority"], p["arrival"], processes.index(p))
                )
            else:
                raise ValueError("Invalid CPU scheduling algorithm.")

            start = current_time
            first_start[process["pid"]] = start
            current_time += process["burst"]
            completion[process["pid"]] = current_time

            gantt.append({
                "pid": process["pid"],
                "start": start,
                "end": current_time,
            })

            pending.remove(process)

    results = []

    for process in processes:
        pid = process["pid"]
        turnaround = completion[pid] - process["arrival"]
        waiting = turnaround - process["burst"]
        response = first_start[pid] - process["arrival"]

        results.append({
            "pid": pid,
            "arrival": process["arrival"],
            "burst": process["burst"],
            "priority": process["priority"],
            "completion": completion[pid],
            "turnaround": turnaround,
            "waiting": waiting,
            "response": response,
        })

    count = len(results)

    return {
        "algorithm": algorithm,
        "gantt": gantt,
        "results": results,
        "average_waiting": round(
            sum(p["waiting"] for p in results) / count, 2
        ),
        "average_turnaround": round(
            sum(p["turnaround"] for p in results) / count, 2
        ),
    }


def banker_algorithm(data):
    """Check whether a resource allocation state is safe."""
    available = data["available"]
    allocation = data["allocation"]
    maximum = data["maximum"]

    if not isinstance(available, list) or not isinstance(allocation, list) or not isinstance(maximum, list):
        raise ValueError("Available, allocation and maximum must be JSON arrays.")

    if not allocation or len(allocation) != len(maximum):
        raise ValueError("Allocation and maximum must contain the same non-zero number of processes.")

    resource_count = len(available)

    if resource_count == 0 or resource_count > 10:
        raise ValueError("Provide between 1 and 10 resource types.")

    if len(allocation) > 20:
        raise ValueError("A maximum of 20 processes is allowed.")

    for matrix in (allocation, maximum):
        if any(not isinstance(row, list) or len(row) != resource_count for row in matrix):
            raise ValueError("Every matrix row must have one value per resource type.")

    values = [available]
    values.extend(allocation)
    values.extend(maximum)

    for row in values:
        for value in row:
            if type(value) is not int or value < 0:
                raise ValueError("Resource values must be non-negative integers.")

    for i in range(len(allocation)):
        for j in range(resource_count):
            if allocation[i][j] > maximum[i][j]:
                raise ValueError("Allocation cannot exceed maximum demand.")

    need = [
        [maximum[i][j] - allocation[i][j] for j in range(resource_count)]
        for i in range(len(allocation))
    ]

    work = available[:]
    finished = [False] * len(allocation)
    safe_sequence = []

    while len(safe_sequence) < len(allocation):
        found = False

        for i in range(len(allocation)):
            if finished[i]:
                continue

            if all(need[i][j] <= work[j] for j in range(resource_count)):
                work = [
                    work[j] + allocation[i][j]
                    for j in range(resource_count)
                ]
                finished[i] = True
                safe_sequence.append(f"P{i}")
                found = True

        if not found:
            break

    return {
        "safe": all(finished),
        "sequence": safe_sequence,
        "need": need,
        "available": available,
    }


def producer_consumer_simulation(capacity, operations):
    """Simulate bounded-buffer producer and consumer operations."""
    if capacity < 1 or capacity > 20:
        raise ValueError("Buffer capacity must be between 1 and 20.")

    buffer = []
    log = []

    for step, operation in enumerate(operations, start=1):
        operation = operation.strip()

        if operation.upper() == "C":
            if not buffer:
                status = "Blocked: buffer is empty. Consumer cannot consume."
            else:
                item = buffer.pop(0)
                status = f"Consumed item {item}."

        elif operation.upper().startswith("P:"):
            item = operation[2:].strip()

            if not item:
                raise ValueError(f"Operation {step}: producer item is missing.")

            if len(buffer) >= capacity:
                status = "Blocked: buffer is full. Producer cannot produce."
            else:
                buffer.append(item)
                status = f"Produced item {item}."

        else:
            raise ValueError(
                f"Operation {step}: use P:item to produce or C to consume."
            )

        log.append({
            "step": step,
            "operation": operation,
            "status": status,
            "buffer": buffer[:],
            "count": len(buffer),
        })

    return {
        "capacity": capacity,
        "log": log,
        "final_buffer": buffer,
    }
