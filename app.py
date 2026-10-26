            

            min_forecasted_date = None
            if not scored_combined_forecasted_df.empty:
                min_forecasted_date = scored_combined_forecasted_df["date"].min()
            if min_forecasted_date is not None and hasattr(min_forecasted_date, 'year'):
                min_forecasted_year = min_forecasted_date.year
            else:
                min_forecasted_year = scored_historical_df['year'].max()

            max_historical_date = None
            if not scored_historical_df.empty:
                max_historical_date = scored_historical_df["date"].max()
            if max_historical_date is not None and hasattr(max_historical_date, 'year'):
                max_historical_year = max_historical_date.year
            else:
                max_historical_year = scored_historical_df['year'].max()

            # If the last year of historical == first year of forecasted, Get the number of distinct days in the shared year in both historical and forecasted dataframes
            if max_historical_year == min_forecasted_year:
                shared_year = max_historical_year  # This is the year present in both
                num_days_shared_historical = scored_historical_df[scored_historical_df['year'] == shared_year]['date'].nunique()
                num_days_shared_forecasted = scored_combined_forecasted_df[scored_combined_forecasted_df['year'] == shared_year]['date'].nunique()
                

            # --- Score Distribution ---
            score_percents_historical = {}
            score_percents_combined_forecasted = {}
            all_dates = pd.concat([scored_historical_df[['year', 'date']], scored_combined_forecasted_df[['year', 'date']]])
            dates_per_year = all_dates.drop_duplicates().groupby('year')['date'].nunique()
            score_cols = [col for col in scored_combined_forecasted_df.columns if col.startswith('score_')]
            score_percents_by_model = []
            for col in score_cols:
                model_percents = {}
                for score_val in [0, 25, 50, 75, 100]:
                    score_percent = scored_combined_forecasted_df[scored_combined_forecasted_df[col] == score_val].groupby('year').size() / dates_per_year #scored_combined_forecasted_df.groupby('year').size()
                    model_percents[score_val] = 100 * score_percent.fillna(0)
                score_percents_by_model.append(model_percents)

            for score_val in [0, 25, 50, 75, 100]:
                # Calculate the denominator: number of distinct dates per year across both historical and combined forecasted dataframes
                score_percent = scored_historical_df[scored_historical_df['score'] == score_val].groupby('year').size() / dates_per_year
                score_percents_historical[score_val] = 100*score_percent.fillna(0)
                dfs = [model[score_val] for model in score_percents_by_model]
                if dfs:
                    combined = pd.concat(dfs, axis=1).mean(axis=1)
                else:
                    combined = pd.Series(dtype=float)
                score_percents_combined_forecasted[score_val] = combined
            
            score_traces = []
            for score_val, color, score_name in zip([0, 25, 50, 75, 100], ['#ba1535', '#ba6715', '#b7ba15', '#43ba15', '#158cba'], ['Hate', 'Dislike', 'Neutral', 'Like', 'Love']): 
                score_traces.append(
                    go.Bar(
                        x=score_percents_historical[score_val].index,
                        y=score_percents_historical[score_val].values,
                        name=score_name,
                        marker_color=color,
                        showlegend=show_legend,
                        legendgroup = score_name
                    )
                )
                score_traces.append(
                    go.Bar(
                        x=score_percents_combined_forecasted[score_val].index,
                        y=score_percents_combined_forecasted[score_val].values,
                        name=score_name,
                        marker_color=color,
                        opacity=0.7,
                        showlegend=False,
                        legendgroup = score_name
                    )
                )
            score_subplots.append((score_traces, min_forecasted_year, f"{city}, {state}"))
            # --- Score Average ---
            avg_score_historical = scored_historical_df.groupby('year')['score'].mean()
            # Take the average score for each of the score columns, then average across those averages by year
            score_cols = [col for col in scored_combined_forecasted_df.columns if col.startswith('score_')]
            avg_scores_per_col = scored_combined_forecasted_df.groupby('year')[score_cols].mean()
            avg_score_forecasted = avg_scores_per_col.mean(axis=1)
            min_score_forecasted = avg_scores_per_col.min(axis=1)
            max_score_forecasted = avg_scores_per_col.max(axis=1)

            # Find the shared year between historical and forecasted
            if shared_year:
                total_days = num_days_shared_historical + num_days_shared_forecasted
                # Weighted average for mean
                hist_avg = avg_score_historical.loc[shared_year]
                fore_avg = avg_score_forecasted.loc[shared_year]
                weighted_avg = (
                    hist_avg * num_days_shared_historical + fore_avg * num_days_shared_forecasted
                ) / total_days
                avg_score_forecasted.loc[shared_year] = weighted_avg

                fore_min = min_score_forecasted.loc[shared_year]
                fore_max = max_score_forecasted.loc[shared_year]
                weighted_min = (
                    hist_avg * (num_days_shared_historical / total_days)
                    + fore_min * (num_days_shared_forecasted / total_days)
                )
                weighted_max = (
                    hist_avg * (num_days_shared_historical / total_days)
                    + fore_max * (num_days_shared_forecasted / total_days)
                )
                min_score_forecasted.loc[shared_year] = weighted_min
                max_score_forecasted.loc[shared_year] = weighted_max

                # Set the avg score historical for the shared year to the forecasted value
                avg_score_historical.loc[shared_year] = avg_score_forecasted.loc[shared_year]

            average_traces = [
                go.Scatter(
                    x=avg_score_historical.index, 
                    y=avg_score_historical.values, 
                    mode='lines', 
                    name='Historical', 
                    line=dict(color='#158cba', width=2),
                    showlegend=show_legend, 
                    legendgroup = 'avg_graphs__h'
                ),
                go.Scatter(
                    x=avg_score_forecasted.index, 
                    y=avg_score_forecasted.values, 
                    mode='lines', 
                    name='Forecasted', 
                    line=dict(color='#ba1535', width=2), 
                    showlegend=show_legend,
                    legendgroup = 'avg_graphs__f'
                ),
                go.Scatter(
                    name='Upper Bound',
                    x=max_score_forecasted.index,
                    y=max_score_forecasted.values,
                    mode='lines',
                    marker=dict(color="#444"),
                    line=dict(width=0),
                    showlegend=False, 
                    legendgroup = 'avg_graphs__f'
                ),
                go.Scatter(
                    name='Lower Bound',
                    x=min_score_forecasted.index,
                    y=min_score_forecasted.values,
                    marker=dict(color="#444"),
                    line=dict(width=0),
                    mode='lines',
                    fillcolor='rgba(68, 68, 68, 0.3)',
                    fill='tonexty',
                    showlegend=False, 
                    legendgroup = 'avg_graphs__f'
                )
            ]
            average_subplots.append((average_traces, f"{city}, {state}"))
            
            # --- Monthly Stacked ---
            scored_historical_df['month'] = scored_historical_df['date'].dt.month
            monthly_avg_hist = scored_historical_df.groupby(['year', 'month'])['score'].mean().reset_index()
            years_hist = sorted(monthly_avg_hist['year'].unique())
            n_hist = len(years_hist)
            hist_traces = []
            for i, year in enumerate(years_hist):
                year_data = monthly_avg_hist[monthly_avg_hist['year'] == year]
                fade = 0.2 + 0.8 * (i + 1) / n_hist
                hist_traces.append(
                    go.Scatter(x=year_data['month'], y=year_data['score'], mode='lines', name=f'{year}', line=dict(color=f'rgba(21, 140, 186,{fade})', width=2), showlegend=show_legend, legendgroup = f'{year}')
                )
            
            scored_combined_forecasted_df['month'] = scored_combined_forecasted_df['date'].dt.month
            score_cols = [col for col in scored_combined_forecasted_df.columns if col.startswith('score_')]
            avg_scores_per_col = scored_combined_forecasted_df.groupby(['year', 'month'])[score_cols].mean()
            monthly_avg_fore = avg_scores_per_col.mean(axis=1).reset_index(name='score')
            years_fore = sorted(monthly_avg_fore['year'].unique())
            n_fore = len(years_fore)
            fore_traces = []
            for i, year in enumerate(years_fore):
                year_data = monthly_avg_fore[monthly_avg_fore['year'] == year]
                fade = 0.2 + 0.8 * (n_fore - i) / n_fore
                fore_traces.append(
                    go.Scatter(x=year_data['month'], y=year_data['score'], mode='lines', name=f'{year}', line=dict(color=f'rgba(186, 21, 53,{fade})', width=2), showlegend=show_legend, legendgroup = f'{year}')
                )
            monthly_stacked_subplots.append((hist_traces + fore_traces, f"{city}, {state}"))
            
            # --- Reason Distribution ---
            all_reasons = list(set(reasons_historical).union(set(reasons_combined_forecasted)))
            reason_counts_historical = {reason: scored_historical_df[scored_historical_df['reason'] == reason].groupby('year').size() for reason in all_reasons}
            
            # For combined forecasted df: get reason count for each reason_* column by year, then average per year for each reason
            reason_cols = [col for col in scored_combined_forecasted_df.columns if col.startswith('reason_')]
            years = scored_combined_forecasted_df['year'].unique()
            reason_counts_forecasted = {}
            reason_mins_forecasted = {}
            reason_maxs_forecasted = {}
            for reason in all_reasons:
                # For each year, count how many times this reason appears in any reason_* column
                yearly_means = []
                yearly_mins = []
                yearly_maxs = []
                for year in sorted(years):
                    df_year = scored_combined_forecasted_df[scored_combined_forecasted_df['year'] == year]
                    # Count occurrences of this reason in all reason_* columns for this year
                    mean_cnt = sum((df_year[col] == reason).sum() for col in reason_cols)  / len(reason_cols)
                    min_cnt = min((df_year[col] == reason).sum() for col in reason_cols) 
                    max_cnt = max((df_year[col] == reason).sum() for col in reason_cols) 
                    # Normalize by number of models (columns) to get average per year
                    yearly_means.append((year, mean_cnt))
                    yearly_mins.append((year, min_cnt))
                    yearly_maxs.append((year, max_cnt))
                # Convert to pandas Series for compatibility with plotting code
                reason_counts_forecasted[reason] = pd.Series(
                    [mean_cnt for year, mean_cnt in yearly_means],
                    index=[year for year, mean_cnt in yearly_means],
                    dtype=float
                )
                reason_mins_forecasted[reason] = pd.Series(
                    [min_cnt for year, min_cnt in yearly_mins],
                    index=[year for year, min_cnt in yearly_mins],
                    dtype=float
                )
                reason_maxs_forecasted[reason] = pd.Series(
                    [max_cnt for year, max_cnt in yearly_maxs],
                    index=[year for year, max_cnt in yearly_maxs],
                    dtype=float
                )

            # Find shared years between historical and forecasted
            if shared_year:
                for reason in all_reasons:
                    hist_series = reason_counts_historical.get(reason)
                    if hist_series is not None:
                        # Add to forecasted series if it exists, else create a new one
                        for forecast_dict in [
                            reason_counts_forecasted,
                            reason_mins_forecasted,
                            reason_maxs_forecasted
                        ]:
                            forecast_series = forecast_dict.get(reason)
                            if forecast_series is not None:
                                # Add historical to forecasted, aligning on index
                                combined_series = forecast_series.add(hist_series.astype(float), fill_value=0)
                            else:
                                # If no forecast data, just use the historical
                                combined_series = hist_series.astype(float).copy()
                            forecast_dict[reason] = combined_series
                    if reason in reason_counts_forecasted:
                        updated_forecast_series = reason_counts_forecasted[reason]
                        if reason in reason_counts_historical:
                            historical_series = reason_counts_historical[reason]
                            # Align and update matching year values only
                            historical_series.update(updated_forecast_series.loc[historical_series.index].astype(float))
                        else:
                            # If the reason wasn't in historical, create a new one with only the years from forecasted
                            reason_counts_historical[reason] = updated_forecast_series.copy()

                
            # Define theme colors for consistent coloring
            reason_to_color = {
                "neutral": "#158cba",
                "too hot, humid": "#3f15ba",
                "too hot, dry": "#7a15ba",
                "too cold, windy": "#ba15a1",
                "too cold, still": "#ba1535",
                "ideal sunny": "#ba6715",
                "ideal overcast": "#b7ba15",
                "light rain": "#43ba15",
                "heavy rain": "#15ba67",
                "snow": "#15b7ba"
            }            
            reason_traces = []
            for reason, color in reason_to_color.items():
                added_trace = False  # Track whether we’ve added at least one visible trace

                # Historical trace (solid line)
                hist_data = reason_counts_historical.get(reason)
                if hist_data is not None and not hist_data.empty:
                    reason_traces.append(
                        go.Scatter(
                            x=hist_data.index,
                            y=hist_data.values,
                            mode='lines',
                            name=reason,
                            line=dict(dash='solid', color=color),
                            marker=dict(color=color),
                            showlegend=show_legend, 
                            legendgroup = reason
                        )
                    )
                    added_trace = True

                # Forecasted trace (dotted line)
                forecast_data = reason_counts_forecasted.get(reason)
                forecast_mins = reason_mins_forecasted.get(reason)
                forecast_maxs = reason_maxs_forecasted.get(reason)
                if forecast_data is not None and forecast_mins is not None and forecast_maxs is not None and not forecast_data.empty:
                    reason_traces.append(
                        go.Scatter(
                            x=forecast_mins.index,
                            y=forecast_mins.values,
                            mode='lines',
                            name='Lower Bound '+reason,
                            line=dict(width=0),
                            marker=dict(color=color),
                            showlegend=False,  # Only show legend if no historical
                            legendgroup = reason
                        )
                    )
                    reason_traces.append(
                        go.Scatter(
                            name='Upper Bound '+reason,
                            x=forecast_maxs.index,
                            y=forecast_maxs.values,
                            marker=dict(color=color),
                            line=dict(width=0),
                            mode='lines',
                            fillcolor=hex_to_rgba(color, 0.3),
                            fill='tonexty',
                            showlegend=False, 
                            legendgroup = reason
                        )
                    )
                    reason_traces.append(
                        go.Scatter(
                            x=forecast_data.index,
                            y=forecast_data.values,
                            mode='lines',
                            name=reason,
                            line=dict(dash='solid', color=color),
                            marker=dict(color=color),
                            showlegend=not added_trace and show_legend,  # Only show legend if no historical
                            legendgroup = reason
                        )
                    )
                    added_trace = True

                # If no data at all, add a dummy invisible trace to lock in the color
                else:
                    reason_traces.append(
                        go.Scatter(
                            x=[None],
                            y=[None],
                            mode='lines',
                            name=reason,
                            line=dict(dash='solid', color=color),
                            marker=dict(color=color),
                            showlegend=show_legend,
                            legendgroup = reason
                        )
                    )
            reason_subplots.append((reason_traces, f"{city}, {state}"))
            
            # --- PM2.5 ---
            pm25_df['year'] = pd.to_datetime(pm25_df['date']).dt.year
            pm25_categories = {
                'Healthy': (0, 12),
                'Moderate': (12, 35.5),
                'Unhealthy for Sensitive': (35.5, 55.5),
                'Unhealthy': (55.5, 150.5),
                'Hazardous': (150.5, float('inf'))
            }
            pm25_data = {}
            for category, (min_val, max_val) in pm25_categories.items():
                if max_val == float('inf'):
                    mask = (pm25_df['pm2_5__micrograms_per_cubic_metre'] >= min_val) & (pm25_df['pm2_5__micrograms_per_cubic_metre'].notna())
                else:
                    mask = (pm25_df['pm2_5__micrograms_per_cubic_metre'] >= min_val) & (pm25_df['pm2_5__micrograms_per_cubic_metre'] < max_val) & (pm25_df['pm2_5__micrograms_per_cubic_metre'].notna())
                yearly_counts = pm25_df[mask].groupby('year').size()
                total_hours_per_year = pm25_df[pm25_df['pm2_5__micrograms_per_cubic_metre'].notna()].groupby('year').size()
                pm25_data[category] = (yearly_counts / total_hours_per_year * 100)

            pm25_traces = []
            for category, color in zip(['Healthy', 'Moderate', 'Unhealthy for Sensitive', 'Unhealthy', 'Hazardous'], ['green', 'yellow', 'orange', 'red', 'purple']):
                pm25_traces.append(
                    go.Bar(
                        x=pm25_data[category].index,
                        y=pm25_data[category].values,
                        name=category,
                        marker_color=color,
                        showlegend=show_legend,
                        legendgroup = category
                    )
                )
            pm25_subplots.append((pm25_traces, f"{city}, {state}"))
            
            
            status_msgs.append(f"{city}, {state}: Data retrieved successfully")
        except Exception as e:
            status_msgs.append(f"{city}, {state}: Error - {str(e)}")
            # Add empty traces for this city
            score_subplots.append(([], 0, f"{city}, {state}"))
            average_subplots.append(([], f"{city}, {state}"))
            pm25_subplots.append(([], f"{city}, {state}"))
            reason_subplots.append(([], f"{city}, {state}"))
            monthly_stacked_subplots.append(([], f"{city}, {state}"))

    # Build subplots for each plot type
    n_cities = len(city_states)

    # Score Distribution
    # Ensure subplot_titles are strings, not tuples
    subplot_titles = [f"{city}, {state}" for city, state in city_states]

    score_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, min_forecasted_year, label) in enumerate(score_subplots):
        for trace in traces:
            score_fig.add_trace(trace, row=1, col=i+1)
        score_fig.add_shape(
            dict(type='line', x0=min_forecasted_year, x1=min_forecasted_year, y0=0, y1=100, yref='paper', line={'dash': 'dash', 'color': 'black'}),
            row=1, col=i+1
        )
        score_fig.update_layout(legend_tracegroupgap=2)
    score_fig.update_layout(
        title='Score Distribution by Year', 
        barmode='stack'
    )
    # Apply x/y axis titles to all subplots
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        score_fig.update_layout({
            xaxis_name: {'title': 'Year'},
            yaxis_name: {'title': 'Percentage of Days'} if i == 1 else {},
        })
    score_fig.update_layout(legend_tracegroupgap=2)

    # Score Average
    avg_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(average_subplots):
        for trace in traces:
            avg_fig.add_trace(trace, row=1, col=i+1)
        avg_fig.add_shape(
            dict(type='line', x0=min_forecasted_year, x1=min_forecasted_year, y0=20, y1=90, yref='paper', line={'dash': 'dash', 'color': 'black'}),
            row=1, col=i+1
        )
    avg_fig.update_layout(
        title='Score Average by Year'
    )
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        avg_fig.update_layout({
            xaxis_name: {'title': 'Year'},
            yaxis_name: {'title': 'Score Average'} if i == 1 else {},
        })
    avg_fig.update_layout(legend_tracegroupgap=2)

    # Monthly Stacked
    monthly_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(monthly_stacked_subplots):
        for trace in traces:
            monthly_fig.add_trace(trace, row=1, col=i+1)
        monthly_fig.add_shape(
            dict(type='line', x0=5, x1=5, y0=0, y1=100, yref='paper', line={'dash': 'dash', 'color': 'rgba(0, 0, 0, 0)'}),
            row=1, col=i+1
        )
    monthly_fig.update_layout(
        title='Monthly Average Stacked Scores by Year'
    )
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        monthly_fig.update_layout({
            xaxis_name: {
                'title': 'Month',
                'tickmode':'array',
                'tickvals':list(range(1, 13)),
                'ticktext':["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            },
            yaxis_name: {'title': 'Average Score'} if i == 1 else {},
        })
    monthly_fig.update_layout(legend_tracegroupgap=2)
    
    monthly_fig.update_layout(
        yaxis_title="Your Y-Axis Label"
    )

    # Reason Distribution
    reason_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(reason_subplots):
        for trace in traces:
            reason_fig.add_trace(trace, row=1, col=i+1)
        reason_fig.add_shape(
            dict(type='line', x0=min_forecasted_year, x1=min_forecasted_year, y0=0, y1=250, yref='paper', line={'dash': 'dash', 'color': 'black'}),
            row=1, col=i+1
        )
    reason_fig.update_layout(
        title='Number of Days by Type (Reason) per Year'
    )
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        reason_fig.update_layout({
            xaxis_name: {'title': 'Year'},
            yaxis_name: {'title': 'Number of Days'} if i == 1 else {},
        })
    reason_fig.update_layout(legend_tracegroupgap=2)

    # PM2.5
    pm25_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(pm25_subplots):
        for trace in traces:
            pm25_fig.add_trace(trace, row=1, col=i+1)
    pm25_fig.update_layout(
        title='PM2.5 Air Quality Distribution by Year', 
        barmode='stack'
    )
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        pm25_fig.update_layout({
            xaxis_name: {'title': 'Year'},
            yaxis_name: {'title': 'Percentage of Hours'} if i == 1 else {},
        })
    pm25_fig.update_layout(legend_tracegroupgap=2)

    # Build the map
    map_trace = go.Scattermap(
        lat=lats,
        lon=lons,
        mode='markers+text',
        marker=go.scattermap.Marker(size=14, color='#158cba'),
        text=labels,
        textposition='top right',
    )
    map_layout = go.Layout(
        title='Selected Cities Map',
        autosize=True,
        hovermode='closest',
        map=dict(
            bearing=0,
            center=dict(lat=np.mean(lats) if lats else 39, lon=np.mean(lons) if lons else -98),
            pitch=0,
            zoom=3
        )
    )
    map_figure = go.Figure(data=[map_trace], layout=map_layout)