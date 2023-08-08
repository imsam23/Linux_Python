import copy
import json
import yaml
import traceback
import ast
import time
import os
from constants import *
from config_api import *
from realm_util import resolve_auth_group_realm, is_wsa_https_proxy_enabled, is_umbrella_https_inspection_enabled, get_web_proxy_mode
from datetime import datetime
from adc_util import ADCConverter
HYBRID_REPORTING_PATH = '/data/db/reporting/db/hybrid_reporting/'
POLICY_DATA_FILE_PATH = '/data/db/reporting/db/hybrid_reporting/policy_data'

class WorkerService:
    def __init__(self, logger=None):
        self.logger = logger
        self.hybrid_reporting_enabled = False
        self.payload_hash = None

    def set_hybrid_reporting_status(self, status):
        self.hybrid_reporting_enabled = status
        self.logger.debug("Updating hybrid_reporting_enabled value [%d]", self.hybrid_reporting_enabled)

    def log_payload_messages(self, payload, policy_counter):
        client_logs = payload.get(LOGGING, [])
        fail_policy = False
        failure_messages = []
        for client_log in client_logs:
            if client_log.get('fail_policy'):
                fail_policy = True
                failure_message = client_log.get('failure_message', '')
                failure_messages.append(str(failure_message))
            # Currently container does not send any logs but we can send logs in future if needed
            for log in client_log.get('logs', []):
                level = log.get('level')
                message = log.get('message')
                if level and message:
                    message = 'Hybrid Umbrella Log: ' + message
                    if level == 'debug':
                        self.logger.debug(message)
                    elif level == 'info':
                        self.logger.info(message)
                    elif level == 'warn':
                        self.logger.warn(message)
                    elif level == 'error':
                        self.logger.error(message)
                    elif level == 'info_alert':
                        self.logger.info_alert(message)
                    elif level == 'warning_alert':
                        self.logger.warning_alert(message)
                    elif level == 'error_alert':
                        self.logger.error_alert(message)

        if fail_policy:
            return {
                POLICY_COUNTER: policy_counter,
                "policy_applied": False,
                "response_json": {"message": ', '.join(failure_messages)}
            }

    def remove_old_policy_data(self, path, filename):
        try:
            files = os.listdir(path)
            paths = [os.path.join(path, basename) for basename in files]
            for file in paths:
                if file != filename:
                    os.remove(file)
        except Exception as e:
            self.logger.debug("Could not remove the old policy files %s ", str(e))

    def save_reporting_data(self, payload):
        # check if reporting payload is list and has atleast a single entry
        if type(payload) == list and len(payload) > 0:
            policy_data = payload[0]
            self.logger.debug("hybrid reporting is enabled and available in payload  %s", policy_data)
            try:
                # create HYBRID_REPORTING_PATH path if it doesn't exist
                if not os.path.isdir(HYBRID_REPORTING_PATH):
                    self.logger.debug('The directory %s is not present. Creating it..', HYBRID_REPORTING_PATH)
                # create the POLICY_DATA_FILE_PATH if doesn't exist
                if not os.path.isdir(POLICY_DATA_FILE_PATH):
                    self.logger.debug('The directory %s is not present. Creating it..', POLICY_DATA_FILE_PATH)
                    os.mkdir(POLICY_DATA_FILE_PATH)
                now = datetime.now()
                filename = POLICY_DATA_FILE_PATH + '/' + 'policy_' + now.strftime("%d%m%y%H%M%S") + '.data'
                # dump the reporting data into policy data file
                with open(filename, 'w') as f_name:
                    json.dump(policy_data, f_name)
                if os.path.exists(filename):
                    self.remove_old_policy_data(POLICY_DATA_FILE_PATH, filename)
            except Exception as ex:
                self.logger.error("Could not write into policy file %s, reason[%s]", filename, str(ex))
                pass
            self.logger.debug("Saved the reporting data in [%s]", filename)

    def pre_apply_config_validation(self, payload, policy_counter):
        unresolved_domains_err = resolve_auth_group_realm(payload)
        if unresolved_domains_err:
            return {
                POLICY_COUNTER: policy_counter,
                "policy_applied": False,
                "response_json": {"message": unresolved_domains_err}
            }

        umbrella_https_proxy_enabled = is_umbrella_https_inspection_enabled(payload)
        self.logger.debug("Umbrella https proxy enabled is %s", umbrella_https_proxy_enabled)
        ok, wsa_https_proxy_enabled = is_wsa_https_proxy_enabled()
        if not ok:
            self.logger.info("HTTPS Proxy Status: %s", wsa_https_proxy_enabled)
            return {
                POLICY_COUNTER: policy_counter,
                "policy_applied": False,
                "response_json": {"message": wsa_https_proxy_enabled}
            }
        if umbrella_https_proxy_enabled and not wsa_https_proxy_enabled:
            msg = "Decryption Policies are currently disabled. " \
                  "To use Decryption Policies, enable the HTTPS Proxy service in SWA."
            return {
                POLICY_COUNTER: policy_counter,
                "policy_applied": False,
                "response_json": {"message": msg}
            }
        elif not umbrella_https_proxy_enabled and not wsa_https_proxy_enabled:
            # if both wsa https proxy and umbrella https proxy disabled then remove the decryption payload
            if payload.get(DECRYPTION_POLICIES):
                decryption_policies = payload.pop(DECRYPTION_POLICIES)
                self.logger.debug("Removed decryption payload is %s", decryption_policies)

        # Removed use_forward_surrogates from identification profile paylod
        # as 'use_forward_surrogates' is not allowed if, web_proxy is already in 'forward' mode
        ok, proxy_mode = get_web_proxy_mode()
        if not ok:
            self.logger.info("Web proxy mode: %s", proxy_mode)
            return {
                POLICY_COUNTER: policy_counter,
                "policy_applied": False,
                "response_json": {"message": proxy_mode}
            }
        elif proxy_mode == WEB_PROXY_MODE_FORWARD:
            for id_profile in payload.get(IDENTIFICATION_PROFILES, []):
                id_profile.get('identification_method', {}).pop('use_forward_surrogates', None)
        if len(payload.get(ACCESS_POLICIES, [])):
            ADCConverter(self.logger).update_ap_adc(payload[ACCESS_POLICIES])

    def serve(self, payload, conn):
        self.payload_hash = None
        # Applies Config Payload data to local WSA
        # Handles Full config and Delta config payload
        policy_counter = 0
        try:
            payload = json.dumps(payload)
            payload = yaml.safe_load(yaml.safe_load(payload))
            # check if reporting key is available then take out from payload
            if REPORTING_DATA in payload:
                pdata = payload.pop(REPORTING_DATA)
                # check if hybrid reporting is enable then save the reporting payload
                if self.hybrid_reporting_enabled:
                    self.save_reporting_data(pdata)
            if POLICY_COUNTER in payload:
                policy_counter = payload[POLICY_COUNTER]
            self.payload_hash = payload.get("payload_hash")
            # Handle logging of messages sent from hybrid umbrella container side
            response = self.log_payload_messages(payload, policy_counter)
            # If there is any umbrella container log message then fail policy
            if response:
                return response
            response = self.pre_apply_config_validation(payload, policy_counter)
            if response:
                self.logger.info("Response: %s", response)
                return response
            # payload = json.loads(payload)
        except Exception as err:
            self.logger.error('Unexpected error while pre validating config: %s' % err)
            return {"response_json": {"message": PAYLOAD_INVALID},
                    "payload": payload}
        if isinstance(payload, str) or isinstance(payload, unicode):
            return {"response_json": {"message": PAYLOAD_INVALID},
                    "payload": payload}
        if not payload:
            return {"response_json": {"message": PAYLOAD_EMPTY},
                    "payload": payload}
        if CONFIGURATION_TYPE not in payload:
            payload[CONFIGURATION_TYPE] = FULL_CONFIG
            # return MISSING_CONF_TYPE

        response = {"message": "Exception - config apply failed"}
        config_filename = None
        try:
            config_filename = self.save_config()
            self.logger.log_trace("SWA Payload:\n%s\n", payload)
            response = self.apply_config(payload)
        except Exception as err:
            self.logger.error('Unexpected error while applying config: %s' % err)
        finally:
            if response and config_filename:
                self.revert_config(config_filename)
            if os.path.exists(SAVED_CONFIG_FILE_LOCATION + config_filename):
                os.remove(SAVED_CONFIG_FILE_LOCATION + config_filename)
        response = {
            POLICY_COUNTER: policy_counter,
            "policy_applied": True if not response else False,
            "response_json": response
        }
        self.logger.info("Response: %s", response)
        return response

    def save_config(self):
        url = BASE_URL + SAVE_CONFIG_URL
        config_filename = time.strftime("%Y%m%d-%H%M%S") + ".xml"
        formdata = {\
            'action': (None, 'save'),
            'filename': (None, config_filename),
            'passphrase_action': (None, 'encrypt')
        }
        response = self.get_api_class(SAVE_CONFIG_URL)(url, payload=None, \
                method=PUT, formdata=formdata).api_call()
        self.logger.info("Configuration Saved in file %s", config_filename)
        return config_filename

    def revert_config(self, config_filename):
        url = BASE_URL + SAVE_CONFIG_URL
        formdata = { \
            'action': (None, 'load'),
            'appliance_file': (None, config_filename),
            'source': (None, 'appliance')
        }
        try:
            response = self.get_api_class(SAVE_CONFIG_URL)(url, payload=None, \
                    method=PUT, formdata=formdata).api_call()
            if len(response) > 1 and not response[0]:
                raise Exception(response[1])
        except Exception as err:
            self.logger.error("Failed to revert Configuration: %s", err)
            return False
        self.logger.info("Configuration reverted from file %s", config_filename)
        return True

    def apply_config(self, payload):
        # Applies Full Config to local WSA device
        # for each Policy Type , Fetches current config from WSA
        # Deletes Unavailable policies in Payload,
        # Updates existing policy
        # Create new policies if not available in WSA

        return_response = {}
        delete_profiles = {}
        eunpage_data_type = "eunpage"
        for data_type in supported_datas:
            if data_type in payload:
                return_response[data_type] = {}
                resource, index_key, ignore_ids, split_payload = self.get_resource(data_type)
                url = BASE_URL + resource
                api_version = V2 if resource.startswith("v2.0") else V3

                if data_type == eunpage_data_type:
                    eunpage_payload = payload[eunpage_data_type][0]
                    resp = self.get_api_class(resource)(url, payload=eunpage_payload, method=PUT).api_call()
                    return_response[data_type][PUT] = resp
                    continue

                get_response_data = self.get_api_class(resource)(
                    url, payload=None, method=GET).api_call()
                if not get_response_data[0]:
                    return {"message": "GET " + data_type + " : " + "fetch failed"}
                get_response_data = ast.literal_eval(str(get_response_data[1]))
                get_response_data = get_response_data if api_version == V2 \
                    else get_response_data[data_type]
                api_method_data = self.get_api_method_data(
                    payload[data_type], \
                    get_response_data, data_type,
                    index_key=index_key, ignore_ids=ignore_ids)
                self.logger.log_trace("%s: %s", data_type, api_method_data)
                for method in [POST, PUT, DELETE]:

                    if len(api_method_data[method]):
                        if method is DELETE:
                            if api_version == V2:
                                if payload[CONFIGURATION_TYPE] == FULL_CONFIG:
                                    load = {index_key: api_method_data[method]}
                                elif payload[CONFIGURATION_TYPE] == \
                                    DELTA_CONFIG:
                                    load = \
                                        {index_key: payload[DELETE][data_type]}
                            else:
                                if payload[CONFIGURATION_TYPE] == FULL_CONFIG:
                                    url = url + '?' + index_key + "s=" + \
                                          ",".join(api_method_data[method])
                                elif payload[CONFIGURATION_TYPE] \
                                    == DELTA_CONFIG:
                                    url = url + '?' + index_key + "s=" + \
                                          ",".join(payload[DELETE][data_type])

                            delete_profiles[data_type] = {
                                "resource": resource,
                                "url": url,
                                "payload": load
                            }
                            continue

                        loads = []
                        if split_payload['enable']:
                            split_count = split_payload['count']
                            data = api_method_data[method]
                            if api_version == V2:
                                loads = [data[i: i + split_count] for i in range(0, len(data), split_count)]
                            else:
                                loads = [{data_type: data[i: i + split_count]} for i in range(0, len(data), split_count)]
                        else:
                            if api_version == V2:
                                loads.append(api_method_data[method])
                            else:
                                loads.append({data_type: api_method_data[method]})

                        for load in loads:
                            self.logger.debug("Applying Config Changes : %s - %s", method, data_type)
                            if api_version == V2:
                                self.logger.debug("Ids %s", ','.join(i[index_key] for i in load))
                            else:
                                self.logger.debug("Ids %s", ','.join(i[index_key] for i in load[data_type]))

                            response = self.get_api_class(resource)( \
                                url, payload=load, \
                                method=method).api_call()

                            self.logger.debug("Applied Config changes for %s", data_type)
                            self.logger.debug("Response: %s", response)

                            if len(response) > 1 and not response[0]:
                                return_response[data_type][method] = response
                                return self.process_response(return_response)

        for data_type in supported_datas[::-1]:
            if data_type in delete_profiles.keys():
                self.logger.log_trace("Deleting - %s, Ids - %s", \
                                  data_type, delete_profiles[data_type]["payload"])

                response = self.get_api_class( \
                    delete_profiles[data_type]["resource"])( \
                    delete_profiles[data_type]["url"], \
                    payload=delete_profiles[data_type]["payload"], \
                    method=DELETE).api_call()

                self.logger.debug("Response: %s", response)
                if len(response) > 1 and not response[0]:
                    return_response[data_type][DELETE] = response
                    return self.process_response(return_response)

        response = self.process_response(return_response)
        return response

    def process_response(self, response):
        error_response = {}
        for group in response.keys():
            for method in response[group].keys():
                if response[group][method]:
                    if len(response[group][method]) <= 1 or response[group][method][0]:
                        continue
                    if group not in error_response.keys():
                        error_response[group] = {}
                    if method not in error_response[group].keys():
                        error_response[group][method] = []
                    try:
                        if "failure_list" in response[group][method][1].keys():
                            for item in response[group][method][1]["failure_list"]:
                                del item["status"]
                            error_response[group][method] = response[group][method][1]["failure_list"]
                        if "error" in response[group][method][1].keys() and group == "eunpage":
                            error_response[group][method] = response[group][method][1]["error"]
                        v2_failure = None
                        if "delete_failure" in response[group][method][1]:
                            v2_failure_del = response[group][method][1]["delete_failure"]
                            for item in v2_failure_del:
                                err = {
                                    "message": item["error_msg"],
                                    "content": item["content"]
                                }
                                error_response[group][method].append(err)
                        if "modify_failure" in response[group][method][1]:
                            v2_failure = response[group][method][1]["modify_failure"]
                        if "add_failure" in response[group][method][1]:
                            v2_failure = response[group][method][1]["add_failure"]
                        if v2_failure:
                            for item in v2_failure:
                                contents = item["content"]
                                err_msg = item["error_msg"]
                                if isinstance(contents, dict):
                                    contents = [contents]
                                for content in contents:
                                    err = {
                                        "message": err_msg,
                                        mapper[group]['index']: content[mapper[group]['index']]
                                    }
                                    error_response[group][method].append(err)
                        if not error_response[group][method]:
                            del error_response[group][method]
                        if not error_response[group]:
                            del error_response[group]
                    except:
                        error_response[group][method].append({"message": "unknown error"})

        return self.process_error_resp(error_response)

    def get_api_class(self, resource):
        # Returns API version based on resource value

        if resource.startswith("v2.0"):
            return APISupportV2
        else:
            return APISupportV3

    def merge_hybrid_wsa_adc(self, h_data, w_data):

        h_data_adc = h_data.get('adc', {}).get('applications', {})
        w_data_adc = w_data.get('adc', {}).get('applications', {})
        if  not (h_data_adc and w_data_adc):
            return

        for h_data_adc_cat, h_data_adc_cat_value in h_data_adc.items():
            w_data_adc_cat_value = w_data_adc.get(h_data_adc_cat, {})
            for item in w_data_adc_cat_value.get('block', []):
                if item not in h_data_adc_cat_value['block']:
                    # h_data_adc_cat_value['block'].append(item)
                    h_data_adc_cat_value['monitor'][item] ={}

    def get_api_method_data(self, hyb_data, wsa_data, data_type, index_key, ignore_ids):
        # Compares Umbrella Payload and WSA current config
        # Returns Dict with POST, PUT payloads and List of IDs to delete

        is_access_policy = data_type == ACCESS_POLICIES
        update = []
        create = []
        delete = []

        for h_data in hyb_data:
            if h_data[index_key] in ignore_ids:
                continue
            for w_data in wsa_data:
                if h_data[index_key] == w_data[index_key]:
                    if is_access_policy:
                        self.merge_hybrid_wsa_adc(h_data, w_data)
                    update.append(h_data)
                    break
            else:
                create.append(h_data)

        for w_data in wsa_data:
            if w_data[index_key] in ignore_ids:
                continue
            for h_data in hyb_data:
                if h_data[index_key] == w_data[index_key]:
                    break
            else:
                if str(w_data[index_key]).startswith("umbrella "):
                    delete.append(str(w_data[index_key]))

        order_map = {
            IDENTIFICATION_PROFILES: 'order',
            ACCESS_POLICIES: 'policy_order',
            DECRYPTION_POLICIES: 'policy_order'
        }

        if data_type in order_map:
            # push policies to bottom using PUT
            order_key = order_map[data_type]
            hyb_put_data = copy.deepcopy(hyb_data)
            items_after_post = len(wsa_data) + len(create)
            # sort in reverse order to avoid priority overwrite
            hyb_put_data.sort(key=lambda x: x[order_key], reverse=True)
            for index, item in enumerate(hyb_put_data):
                item[order_key] = items_after_post - index - 1

            update = hyb_put_data

        ret_value = {
            "POST": create,
            "PUT": update,
            "DELETE": delete
        }

        return ret_value

    def get_resource(self, data_type):
        return mapper[data_type]['api'], mapper[data_type]['index'], \
               mapper[data_type]['ignore_ids'], \
               mapper[data_type].get('split_payload', {'enable' : False, 'count' : None})

    def process_error_resp(self, error_resp):
        new_resp = {}
        for data_type, val in error_resp.items():
            mapped_data_type = DATA_TYPE_MAPPER.get(data_type)
            if mapped_data_type and isinstance(val, dict):
                new_resp[mapped_data_type] = {}
                for action, resp in val.items():
                    mapped_action = API_METHOD_MAPPER.get(action)
                    if mapped_action:
                        action_msg = 'Error occurred while {} {}'.format(mapped_action, mapped_data_type)
                        new_resp[mapped_data_type][action_msg] = resp
                    else:
                        new_resp[mapped_data_type][action] = resp
            else:
                new_resp[data_type] = val
        return new_resp

if __name__ == "__main__":  # pragma no cover
    WorkerService().serve("Message from main()", None)
