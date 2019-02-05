import json, threading, os, time, atexit

from flask import Flask, request, json
from functools import partial
from .model import manager
from .util import logger
from apscheduler.schedulers.background import BackgroundScheduler

# logger
logger = logger.Logger("app")

# data lock
lock = threading.RLock()
print(lock)

static_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
config_path = os.path.join(static_file, 'data/config.json')
ir_path = os.path.join(static_file, 'data/IR')

manager = manager.Manager(config_path, ir_path)
command_manager = manager.commandManager
group_manager = manager.groupManager
device = manager.deviceUnit


def create_app(test_config=None):
        # create and configure the app
        app = Flask(__name__, instance_relative_config=True, static_url_path='/static')
        app.config.from_mapping(
            SECRET_KEY='b\x83\xa2\xd2\xb1l\xf3\x0b2\x88\xc3\x82j\xc6\xc9\xd9w',
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

        @app.before_first_request
        def init_scheduler():
            global lock
            print(lock)
            scheduler = BackgroundScheduler()
            execute = partial(manager.merge_data, lock)
            scheduler.add_job(func=execute, trigger="interval", seconds=10)
            scheduler.start()
            # Shut down the scheduler when exiting the app
            atexit.register(lambda: scheduler.shutdown())

        @app.route('/', methods=['GET'])
        def greet():
            return "Black Bean app running"

        @app.route('/groups', methods=['GET'])
        def list_groups():
            response = app.response_class(
                response=json.dumps(group_manager.get_all()),
                status=200,
                mimetype='application/json'
            )
            return response

        @app.route('/groups/<name>', methods=['GET', 'POST', 'DELETE'])
        def group(name):
            group = group_manager.get(name)

            if request.method == 'POST':
                if group:
                    return app.response_class(
                        response=json.dumps({"error": "Group already exists"}),
                        status=404,
                        mimetype='application/json'
                    )
                else:
                    group = group_manager.create(name)
                    return app.response_class(
                        response=json.dumps(group),
                        status=200,
                        mimetype='application/json'
                    )

            elif request.method =='GET':
                if not group:
                    return app.response_class(
                        response=json.dumps({"error": "Group not found"}),
                        status=404,
                        mimetype='application/json'
                    )
                else:
                    for cmd_name in group["commands"]:
                        command = command_manager.get(cmd_name)
                        if command:
                            device.send_command(command)

                    return app.response_class(
                        response=json.dumps(group),
                        status=200,
                        mimetype='application/json'
                    )

            elif request.method == 'DELETE':
                    group_manager.delete(name)
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
            group = group_manager.get(name)
            command_dict = command_manager.get(command)
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
                response = group_manager.add(name, command)
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
                response = group_manager.remove(name, command)
                return app.response_class(
                    status=204,
                    mimetype='application/json'
                )


        @app.route('/commands', methods=['GET'])
        def list_commands():
            response = app.response_class(
                response=json.dumps(command_manager.get_all()),
                status=200,
                mimetype='application/json'
            )
            return response

        @app.route('/commands/<name>', methods=['GET', 'POST', "DELETE"])
        def command(name):
            command = command_manager.get(name)
            if request.method == 'POST':
                if name not in command_manager.get_all():
                    lock.acquire()
                    sequence = device.learn_command()
                    command = {
                        "name": name,
                        "sequence": sequence
                    }
                    command_manager.add(command)
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

            elif request.method == 'GET':
                if not command:
                    logger.error("Command " + name + " not found")
                    return app.response_class(
                        response=json.dumps({"error": "Command not found"}),
                        status=404,
                        mimetype='application/json'
                    )
                else:
                    device.send_command(command)
                    return app.response_class(
                        status=204,
                        mimetype='application/json'
                    )
            elif request.method == 'DELETE':
                try:
                    command_manager.delete(command)
                except TypeError:
                    pass

                return app.response_class(
                    status=204,
                    mimetype='application/json'
                )

        return app
