import os
import json
import sys
import threading
import time

from src import commands, groups, device, logger, utils
from flask import Flask, request, json

# logger
logger = logger.Logger("app")

# data lock
lock = threading.RLock()


def create_app(test_config=None):
    def merge_data():
        path = "data/IR"
        interval = 60

        while (True):
            time.sleep(interval)

            logger.info("Merging data - Critical section begins ")
            starttime = time.time()
            lock.acquire()
            utils.wipe_folder(path)
            dict = {}
            dict["device"] = {
                "host": deviceUnit.device.host,
                # "mac":deviceUnit.device.mac,
                "devtype": deviceUnit.device.devtype
            }
            dict["commands"] = list(map(lambda x: {"name": x}, commandFactory.get_all()))
            dict["groups"] = groupFactory.get_all()

            for cmd in commandFactory.list:
                name = cmd["name"]
                cmd_path = path + "/" + name
                try:
                    file = open(cmd_path, "wb+")
                    file.write(cmd["sequence"])
                    file.close()
                except FileNotFoundError:
                    logger.error("IR file not found")
                    return
            jdict = json.dumps(dict, indent=4)
            file = open("data/config.json", "w")
            file.write(jdict)
            file.close()
            lock.release()
            elapsed = time.time() - starttime
            logger.debug(jdict)
            logger.info("Merging data - Critical section ends Took: " + str(elapsed) + "s")

    # fetch data
    logger.info("Fetching data")
    json_data = open('data/config.json').read()
    data = json.loads(json_data)
    try:
        commandFactory = commands.Commands(data["commands"])
        groupFactory = groups.Groups(data["groups"])
        deviceUnit = device.Device(data)
    except Exception as e:
        logger.error("Command/Group/Device creation error: " + str(e))
        sys.exit(1)

    # create and configure the app
    logger.info("Creating app")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Job schedule
    logger.info("Thread setup")
    thread = threading.Thread(target=merge_data)
    thread.start()

    @app.route('/', methods=['GET'])
    def greet():
        return "Black Bean app running"

    @app.route('/groups', methods=['GET'])
    def list_groups():
        response = app.response_class(
            response=json.dumps(groupFactory.get_all()),
            status=200,
            mimetype='application/json'
        )
        return response

    @app.route('/groups/<name>', methods=['GET', 'POST', 'DELETE'])
    def group(name):
        group = groupFactory.get(name)
        if request.method == 'POST':
            if group:
                return app.response_class(
                    response=json.dumps({"error": "Group already exists"}),
                    status=404,
                    mimetype='application/json'
                )
            else:
                group = groupFactory.create(name)
                return app.response_class(
                    response=json.dumps(group),
                    status=200,
                    mimetype='application/json'
                )
        else:
            if not group:
                return app.response_class(
                    response=json.dumps({"error": "Group not found"}),
                    status=404,
                    mimetype='application/json'
                )
            if request.method == 'GET':
                for cmd_name in group["commands"]:
                    command = commandFactory.get(cmd_name)
                    if command:
                        deviceUnit.send_command(command)

                return app.response_class(
                    response=json.dumps(group),
                    status=200,
                    mimetype='application/json'
                )
            if request.method == 'DELETE':
                groupFactory.delete(name)
                return app.response_class(
                    status=204,
                    mimetype='application/json'
                )
            else:
                return app.response_class(
                    response=json.dumps({"error": "Unknown method"}),
                    status=400,
                    mimetype='application/json'
                )

    @app.route('/groups/<name>/<command>', methods=['POST', 'DELETE'])
    def edit_group(name, command):
        group = groupFactory.get(name)
        command_dict = commandFactory.get(command)
        if not group:
            return app.response_class(
                response=json.dumps({"error": "Group not found"}),
                status=404,
                mimetype='application/json'
            )
        if not command_dict:
            return app.response_class(
                response=json.dumps({"error": "Command not found"}),
                status=404,
                mimetype='application/json'
            )
        if request.method == 'POST':
            response = groupFactory.add(name, command)
            print(response)
            status=200
            if not response:
                response={"error":"Command already in a group"}
                status = 400

            return app.response_class(
                response=json.dumps(response),
                status=status,
                mimetype='application/json'
            )

        if request.method == 'DELETE':
            response = groupFactory.remove(name, command)
            status = 200
            if not response:
                response = {"error": "Error removing command"}
                status = 400

            return app.response_class(
                # response=json.dumps(response),
                status=status,
                mimetype='application/json'
            )


    @app.route('/commands', methods=['GET'])
    def list_commands():
        response = app.response_class(
            response=json.dumps(commandFactory.get_all()),
            status=200,
            mimetype='application/json'
        )
        return response

    @app.route('/commands/<name>', methods=['GET', 'POST', "DELETE"])
    def command(name):
        if request.method == 'POST':
            if name not in commandFactory.get_all():
                lock.acquire()
                sequence = deviceUnit.learn_command()
                command = {
                    "name": name,
                    "sequence": sequence
                }
                commandFactory.add(command)
                response = app.response_class(
                    response=json.dumps({"name": name}),
                    status=200,
                    mimetype='application/json'
                )
                lock.release()
            else:
                response = app.response_class(
                    response=json.dumps({"error": "That command already exists"}),
                    status=400,
                    mimetype='application/json')

            return response
        else:
            command = commandFactory.get(name)
            if not command:
                logger.error("Command " + name + " not found")
                return app.response_class(
                    response=json.dumps({"error": "Command not found"}),
                    status=404,
                    mimetype='application/json'
                )
            if request.method == 'GET':
                deviceUnit.send_command(command)
                return app.response_class(
                    status=204,
                    mimetype='application/json'
                )
            elif request.method == 'DELETE':
                commandFactory.delete(command)
                return app.response_class(
                    status=204,
                    mimetype='application/json'
                )

    return app
