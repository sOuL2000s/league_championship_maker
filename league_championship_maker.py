import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# Classes for Team and Tournament
class Team:
    def __init__(self, name):
        self.name = name
        self.points = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.goals_scored = 0
        self.goals_conceded = 0

    @property
    def goal_difference(self):
        return self.goals_scored - self.goals_conceded

class Tournament:
    def __init__(self):
        self.teams = []
        self.matches = []

    def add_team(self, team_name):
        team = Team(team_name)
        self.teams.append(team)

    def generate_schedule(self):
        self.matches = []
        num_teams = len(self.teams)
        if num_teams % 2 == 1:
            self.teams.append(Team("BYE"))

        for round_number in range(2 * (num_teams - 1)):
            round_matches = []
            for i in range(num_teams // 2):
                home_team = self.teams[i]
                away_team = self.teams[num_teams - i - 1]
                if round_number % 2 == 0:
                    round_matches.append((home_team, away_team, None, None))  # (home team, away team, home score, away score)
                else:
                    round_matches.append((away_team, home_team, None, None))
            self.matches.extend(round_matches)
            self.teams.insert(1, self.teams.pop())

    def update_result(self, home_team_name, away_team_name, home_score, away_score):
        for match in self.matches:
            if match[0].name == home_team_name and match[1].name == away_team_name:
                match[2] = home_score
                match[3] = away_score
                self.calculate_points(match[0], match[1], home_score, away_score)
                break

    def calculate_points(self, home_team, away_team, home_score, away_score):
        home_team.goals_scored += home_score
        away_team.goals_scored += away_score
        home_team.goals_conceded += away_score
        away_team.goals_conceded += home_score

        if home_score > away_score:
            home_team.wins += 1
            home_team.points += 3
            away_team.losses += 1
        elif away_score > home_score:
            away_team.wins += 1
            away_team.points += 3
            home_team.losses += 1
        else:
            home_team.draws += 1
            away_team.draws += 1
            home_team.points += 1
            away_team.points += 1

    def save_data(self):
        data = {
            "teams": [{"name": team.name, "points": team.points, "wins": team.wins,
                       "draws": team.draws, "losses": team.losses, "goals_scored": team.goals_scored,
                       "goals_conceded": team.goals_conceded} for team in self.teams if team.name != "BYE"],
            "matches": [{"home": match[0].name, "away": match[1].name,
                         "home_score": match[2], "away_score": match[3]} for match in self.matches if "BYE" not in [match[0].name, match[1].name]]
        }
        with open("tournament_data.json", "w") as file:
            json.dump(data, file)

    def load_data(self):
        if os.path.exists("tournament_data.json"):
            with open("tournament_data.json", "r") as file:
                data = json.load(file)
                self.teams = [Team(team_data["name"]) for team_data in data["teams"]]
                for team, team_data in zip(self.teams, data["teams"]):
                    team.points = team_data["points"]
                    team.wins = team_data["wins"]
                    team.draws = team_data["draws"]
                    team.losses = team_data["losses"]
                    team.goals_scored = team_data["goals_scored"]
                    team.goals_conceded = team_data["goals_conceded"]
                self.matches = [(self.get_team_by_name(match["home"]),
                                 self.get_team_by_name(match["away"]),
                                 match["home_score"],
                                 match["away_score"]) for match in data["matches"]]

    def get_team_by_name(self, name):
        for team in self.teams:
            if team.name == name:
                return team
        return None

class LeagueChampionshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("League Championship Maker")
        self.tournament = Tournament()
        self.tournament.load_data()
        self.setup_ui()

    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')

        setup_tab = ttk.Frame(notebook)
        notebook.add(setup_tab, text="Setup Tournament")
        self.setup_tournament_ui(setup_tab)

        match_tab = ttk.Frame(notebook)
        notebook.add(match_tab, text="Fixtures")
        self.schedule_ui(match_tab)

        table_tab = ttk.Frame(notebook)
        notebook.add(table_tab, text="Points Table")
        self.points_table_ui(table_tab)

        delete_tab = ttk.Frame(notebook)
        notebook.add(delete_tab, text="Delete Data")
        self.delete_data_ui(delete_tab)

    def setup_tournament_ui(self, frame):
        tk.Label(frame, text="Enter Team Name").pack(pady=5)
        self.team_entry = tk.Entry(frame)
        self.team_entry.pack()

        tk.Button(frame, text="Add Team", command=self.add_team).pack(pady=10)
        tk.Button(frame, text="Generate Schedule", command=self.generate_schedule).pack(pady=10)

    def add_team(self):
        team_name = self.team_entry.get().strip()
        if team_name:
            self.tournament.add_team(team_name)
            messagebox.showinfo("Team Added", f"Team '{team_name}' added successfully!")
            self.team_entry.delete(0, tk.END)
            self.tournament.save_data()

    def generate_schedule(self):
        self.tournament.generate_schedule()
        messagebox.showinfo("Schedule Generated", "The match schedule has been generated!")
        self.update_schedule_table()
        self.tournament.save_data()

    def schedule_ui(self, frame):
        self.schedule_table = ttk.Treeview(frame, columns=("Home Team", "Away Team", "Home Score", "Away Score"), show="headings")
        for col in self.schedule_table["columns"]:
            self.schedule_table.heading(col, text=col)
        self.schedule_table.pack()
        self.update_schedule_table()

        tk.Button(frame, text="Update Match Result", command=self.update_match_result).pack(pady=10)

    def update_schedule_table(self):
        for row in self.schedule_table.get_children():
            self.schedule_table.delete(row)

        for match in self.tournament.matches:
            if match[0].name != "BYE" and match[1].name != "BYE":
                self.schedule_table.insert("", "end", values=(match[0].name, match[1].name, match[2] or "", match[3] or ""))

    def update_match_result(self):
        selected_item = self.schedule_table.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a match to update.")
            return

        match = self.schedule_table.item(selected_item)["values"]
        home_team, away_team = match[0], match[1]

        try:
            home_score = int(self.prompt_score(f"Enter score for {home_team}"))
            away_score = int(self.prompt_score(f"Enter score for {away_team}"))
        except ValueError:
            messagebox.showerror("Error", "Invalid score. Please enter a valid integer.")
            return

        self.tournament.update_result(home_team, away_team, home_score, away_score)
        self.update_points_table()
        self.update_schedule_table()
        self.tournament.save_data()

    def prompt_score(self, prompt_text):
        return tk.simpledialog.askstring("Input", prompt_text)

    def points_table_ui(self, frame):
        self.table = ttk.Treeview(frame, columns=("Team", "Points", "Wins", "Draws", "Losses", "Goals Scored", "Goals Conceded", "Goal Difference"), show="headings")
        for col in self.table["columns"]:
            self.table.heading(col, text=col)
        self.table.pack()
        self.update_points_table()

    def update_points_table(self):
        for row in self.table.get_children():
            self.table.delete(row)

        sorted_teams = sorted(self.tournament.teams, key=lambda x: (-x.points, x.goal_difference, x.goals_scored))
        for team in sorted_teams:
            self.table.insert("", "end", values=(team.name, team.points, team.wins, team.draws, team.losses, team.goals_scored, team.goals_conceded, team.goal_difference))

    def delete_data_ui(self, frame):
        tk.Button(frame, text="Delete All Data", command=self.delete_all_data).pack(pady=20)

    def delete_all_data(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete all tournament data?"):
            self.tournament = Tournament()
            self.tournament.save_data()
            self.update_schedule_table()
            self.update_points_table()
            messagebox.showinfo("Data Deleted", "All tournament data has been deleted.")

# Run the application
root = tk.Tk()
app = LeagueChampionshipGUI(root)
root.mainloop()
