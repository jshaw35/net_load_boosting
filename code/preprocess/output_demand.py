# %%
import os
import sys

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    base_dir = os.getcwd()
sys.path.append(os.path.join(base_dir, "..", "utils"))
import preprocess as pc

# %%
scenario = "SSP245"
members = ["A"]
boost = None
ds_demand = pc.open_weather_insensitive_demand(scenario, boost, members)

# %%
out_path = os.path.join(base_dir, "..", "..", "outputs")
os.makedirs(out_path, exist_ok=True)
ds_demand.to_dataset(name="GWh").to_netcdf(
    os.path.join(out_path, f"weather-insensitive_demand_{scenario}.nc")
)

# %%