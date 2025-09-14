"""Seed initial climate zones."""

from models.weather import ClimateZone


def get_seed_climate_zones():
    return [
        ClimateZone(name="north", pattern="temperate", avg_high=20, avg_low=10),
        ClimateZone(name="south", pattern="tropical", avg_high=30, avg_low=20),
        ClimateZone(name="desert", pattern="arid", avg_high=35, avg_low=25),
    ]
