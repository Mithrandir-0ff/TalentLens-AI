import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict
load_dotenv()

API_KEY = os.getenv("RAPIDAPI_KEY")

API_HOST = "sofascore.p.rapidapi.com"





def calculate_age(timestamp):
    if not timestamp:
        return None
    
    try:
        if timestamp > 10000000000:
            timestamp = timestamp / 1000
        
        birth_year = datetime.fromtimestamp(timestamp).year
        current_year = datetime.now().year
        
        return current_year - birth_year
    except Exception as e:
        return None

def get_player_id(player_name: str):
    
    url = f"https://{API_HOST}/search"

    querystring = {"q": player_name,"type":"all","page":"0"}

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        

        results = data.get("results", [])
        
        players = [r for r in results if r.get("type") == "player"]

        if not players:
            print(f"Игрок {player_name} не найден.")
            return None
        
        best_match = players[0].get("entity", {})
        
        return {
            "id": best_match.get("id"),
            "name": best_match.get("name")
        }

    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return None
    
def get_player_stats(player_id: int):
    url = f"https://{API_HOST}/players/get-last-year-summary"
    querystring = {"playerId":f"{player_id}"}


    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
    
        summary = data.get('summary', [])
        tournaments_map = data.get('uniqueTournamentsMap', {})
        
        ratings = [float(item['value']) for item in summary if item.get('value')]
        last_10 = ratings[-10:]
        avg_rating = sum(last_10) / len(last_10) if last_10 else 0

        processed_matches = []
        for item in summary[-15:]:
           
            t_id = item.get('uniqueTournamentId')
            
            t_info = tournaments_map.get(str(t_id), {})
            t_name = t_info.get('name', 'Unknown Tournament')

            raw_ts = item.get('timestamp')
            if raw_ts:
                
                readable_date = datetime.fromtimestamp(raw_ts).strftime('%Y-%m-%d')
            else:
                readable_date = "Unknown Date"
            
            processed_matches.append({
                "timestamp": readable_date,
                "rating": float(item.get('value', 0)),
                "tournament": t_name
            })

        return {
            "recent_form_avg": round(avg_rating, 2),
            "recent_matches": processed_matches 
        }

    except Exception as e:
        return {"error": f"Ошибка получения статистики: {str(e)}"}

    except Exception as e:
        print(f"Ошибка получения статы: {e}")
        return None
    

def get_player_detailed_info(player_id: int):
        url = f"https://{API_HOST}/players/detail"
        querystring = {"playerId":f"{player_id}"}


        headers = {
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": API_HOST,
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()

            player = data.get('player', {})
            birth_ts = player.get('dateOfBirthTimestamp', 0)
            age = 0
            if birth_ts:
                age = 2026 - datetime.fromtimestamp(birth_ts).year

            return {
            "name": player.get('name'),
            "club": player.get('team', {}).get('name'),
            "country": player.get('country', {}).get('name'),
            "position": ", ".join(player.get('positionsDetailed', [])),
            "age": age,
            "height": player.get('height'),
            "foot": player.get('preferredFoot'),
            "market_value": player.get('proposedMarketValue'),
            "jersey": player.get('jerseyNumber')
            }

        except Exception as e:
            print(f"Ошибка при получении деталей игрока {player_id}: {e}")
            return None
        

def normalize_season(season_str: str) -> str:
  
    if not season_str or '/' not in season_str:
        return season_str
    
    parts = season_str.split('/')
    
    start_year = parts[0].strip()[-2:]
    end_year = parts[1].strip()[-2:]
    
    return f"{start_year}/{end_year}"

def get_full_player_scout_data(player_id: int, season_year: str = "25/26"):

    details = get_player_detailed_info(player_id)
    if not details:
        return None
    
    url = f"https://{API_HOST}/players/get-all-statistics"
    querystring = {"playerId":f"{player_id}"}


    headers = {
         "x-rapidapi-key": API_KEY,
           "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        seasons_data = data.get('seasons', [])
        all_stats_report = []

        for item in seasons_data:
            current_year_raw = item.get('year', '')
            current_year = normalize_season(str(current_year_raw))
            target_year = normalize_season(str(season_year))
            if current_year == target_year:
                
                st = item.get('statistics', {})
                tournament = item.get('uniqueTournament', {}).get('name', 'Unknown')
                
            
                full_stats = {
                    "tournament": tournament,
                    "appearances": st.get('appearances'),
                    "minutesPlayed": st.get('minutesPlayed'),
                    "rating": st.get('rating'),
                    "goals": st.get('goals'),
                    "assists": st.get('assists'),
                    "goalsAssistsSum": st.get('goalsAssistsSum'),
                    "expectedGoals": round(st.get('expectedGoals', 0), 2),
                    "expectedAssists": round(st.get('expectedAssists', 0), 2),
                    "shotsOnTarget": st.get('shotsOnTarget'),
                    "totalShots": st.get('totalShots'),
                    "shotsFromInsideTheBox": st.get('shotsFromInsideTheBox'),
                    "bigChancesCreated": st.get('bigChancesCreated'),
                    "bigChancesMissed": st.get('bigChancesMissed'),
                    "keyPasses": st.get('keyPasses'),
                    "passToAssist": st.get('passToAssist'),
                    "accuratePasses": st.get('accuratePasses'),
                    "totalPasses": st.get('totalPasses'),
                    "accuratePassesPercentage": st.get('accuratePassesPercentage'),
                    "accurateCrosses": st.get('accurateCrosses'),
                    "totalCross": st.get('totalCross'),
                    "accurateCrossesPercentage": st.get('accurateCrossesPercentage'),
                    "accurateLongBalls": st.get('accurateLongBalls'),
                    "totalLongBalls": st.get('totalLongBalls'),
                    "accurateLongBallsPercentage": st.get('accurateLongBallsPercentage'),
                    "successfulDribbles": st.get('successfulDribbles'),
                    "tackles": st.get('tackles'),
                    "interceptions": st.get('interceptions'),
                    "blockedShots": st.get('blockedShots'),
                    "dribbledPast": st.get('dribbledPast'),
                    "cleanSheet": st.get('cleanSheet'),
                    "goalsConceded": st.get('goalsConceded'),
                    "errorLeadToGoal": st.get('errorLeadToGoal'),
                    "yellowCards": st.get('yellowCards'),
                    "redCards": st.get('redCards'),
                    "saves": st.get('saves')
            }
                all_stats_report.append(full_stats)

        return {
            "profile": details,
            "season_stats": all_stats_report
        }

    except Exception as e:
        print(f"Ошибка выгрузки полной статистики {player_id}: {e}")
        return {"profile": details, "error": "Stats unavailable"}

def search_team_id(query: str):
    url = f"https://{API_HOST}/teams/search"
    querystring = {"name": query}


    headers = {
         "x-rapidapi-key": API_KEY,
           "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        teams = []
        for team in data.get('teams', []):
            teams.append({
                "name": team.get('name'),
                "id": team.get('id'),
                "country": team.get('country', {}).get('name')
            })
        return teams[:5] 
    except Exception as e:
        return f"Error searching team: {e}"

def get_team_player_stats(team_id: int, tournament_id: int, season_id: int):

    
    url_stats = f"https://{API_HOST}/teams/get-player-statistics"
    url_squad = f"https://{API_HOST}/teams/get-squad"
    
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }
    
    players_dict = {}
    
    try:
        response_stats = requests.get(
            url_stats,
            headers=headers,
            params={
                "teamId": str(team_id),
                "tournamentId": str(tournament_id),
                "seasonId": str(season_id),
                "type": "overall"
            }
        )
        
        if response_stats.status_code == 200:
            data_stats = response_stats.json()
            top_players = data_stats.get('topPlayers', {})
            
            for category, players_list in top_players.items():
                if isinstance(players_list, list):
                    for player_obj in players_list:
                        player = player_obj.get('player', {})
                        stats = player_obj.get('statistics', {})
                        player_id = player.get('id')
                        
                        if player_id and player_id not in players_dict:
                            players_dict[player_id] = {
                                "id": player_id,
                                "name": player.get('name'),
                                "position": player.get('position'),
                                "age": None,  
                                "rating": stats.get('rating'),
                                "nationality": player.get('country', {}).get('name'),
                                "appearances": stats.get('appearances'),
                                "goals": stats.get('goals', 0),
                                "assists": stats.get('assists', 0)
                            }
        
        response_squad = requests.get(
            url_squad,
            headers=headers,
            params={"teamId": str(team_id)}
        )
        
        if response_squad.status_code == 200:
            squad_data = response_squad.json()
            squad_players = squad_data.get('players', [])
            
            for player_obj in squad_players:
                player = player_obj.get('player', {})
                player_id = player.get('id')
                birth_ts = player.get('dateOfBirthTimestamp')
                
                if player_id in players_dict:
                    players_dict[player_id]['age'] = calculate_age(birth_ts)
                    if not players_dict[player_id].get('nationality'):
                        players_dict[player_id]['nationality'] = player.get('country', {}).get('name')
                
                elif player_id:
                    players_dict[player_id] = {
                        "id": player_id,
                        "name": player.get('name'),
                        "position": player.get('position'),
                        "age": calculate_age(birth_ts),
                        "rating": None,
                        "nationality": player.get('country', {}).get('name'),
                        "appearances": None,
                        "jersey": player.get('jerseyNumber')
                    }
        
        result = list(players_dict.values())
        result.sort(key=lambda x: x.get('rating') or 0, reverse=True)
        
        return result[:30]
        
    except Exception as e:
        return f"Error fetching team stats: {e}"

def search_tournament_id(query: str) -> List[Dict]:
    url = "https://sofascore.p.rapidapi.com/tournaments/search"
    
    querystring = {"name": query}
    
    headers = {
        "x-rapidapi-key": API_KEY, 
        "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        tournaments = []
        unique_tournaments = data.get("uniqueTournaments", [])
        
        for ut in unique_tournaments:
            tournaments.append({
                "name": ut.get("name"),
                "id": ut.get("id"),
                "category": ut.get("category", {}).get("name"),
                "current_season_id": ut.get("unqiueTournamentSeasonId") 
            })
        
        query_lower = query.lower()
        results = [t for t in tournaments if query_lower in t["name"].lower()]
        
        return results if results else "No tournaments found for this query."
        
    except Exception as e:
        return f"Error fetching tournaments: {str(e)}"


def get_tournament_seasons(tournament_id: int) -> List[Dict]:

    url = f"https://sofascore.p.rapidapi.com/tournaments/get-seasons"
    querystring = {"tournamentId": str(tournament_id)}

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        seasons = []
        for s in data.get("seasons", []):
            seasons.append({
                "season_id": s.get("id"),
                "year": s.get("year"),
                "name": s.get("name")
            })
        
        return seasons if seasons else "No seasons found for this tournament."
        
    except Exception as e:
        return f"Error fetching seasons: {str(e)}"