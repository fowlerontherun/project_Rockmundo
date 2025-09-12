from models.transport import Transport, TransportBooking
from models.ai_tour_manager import AITourManagerSettings
from typing import List

# Dummy in-memory transport fleet
fleet: List[Transport] = []
transport_bookings: List[TransportBooking] = []

def optimize_transport_for_tour(band_id: int, total_gear_weight: float, crew_size: int, budget: float):
    suitable_options = []
    for transport in fleet:
        if (transport.capacity_weight >= total_gear_weight and 
            transport.capacity_people >= crew_size and 
            transport.rental_cost <= budget):
            suitable_options.append(transport)

    if not suitable_options:
        return None

    # Sort by lowest cost for now
    selected = sorted(suitable_options, key=lambda t: t.rental_cost)[0]

    booking = TransportBooking(
        band_id=band_id,
        transport_id=selected.id,
        cost=selected.rental_cost,
        status="booked"
    )
    transport_bookings.append(booking)
    return booking

def get_transport_bookings():
    return transport_bookings