# NWM Streamflow Forecast Dashboard

This project evaluates the performance of the National Water Model (NWM) in predicting streamflow for the West Branch Little River, a small mountainous watershed in Stowe, Vermont. The study focuses on approximately 50 hydrologic events influenced by both snowmelt and rainfall, comparing NWM predicted streamflow with United States Geological Survey (USGS) observations. Key performance metrics, such as Pearson correlation coefficient (Cor), Percent Bias (PBIAS), and Nash-Sutcliffe Efficiency (NSE), were calculated for each event to assess the model's accuracy. These results were visualized in a custom-built interactive dashboard developed using Flask, which allows users to filter by season, explore event-level performance and display their respective hydrograph. Events were assigned to seasons, and a Kruskal-Wallis statistical test was conducted to determine if there was a significant difference between PBIAS by season. While there were no statistically significant differences between seasons, the model displayed consistently poor performance across all seasons, particularly in the summer. This project highlights the need for continued refinement of large-scale hydrologic models and offers a tool for evaluating streamflow forecast performance that can be applied to additional sites.

## Live Application

Hosted on the University of Vermont Silk Server:  
**[https://water.w3.uvm.edu/projects/nwm-dashboard/](https://water.w3.uvm.edu/projects/nwm-dashboard/)**

## Features

- Interactive time series plots using **Plotly.js**
- Dynamic event table with sortable columns and pagination
- Seasonal PBIAS boxplot and statistical testing using **Kruskal-Wallis**
- Real-time NWM forecast viewer
- Event classification by season

