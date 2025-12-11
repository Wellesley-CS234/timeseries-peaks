import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from scipy.signal import find_peaks
import plotly.express as px
import plotly.graph_objects as go
from data_preparation import load_and_prepare_data
from peak_finder import generate_peak_summary_report

st.set_page_config(layout="wide", page_title="Wikipedia Page View Analysis (Plotly)")

def toggle_report_visibility():
    """Toggles the state variable controlling the report's visibility."""
    # Ensure the state exists before toggling
    if 'show_report' not in st.session_state:
        st.session_state['show_report'] = True # Default to show on first click
    else:
        st.session_state['show_report'] = not st.session_state['show_report']

st.title("Wikipedia Page Views: Interactive Analysis (Plotly)")
st.markdown("Zoom into the 2-year time series using the rangeslider at the bottom to explore daily activity.")

df_wide, article_cols, peak_dates_df = load_and_prepare_data()

annotate_peaks = st.checkbox("Annotate Dynamically Detected Peaks with Top 3 Articles", value=True)

# 1. Base Plotly Figure
fig = px.line(df_wide, x='Date', y='Total Views', 
              title="Total Wikipedia Page Views (2024-2025)")

# 2. Add Rangeslider for Zooming 
fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(visible=True),
        type="date"
    )
)

# 3. Dynamic Peak Annotation Logic (Plotly)
annotations = []
BOX_Y_ANCHOR_OFFSET = 500  # Anchor the box 500 views above the peak

# Define the arrow and box shifts in pixels:
ARROW_X_OFFSET = 30  
ARROW_Y_OFFSET = -30 
BOX_X_SHIFT_PX = 20  

if annotate_peaks and not peak_dates_df.empty:
    
    # Add Red Markers for Peaks (using a scatter trace)
    fig.add_trace(go.Scatter(
        x=peak_dates_df['Date'],
        y=peak_dates_df['Total Views'],
        mode='markers',
        marker=dict(size=10, color='red'),
        name='Peak'
    ))

    for _, row in peak_dates_df.iterrows():
        peak_date = row['Date']
        data_at_peak = df_wide[df_wide['Date'] == peak_date].iloc[0]
        peak_total_views = data_at_peak['Total Views']
        
        contributions = []
        for col in article_cols:
            views = data_at_peak[col]
            percent = (views / peak_total_views * 100) if peak_total_views > 0 else 0
            contributions.append({'Article Name': col.replace('Article ', ''), 'Views': views, 'Percent': percent})
        
        top_3 = sorted(contributions, key=lambda x: x['Views'], reverse=True)[:3]
        
        # Build the multi-line text using HTML breaks (<br>)
        annotation_text = f"<b>Peak: {peak_date.strftime('%b %d, %Y')}</b><br>{int(row['Total Views']):,} views"
        
        for item in top_3:
            annotation_text += f"<br>{item['Article Name']} {item['Percent']:.0f}%"

        Y_Anchor = row['Total Views'] + BOX_Y_ANCHOR_OFFSET
        # --- Create the Annotation Object ---
        annotations.append(
            dict(
                x=peak_date,
                y=Y_Anchor, 
                xref="x", yref="y",
                text=annotation_text,
                showarrow=True,
                arrowhead=1,
                ax=ARROW_X_OFFSET, 
                ay=ARROW_Y_OFFSET, 
                bgcolor="salmon",
                bordercolor="red",
                borderwidth=2,
                borderpad=4,
                opacity=0.8,
                align="left",
                font=dict(color="black", size=12),
                xanchor='left',
                xshift=BOX_X_SHIFT_PX 
        )
    )

    # Update figure layout with all dynamically generated annotations
    fig.update_layout(annotations=annotations)

# 4. Display the Plotly chart
st.plotly_chart(fig, use_container_width=True)


## Button for dataframe

# Ensure state is initialized (important for first run)
if 'show_report' not in st.session_state:
    st.session_state['show_report'] = False

# Determine the button's label based on the current state
label = "Hide Peak Contribution Report" if st.session_state['show_report'] else "Generate & Show Peak Contribution Report"

# Use st.button with the on_click callback
# This guarantees the state is updated *before* the script re-executes.
st.button(label, on_click=toggle_report_visibility)


# --- 5. CONDITIONAL REPORT DISPLAY ---

# Use the button press (via session_state) to trigger the report display
if 'show_report' in st.session_state and st.session_state['show_report']:
    
    st.markdown("---")
    st.subheader("🚨 Dynamic Peak Contribution Report")
    st.info("This table shows the top 3 contributing articles for the automatically detected highest spikes in the 2-year period.")
    
    # Call the analysis function
    peak_report_df = generate_peak_summary_report(df_wide, peak_dates_df, article_cols)

    st.dataframe(
        peak_report_df, 
        use_container_width=True,
        # Format Total Peak Views nicely
        column_config={
            "Total Peak Views": st.column_config.NumberColumn(format="%d")
        }
    )