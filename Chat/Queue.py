class Queue:

    def __init__(self):
        self.queue = []

    # Add an element
    def enqueue(self, item):
        self.queue.append(item)

    # Remove an element
    def dequeue(self):
        if self.has_next():
            return self.queue.pop(0)
        return None

    # check if next element exists
    def has_next(self):
        return len(self.queue) > 0

    def __contains__(self, item):
        return item in self.queue

    # Display the queue
    def display(self):
        return self.queue
