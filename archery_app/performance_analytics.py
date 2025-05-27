"""
performance_analytics.py
Archer Performance Analytics Dashboard
Author: CloudBros Team
Date: May 2025
"""

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Import from your existing database module
from archery_app.database import get_connection, get_archers, get_archer_statistics, verify_connection, display_connection_error, initialize_connection

def calculate_statistics_from_scores(recent_scores):
    """Calculate statistics from the recent scores data"""
    if not recent_scores:
        return {}
    
    scores = [score['TotalScore'] for score in recent_scores]
    scores_array = np.array(scores)
    
    stats = {
        'mean': np.mean(scores_array),
        'median': np.median(scores_array),
        'std_dev': np.std(scores_array),
        'min_score': np.min(scores_array),
        'max_score': np.max(scores_array),
        'count': len(scores_array),
        'range': np.max(scores_array) - np.min(scores_array),
        'coefficient_variation': (np.std(scores_array) / np.mean(scores_array)) * 100 if np.mean(scores_array) > 0 else 0
    }
    return stats

def create_performance_plot(archer_stats):
    """Create comprehensive performance visualization using matplotlib only"""
    recent_scores = archer_stats.get('RecentScores', [])
    if not recent_scores:
        return None
    
    # Extract data
    scores = [score['TotalScore'] for score in recent_scores]
    dates = [score['Date'] for score in recent_scores]
    rounds = [score['RoundName'] for score in recent_scores]
    
    # Reverse to show chronological order (oldest to newest)
    scores = scores[::-1]
    dates = dates[::-1]
    rounds = rounds[::-1]
    
    # Calculate statistics
    stats = calculate_statistics_from_scores(recent_scores)
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Archer Performance Analytics Dashboard', fontsize=16, fontweight='bold')
    
    # 1. Score Trend Over Time
    ax1.plot(range(len(scores)), scores, 'o-', alpha=0.7, linewidth=2, markersize=6, color='#1f77b4')
    ax1.axhline(y=stats['mean'], color='red', linestyle='--', linewidth=2, label=f"Mean: {stats['mean']:.1f}")
    ax1.axhline(y=stats['median'], color='green', linestyle='--', linewidth=2, label=f"Median: {stats['median']:.1f}")
    ax1.fill_between(range(len(scores)), 
                     stats['mean'] - stats['std_dev'], 
                     stats['mean'] + stats['std_dev'], 
                     alpha=0.2, color='orange', label=f"±1σ: {stats['std_dev']:.1f}")
    ax1.set_title('Score Progression Over Time (Recent 5)')
    ax1.set_xlabel('Session Number')
    ax1.set_ylabel('Total Score')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Score Distribution Histogram
    ax2.hist(scores, bins=min(5, len(scores)), 
             alpha=0.7, color='skyblue', edgecolor='black')
    ax2.axvline(stats['mean'], color='red', linestyle='--', linewidth=2, label=f"Mean: {stats['mean']:.1f}")
    ax2.axvline(stats['median'], color='green', linestyle='--', linewidth=2, label=f"Median: {stats['median']:.1f}")
    ax2.set_title('Score Distribution (Recent 5)')
    ax2.set_xlabel('Score')
    ax2.set_ylabel('Frequency')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Performance by Round Type
    round_scores = {}
    for i, round_name in enumerate(rounds):
        if round_name not in round_scores:
            round_scores[round_name] = []
        round_scores[round_name].append(scores[i])
    
    if len(round_scores) > 1:
        round_names = list(round_scores.keys())
        round_averages = [np.mean(round_scores[name]) for name in round_names]
        
        bars = ax3.bar(round_names, round_averages, alpha=0.7, color=['lightblue', 'lightgreen', 'lightcoral'][:len(round_names)])
        ax3.set_title('Average Score by Round Type')
        ax3.set_ylabel('Average Score')
        ax3.set_xlabel('Round Type')
        
        # Add value labels on bars
        for bar, value in zip(bars, round_averages):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                    f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Rotate x-axis labels if needed
        plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
    else:
        ax3.text(0.5, 0.5, 'Single round type\nin recent scores', 
                ha='center', va='center', transform=ax3.transAxes, fontsize=12)
        ax3.set_title('Performance by Round Type')
    
    # 4. Score vs Possible Score (if available)
    possible_scores = [score.get('PossibleScore', 0) for score in recent_scores]
    if any(possible_scores):
        # Calculate percentages
        percentages = [(scores[i]/possible_scores[i])*100 if possible_scores[i] > 0 else 0 
                      for i in range(len(scores))]
        
        ax4.plot(range(len(percentages)), percentages, 'o-', alpha=0.7, linewidth=2, 
                markersize=6, color='purple')
        ax4.set_title('Score Percentage of Possible')
        ax4.set_xlabel('Session Number')
        ax4.set_ylabel('Percentage (%)')
        ax4.grid(True, alpha=0.3)
        
        avg_percentage = np.mean(percentages)
        ax4.axhline(y=avg_percentage, color='red', linestyle='--', 
                   label=f"Avg: {avg_percentage:.1f}%")
        ax4.legend()
    else:
        ax4.text(0.5, 0.5, 'Possible scores\nnot available', 
                ha='center', va='center', transform=ax4.transAxes, fontsize=12)
        ax4.set_title('Score Efficiency Analysis')
    
    plt.tight_layout()
    return fig

def get_performance_insights(archer_stats):
    """Generate performance insights and recommendations"""
    insights = []
    
    score_stats = archer_stats.get('ScoreStats', {})
    recent_scores = archer_stats.get('RecentScores', [])
    
    if not score_stats or score_stats.get('TotalScores', 0) == 0:
        return ["No score data available for analysis."]
    
    # Performance Level Analysis
    avg_score = score_stats.get('AverageScore', 0)
    if avg_score >= 500:
        insights.append("🏆 **Elite Level**: Outstanding performance level!")
    elif avg_score >= 400:
        insights.append("🥇 **Advanced Level**: Strong competitive performance.")
    elif avg_score >= 300:
        insights.append("🥈 **Intermediate Level**: Good foundation, room for improvement.")
    else:
        insights.append("🎯 **Developing Level**: Focus on fundamentals and practice.")
    
    # Total Scores Analysis
    total_scores = score_stats.get('TotalScores', 0)
    if total_scores >= 50:
        insights.append(f"📊 **Experienced Archer**: {total_scores} recorded scores show commitment to the sport.")
    elif total_scores >= 20:
        insights.append(f"📈 **Regular Shooter**: {total_scores} scores recorded, building good experience.")
    else:
        insights.append(f"🎯 **Getting Started**: {total_scores} scores recorded, keep practicing!")
    
    # Recent Performance Trend (if we have recent scores)
    avg_score = float(avg_score)
    if len(recent_scores) >= 3:
        recent_avg = np.mean([score['TotalScore'] for score in recent_scores[:3]])
        if recent_avg > avg_score:
            insights.append("📈 **Improving**: Recent scores are above your average!")
        elif recent_avg < avg_score * 0.9:
            insights.append("📉 **Recent Dip**: Recent scores below average, consider form review.")
        else:
            insights.append("🔄 **Consistent**: Recent performance matches your average.")
    
    # Equipment Preference
    preferred_equipment = archer_stats.get('PreferredEquipment', {})
    if preferred_equipment:
        equipment_name = preferred_equipment.get('EquipmentType', 'Unknown')
        usage_count = preferred_equipment.get('UsageCount', 0)
        insights.append(f"🏹 **Equipment**: Primarily uses {equipment_name} ({usage_count} sessions).")
    
    # Favorite Round
    favorite_round = archer_stats.get('FavoriteRound', {})
    if favorite_round:
        round_name = favorite_round.get('RoundName', 'Unknown')
        usage_count = favorite_round.get('UsageCount', 0)
        insights.append(f"🎯 **Favorite Round**: {round_name} ({usage_count} times shot).")
    
    return insights

def show_performance_analytics():
    """Main function to display the performance analytics page"""
    # Initialize connection check
    initialize_connection()
    
    # Check database connection
    if not verify_connection():
        display_connection_error()
        return
    
    # Page header
    st.title("📊 Archer Performance Analytics")
    st.markdown("---")
    
    # Archer selection
    st.subheader("Select Archer for Analysis")
    
    try:
        archers = get_archers()
    except Exception as e:
        st.error(f"Failed to load archers: {e}")
        return
    
    if not archers:
        st.error("No archers found in the database.")
        return
    
    # Create selectbox with archer names
    archer_options = {archer['ArcherName']: archer['ArcherID'] for archer in archers}
    archer_names = list(archer_options.keys())
    selected_archer_name = st.selectbox("Choose an archer:", ["Select an archer..."] + archer_names)
    
    if selected_archer_name == "Select an archer...":
        st.info("Please select an archer to view their performance analytics.")
        return
    
    selected_archer_id = archer_options[selected_archer_name]
    
    # Get comprehensive archer statistics
    try:
        archer_stats = get_archer_statistics(selected_archer_id)
    except Exception as e:
        st.error(f"Failed to load archer statistics: {e}")
        return
    
    if not archer_stats:
        st.error("No data found for the selected archer.")
        return
    
    # Display archer basic info
    st.markdown(f"### {archer_stats['ArcherName']}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Gender:** {archer_stats.get('Gender', 'Not specified')}")
    with col2:
        st.write(f"**Age:** {archer_stats.get('Age', 'Not specified')}")
    with col3:
        st.write(f"**Status:** {'Active' if archer_stats.get('IsActive') else 'Inactive'}")
    
    st.markdown("---")
    
    # Display key metrics
    score_stats = archer_stats.get('ScoreStats', {})
    
    if not score_stats or score_stats.get('TotalScores', 0) == 0:
        st.warning(f"No approved scores found for {selected_archer_name}.")
        st.info("Make sure the archer has submitted scores that have been approved.")
        return
    
    st.subheader("📈 Performance Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Average Score", f"{score_stats.get('AverageScore', 0):.1f}")
    with col2:
        st.metric("Highest Score", f"{score_stats.get('HighestScore', 0):.0f}")
    with col3:
        st.metric("Lowest Score", f"{score_stats.get('LowestScore', 0):.0f}")
    with col4:
        st.metric("Total Sessions", f"{score_stats.get('TotalScores', 0)}")
    with col5:
        range_score = score_stats.get('HighestScore', 0) - score_stats.get('LowestScore', 0)
        st.metric("Score Range", f"{range_score:.0f}")
    
    # Advanced statistics
    with st.expander("📊 Detailed Information"):
        col1, col2 = st.columns(2)
        with col1:
            preferred_equipment = archer_stats.get('PreferredEquipment', {})
            if preferred_equipment:
                st.write(f"**Preferred Equipment:** {preferred_equipment.get('EquipmentType', 'N/A')}")
            
            favorite_round = archer_stats.get('FavoriteRound', {})
            if favorite_round:
                st.write(f"**Favorite Round:** {favorite_round.get('RoundName', 'N/A')}")
        
        with col2:
            st.write(f"**Average Score:** {score_stats.get('AverageScore', 0):.2f}")
            st.write(f"**Score Consistency:** {range_score:.0f} point range")
    
    st.markdown("---")
    
    # Create and display visualizations
    st.subheader("📊 Performance Visualizations")
    fig = create_performance_plot(archer_stats)
    
    if fig:
        st.pyplot(fig)
    else:
        st.info("Not enough recent score data for detailed visualizations.")
    
    st.markdown("---")
    
    # Performance insights
    st.subheader("🔍 Performance Insights")
    insights = get_performance_insights(archer_stats)
    
    for insight in insights:
        st.markdown(insight)
    
    # Raw data table (expandable)
    recent_scores = archer_stats.get('RecentScores', [])
    if recent_scores:
        with st.expander("📋 View Recent Score Data"):
            df_data = []
            for score in recent_scores:
                df_data.append({
                    'Score': score['TotalScore'],
                    'Date': score['Date'].strftime('%Y-%m-%d') if hasattr(score['Date'], 'strftime') else str(score['Date']),
                    'Round': score['RoundName'],
                    'Equipment': score['EquipmentType'],
                    'Possible Score': score.get('PossibleScore', 'N/A')
                })
            
            if df_data:
                st.table(df_data)

# Entry point for the page
if __name__ == "__main__":
    show_performance_analytics()
