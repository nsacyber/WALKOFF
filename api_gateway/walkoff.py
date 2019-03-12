from gevent import monkey

monkey.patch_all()  # noqa: Monkey patching needs to occur as early as possible.

import argparse
import logging
import os
import sys
import traceback

from gevent import pywsgi

import api_gateway

# ToDo: For now, these two imports need to be in this order. We init the config, then init the app based on the config
import api_gateway.config
from api_gateway.server.app import app

app.debug = True

# from api_gateway.jsonplaybookloader import load_workflow
# from api_gateway.executiondb.workflow import Workflow
# from api_gateway.helpers import compose_api

logger = logging.getLogger('API-GATEWAY')


def run(host, port, debug):
    print_banner()
    server = setup_server(host, port, debug)
    server.serve_forever()


def print_banner():
    banner = f'***** Running WALKOFF v.{api_gateway.__version__} *****'
    header_footer_banner = '*' * len(banner)
    logger.info(header_footer_banner)
    logger.info(banner)
    logger.info(header_footer_banner)


def setup_server(host, port, debug):
    if os.path.isfile(api_gateway.config.Config.CERTIFICATE_PATH) and os.path.isfile(
            api_gateway.config.Config.PRIVATE_KEY_PATH):
        server = pywsgi.WSGIServer((host, port), application=app,
                                   keyfile=api_gateway.config.Config.PRIVATE_KEY_PATH,
                                   certfile=api_gateway.config.Config.CERTIFICATE_PATH)
        protocol = 'https'
    else:
        logger.warning('Cannot find certificates. Using HTTP')
        server = pywsgi.WSGIServer((host, port), application=app)
        protocol = 'http'

    logger.info(f'Listening on host {protocol}://{host}:{port}')
    return server


def parse_args():
    parser = argparse.ArgumentParser(description="Entrypoint for WALKOFF API Gateway")
    parser.add_argument('-v', '--version', help="Print current version of WALKOFF", action='store_true')
    parser.add_argument('-p', '--port', help="Port to bind the API Gateway to")
    parser.add_argument('-i', '--ip', help="IP to bind the API Gateway to", type=int)
    parser.add_argument('-c', '--config', help="Configuration file to use")
    parser.add_argument('-d', '--debug', help="Enable debug mode", action="store_true")  # ToDo: does nothing
    args_ = parser.parse_args()
    if args_.version:
        print(api_gateway.__version__)
        exit(0)

    return args_


def convert_host_port(args_):
    ip = api_gateway.config.Config.IP if args_.ip is None else args_.ip
    port = api_gateway.config.Config.PORT if args_.port is None else args_.port
    return ip, port


#
# def import_workflows():
#     if os.path.exists(api_gateway.config.Config.WORKFLOWS_PATH):
#         workflow_ids = [workflow.id_ for workflow in app.running_context.execution_db.session.query(Workflow).all()]
#         workflow_names = [workflow.name for workflow in app.running_context.execution_db.session.query(Workflow).all()]
#
#         logger.info(f"Importing workflows from {api_gateway.config.Config.WORKFLOWS_PATH}")
#
#         for p in os.listdir(api_gateway.config.Config.WORKFLOWS_PATH):
#             full_path = os.path.join(api_gateway.config.Config.WORKFLOWS_PATH, p)
#
#             if os.path.isfile(full_path):
#                 workflow = load_workflow(full_path)
#                 if not workflow:
#                     logger.info(f"Could not load {p}.")
#                 elif workflow.id_ in workflow_ids:
#                     logger.info(f"Could not load {p}: Workflow with ID {workflow.id_} already exists.")
#                 elif workflow.name in workflow_names:
#                     logger.info(f"Could not load {p}: Workflow with name {workflow.name} already exists.")
#                 else:
#                     logger.info(f"Imported {p} with ID {workflow.id_} and name {workflow.name}.")
#                     app.running_context.execution_db.session.add(workflow)
#
#         app.running_context.execution_db.session.commit()


if __name__ == "__main__":
    args = parse_args()
    exit_code = 0
    # import_workflows()
    try:
        run(*convert_host_port(args), args.debug)
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt! Please wait a few seconds for WALKOFF to shut down.')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exc()
        exit_code = 1
    finally:
        logger.info('Shutting down server')
        sys.exit(exit_code)
