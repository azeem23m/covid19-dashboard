import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

# Preprocessing
def missing_numbers(df):
    for num_col in df.select_dtypes(include='number'):
        df[num_col].fillna(0, inplace=True)

df_country = pd.read_csv("country_wise_latest.csv")
df_complete = pd.read_csv("covid_19_clean_complete.csv")

df_complete["Date"] = pd.to_datetime(df_complete["Date"])
df_complete.fillna({"Province/State": ""}, inplace=True)

missing_numbers(df_country)
missing_numbers(df_complete)

df_country["Active / 100 Cases"] = 100 - df_country["Deaths / 100 Cases"] - df_country["Recovered / 100 Cases"]

# Initialize App
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "COVID-19 Dashboard"

# App Layout
app.layout = html.Div([
    html.Div(id="_"),
    html.H1("COVID-19 Dashboard", style={"textAlign": "center"}),
    dcc.Tabs([
        dcc.Tab(label="Overview", children=[
            html.Div([
                html.Div([
                    html.H3("Global Statistics", style={"textAlign": "center"}),
                    html.Div([
                        html.Div([
                            html.H4("Confirmed Cases", className="stats-header"),
                            html.H2(id="total-cases", className="stats-number")
                        ], style={"textAlign": "center", "backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px", "flex": "1", "margin": "10px"}),
                        html.Div([
                            html.H4("Deaths", className="stats-header"),
                            html.H2(id="total-deaths", className="stats-number")
                        ], style={"textAlign": "center", "backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px", "flex": "1", "margin": "10px"}),
                        html.Div([
                            html.H4("Recovered", className="stats-header"),
                            html.H2(id="total-recovered", className="stats-number")
                        ], style={"textAlign": "center", "backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px", "flex": "1", "margin": "10px"})
                    ], style={"display": "flex", "justifyContent": "space-around", "margin": "20px"}),
                    dcc.Graph(id="daily-trend")
                ])
            ])
        ]),
        dcc.Tab(label="Top Countries", children=[
            html.Div([
                dcc.Dropdown(
                    id="metric-dropdown",
                    options=[
                        {"label": "Confirmed Cases", "value": "Confirmed"},
                        {"label": "Deaths", "value": "Deaths"},
                        {"label": "Recovered", "value": "Recovered"},
                        {"label": "Active Cases", "value": "Active"}
                    ],
                    value="Confirmed",
                    style={"width": "50%", "margin": "10px auto"}
                ),
                dcc.Graph(id="top-countries-chart")
            ])
        ]),
        dcc.Tab(label="Country Analysis", children=[
            html.Div([
                dcc.Dropdown(
                    id="country-input",
                    options=[{"label": country, "value": country} for country in df_country['Country/Region'].unique()],
                    value="US",
                    placeholder="Select a country",
                    style={"width": "50%", "margin": "10px auto"}
                ),
                html.Div([
                    dcc.Graph(id="country-bar", style={"flex": "1", "padding": "10px", "height": "600px"}),
                    dcc.Graph(id="country-pie", style={"flex": "1", "padding": "10px"})
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "25px"})
            ])
        ]),
        dcc.Tab(label="Geographical Spread", children=[
            html.Div([
                dcc.Dropdown(
                    id="case-input",
                    options=[{"label": case, "value": case} for case in ["Confirmed", "Deaths", "Recovered", "Active"]],
                    value="Active",
                    placeholder="Select a Case",
                    style={"width": "50%", "margin": "10px auto"}
                ),
                html.Div([
                    dcc.Graph(id="geo-map")
                ])
            ])
        ])
    ])
])

@app.callback(
    [Output("total-cases", "children"),
     Output("total-deaths", "children"),
     Output("total-recovered", "children")],
    [Input("_", "children")]
)
def update_stats(_):
    cases = f"{int(df_country['Confirmed'].sum()):,}"
    deaths = f"{int(df_country['Deaths'].sum()):,}"
    recovered = f"{int(df_country['Recovered'].sum()):,}"
    return cases, deaths, recovered

@app.callback(
    Output("daily-trend", "figure"),
    [Input("_", "children")]
)
def update_trend(_):
    df_trend = df_complete.groupby("Date")[["Confirmed", "Deaths", "Recovered"]].sum().reset_index()
    fig = px.line(df_trend, x="Date", y=["Confirmed", "Deaths", "Recovered"],
                  title="Global COVID-19 Trends")
    fig.update_layout(height=500)
    return fig

@app.callback(
    Output("country-pie", "figure"),
    [Input("country-input", "value")]
)
def country_pie(selected_country):
    filtered_data = df_country[df_country['Country/Region'] == selected_country]
    values = filtered_data.iloc[0][["Active / 100 Cases", "Deaths / 100 Cases", "Recovered / 100 Cases"]]
    labels = ["Active", "Deaths", "Recovered"]
    fig = px.pie(
        values=values,
        names=labels,
        title=f"COVID-19 Distribution in {selected_country}"
    )
    return fig

@app.callback(
    Output("country-bar", "figure"),
    [Input("country-input", "value")]
)
def country_bar(country):
    filtered_data = df_country[df_country['Country/Region'] == country]
    plot_data = {
        "x": ["Confirmed", "Deaths", "Recovered", "Active"],
        "y": filtered_data[["Confirmed", "Deaths", "Recovered", "Active"]].iloc[0].values
    }
    fig = px.bar(plot_data, x="x", y="y", labels={"y": "No. of Cases", "x": "Type of Case"})
    return fig

@app.callback(
    Output("geo-map", "figure"),
    [Input("case-input", "value")]
)
def geo_map(case):
    fig = px.choropleth(
        df_country,
        locations="Country/Region",
        locationmode="country names",
        color=case,
        hover_name="Country/Region",
        hover_data=[case],
        color_continuous_scale="Viridis",
        title=f"Global COVID-19 {case} Cases"
    )
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        width=1200,
        height=800
    )
    return fig

@app.callback(
    Output("top-countries-chart", "figure"),
    [Input("metric-dropdown", "value")]
)
def top_countries(metric):
    top_10 = df_country.nlargest(10, metric)
    fig = px.bar(top_10, x="Country/Region", y=metric,
                 title=f"Top 10 Countries by {metric} Cases")
    fig.update_layout(xaxis_tickangle=-45)
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)