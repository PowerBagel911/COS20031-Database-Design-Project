import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import random
from archery_app.database import get_connection, get_archers, get_archer_statistics

def calculate_win_probability(archer1_stats, archer2_stats):
    """
    Calculate a simple win probability based on average scores.
    Returns probability (0-1) for archer1 winning against archer2.
    """
    # Simple calculation based on average scores
    # You could make this more sophisticated with more factors
    if not archer1_stats["ScoreStats"]["AverageScore"] or not archer2_stats["ScoreStats"]["AverageScore"]:
        return 0.5  # Default to 50% if no data
    
    avg1 = float(archer1_stats["ScoreStats"]["AverageScore"] or 0)
    avg2 = float(archer2_stats["ScoreStats"]["AverageScore"] or 0)
    
    if avg1 + avg2 == 0:
        return 0.5
    
    # Simple probability based on average scores
    prob = avg1 / (avg1 + avg2)
    
    # Add some randomness to make it interesting (optional)
    # We'll keep it mostly determined by scores but add a bit of unpredictability
    prob = prob * 0.8 + np.random.random() * 0.2
    
    return min(max(prob, 0.1), 0.9)  # Keep between 10-90% for interest

def format_percentage(value):
    """Format a decimal probability as a percentage string."""
    return f"{value * 100:.1f}%"

def calculate_odds(probability):
    """Convert a win probability to betting odds format."""
    if probability <= 0 or probability >= 1:
        return "N/A"  # Invalid probability
    
    # Calculate decimal odds (1/probability)
    decimal_odds = 1 / probability
    
    # Round to 2 decimal places
    return f"{decimal_odds:.2f}"

def display_archer_card(stats):
    """Display an archer's information and statistics in a card-like format."""
    if not stats:
        st.error("No data available for this archer.")
        return
    
    # Profile section
    st.subheader(stats["ArcherName"])
    st.write(f"**Age:** {stats['Age']} | **Gender:** {'Male' if stats['Gender'] == 'M' else 'Female'}")
    
    # Stats section
    if stats["ScoreStats"]["TotalScores"] > 0:
        st.write("### Score Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Score", f"{float(stats['ScoreStats']['AverageScore'] or 0):.1f}")
            st.metric("Total Scores", stats["ScoreStats"]["TotalScores"])
        with col2:
            st.metric("Highest Score", stats["ScoreStats"]["HighestScore"])
            if stats["PreferredEquipment"]:
                st.metric("Preferred Equipment", stats["PreferredEquipment"]["EquipmentType"])
        
        # Recent performance
        if stats["RecentScores"]:
            st.write("### Recent Scores")
            df = pd.DataFrame(stats["RecentScores"])
            df["Score %"] = df.apply(lambda x: f"{(x['TotalScore']/x['PossibleScore'])*100:.1f}%", axis=1)
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
            st.dataframe(df[["Date", "RoundName", "TotalScore", "Score %", "EquipmentType"]], 
                         hide_index=True, use_container_width=True)
    else:
        st.warning("This archer has no recorded scores yet.")

def create_comparison_chart(archer1_stats, archer2_stats):
    """Create a comparison chart between two archers."""
    # Create comparison metrics
    if (not archer1_stats["ScoreStats"]["AverageScore"] or 
        not archer2_stats["ScoreStats"]["AverageScore"]):
        st.warning("Not enough data to create comparison charts.")
        return
    
    # Create DataFrame for metrics comparison
    metrics = {
        "Metric": ["Average Score", "Highest Score", "Total Scores"],
        archer1_stats["ArcherName"]: [
            float(archer1_stats["ScoreStats"]["AverageScore"] or 0),
            int(archer1_stats["ScoreStats"]["HighestScore"] or 0),
            int(archer1_stats["ScoreStats"]["TotalScores"] or 0)
        ],
        archer2_stats["ArcherName"]: [
            float(archer2_stats["ScoreStats"]["AverageScore"] or 0),
            int(archer2_stats["ScoreStats"]["HighestScore"] or 0),
            int(archer2_stats["ScoreStats"]["TotalScores"] or 0)
        ]
    }
    
    df = pd.DataFrame(metrics)
    
    # Normalize values for better visualization
    df_plot = df.copy()
    for col in df.columns[1:]:
        max_val = df[col].max()
        if max_val > 0:
            df_plot[col] = df[col] / max_val
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Get archer names for better labels
    archer1_name = archer1_stats["ArcherName"].split()[-1]  # Just last name for brevity
    archer2_name = archer2_stats["ArcherName"].split()[-1]
    
    bar_width = 0.35
    index = np.arange(len(metrics["Metric"]))
    
    ax.bar(index - bar_width/2, df_plot[archer1_stats["ArcherName"]], bar_width, 
           label=archer1_name, color='#1f77b4')
    ax.bar(index + bar_width/2, df_plot[archer2_stats["ArcherName"]], bar_width, 
           label=archer2_name, color='#ff7f0e')
    
    # Add the actual values as text on top of the bars
    for i, v in enumerate(df[archer1_stats["ArcherName"]]):
        ax.text(i - bar_width/2, df_plot[archer1_stats["ArcherName"]][i] + 0.05, 
                f"{v:.1f}" if i == 0 else f"{int(v)}", ha='center')
    
    for i, v in enumerate(df[archer2_stats["ArcherName"]]):
        ax.text(i + bar_width/2, df_plot[archer2_stats["ArcherName"]][i] + 0.05, 
                f"{v:.1f}" if i == 0 else f"{int(v)}", ha='center')
    
    ax.set_xticks(index)
    ax.set_xticklabels(metrics["Metric"])
    ax.legend()
    ax.set_ylim(0, 1.2)  # Make room for text
    ax.set_title("Performance Comparison (Normalized)")
    ax.set_ylabel("Relative Performance")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Show plot
    st.pyplot(fig)
    
    # Add explanation
    st.caption("*Note: Values are normalized to make comparison easier. Actual values shown on top of bars.*")

def display_win_probability(prob_archer1, name1, name2):
    """Display a visual win probability gauge."""
    st.subheader("Match Win Probability")
    
    # Create columns for the probability display
    col1, col2, col3 = st.columns([2, 6, 2])
    
    with col1:
        st.write(f"**{name1.split()[-1]}**")
        st.write(f"**{format_percentage(prob_archer1)}**")
    
    with col2:
        # Create a progress bar to visualize the probability
        # Streamlit's progress bar goes from 0 to 100
        st.progress(prob_archer1)
    
    with col3:
        st.write(f"**{name2.split()[-1]}**")
        st.write(f"**{format_percentage(1 - prob_archer1)}**")
    
    # Add a disclaimer about the probability
    st.caption("*This probability is based on past performance and includes some randomness for unpredictability.*")

def display_betting_interface(archers_list, odds_list, mode="1v1"):
    """Display a front-end betting interface."""
    st.markdown("---")
    st.subheader("🎲 Betting Simulator")
    st.write("Place a virtual bet on your favorite archer!")
    
    # Add an explanation of how betting odds work
    with st.expander("How betting odds work"):
        st.markdown("""
        ### Understanding Betting Odds
        
        In betting terminology, the **odds** represent the potential payout if you win:
        
        - **Lower odds** (e.g., 1.50) mean higher chance of winning but smaller payout
        - **Higher odds** (e.g., 4.00) mean lower chance of winning but larger payout
        
        For example:
        - If you bet \$100 on odds of 1.50 and win, you get \$150 back (\$50 profit)
        - If you bet \$100 on odds of 4.00 and win, you get \$400 back (\$300 profit)
        
        The archer with the lowest odds is considered the favorite to win.
        """)
    
    # Initialize session state for bets if needed
    if "bet_amount" not in st.session_state:
        st.session_state.bet_amount = 100
    if "bet_placed" not in st.session_state:
        st.session_state.bet_placed = False
    if "selected_archer" not in st.session_state:
        st.session_state.selected_archer = None
    if "potential_winnings" not in st.session_state:
        st.session_state.potential_winnings = 0
    
    # Create betting form
    with st.form("betting_form"):
        # Create a more detailed betting options table first
        betting_data = []
        for i, archer in enumerate(archers_list):
            win_prob = 1 / float(odds_list[i])  # Convert odds back to probability
            betting_data.append({
                "Archer": archer["ArcherName"],
                "Odds": odds_list[i],
                "Win Probability": format_percentage(win_prob),
                "Payout per $100": f"${float(odds_list[i]) * 100:.0f}"
            })
        
        st.dataframe(
            pd.DataFrame(betting_data),
            hide_index=True,
            use_container_width=True
        )
        
        # Select archer to bet on
        selected_archer_idx = st.selectbox(
            "Select archer to bet on:",
            options=range(len(archers_list)),
            format_func=lambda i: f"{archers_list[i]['ArcherName']} (Odds: {odds_list[i]} - {betting_data[i]['Win Probability']} chance)"
        )
        
        # Bet amount slider
        bet_amount = st.slider("Bet Amount ($)", min_value=10, max_value=1000, value=st.session_state.bet_amount, step=10)
        
        # Calculate potential winnings
        odds_value = float(odds_list[selected_archer_idx])
        potential_winnings = bet_amount * odds_value
        
        # Display potential winnings calculation
        profit = potential_winnings - bet_amount
        # st.write(f"Potential Return: ${potential_winnings:.2f} (Stake + ${profit:.2f} profit)")
        
        # Submit button
        submitted = st.form_submit_button("Place Bet", type="primary")
        
        if submitted:
            st.session_state.bet_amount = bet_amount
            st.session_state.selected_archer = archers_list[selected_archer_idx]["ArcherName"]
            st.session_state.bet_odds = odds_list[selected_archer_idx]
            st.session_state.potential_winnings = potential_winnings
            st.session_state.bet_placed = True
    
    # Display bet confirmation outside the form if a bet was placed
    if st.session_state.bet_placed:
        st.success(f"Bet placed on {st.session_state.selected_archer} for ${st.session_state.bet_amount}. " 
                  f"Potential winnings: ${st.session_state.potential_winnings:.2f}")
        
        # Add a disclaimer
        st.caption("*This is a simulation only. No real money is involved.*")

def simulate_1v1_matchup(archer1_id, archer2_id):
    """Simulate a 1v1 matchup between two archers."""
    # Get detailed stats for both archers
    archer1_stats = get_archer_statistics(archer1_id)
    archer2_stats = get_archer_statistics(archer2_id)
    
    if not archer1_stats or not archer2_stats:
        st.error("Could not retrieve data for one or both archers.")
        return None, None
    
    # Calculate win probability
    prob_archer1 = calculate_win_probability(archer1_stats, archer2_stats)
    
    # Display the matchup header
    st.markdown("---")
    st.header(f"{archer1_stats['ArcherName']} vs {archer2_stats['ArcherName']}")
    st.write(f"*Simulated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}*")
    
    # Display win probability
    display_win_probability(prob_archer1, archer1_stats["ArcherName"], archer2_stats["ArcherName"])
    
    # Create comparison chart
    st.markdown("---")
    st.subheader("Performance Comparison")
    create_comparison_chart(archer1_stats, archer2_stats)
    
    # Display individual archer cards
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        display_archer_card(archer1_stats)
    
    with col2:
        display_archer_card(archer2_stats)
    
    # Calculate betting odds
    odds_archer1 = calculate_odds(prob_archer1)
    odds_archer2 = calculate_odds(1 - prob_archer1)
    
    # Setup for betting interface
    archers_list = [archer1_stats, archer2_stats]
    odds_list = [odds_archer1, odds_archer2]
    
    # Display betting interface
    display_betting_interface(archers_list, odds_list, mode="1v1")
    
    # Determine winner if bet is placed
    if st.session_state.bet_placed and st.button("Simulate Match Result", type="primary"):
        st.markdown("---")
        st.subheader("🏆 Match Result")
        
        # Simulate match result (using probability but with randomness)
        result = random.random()
        if result < prob_archer1:
            winner = archer1_stats
            loser = archer2_stats
            win_prob = prob_archer1
        else:
            winner = archer2_stats
            loser = archer1_stats
            win_prob = 1 - prob_archer1
        
        # Display result
        st.write(f"**Winner: {winner['ArcherName']}** with a {format_percentage(win_prob)} chance!")
        
        # Calculate a realistic score based on archers' average scores and add some randomness
        winner_avg = float(winner["ScoreStats"]["AverageScore"] or 300)
        loser_avg = float(loser["ScoreStats"]["AverageScore"] or 280)
        
        winner_score = int(winner_avg + random.uniform(-20, 20))
        loser_score = int(loser_avg + random.uniform(-30, 10))
        
        # Ensure winner's score is higher
        if winner_score <= loser_score:
            winner_score = loser_score + random.randint(1, 10)
        
        st.write(f"**Final Score:** {winner['ArcherName']}: {winner_score} | {loser['ArcherName']}: {loser_score}")
        
        # Display bet result if the user placed a bet
        if st.session_state.bet_placed:
            st.markdown("---")
            st.subheader("🎲 Betting Result")
            
            if st.session_state.selected_archer == winner["ArcherName"]:
                st.success(f"Congratulations! Your bet on {st.session_state.selected_archer} won! "
                          f"You would have won ${st.session_state.potential_winnings - st.session_state.bet_amount:.2f} profit.")
            else:
                st.error(f"Sorry! Your bet on {st.session_state.selected_archer} lost. "
                        f"You would have lost your ${st.session_state.bet_amount} stake.")
    
    return archer1_stats, archer2_stats

def simulate_tournament(archer_ids):
    """Simulate a 4-person competition where all archers shoot together."""
    if len(archer_ids) != 4:
        st.error("Tournament simulation requires exactly 4 archers.")
        return
    
    # Get stats for all archers
    archer_stats = []
    for archer_id in archer_ids:
        stats = get_archer_statistics(archer_id)
        if not stats:
            st.error(f"Could not retrieve data for archer ID {archer_id}.")
            return
        archer_stats.append(stats)
    
    # Display competition header
    st.markdown("---")
    st.header("🏆 4-Person Competition")
    st.write("All four archers will shoot in the same round and be ranked by final score.")
    
    # Calculate probabilities and odds for each archer
    win_probs = []
    odds_list = []
    
    # Calculate a simple win probability for each archer based on their average score
    total_avg_score = 0
    for archer in archer_stats:
        avg_score = float(archer["ScoreStats"]["AverageScore"] or 0)
        total_avg_score += avg_score
    
    # If no one has scores, assign equal probabilities
    if total_avg_score == 0:
        win_probs = [0.25, 0.25, 0.25, 0.25]
    else:
        # Calculate relative probabilities based on average scores
        for archer in archer_stats:
            avg_score = float(archer["ScoreStats"]["AverageScore"] or 0)
            # Add some randomness to make it interesting
            prob = (avg_score / total_avg_score) * 0.8 + (random.random() * 0.2 / 4)
            win_probs.append(prob)
        
        # Normalize probabilities to sum to 1
        prob_sum = sum(win_probs)
        win_probs = [p/prob_sum for p in win_probs]
    
    # Calculate odds for each archer
    for prob in win_probs:
        odds_list.append(calculate_odds(prob))
    
    # Create a table showing all archers and their odds
    competition_data = []
    for i, archer in enumerate(archer_stats):
        competition_data.append({
            "Archer": archer["ArcherName"],
            "Average Score": f"{float(archer['ScoreStats']['AverageScore'] or 0):.1f}",
            "Win Probability": f"{win_probs[i]*100:.1f}%",
            "Betting Odds": odds_list[i],
            "Payout per $100": f"${float(odds_list[i]) * 100:.0f}"
        })
    
    st.subheader("Competition Participants")
    
    # Add a note explaining the odds
    st.info("**Note:** Lower odds (e.g., 2.50) indicate a higher chance of winning but smaller payout. " 
            "Higher odds (e.g., 5.00) mean a lower chance of winning but larger payout if successful.")
    
    st.dataframe(
        pd.DataFrame(competition_data),
        hide_index=True,
        use_container_width=True
    )
    
    # ----- PRE-COMPETITION ANALYSIS -----
    st.markdown("## Pre-Competition Analysis")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Score Comparison", "Radar Analysis", "Historical Performance"])
    
    with tab1:
        # Create a bar chart comparing average scores
        fig, ax = plt.subplots(figsize=(10, 6))
        
        names = [a["ArcherName"].split()[-1] for a in archer_stats]  # Just last names for brevity
        avg_scores = [float(a["ScoreStats"]["AverageScore"] or 0) for a in archer_stats]
        high_scores = [int(a["ScoreStats"]["HighestScore"] or 0) for a in archer_stats]
        
        x = np.arange(len(names))
        width = 0.35
        
        avg_bars = ax.bar(x - width/2, avg_scores, width, label='Average Score', color='skyblue')
        high_bars = ax.bar(x + width/2, high_scores, width, label='Highest Score', color='orange')
        
        # Add the actual values as text on top of the bars
        for bar in avg_bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 5,
                    f'{height:.1f}', ha='center', fontweight='bold')
        
        for bar in high_bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 5,
                    f'{height}', ha='center', fontweight='bold')
        
        ax.set_ylabel('Score')
        ax.set_title('Average vs Highest Score Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(names)
        ax.legend()
        ax.set_ylim(0, max(max(avg_scores), max(high_scores)) * 1.15)  # Make room for text
        
        st.pyplot(fig)
        
        # Add a table with detailed statistics
        st.subheader("Detailed Statistics")
        detailed_stats = []
        for archer in archer_stats:
            score_stats = archer["ScoreStats"]
            if score_stats["TotalScores"] > 0:
                consistency = float(score_stats["HighestScore"] or 0) - float(score_stats["LowestScore"] or 0)
                avg_percent = float(score_stats["AverageScore"] or 0) / 360 * 100  # Assuming max possible is 360
            else:
                consistency = 0
                avg_percent = 0
                
            detailed_stats.append({
                "Archer": archer["ArcherName"],
                "Total Scores": int(score_stats["TotalScores"] or 0),
                "Average": f"{float(score_stats['AverageScore'] or 0):.1f}",
                "Highest": int(score_stats["HighestScore"] or 0),
                "Lowest": int(score_stats["LowestScore"] or 0),
                "Range": int(consistency),
                "Avg %": f"{avg_percent:.1f}%"
            })
        
        st.dataframe(
            pd.DataFrame(detailed_stats),
            hide_index=True,
            use_container_width=True
        )
    
    with tab2:
        # Create a radar chart to compare archers on multiple metrics
        st.subheader("Archer Capabilities Comparison")
        
        # Define the metrics for radar chart
        # Normalize all metrics to 0-100 scale for radar chart
        radar_data = []
        for i, archer in enumerate(archer_stats):
            score_stats = archer["ScoreStats"]
            
            # Calculate normalized metrics (0-100 scale)
            if score_stats["TotalScores"] > 0:
                # Avg score percentage (assuming 360 max)
                avg_score_pct = min(float(score_stats["AverageScore"] or 0) / 360 * 100, 100)
                
                # Experience (number of scores recorded, cap at 30 for 100%)
                experience = min(int(score_stats["TotalScores"] or 0) / 30 * 100, 100)
                
                # Consistency (inverse of range between high and low, smaller is better)
                score_range = float(score_stats["HighestScore"] or 0) - float(score_stats["LowestScore"] or 0)
                consistency = max(100 - (score_range / 50 * 100), 0)  # Assuming 50-point range is 0%
                
                # High score capability 
                high_score_cap = min(float(score_stats["HighestScore"] or 0) / 360 * 100, 100)
                
                # Recent form - average of recent scores compared to their average
                recent_form = 50  # Default to neutral
                if archer["RecentScores"]:
                    recent_avg = sum(s["TotalScore"] for s in archer["RecentScores"]) / len(archer["RecentScores"])
                    overall_avg = float(score_stats["AverageScore"] or 0)
                    if overall_avg > 0:
                        recent_form = min((recent_avg / overall_avg) * 50, 100)  # Scale so 100% = recent twice as good as average
            else:
                # Default values if no scores
                avg_score_pct = 0
                experience = 0
                consistency = 0
                high_score_cap = 0
                recent_form = 0
            
            radar_data.append({
                "Archer": archer["ArcherName"].split()[-1],  # Last name only for radar chart
                "Average": avg_score_pct,
                "Experience": experience,
                "Consistency": consistency,
                "High Score": high_score_cap,
                "Recent Form": recent_form
            })
        
        # Create radar chart with matplotlib
        categories = ['Average', 'Experience', 'Consistency', 'High Score', 'Recent Form']
        N = len(categories)
        
        # Create angle for each category
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Create subplot with polar projection for radar chart
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        
        # Draw one line per archer and fill area
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Different color for each archer
        for i, archer_data in enumerate(radar_data):
            values = [archer_data[cat] for cat in categories]
            values += values[:1]  # Close the loop
            
            ax.plot(angles, values, linewidth=2, linestyle='solid', label=archer_data["Archer"], color=colors[i])
            ax.fill(angles, values, alpha=0.1, color=colors[i])
        
        # Add category labels
        plt.xticks(angles[:-1], categories)
        
        # Add legend
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        
        # Add title
        plt.title('Archer Capabilities Radar Chart', size=15, y=1.1)
        
        st.pyplot(fig)
        
        # Add explanation
        st.write("""
        ### Radar Chart Explanation:
        
        - **Average**: Normalized average score (higher is better)
        - **Experience**: Based on number of recorded scores (higher = more experience)
        - **Consistency**: Inverse of the range between highest and lowest scores (higher = more consistent)
        - **High Score**: Normalized highest recorded score (higher is better)
        - **Recent Form**: Recent performance compared to overall average (higher = improving)
        """)
    
    with tab3:
        st.subheader("Recent Score Trends")
        
        # Create line graph of recent scores for each archer
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for i, archer in enumerate(archer_stats):
            if archer["RecentScores"]:
                scores = [s["TotalScore"] for s in reversed(archer["RecentScores"])]
                dates = [s["Date"] for s in reversed(archer["RecentScores"])]
                
                # Convert dates to string for x-axis if needed
                date_labels = [d.strftime("%m/%d") if hasattr(d, "strftime") else str(d) for d in dates]
                
                # Plot line
                ax.plot(range(len(scores)), scores, marker='o', label=archer["ArcherName"].split()[-1], linewidth=2)
                
                # Add score labels
                for j, score in enumerate(scores):
                    ax.text(j, score + 5, str(score), ha='center', fontsize=8)
            
        # Set labels and title
        ax.set_ylabel('Score')
        ax.set_title('Recent Score Trends')
        
        # Set x-axis ticks to match the number of scores
        max_scores = max([len(a["RecentScores"]) for a in archer_stats if a["RecentScores"]], default=0)
        if max_scores > 0:
            ax.set_xticks(range(max_scores))
            ax.set_xticklabels([f"Game {i+1}" for i in range(max_scores)])
        
        ax.legend()
        st.pyplot(fig)
        
        # Add a table showing the most recent score of each archer
        st.subheader("Most Recent Scores")
        recent_data = []
        for archer in archer_stats:
            if archer["RecentScores"]:
                most_recent = archer["RecentScores"][0]  # First one is most recent
                recent_data.append({
                    "Archer": archer["ArcherName"],
                    "Most Recent Score": most_recent["TotalScore"],
                    "Date": most_recent["Date"].strftime("%Y-%m-%d") if hasattr(most_recent["Date"], "strftime") else most_recent["Date"],
                    "Round": most_recent["RoundName"],
                    "Equipment": most_recent["EquipmentType"]
                })
            else:
                recent_data.append({
                    "Archer": archer["ArcherName"],
                    "Most Recent Score": "No data",
                    "Date": "N/A",
                    "Round": "N/A",
                    "Equipment": "N/A"
                })
        
        st.dataframe(
            pd.DataFrame(recent_data),
            hide_index=True,
            use_container_width=True
        )
    
    # Display betting interface
    display_betting_interface(archer_stats, odds_list, mode="tournament")
    
    # Add a quick prediction feature
    # st.markdown("---")
    # st.subheader("🔮 Quick Prediction")

def get_ordinal_suffix(n):
    """Return the ordinal suffix for a number (1st, 2nd, 3rd, etc.)"""
    if 11 <= (n % 100) <= 13:
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')

def display_live_competition_view():
    st.header("🎯 Archer Matchup Simulator")
    st.write("Select a mode and choose archers to simulate a matchup or tournament.")
    
    # Mode selection (1v1 or Tournament)
    mode = st.radio(
        "Select Mode:",
        ["1v1 Matchup", "4-Person Competition"],
        horizontal=True
    )
    
    # Get list of archers
    archers = get_archers()
    
    if not archers:
        st.error("No archers found in the database. Please add archers first.")
        return
    
    # Reset bet status when changing mode
    if "prev_mode" not in st.session_state or st.session_state.prev_mode != mode:
        st.session_state.bet_placed = False
        st.session_state.prev_mode = mode
    
    if mode == "1v1 Matchup":
        # Create selection dropdowns for 1v1 mode
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("First Archer")
            archer1_id = st.selectbox(
                "Select first archer",
                options=[a["ArcherID"] for a in archers],
                format_func=lambda x: next((a["ArcherName"] for a in archers if a["ArcherID"] == x), ""),
                key="archer1"
            )
        
        with col2:
            st.subheader("Second Archer")
            # Filter out the first archer from the second dropdown
            filtered_archers = [a for a in archers if a["ArcherID"] != archer1_id]
            archer2_id = st.selectbox(
                "Select second archer",
                options=[a["ArcherID"] for a in filtered_archers],
                format_func=lambda x: next((a["ArcherName"] for a in archers if a["ArcherID"] == x), ""),
                key="archer2",
                index=0 if filtered_archers else None
            )
        
        # Button to simulate the matchup
        if st.button("Analyze Matchup", use_container_width=True, type="primary"):
            with st.spinner("Analyzing archer data..."):
                simulate_1v1_matchup(archer1_id, archer2_id)
    
    else:  # Tournament mode
        st.subheader("Select 4 Archers for Competition")
        
        # Create a 2x2 grid for archer selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**First Two Archers**")
            archer1_id = st.selectbox(
                "Select first archer",
                options=[a["ArcherID"] for a in archers],
                format_func=lambda x: next((a["ArcherName"] for a in archers if a["ArcherID"] == x), ""),
                key="tournament_archer1"
            )
            
            # Filter out already selected archers
            filtered_archers1 = [a for a in archers if a["ArcherID"] != archer1_id]
            archer2_id = st.selectbox(
                "Select second archer",
                options=[a["ArcherID"] for a in filtered_archers1],
                format_func=lambda x: next((a["ArcherName"] for a in archers if a["ArcherID"] == x), ""),
                key="tournament_archer2"
            )
        
        with col2:
            st.write("**Second Two Archers**")
            # Filter out already selected archers
            filtered_archers2 = [a for a in archers if a["ArcherID"] not in [archer1_id, archer2_id]]
            archer3_id = st.selectbox(
                "Select third archer",
                options=[a["ArcherID"] for a in filtered_archers2],
                format_func=lambda x: next((a["ArcherName"] for a in archers if a["ArcherID"] == x), ""),
                key="tournament_archer3",
                index=0 if filtered_archers2 else None
            )
            
            # Filter out already selected archers
            filtered_archers3 = [a for a in archers if a["ArcherID"] not in [archer1_id, archer2_id, archer3_id]]
            archer4_id = st.selectbox(
                "Select fourth archer",
                options=[a["ArcherID"] for a in filtered_archers3],
                format_func=lambda x: next((a["ArcherName"] for a in archers if a["ArcherID"] == x), ""),
                key="tournament_archer4",
                index=0 if filtered_archers3 else None
            )
        
        # Button to analyze tournament
        if st.button("Analyze Competition", use_container_width=True, type="primary"):
            with st.spinner("Analyzing competition data..."):
                simulate_tournament([archer1_id, archer2_id, archer3_id, archer4_id])

if __name__ == '__main__':
    # This part is for testing the page independently if needed
    display_live_competition_view() 