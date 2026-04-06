class Data:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Data, cls).__new__(cls)
            # Initialize variables ONLY once
            cls._instance.starting_hp = 150
            cls._instance.current_hp = cls._instance.starting_hp
            cls._instance.starting_cash = 650
            cls._instance.current_cash = cls._instance.starting_cash
            cls._instance.path_points = [
                (0,168), (513,418), (611,184), (1358,350), (709,425), (700, 586), (758, 1080)
            ]
        return cls._instance

    def update_hp(self, dmg):
        self.current_hp -= dmg