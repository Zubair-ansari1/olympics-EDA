from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from shiny.express import ui, input, render
from shiny import reactive
import folium
from folium.plugins import HeatMap

ui.page_opts()

directory = Path(__file__).parent.parent
nocs = pd.read_csv(f"{directory}/clean-data/noc_regions.csv")
noc_to_region = dict(zip(nocs['NOC'], nocs['region']))

with ui.layout_sidebar():
    with ui.sidebar(open='open', width=190):
        ui.input_select("country","Select Country", noc_to_region, selected='IND')
        ui.input_checkbox("winter","Include winter games?", True)
        ui.input_checkbox("medalists","only include medalists?", False)

    with ui.card():
        "Medals"
        @render.plot
        def show_medals():
            df = get_medals()
            plt.plot(df["year"], df["medal"])
            plt.xlabel("Year")
            plt.ylabel("Medal count")
            plt.title("Medals by year")
            # plt.tight_layout()
            
        #    return get_medals()
        # print medals by country over time

    with ui.card():
        "Heatmap"
        @render.ui
        def show_heatmap():
            df = bios_df()
            m = folium.Map(location=[df["lat"].mean(), df["long"].mean()], zoom_start=2)
            heat_data = [[row["lat"], row["long"]] for index, row in df.iterrows()]
            HeatMap(heat_data).add_to(m)
            return m

    with ui.card():        
        @render.data_frame
        def result():
            return results_df().head(100)
            # return df.head(100)

@reactive.calc
def bios_df():
    directory = Path(__file__).parent.parent
    bios = pd.read_csv(f"{directory}/clean-data/bios_locs.csv")
    bios = bios[bios["born_country"] == input.country()]
    country_df = bios[(bios["lat"].notna()) & (bios["long"].notna())]
    return country_df

@reactive.calc
def results_df():
    directory = Path(__file__).parent.parent
    df = pd.read_csv(f"{directory}/clean-data/results.csv")
    df = df[df["noc"] == input.country()]
    if not input.winter():
        df = df[df["type"] == 'Summer']
    if input.medalists():
        df = df[df["medal"].notna()]    
    return df

@reactive.calc
def get_medals():
    df = results_df()
    medals = df[(df['medal'].notna()) & (~df["event"].str.endswith("(YOG)"))]
    medals_filtered = medals.drop_duplicates(['year','type','discipline','event','noc','medal'])
    medals_by_year = medals_filtered.groupby(["noc","year"])["medal"].count().loc[input.country()]
    return medals_by_year.reset_index()

