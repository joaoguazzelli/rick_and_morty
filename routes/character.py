from flask import request, jsonify
from utils.database import db
from datetime import datetime


def create_char(app):
    @app.route('/create_char', methods=['POST'])
    def create():
        name = request.get_json().get("name")
        status = request.get_json().get("status")
        species = request.get_json().get("species")
        gender = request.get_json().get("gender")
        origin = request.get_json().get("origin")
        location = request.get_json().get("location")

        if not all([name, status, species, gender, origin, location]):
            raise ValueError("Bad Request : empty value in payload.")
        if status not in ["Alive", "Dead", "unknown"]:
            raise ValueError("Bad Request : status value not in [Dead, Alive, unknow].")
        if gender not in ["Male", "Female", "Genderless", "unknow"]:
            raise ValueError("Bad Request : gender value not in [Male, Female, Genderless, unknow].")
        if location == 'unknown' or not db.location.find_one({"name": location}):
            raise ValueError("Bad Request : location name dont exist in db.")
        if not db.location.find_one({"name": origin}):
            raise ValueError("Bad Request : origin name dont exist in db.")

        location_url = ""
        origin_url = ""
        if origin != 'unknow':
            origin_url = db.location.find_one({"name": origin}, {"url": 1, "_id": 0})["url"]
        if location != 'unknow':
            location_url = db.location.find_one({"name": location}, {"url": 1, "_id": 0})["url"]

        if db.character.find_one(
                {"name": name, "status": status, "species": species, "gender": gender, "origin": [origin, origin_url],
                 "location": [location, location_url]}):
            return jsonify(message="Bad Request: character already exist in db.", status_code=400)

        last_id = db.character.find({}, {"id": 1, "_id": 0}).sort("_id", -1).limit(1)
        new_id = int(last_id[0].get("id")) + 1
        data = {
            "id": new_id,
            "name": name,
            "status": status,
            "species": species,
            "gender": gender,
            "origin": [origin, origin_url],
            "location": [location, location_url],
            "url": f"https://rickandmortyapi.com/api/character/{new_id}",
            "created": datetime.now().isoformat()
        }
        db.character.insert_one(data)
        return jsonify(message="Success: character created.", data={"data": data}, status_code=201)


def delete_char(app):
    @app.route('/delete_char/<int:id>', methods=['DELETE'])
    def delete(char_id):
        char = db.character.find_one({"id": id})
        if not char:
            return jsonify(message='Bad Request: id not found in the db.', data=[], status_code=400)
        db.character.delete_one({'id': char_id})
        db.location.update_many({}, {"$pull": {"residents": char['url']}})

        data = {
            "id": id,
            "name": char["name"],
            "status": char["status"],
            "species": char["species"],
            "gender": char["gender"],
            "origin": char["origin"],
            "location": char["location"],
            "url": char["url"],
            "created": char["created"]
        }

        return jsonify(message="Success: character deleted.", data=[{"data": data}], status_code=201)


def read_char(app):
    @app.route('/read_char_all', methods=['GET'])
    def read_all():
        page = request.args.get("page", 1, type=int)
        characters = db.character.aggregate([
            {"$skip": (page - 1) * 10},
            {"$limit": 10}
        ])
        data = []
        for character in characters:
            data.append({
                "id": character["id"],
                "name": character["name"],
                "status": character["status"],
                "species": character["species"],
                "gender": character["gender"],
                "origin": character["origin"],
                "location": character["location"],
                "url": character["url"],
                "created": character["created"]
            })
        count = db.character.count_documents({})
        info = {
            "count": count,
            "pages": count // 10,
            "next": f"{request.base_url}?page={page + 1}" if page < count / 10 else None,
            "prev": f"{request.base_url}?page={page - 1}" if page > 1 else None
        }

        return jsonify(message="Success", data={"info": info, "data": data}, status_code=201)

    @app.route("/read_char/<int:id>", methods=['GET'])
    def read(char_id):
        char = db.character.find_one({"id": char_id})
        if char:
            data = {
                "id": char["id"],
                "name": char["name"],
                "status": char["status"],
                "species": char["species"],
                "gender": char["gender"],
                "origin": char["origin"],
                "location": char["location"],
                "url": char["url"],
                "created": char["created"]
            }
        else:
            return jsonify(message="Bad Request: id not found in db.", data=[], status_code=400)
        return jsonify(message="Success", data={"data": data}, status_code=201)


def update_char(app):
    @app.route('/update', methods=['PUT'])
    def update(char_id):
        character_exist = db.character.find_one({"id": id})
        if not character_exist:
            return jsonify(message='Bad Request: id dont exist.', data=[], status_code=201)

        response = request.get_json()

        for key in response.keys():
            if key == 'status':
                if response.get(key) != 'unknown':
                    if not response.get(key) in ["Alive", "Dead", "unknown"]:
                        return jsonify(message='Bad Request : status value not in [Dead, Alive, unknown].')

            elif key == 'gender':
                if response.get(key) != 'unknown':
                    if not response.get(key) in ["Male", "Female", "Genderless", "unknown"]:
                        return jsonify(message='Bad Request : gender value not in [Male, Female, Genderless, unknown].')
            elif key == "location":
                if response.get(key) != "unknow":
                    if not db.location.find_one({"name": response.get(key)}):
                        return jsonify(message="Bad Request : location name dont exist in db.", status_code=400)
            elif key == "origin":
                if response.get(key) != "unknow":
                    if not db.location.find_one({"name": response.get(key)}):
                        return jsonify(message="Bad Request : origin name dont exist in db.", status_code=400)

            if response.get(key) == "":
                return jsonify(message=f'Bad Request: {key} value is invalid.', data=[], status_code=400)

        db.character.update_one(response)

        return jsonify(message='Success: character updated', data=[{"data": response}], status_code=201)
