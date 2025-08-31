"""Routes for purchasing indie release packages."""

from flask import Blueprint, jsonify, request

from backend.services.indie_release_service import IndieReleaseService

indie_release_routes = Blueprint("indie_release_routes", __name__)
service = IndieReleaseService()


@indie_release_routes.route("/indie/releases", methods=["POST"])
def purchase_release():
    data = request.json or {}
    band_id = int(data.get("band_id"))
    distribution = data.get("distribution", "digital")
    promotion = data.get("promotion", "none")
    physical = data.get("physical", "none")
    vendor_terms = data.get("vendor_terms") or {}
    release = service.purchase_release(
        band_id,
        distribution,
        promotion,
        physical,
        vendor_terms=vendor_terms,
    )
    return jsonify(release), 201


@indie_release_routes.route("/indie/releases/<int:band_id>", methods=["GET"])
def list_releases(band_id: int):
    return jsonify(service.list_releases(band_id))
