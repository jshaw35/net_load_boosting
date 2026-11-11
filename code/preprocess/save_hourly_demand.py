# %%
import os
import sys
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# %%
def load_c2e_heating_demand(c2e_path, years=np.arange(2015, 2051)):

    year_list = []
    for year in years:
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
            c2e_combined_country_GWh = c2e_combined.loc[highRES_country_codes_inv[country_code]]
            c2e_combined_country_electrified_GWh = c2e_combined_electrified.loc[highRES_country_codes_inv[country_code]]
            c2e_combined_country_GWh_ds = c2e_combined_country_GWh.to_xarray().assign_coords(country=highRES_country_codes_inv[country_code], heating_scenario="current_electrified").expand_dims(["country", "heating_scenario"])
            c2e_combined_country_electrified_GWh_ds = c2e_combined_country_electrified_GWh.to_xarray().assign_coords(country=highRES_country_codes_inv[country_code], heating_scenario="fully_electrified").expand_dims(["country", "heating_scenario"])
            country_ds = xr.combine_by_coords([c2e_combined_country_GWh_ds, c2e_combined_country_electrified_GWh_ds])[highRES_country_codes_inv[country_code]]
            country_ds.name = "heating_cooling_demand_GWh"
            country_list.append(country_ds)
        year_list.append(xr.concat(country_list, dim="country"))

        out_ds = xr.combine_by_coords(year_list).rename({"index": "time"})
        out_ds["time"] = pd.to_datetime(out_ds["time"])
    return out_ds

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
load_path = "/Users/jonahshaw/Library/CloudStorage/OneDrive-UniversitetetiOslo/Projects/pathways_planning/pathwaysplanning_highRES/demand/"
scenario = "SSP245"
c2e_wi_demand = xr.open_dataarray(
    os.path.join(load_path, f"weather-insensitive_demand_{scenario}.nc"),
).sel(time=slice("2025", "2050"), capacity_scenario=["current", "future"]).squeeze()
c2e_wi_demand = c2e_wi_demand.assign_coords(
    time=c2e_wi_demand.indexes["time"].to_datetimeindex()
)
c2e_wi_demand.name = "weather_insensitive_demand_GWh"

c2e_path = "/Users/jonahshaw/Library/CloudStorage/OneDrive-UniversitetetiOslo/Projects/pathways_planning/C2E_data/only_csv"
c2e_heatingcooling_demand = load_c2e_heating_demand(c2e_path, years=np.arange(2025, 2051))

# Select only the shared countries
shared_countries = [str(i) for i in c2e_wi_demand.country.values if i in c2e_heatingcooling_demand.country.values]
c2e_demand_merged = xr.merge([c2e_wi_demand, c2e_heatingcooling_demand]).sel(country=shared_countries).drop(["technology", "member"])

# Reindex time to hour of the year
# Add hour_of_year coordinate but make sure to remove leap days added by the dt accessor.
c2e_demand_merged = c2e_demand_merged.assign_coords(
    year=c2e_demand_merged["time.year"],
    hour_of_year=(
        c2e_demand_merged["time"].dt.dayofyear
        - 1
        - (c2e_demand_merged["time"].dt.is_leap_year & (c2e_demand_merged["time"].dt.month > 2))
    ) * 24 + c2e_demand_merged["time"].dt.hour + 1
)
# Reindex by casting to a pandas DataFrame and replacing time in the multi-index with year and hour_of_year.
c2e_demand_reindexed = xr.merge([c2e_demand_merged["weather_insensitive_demand_GWh"].to_dataframe().reset_index().set_index(["country", "capacity_scenario", "heating_scenario", "year", "hour_of_year"]).to_xarray(), c2e_demand_merged["heating_cooling_demand_GWh"].to_dataframe().reset_index().set_index(["country", "heating_scenario", "year", "hour_of_year"]).to_xarray()])

# Remove time as a variable and add it as a coordinate
c2e_demand_reindexed = c2e_demand_reindexed.drop_vars("time").assign_coords(time=c2e_demand_merged["time"])

c2e_demand_reindexed.to_netcdf(os.path.join(load_path, f"c2e_demand_merged_{scenario}.nc"))

# %%
# Example plots showing equivalence of the two datasets after reindexing
fig, ax = plt.subplots(figsize=(12, 6))
year=2036
country = "Spain"
capacity_scenario = "current"
generation_scenario = "current_electrified"
country_demand = c2e_demand_merged.sel(country=country, capacity_scenario=capacity_scenario, heating_scenario=generation_scenario, time=slice(f"{year}-01-01", f"{year}-12-31"))
country_demand = country_demand["weather_insensitive_demand_GWh"] + country_demand["heating_cooling_demand_GWh"]
ax.plot(country_demand["time"], country_demand, label=f"{country} {year} {capacity_scenario} {generation_scenario}")
ax.set_title(f"Hourly demand for {country} in {year} ({capacity_scenario}, {generation_scenario}) Total: {1e-3*country_demand.sum().values:.2f} TWh")
ax.set_xlabel("Time")
ax.set_ylabel("Hour Demand (GWh)")

fig, ax = plt.subplots(figsize=(12, 6))
year=2036
country = "Spain"
capacity_scenario = "current"
generation_scenario = "current_electrified"
country_demand = c2e_demand_reindexed.sel(country=country, capacity_scenario=capacity_scenario, heating_scenario=generation_scenario, year=year)
country_demand = country_demand["weather_insensitive_demand_GWh"] + country_demand["heating_cooling_demand_GWh"]
ax.plot(country_demand["hour_of_year"], country_demand, label=f"{country} {year} {capacity_scenario} {generation_scenario}", linestyle="--")
ax.set_title(f"Hourly demand for {country} in {year} ({capacity_scenario}, {generation_scenario}) Total: {1e-3*country_demand.sum().values:.2f} TWh")
ax.set_xlabel("Time")
ax.set_ylabel("Hour Demand (GWh)")

# %%