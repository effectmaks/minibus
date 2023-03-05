class Age:
    def __init__(self):
        self.a = 0


class Javatpoint:
    def __init__(self):
        self._list_age = Age()

    @property
    def list_age(self):
        return self._list_age.a

    @list_age.setter
    def list_age(self, x):
        self._list_age.a = x


if __name__ == '__main__':
    John = Javatpoint()
    John.list_age = 25
    print(John.list_age)