import lymph


class TaskService(lymph.Interface):
    @lymph.task()
    def sum(self, numbers=None):
        print "got", numbers
        print "sum", sum(numbers)

    @lymph.rpc()
    def sum_numbers(self, numbers):
        self.sum.apply(numbers=numbers)
