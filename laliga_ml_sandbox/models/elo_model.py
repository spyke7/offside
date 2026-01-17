class EloModel:
    def __init__(self, k_factor=20, initial_rating=1500):
        self.k = k_factor
        self.initial_rating = initial_rating
        self.ratings = {}

    def get_rating(self, team):
        return self.ratings.get(team, self.initial_rating)

    def expected_score(self, rating_a, rating_b):
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update(self, home_team, away_team, home_goals, away_goals):
        ra = self.get_rating(home_team)
        rb = self.get_rating(away_team)

        ea = self.expected_score(ra, rb)
        eb = self.expected_score(rb, ra)

        if home_goals > away_goals:
            sa, sb = 1, 0
        elif home_goals < away_goals:
            sa, sb = 0, 1
        else:
            sa = sb = 0.5

        self.ratings[home_team] = ra + self.k * (sa - ea)
        self.ratings[away_team] = rb + self.k * (sb - eb)

    def get_diff(self, home_team, away_team):
        return self.get_rating(home_team) - self.get_rating(away_team)
