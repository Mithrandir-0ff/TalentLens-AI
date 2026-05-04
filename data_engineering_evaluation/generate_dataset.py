import json
import random
from itertools import product
random.seed(98)
scenarios = [
    "player_analysis",
    "criteria_search",
    "club_search",
    "stats_search",
    "comparison"
]

positions = ["Goalkeeper", "Defender", "Midfielder", "Forward"]

leagues = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]

complexity_levels = ["simple", "medium", "complex"]

age_groups = ["youth", "mid", "experienced"]

players_data = {
    "Pedri": {
        "position": "Midfielder",
        "league": "La Liga",
        "club": "Barcelona",
        "age_group": "mid"
    },
    "Yamal": {
        "position": "Forward",
        "league": "La Liga",
        "club": "Barcelona",
        "age_group": "youth"
    },
    "Raphinha": {
        "position": "Forward",
        "league": "La Liga",
        "club": "Barcelona",
        "age_group": "mid"
    },
    "Fermin": {
        "position": "Midfielder",
        "league": "La Liga",
        "club": "Barcelona",
        "age_group": "youth"
    },
    "Cubarsi": {
        "position": "Defender",
        "league": "La Liga",
        "club": "Barcelona",
        "age_group": "youth"
    },
    "Bruno Fernandes": {
        "position": "Midfielder",
        "league": "Premier League",
        "club": "Manchester United",
        "age_group": "experienced"
    },
    "Saliba": {
        "position": "Defender",
        "league": "Premier League",
        "club": "Arsenal",
        "age_group": "mid"
    },
    "Senesi": {
        "position": "Defender",
        "league": "Premier League",
        "club": "Bournemouth",
        "age_group": "mid"
    },

    "Alisson": {
        "position": "Goalkeeper",
        "league": "Premier League",
        "club": "Liverpool",
        "age_group": "experienced"
    },
    "Alvarez": {
        "position": "Forward",
        "league": "La Liga",
        "club": "Atletico Madrid",
        "age_group": "mid"
    },
    "Ryerson": {
        "position": "Defender",
        "league": "Bundesliga",
        "club": "Borussia Dortmund",
        "age_group": "mid"
    },
    "Safonov": {
        "position": "Goalkeeper",
        "league": "Ligue 1",
        "club": "PSG",
        "age_group": "mid"
    },
    "Bastoni": {
        "position": "Defender",
        "league": "Serie A",
        "club": "Inter Milan",
        "age_group": "mid"
    },
    "Caicedo": {
        "position": "Midfielder",
        "league": "Premier League",
        "club": "Chelsea",
        "age_group": "mid"
    },
    "Haaland": {
        "position": "Forward",
        "league": "Premier League",
        "club": "Manchester City",
        "age_group": "mid"
    },
    "Kane": {
        "position": "Forward",
        "league": "Bundesliga",
        "club": "Bayern Munich",
        "age_group": "experienced"
    },
    "Karl": {
        "position": "Midfielder",
        "league": "Bundesliga",
        "club": "Bayern Munich",
        "age_group": "youth"
    },
    "Modric": {
        "position": "Midfielder",
        "league": "Serie A",
        "club": "AC Milan",
        "age_group": "experienced"
    },
    "Vitinha": {
        "position": "Midfielder",
        "league": "Ligue 1",
        "club": "PSG",
        "age_group": "mid"
    },
    "Mainoo": {
        "position": "Midfielder",
        "league": "Premier League",
        "club": "Manchester United",
        "age_group": "youth"
    },
    "Ngumoha": {
        "position": "Forward",
        "league": "Premier League",
        "club": "Liverpool",
        "age_group": "youth"
    },
}
clubs = {
    "Premier League": ["Manchester City", "Arsenal", "Manchester United", "Liverpool", "Bournemouth"],
    "La Liga": ["Barcelona", "Real Madrid", "Atletico Madrid"],
    "Bundesliga": ["Bayern Munich", "Borussia Dortmund", "Bayer Leverkusen"],
    "Serie A": ["Inter Milan", "AC Milan", "Juventus", "Napoli"],
    "Ligue 1": ["PSG", "Monaco", "Marsellie"]
}

seasons = ["24/25", "25/26"]

stats_criteria = [
    "more than 10 goals per season",
    "more than 9 assists per season",
    "more than 3 set-piece goals",
    "pass accuracy above 85%",
    "rating above 7.5 per season",
    "more than 50 dribbles per season",
    "more than 100 tackles per season",
    "xG above 8 per season"
]

target_counts = {
    "player_analysis": 25,
    "criteria_search": 32,
    "club_search": 25,
    "stats_search": 20,
    "comparison": 12
}


templates = {
    "player_analysis": [
        "Analyze {player} for the {season} season",
        "Give a scouting report for player {player}",
        "Evaluate the form and statistics of {player} for {season}",
        "Provide a full analysis of player {player}",
    ],
    "criteria_search": [
        "Find the best {position} from {league}",
        "Find a young {position} under 23 from {league}",
        "Recommend a {position} for transfer from {league}",
        "Find an experienced {position} from {league}"
    ],
    "club_search": [
        "Who is the best {position} at {club}?",
        "Find the strongest {position} in {club} squad",
        "Evaluate the best {position} from {club}",
        "Recommend a {position} from {club} for transfer",
    ],
    "stats_search": [
        "Find a {position} from {league} with {stats}",
        "Find a {position} in {league} showing {stats}",
        "Recommend a {position} from {league} who has {stats}",
    ],
    "comparison": [
        "Compare {player1} with {player2}",
        "Compare {player1} with {player2} as a {position}",
        "Compare {player1} and {player2} from {league}"
]
}

def get_expected_tools(scenario: str, complexity: str) -> list:

    base = ["fetch_scouting"]

    if scenario == "player_analysis":
        return base + [
            "get_player_id_tool",
            "get_player_full_scout_data_tool"
        ]
    
    if scenario == "criteria_search":
        return base + [
            "search_tournament_id_tool",
            "get_tournament_seasons_tool",
            "get_team_player_stats_tool",
            "get_player_full_scout_data_tool"
        ]
    
    if scenario == "club_search":
        return base + [
            "search_team_id_tool",
            "search_tournament_id_tool",
            "get_tournament_seasons_tool",
            "get_team_player_stats_tool",
            "get_player_full_scout_data_tool"
        ]
    
    if scenario == "stats_search":
        return base + [
            "search_tournament_id_tool",
            "get_tournament_seasons_tool",
            "get_team_player_stats_tool",
            "get_player_full_scout_data_tool"
        ]
    
    if scenario == "comparison":
        return base + [
            "get_player_id_tool",
            "get_player_full_scout_data_tool",
            "get_player_full_scout_data_tool"
        ]
    
    return base

def is_valid(example: dict) -> bool:

    if len(example["query"].split()) < 5:
        return False
    
    if not example["expected_tools"]:
        return False
    
    if not example["query"]:
        return False
    
    return True

def generate_dataset() -> list:

    examples = []
    idx = 1

    for scenario, target in target_counts.items():
        count = 0
        attempts = 0

        while count < target and attempts < 2000:
            attempts += 1

            complexity = random.choice(complexity_levels)

            template = random.choice(templates[scenario])


            if scenario == "player_analysis":

                player = random.choice(list(players_data.keys()))
                player_info = players_data[player]

                query = template.format(
                    player=player,
                    season=random.choice(seasons)
                )

                position = player_info["position"]
                league = player_info["league"]
                age_group = player_info["age_group"]


            elif scenario == "comparison":

                players_list = list(players_data.keys())
                player1 = random.choice(players_list)

                same_position_players = [
                    p for p in players_data
                    if players_data[p]["position"] == players_data[player1]["position"]
                    and p != player1
                ]

                if not same_position_players:
                    continue

                player2 = random.choice(same_position_players)

                position = players_data[player1]["position"]
                league = players_data[player1]["league"]
                age_group = players_data[player1]["age_group"]

                query = template.format(
                    player1=player1,
                    player2=player2,
                    position=position,
                    league=league
                )

            elif scenario == "club_search":

                league = random.choice(leagues)
                club = random.choice(clubs[league])
                position = random.choice(positions)
                age_group = random.choice(age_groups)

                query = template.format(
                    position=position,
                    club=club
                )

            elif scenario == "criteria_search":

                league = random.choice(leagues)
                position = random.choice(positions)
                age_group = random.choice(age_groups)

                query = template.format(
                    position=position,
                    league=league
                )

            elif scenario == "stats_search":

                league = random.choice(leagues)
                position = random.choice(positions)
                age_group = random.choice(age_groups)

                query = template.format(
                    position=position,
                    league=league,
                    stats=random.choice(stats_criteria)
                )

            else:
                continue

            example = {
                "id": idx,
                "query": query,
                "scenario": scenario,
                "complexity": complexity,
                "position": position,
                "league": league,
                "age_group": age_group,
                "expected_tools": get_expected_tools(scenario, complexity),
                "is_valid": True
            }

            if not is_valid(example):
                continue

            examples.append(example)
            idx += 1
            count += 1

    return examples

if __name__ == '__main__':
    
    print('Генерируем датасет')

    dataset = generate_dataset()

    queries = [e["query"] for e in dataset]
    unique_queries = list(set(queries))
    duplicates = len(queries) - len(unique_queries)
    print(f"Всего примеров: {len(dataset)}")
    if duplicates > 0:
        print(f"Количество дубликатов: {duplicates}, удаляем")
        seen = set()
        clean_dataset = []
        for e in dataset:
            if e["query"] not in seen:
                seen.add(e["query"])
                clean_dataset.append(e)
        dataset = clean_dataset

    print("Статистика:")
    print(f"Всего примеров(после удаления дубликатов): {len(dataset)}")
    print(f"Удалено дубликатов: {duplicates}")

    print("Распределение по сценариям:")
    for scenario in scenarios:
        count = len([e for e in dataset if e["scenario"] == scenario])
        percent = round(count / len(dataset) * 100, 1)
        print(f" {scenario}: {count} ({percent}%)")

    print("Распределение по лигам")
    for league in leagues:
        count = len([e for e in dataset if e["league"] == league])
        percent = round(count / len(dataset) * 100, 1)
        print(f" {league}: {count} ({percent}%)")

    print("Распределение по сложности:")
    for level in complexity_levels:
        count = len([e for e in dataset if e["complexity"] == level])
        percent = round(count / len(dataset) * 100, 1)
        print(f" {level}: {count} ({percent}%)")

    print(f"Распределение по позициям:")
    for position in positions:
        count = len([e for e in dataset if e["position"] == position])
        percent = round(count / len(dataset) * 100, 1)
        print(f"  {position}: {count} ({percent}%)")

    print(f"Распределение по возрастным группам:")
    for age in age_groups:
        count = len([e for e in dataset if e["age_group"] == age])
        percent = round(count / len(dataset) * 100, 1)
        print(f"  {age}: {count} ({percent}%)")

    output = {
        "meta": {
            "total": len(dataset),
            "duplicates_removed": duplicates,
            "scenarios": target_counts,
        },
        "examples": dataset
    }

    with open("data_engineering_evaluation/dataset.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Датасет сохранен в ata_engineering_evaluation/dataset.json")