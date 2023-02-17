from flask import request, jsonify
from utils.database import db
from datetime import datetime


def create_location(app):
    @app.route("/create_location", methods=['POST'])
    def create():
        name = request.get_json().get("name")
        dimension = request.get_json().get("dimension")
        residents = request.get_json().get("residents")

        if not all([name, dimension]):
            raise ValueError("Bad Request : empty value in payload.")

        if db.location.find_one({'name': name, 'dimension': dimension}):
            return jsonify(message="Bad Request: location already exist in db.", status_code=400)

        resident_list = []
        if len(residents) > 0:
            resident_exist = db.character.find({'names': {"$all": residents}})
            for resident in resident_exist:
                resident_list.append(resident["url"])

        last_id = db.location.find({}, {"id": 1, "_id": 0}).sort("_id", -1).limit(1)
        new_id = int(last_id[0].get("id")) + 1
        data = {
            "id": new_id,
            "name": name,
            "dimension": dimension,
            "residents": resident_list,
            "url": f"https://rickandmortyapi.com/api/character/{new_id}",
            "created": datetime.now().isoformat()
        }
        db.character.insert_one(data)
        return jsonify(message="Success: location created.", data={"data": data}, status_code=201)


def delete_location(app):
    @app.route("/delete_location/<int:id>", methods=["DELETE"])
    def delete(locat_id):
        location_exist = db.location.find_one({"id": locat_id})
        if not location_exist:
            return jsonify(message="Bad Request: id not found in the db.", data=[], status_code=400)

        db.location.delete_one({"id": locat_id})

        db.character.update_many({"locations.url": location_exist["url"]},
                                 {"$set": {"locations.$.name": "unknown", "locations.$.url": ""}})

        data = {
            "id": location_exist["id"],
            "name": location_exist["name"],
            "dimension": location_exist[""],
            "residents": location_exist["residents"],
            "url": location_exist["url"],
            "created": location_exist["created"]
        }

        return jsonify(message="Success: location deleted.", data=[{"data": data}], status_code=201)


def read_location(app):
    @app.route("/read_location_all", methods=["GET"])
    def read_all():
        page = request.args.get("page", 1, type=int)
        locations = db.location.aggregate([
            {"$skip": (page - 1) * 10},
            {"$limit": 10}
        ])
        data = []
        for location in locations:
            data.append({
                "id": location["id"],
                "name": location["name"],
                "dimension": location["dimension"],
                "residents": location["residents"],
                "url": location["url"],
                "created": location["created"]
            })
        count = db.location.count_documents({})
        info = {
            "count": count,
            "pages": count // 10,
            "next": f"{request.base_url}?page={page + 1}" if page < count / 10 else None,
            "prev": f"{request.base_url}?page={page - 1}" if page > 1 else None
        }

        return jsonify(message="Success", data=[{"info": info, "data": data}], status_code=201)

    @app.route("/read_location/<int:id>", methods=['GET'])
    def read(locat_id):
        location_exist = db.location.find_one({"id": locat_id})
        if location_exist:
            data = {
                "id": location_exist["id"],
                "name": location_exist["name"],
                "dimension": location_exist["dimension"],
                "residents": location_exist["residents"],
                "url": location_exist["url"],
                "created": location_exist["created"]
            }
        else:
            return jsonify(message="Bad Request: id not found in db.", data=[], status_code=201)
        return jsonify(message="Success", data={"data": data}, status_code=201)


def update_location(app):
    @app.route("/update_location/<int:id>", methods=['PUT'])
    def update_loc(locat_id):
        location_exist = db.location.find_one({"id": locat_id})
        if not location_exist:
            return jsonify(message='Bad Request: id dont exist.', data=[], status_code=201)

        response = request.get_json()

        for key in response.keys():
            if key == 'name':
                name = response.get(key)
                if name == "":
                    return jsonify(message='Bad Request: name is empty.', data=[], status_code=201)
                else:
                    name_exist = db.location.find_one({"name": name})
                    if name_exist:
                        return jsonify(message='Bad Request: name already exist.', data=[], status_code=201)
            elif key == "dimension":
                dimension = response.get(key)
                if dimension == "":
                    response[key] = "unknown"

        db.location.update_one(response)

        return jsonify(message='Success: location updated', data=[{"data": response}], status_code=201)
