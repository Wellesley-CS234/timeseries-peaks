import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import timedelta
from scipy.signal import find_peaks


@st.cache_data
def load_and_prepare_data():
    # --- Data Generation (Modified for 10 Articles) ---
    start_date = pd.to_datetime('2024-01-01')
    end_date = pd.to_datetime('2025-12-31')
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    N = len(date_range)
    
    # Base views and DataFrame setup remains the same
    # ... (code to generate df with Total Views) ...
    base_views = np.abs(1000 + np.linspace(0, 500, N) + 100 * np.sin(np.linspace(0, 4 * np.pi, N)) + np.random.normal(0, 50, N)).astype(int)
    df = pd.DataFrame({'Date': date_range, 'Total Views': base_views})
    
    # Initialize 10 articles (A0 to A9)
    article_cols = [f'Article A{i}' for i in range(10)]
    
    # Distribute base views among 10 articles (roughly 10% each)
    for col in article_cols:
        df[col] = (df['Total Views'] * (np.random.rand() * 0.05 + 0.08)).astype(int) # Random initial 8-13%
    
    # Re-calculate Total Views based on the sum of articles to ensure consistency
    df['Total Views'] = df[article_cols].sum(axis=1)

    # --- Inject Peaks Dynamically (Example Peaks) ---
    peaks_data = [
        ('2024-03-15', 5000, 'Article A1'),
        ('2024-09-01', 8000, 'Article A5'),
        ('2025-05-20', 6000, 'Article A8')
    ]
    # ... (inject_peak function remains the same, but using the new article names) ...
    
    def inject_peak(df, date_str, spike_size, dominant_article):
        # ... (implementation of inject_peak using article_cols) ...
        peak_date = pd.to_datetime(date_str)
        spike_days = pd.date_range(start=peak_date - timedelta(days=3), end=peak_date + timedelta(days=3), freq='D')
        
        non_dominant_articles = [c for c in article_cols if c != dominant_article]

        for date in spike_days:
            if date in df['Date'].values:
                day_index = df[df['Date'] == date].index[0]
                center_index = df[df['Date'] == peak_date].index[0]
                decay = np.exp(-((day_index - center_index)**2) / 10)

                spike_views = int(spike_size * decay)
                
                # Update total views
                # Note: We update article views first, then recalculate Total Views
                
                # Dominant article gets ~70% of the spike
                dominant_spike = int(spike_views * 0.7 + np.random.randint(-100, 100))
                # The remaining ~30% is split between others
                other_spike = (spike_views - dominant_spike) / len(non_dominant_articles)

                df.loc[df['Date'] == date, dominant_article] += dominant_spike
                for article in non_dominant_articles:
                    df.loc[df['Date'] == date, article] += other_spike
                
                # Recalculate total views for the day
                df.loc[df['Date'] == date, 'Total Views'] = df.loc[df['Date'] == date, article_cols].sum(axis=1)
        return df
        
    for date, size, article in peaks_data:
        df = inject_peak(df, date, size, article)
    
    # --- Dynamic Peak Finding  ---
    
    # Find indices of all peaks using a relative threshold
    # The 'prominence' parameter is key: it ensures we only find peaks that stand out significantly
    # from the surrounding noise/trend (e.g., 20% of the max view count)
    max_views = df['Total Views'].max()
    peak_indices, _ = find_peaks(
        df['Total Views'], 
        prominence=0.2 * max_views, # Threshold to find only major events
        distance=30 # Only allow one peak per 30-day window
    )
    
    # Create the DataFrame of the found peaks
    peak_dates_df = df.iloc[peak_indices][['Date', 'Total Views']]
    
    return df, article_cols, peak_dates_df # Return the new articles list and dynamic peaks

