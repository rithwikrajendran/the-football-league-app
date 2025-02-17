import streamlit as st
import pandas as pd

# Load data from an Excel file
@st.cache_data(ttl=30)
def load_data(file_path):
    """
    Load data from an Excel file. Cache it with a TTL to refresh periodically.
    """
    data = pd.read_excel(file_path)
    return data

def compute_player_stats(df):
    """
    Create the league table
    """
    df = df.fillna('None')
    df['Home Goals'] = df['Result'].apply(lambda x: int(x.split('-')[0]))
    df['Away Goals'] = df['Result'].apply(lambda x: int(x.split('-')[-1]))
    df['Home Captain'] = df['Captains'].apply(lambda x: x.split(', ')[0] if x is not 'None' else 'None')
    df['Away Captain'] = df['Captains'].apply(lambda x: x.split(', ')[-1] if x is not 'None' else 'None')

    df = df.drop(
        labels=['Result', 'Captains'], axis=1
    )
    total_matches = len(df)
    # Split home and away teams and explode rows for individual players
    df_home = df[['Matchday', 'Home Team', 'Home Goals', 'Away Goals', 'Man of the Match', 'Home Captain']].copy()
    df_home['player'] = df_home['Home Team'].str.split(', ')
    df_home = df_home.explode('player')
    df_home['team'] = 'home'
    
    df_away = df[['Matchday', 'Away Team', 'Home Goals', 'Away Goals', 'Man of the Match', 'Away Captain']].copy()
    df_away['player'] = df_away['Away Team'].str.split(', ')
    df_away = df_away.explode('player')
    df_away['team'] = 'away'
    
    # Concatenate both DataFrames
    player_data = pd.concat([df_home, df_away], ignore_index=True)
    
    # Define functions to calculate each metric
    def calc_points(row):
        if row['team'] == 'home':
            if row['Home Goals'] > row['Away Goals']:
                return 3
            elif row['Home Goals'] == row['Away Goals']:
                return 1
            else:
                return 0
        else:
            if row['Away Goals'] > row['Home Goals']:
                return 3
            elif row['Away Goals'] == row['Home Goals']:
                return 1
            else:
                return 0
    
    def calc_win(row):
        if row['team'] == 'home' and row['Home Goals'] > row['Away Goals']:
            return 1
        elif row['team'] == 'away' and row['Away Goals'] > row['Home Goals']:
            return 1
        else:
            return 0
    
    def calc_draw(row):
        return 1 if row['Home Goals'] == row['Away Goals'] else 0
    
    def calc_loss(row):
        if row['team'] == 'home' and row['Home Goals'] < row['Away Goals']:
            return 1
        elif row['team'] == 'away' and row['Away Goals'] < row['Home Goals']:
            return 1
        else:
            return 0
    
    def calc_goals_scored(row):
        return row['Home Goals'] if row['team'] == 'home' else row['Away Goals']
    
    def calc_goals_conceded(row):
        return row['Away Goals'] if row['team'] == 'home' else row['Home Goals']
    
    def calc_motm(row):
        return 1 if row['player'] == row['Man of the Match'] else 0
    
    # Apply calculations
    player_data['points'] = player_data.apply(calc_points, axis=1)
    player_data['win'] = player_data.apply(calc_win, axis=1)
    player_data['draw'] = player_data.apply(calc_draw, axis=1)
    player_data['loss'] = player_data.apply(calc_loss, axis=1)
    player_data['goals_scored'] = player_data.apply(calc_goals_scored, axis=1)
    player_data['goals_conceded'] = player_data.apply(calc_goals_conceded, axis=1)
    player_data['motm_won'] = player_data.apply(calc_motm, axis=1)
    
    # Group by player and compute aggregates
    player_stats = player_data.groupby('player').agg(
        matches_played=('Matchday', 'nunique'),
        wins=('win', 'sum'),
        draws=('draw', 'sum'),
        losses=('loss', 'sum'),
        goals_scored=('goals_scored', 'sum'),
        goals_conceded=('goals_conceded', 'sum'),
        points=('points', 'sum'),
        motm=('motm_won', 'sum')
    ).reset_index()
    
    # Calculate goal_difference and other metrics
    player_stats['Goal Difference'] = player_stats['goals_scored'] - player_stats['goals_conceded']
    player_stats['PPG'] = round(player_stats['points'] / player_stats['matches_played'], 3)
    player_stats['Win %'] = round((player_stats['wins'] / player_stats['matches_played']) * 100, 3)
    player_stats['Qualify Status'] = player_stats['matches_played'].apply(
        lambda x: "Q" if x/total_matches >= 0.4 else "N"
    )
    
    player_stats = player_stats.sort_values(
        by=['Qualify Status', 'PPG', 'Goal Difference', 'goals_scored', 'Win %', 'motm'], 
        ascending=[False, False, False, False, False, False]
    ).reset_index()
    
    player_stats = player_stats.rename(
        mapper={
            'player': 'Player',
            'matches_played': 'Played',
            'wins': 'Won',
            'draws': 'Drawn',
            'losses': 'Lost',
            'points': 'Points',
            'goals_scored': 'GF',
            'goals_conceded': 'GA',
            'Goal Difference': 'GD',
            'motm': 'Man of the Match'
        },
        axis=1
    )
    
    return player_stats[[
        'Player', 'Played', 'Won', 'Drawn', 'Lost', 'Points', 'GF', 'GA', 'GD', 'PPG', 'Win %', 'Man of the Match', 'Qualify Status'
    ]]

def main():
    st.title("The Football League - 2024 - League Table")

    # File path to the Excel file
    excel_file = "footy_stats_24_25.xlsx"  # Replace this with the path to your Excel file

    # Load the input data
    ip_data = load_data(excel_file)

    # Get the league table
    data = compute_player_stats(ip_data)
    
    # Display the filtered data
    st.dataframe(data)


if __name__ == "__main__":
    main()
