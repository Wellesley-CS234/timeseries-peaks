# peak_finder.py

import pandas as pd
import streamlit as st
import numpy as np # Add numpy import

def generate_peak_summary_report(df_full, peak_df, article_cols, num_contributors=3):
    """
    Generates a fixed-column report summarizing the top contributors for each peak event.
    The output is the desired 1 + 1 + (N * 3) column structure.
    """
    
    report_rows = []
    
    for index, peak_row in peak_df.iterrows():
        peak_date = peak_row['Date']
        peak_total_views = peak_row['Total Views'] # Use 'Views' column from peak_dates_df
        
        # Get the full data row from the wide table
        full_data_row = df_full[df_full['Date'].eq(peak_date)]
        
        if full_data_row.empty:
            continue
            
        # Extract view counts for all articles on this peak day
        article_views = full_data_row.iloc[0][article_cols]
        
        # Calculate contributions and combine into a summary table
        contributions = pd.DataFrame({
            'Title': article_views.index.str.replace('Article ', 'A'),
            'Views': article_views.values,
        })
        contributions['Percent'] = (contributions['Views'] / peak_total_views) * 100
        
        # Sort by views to find the top contributors
        top_contributors = contributions.sort_values(by='Views', ascending=False).head(num_contributors)
        
        # Start building the final report row
        summary_row = {
            'Date': peak_date.strftime('%Y-%m-%d'),
            'Total Views': peak_total_views
        }
        
        # Flatten the top N contributors into fixed columns
        for i in range(num_contributors):
            contributor_rank = i + 1
            if i < len(top_contributors):
                contributor = top_contributors.iloc[i]
                summary_row[f'Top Contributor {contributor_rank} Title'] = contributor['Title']
                summary_row[f'Top Contributor {contributor_rank} Views'] = int(contributor['Views'])
                summary_row[f'Top Contributor {contributor_rank} %'] = round(contributor['Percent'], 1)
            else:
                # Fill with None/NaN if there aren't enough contributors (rare)
                summary_row[f'Top Contributor {contributor_rank} Title'] = None
                summary_row[f'Top Contributor {contributor_rank} Views'] = None
                summary_row[f'Top Contributor {contributor_rank} %'] = None
                
        report_rows.append(summary_row)

    # Create the final DataFrame
    return pd.DataFrame(report_rows)

def generate_exploratory_peak_table(df_full, peak_df, article_cols):
    """
    Creates a new DataFrame showing all daily data joined with peak contribution 
    only on the days that are peaks.
    """
    
    # 1. Start with a copy of the full data
    exploratory_df = df_full.copy()
    
    # 2. Initialize the new columns (These were temporary and can be removed, 
    # but we'll leave them for context)
    exploratory_df['Peak Date'] = pd.NaT 
    exploratory_df['Peak Contrib %'] = 0.0
    
    # 3. Iterate over the detected peaks and populate the contribution data
    # st.write(peak_df.head()) # Keep this commented or remove it in production
    for index, row in peak_df.iterrows():
        peak_date = row['Date']
        peak_total_views = row['Total Views'] 
        
        full_data_row = df_full[df_full['Date'].eq(peak_date)] 
        
        if not full_data_row.empty:
            article_views = full_data_row.iloc[0][article_cols]
            contributions_percent = (article_views / peak_total_views) * 100
        
            # Find the row index for the assignment (in the exploratory_df)
            row_index = exploratory_df[exploratory_df['Date'].eq(peak_date)].index[0]
            
            # Iterate over all article columns to populate the data
            for col in article_cols:
                article_name = col.replace('Article ', 'A')
                contribution = contributions_percent[col]
                
                # Create the unique contribution column for each article
                contribution_col_name = f'Contribution ({article_name} %)'
                
                # Initialize the column if it doesn't exist
                if contribution_col_name not in exploratory_df.columns:
                    exploratory_df[contribution_col_name] = np.nan
                
                # Assign the calculated percentage to the specific article's peak day
                exploratory_df.loc[row_index, contribution_col_name] = contribution
            
    # Clean up the table for display
    exploratory_df = exploratory_df.drop(columns=['Peak Date', 'Peak Contrib %'])
    
    # Reorder columns for better viewing
    all_cols = ['Date', 'Total Views'] + [
        col for pair in zip(article_cols, [f'Contribution ({c.replace("Article ", "A")} %)' for c in article_cols]) 
        for col in pair if col in exploratory_df.columns
    ]
    
    return exploratory_df[all_cols]


