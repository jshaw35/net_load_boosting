# %%
import os
import sys
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    base_dir = os.getcwd()
sys.path.append(os.path.join(base_dir, "..", "utils"))
import preprocess as pc

# %%
def load_c2e_heating_demand(c2e_path):

    c2e_years = np.arange(2015, 2025)
    c2e_country_dict = {i : [] for i in highRES_country_codes}
    c2e_country_electrified_dict = {i : [] for i in highRES_country_codes}
    year_list = []
    for year in c2e_years:
        c2e_heating = pd.read_csv(f"{c2e_path}/heating-demand_{year}.csv")
        c2e_heating_electrified = pd.read_csv(f"{c2e_path}/heating-demand_{year}_fully-electrified.csv")
        c2e_cooling = pd.read_csv(f"{c2e_path}/cooling-demand_{year}.csv")
        c2e_combined = c2e_heating.set_index("country") + c2e_cooling.set_index("country")
        c2e_combined_electrified = c2e_heating_electrified.set_index("country") + c2e_cooling.set_index("country")
        country_list = []
        for country_code in highRES_country_codes:
            if highRES_country_codes_inv[country_code] not in c2e_combined.index:
                print(f"Warning: {country_code} not found in C2E data for year {year}. Skipping.")
                continue
            c2e_combined_country_TWh = c2e_combined.loc[highRES_country_codes_inv[country_code]] * 1e-3 # Convert from GWh to MWh
            c2e_combined_country_electrified_TWh = c2e_combined_electrified.loc[highRES_country_codes_inv[country_code]] * 1e-3
            c2e_combined_country_TWh_ds = c2e_combined_country_TWh.to_xarray().assign_coords(country=highRES_country_codes_inv[country_code], heating_scenario="current_electrified").expand_dims(["country", "heating_scenario"])
            c2e_combined_country_electrified_TWh_ds = c2e_combined_country_electrified_TWh.to_xarray().assign_coords(country=highRES_country_codes_inv[country_code], heating_scenario="fully_electrified").expand_dims(["country", "heating_scenario"])
            country_ds = xr.combine_by_coords([c2e_combined_country_TWh_ds, c2e_combined_country_electrified_TWh_ds])[highRES_country_codes_inv[country_code]]
            country_ds.name = "demand_TWh"
            country_list.append(country_ds)
            # country_list.append(xr.combine_by_coords([c2e_combined_country_TWh_ds, c2e_combined_country_electrified_TWh_ds]))
        year_list.append(xr.concat(country_list, dim="country"))

        out_ds = xr.combine_by_coords(year_list).rename({"index": "time"})
        out_ds["time"] = pd.to_datetime(out_ds["time"])
    return out_ds

    c2e_weather_demand_df = pd.DataFrame.from_dict(c2e_country_dict, orient="index", columns=c2e_years).T
    c2e_weather_demand_electrified_df = pd.DataFrame.from_dict(c2e_country_electrified_dict, orient="index", columns=c2e_years).T

    return c2e_weather_demand_df, c2e_weather_demand_electrified_df

    # c2e_years = np.arange(2015, 2025)
    # c2e_weather_demand = {}
    # for year in c2e_years:
    #     c2e_heating = pd.read_csv(f"{c2e_path}/heating-demand_{year}.csv")
    #     c2e_cooling = pd.read_csv(f"{c2e_path}/cooling-demand_{year}.csv")
    #     c2e_combined = c2e_heating.set_index("country") + c2e_cooling.set_index("country")
    #     c2e_combined_country_TWh = c2e_combined.loc[highRES_country_codes_inv[country_code]].sum()
    #     c2e_weather_demand[year] = c2e_combined_country_TWh
    # c2e_weather_demand_df = pd.DataFrame.from_dict(c2e_weather_demand, orient="index", columns=["C2E_heating_cooling_demand_TWh"])

    # return c2e_weather_demand_df


# %%

highRES_country_code_mapping = {
    "Austria" : "AT",
    "Belgium" : "BE",
    "Bulgaria" : "BG", #
    "Switzerland" : "CH", #
    "Czech Republic" : "CZ", #
    "Germany" : "DE",
    "Denmark" : "DK",
    "Estonia" : "EE" ,
    "Spain" : "ES",
    "Finland" : "FI", #
    "France" : "FR",
    "United Kingdom" : "UK",
    "Greece" : "GR",
    "Croatia" : "HR", #
    "Hungary" : "HU", #
    "Ireland" : "IE",
    "Italy" : "IT",
    "Lithuania" : "LT",
    "Luxembourg" : "LU",
    "Latvia" : "LV",
    "Netherlands" : "NL",
    "Norway" : "NO",
    "Poland" : "PL", #
    "Portugal" : "PT",
    "Romania" : "RO", #
    "Sweden" : "SE",
    "Slovenia" : "SI", #
    "Slovakia" : "SK" #
}
highRES_country_codes_inv = {v: k for k, v in highRES_country_code_mapping.items()}
highRES_country_codes = list(highRES_country_code_mapping.values())
highRES_countries = list(highRES_country_codes_inv.values())

# %%
load_path = os.path.join(base_dir, "..", "..", "outputs")
scenario = "SSP245"
c2e_demand = xr.open_dataarray(
    os.path.join(load_path, f"weather-insensitive_demand_{scenario}.nc")
)

c2e_path = "/Users/jonahshaw/Library/CloudStorage/OneDrive-UniversitetetiOslo/Projects/pathways_planning/C2E_data/only_csv"
c2e_heatingcooling = load_c2e_heating_demand(c2e_path)

# %%
# Load data from this dataset for comparison: https://zenodo.org/records/10820928
demand_path = os.path.join(base_dir, "..", "..", "inputs")
test_demand = pd.read_csv(os.path.join(demand_path, "demand_hourly.csv")).rename(columns={"Unnamed: 0": "time"})
test_demand["time"] = pd.to_datetime(test_demand["time"])
test_ds = test_demand.set_index("time").to_xarray().to_array().rename({"variable": "country"})

#%%
# Compare the dataset across shared years (2015 - 2023)
time_sel = slice("2015-01-01", "2023-12-31")
c2e_demand_sel = c2e_demand.sel(time=time_sel)
c2e_heatingcooling_sel = c2e_heatingcooling.sel(time=time_sel)
test_sel = test_ds.sel(time=time_sel)

# Shared countries
c2e_demand_ind_countries = set(c2e_demand_sel.country.values)
c2e_demand_heating_countries = set(c2e_heatingcooling_sel.country.values)
highres_countries = set(highRES_country_codes_inv[c] for c in test_sel.country.values if c in highRES_country_codes_inv)
shared_countries = list(c2e_demand_ind_countries & c2e_demand_heating_countries & highres_countries)

# %%
c2e_sel_dict = {
    "heating_scenario": "current_electrified",
    "capacity_scenario": "current",
}
for country in shared_countries:
    fig, ax = plt.subplots(figsize=(12, 6))
    c2e_country = c2e_demand_sel.sel(country=country, **c2e_sel_dict).squeeze()*1e3
    c2e_country_heating = c2e_heatingcooling_sel['demand_TWh'].sel(country=country, heating_scenario="current_electrified").squeeze()*1e6
    assert len(c2e_country["time"]) == len(c2e_country_heating["time"]), f"Time dimension mismatch for country {country}"
    c2e_country_heating["time"] = c2e_country["time"]
    c2e_total = c2e_country + c2e_country_heating
    c2e_average_year = c2e_country.groupby("time.dayofyear").mean(dim="time")
    test_country = test_sel.sel(country=highRES_country_code_mapping[country])
    test_average_year = test_country.groupby("time.dayofyear").mean(dim="time")
    years = pd.Series(c2e_country["time.year"].values).unique()
    # C2E independent demand
    for year in years:
        year_data = c2e_country.sel(time=c2e_country["time.year"] == year)
        ax.plot(
            year_data["time.dayofyear"], year_data,
            alpha=0.15,
            c="blue"
        )
    ax.plot(
        c2e_average_year["dayofyear"], c2e_average_year,
        c="blue",
        # label=f"C2E ind. {year}",
    )
    # C2E heating demand
    for year in years:
        year_data = c2e_country_heating.sel(time=c2e_country_heating["time.year"] == year)
        ax.plot(
            year_data["time.dayofyear"], year_data,
            alpha=0.25,
            c="green"
        )
    ax.plot(
        c2e_country_heating.groupby("time.dayofyear").mean(dim="time")["dayofyear"], 
        c2e_country_heating.groupby("time.dayofyear").mean(dim="time"),
        c="green",
        zorder=10,
    )
    # Plot combined C2E demand
    for year in years:
        year_data = c2e_total.sel(time=c2e_total["time.year"] == year)
        ax.plot(
            year_data["time.dayofyear"], year_data,
            alpha=0.15,
            c="purple"
        )
    ax.plot(
        c2e_total.groupby("time.dayofyear").mean(dim="time")["dayofyear"], 
        c2e_total.groupby("time.dayofyear").mean(dim="time"),
        c="purple",
        zorder=10,
    )
    # Test dataset
    for year in years:
        year_data = test_country.sel(time=test_country["time.year"] == year)
        ax.plot(
            year_data["time.dayofyear"], year_data,
            alpha=0.12,
            c="orange",
            zorder=0,
        )
    ax.plot(
        test_average_year["dayofyear"], test_average_year,
        c="orange",
        zorder=10,
    )
    fig.suptitle(f"Hourly demand comparison for {country} (2015-2023) C2E {1e-6*c2e_total.groupby("time.year").sum().mean().values:.2f} TWh, Test dataset {1e-6*24*test_average_year.sum().values:.2f} TWh",y=0.92)
    # ax.text(0.02, 0.94, f"Avg. annual demand: C2E {1e-6*c2e_total.groupby("time.year").sum().mean().values:.2f} TWh, Test dataset {1e-6*24*test_average_year.sum().values:.2f} TWh", ha="left", fontsize=10, transform=fig.transFigure)
    # plt.legend()
    plt.show()
    # break

# %%
c2e_current_dict = {
    "heating_scenario": "current_electrified",
    "capacity_scenario": "current",
}
c2e_future_dict = {
    "heating_scenario": "fully_electrified",
    "capacity_scenario": "future",
}
for country in shared_countries:
    fig, ax = plt.subplots(figsize=(12, 6))
    title = f"Hourly demand comparison for {country} (2015-2023)"

    test_country = test_sel.sel(country=highRES_country_code_mapping[country])
    test_average_year = test_country.groupby("time.dayofyear").mean(dim="time")
    years = pd.Series(test_country["time.year"].values).unique()

    title += f" Test dataset {1e-6*24*test_average_year.sum().values:.2f} TWh"

    # Test dataset
    for year in years:
        year_data = test_country.sel(time=test_country["time.year"] == year)
        ax.plot(
            year_data["time.dayofyear"], year_data,
            alpha=0.12,
            c="orange",
            zorder=0,
        )
    ax.plot(
        test_average_year["dayofyear"], test_average_year,
        c="orange",
        zorder=10,
        label=f"Test dataset"
    )

    for scenario, c2e_sel_dict, color in zip(["Current", "Future"], [c2e_current_dict, c2e_future_dict], ["blue", "green"]):

        c2e_country = c2e_demand_sel.sel(country=country, **c2e_sel_dict).squeeze()*1e3
        c2e_country_heating = c2e_heatingcooling_sel['demand_TWh'].sel(country=country, heating_scenario=c2e_sel_dict["heating_scenario"]).squeeze()*1e6
        assert len(c2e_country["time"]) == len(c2e_country_heating["time"]), f"Time dimension mismatch for country {country}"
        c2e_country_heating["time"] = c2e_country["time"]
        c2e_total = c2e_country + c2e_country_heating
        c2e_average_year = c2e_total.groupby("time.dayofyear").mean(dim="time")

        title += f", C2E {scenario} {24*1e-6*c2e_average_year.sum().values:.2f} TWh"

        # Plot combined C2E demand
        for year in years:
            year_data = c2e_total.sel(time=c2e_total["time.year"] == year)
            ax.plot(
                year_data["time.dayofyear"], year_data,
                alpha=0.15,
                c=color,
            )
        ax.plot(
            c2e_average_year["dayofyear"], 
            c2e_average_year,
            c=color,
            zorder=10,
            label=f"C2E {scenario}",
        )
    fig.suptitle(title,y=0.92)

    plt.legend()
    plt.show()
    # break

# %%