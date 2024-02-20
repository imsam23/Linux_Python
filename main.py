# $$
# Copyright (c) 2020 Cisco Systems, Inc.
# All rights reserved.
# Unauthorized redistribution prohibited

"""url_categories.py
Implements the URL Categories feature, which allows retrieving, creating, editing and
deleting URL Categories.
"""
import math
import datetime
import re
import copy
from urlparse import urlsplit, urlparse, parse_qs
from shared.URLCategories import URLCategories, CustomCategory, ExternalFeedCategory
from shared.NewPolicyGroups import (PT_HTTP, PT_HTTPS, PT_ROUTING,
                                    PT_DLP_ONBOX, PT_SOCKS, PT_WTT,
                                    PT_DLP_OFFBOX, PT_IDENTITY, PT_OUT_AMW,
                                    POLICY_CLASSES, Policies, GLOBAL_GROUP_ID)
from shared.HTTPS import HTTPS
from shared.Hybrid import Hybrid
from shared.URLCategories import validateRegex
from shared.URLCategories import validateRegexNoEscapeValidate
from shared.URLCategories import validateURL

import features
import ui_checker
import config_util

from url_register import route
from validation_decorator import decorator_4xx
from access_permit_decorators import access_permit
from commit_interface import commit
from request_body_handler import request_parser
import constants
from url_categories_validation import CategoriesValidation, UrlCategoryUtils
from certificate_validation import CertificateValidation
from utils import Utilities


@route(constants.URL_CATEGORIES)
class URLCategoriesClass(object):
    """
    Implements the URL Categories feature, which allows retrieving, creating, editing and
    deleting URL Categories.
    """

    def __init__(self):
        self.res = {"res_data": [],
                    "res_message": constants.DATA_RECEIVED,
                    "res_code": constants.OK}
        self.commit_obj = commit('')
        self.url_categories = None
        self.https = None
        self.policies = None
        self.hybrid = None
        self.has_privileges = True
        self.delegated_admin = False
        self.hide_inaccessible_rows = False
        self.sandbox_environment = features.has_capability(constants.CATEGORY_SANDBOX_ENV)
        self.use_management_for_proxy = None
        self.available_interfaces = None
        self.user_language = None
        self.custom_role = None
        self.user_groups = None

    def update_response(self, data=None, message=None, code=None):
        """
        Formats response based on the parameters.
        """
        if data:
            self.res["res_data"] = data
        if message:
            self.res["res_message"] = message
        if code:
            self.res["res_code"] = code

    def prepare_response(self, operation, success_list, failure_list, len_success, len_failure):
        """
        Prepares response dictionary based on the success and failure list.
        """
        result = {}
        message = ""
        if success_list:
            result[operation + "_success"] = success_list
            message += constants.SUCCESS.format(len_success)

        if failure_list:
            result[operation + "_failure"] = failure_list
            message += constants.FAILURE.format(len_failure)

        if operation in ["delete", "find", "modify"] and success_list:
            code = constants.OK
        elif operation in ["delete", "find", "modify"] and failure_list:
            code = constants.BAD_REQUEST
        elif success_list:
            code = constants.CREATED
        else:
            code = constants.BAD_REQUEST

        if success_list and failure_list:
            code = constants.PARTIAL_SUCCESS
        self.update_response(result, message, code)

    def check_privileges(self, custom_role, uri_ctx):
        """Define whether Custom Role user has privileges to view custom URL
        categories:
            1) check whether user's custom role exists;
            2) check whether custom role user has at least one category
               assigned
        """
        has_privileges = False
        wsa = Utilities.get_sandbox_api_client()
        custom_roles = wsa.read_var(constants.SYSTEM_USER_CUSTOM_ROLES)
        policy_tags = uri_ctx.varstore.read_var(constants.PROX_ACL_RULES_URL_TAGS)
        # If Custom Role exists.
        if custom_role in custom_roles.keys():
            for item in policy_tags.values():
                # If Custom Role has assigned policies.
                if custom_role in item:
                    has_privileges = True
                    break
        return has_privileges

    def is_category_editable(self, uri_ctx, cat_code):
        """
        Check whether custom role user has privileges to edit custom URL
        category. Return True or False.
        """
        if not self.delegated_admin:
            return True
        url_tags = uri_ctx.varstore.read_var(constants.PROX_ACL_RULES_URL_TAGS)
        return self.custom_role in url_tags.get(str(cat_code), [])

    def hide_inaccessible_category(self, custom_role):
        """
        Return info whether custom role has privileges to see inaccessible
        rows or not.
        """
        wsa = Utilities.get_sandbox_api_client()
        custom_roles = wsa.read_var(constants.SYSTEM_USER_CUSTOM_ROLES)
        if custom_roles.has_key(custom_role):
            return custom_roles[custom_role]['hide_inaccessible_rows']
        # The custom role no longer exists; this user shouldn't see anything
        return True

    def initialization(self, uri_ctx):
        """
        Initializing objects.
        """
        self.url_categories = URLCategories(uri_ctx.varstore, uri_ctx.commandd,
                                            uri_ctx.user_name)
        self.https = HTTPS(uri_ctx.varstore, uri_ctx.commandd,
                           uri_ctx.user_name)
        self.https.load()
        self.policies = Policies(uri_ctx.varstore, uri_ctx.commandd,
                                 uri_ctx.user_name)

        self.hybrid = Hybrid(uri_ctx.varstore,
                             uri_ctx.commandd,
                             uri_ctx.user_name)

        # Define whether Custom Role user has privileges to view custom URL
        # categories.

        self.sandbox_environment = features.has_capability(constants.CATEGORY_SANDBOX_ENV)
        self.use_management_for_proxy = uri_ctx.varstore.read_var(constants.USE_MGMT_FOR_PROXY_VAR)
        self.available_interfaces = [constants.MANAGEMENT_SMALL] if self.use_management_for_proxy \
            else [constants.MANAGEMENT_SMALL, constants.DATA_SMALL]

        self.user_language = Utilities.get_language(uri_ctx)

        self.custom_role = None
        self.user_groups = Utilities.get_user_groups(uri_ctx)
        # If user is delegated admin then check whether the user
        # has access to categories under assigned custom roles.
        if self.user_groups[0] == 'delegatedadmin':
            all_users = uri_ctx.varstore.read_var(constants.SYSTEM_USERS)
            self.custom_role = all_users[uri_ctx.user_name].get('delegated_id')
            self.has_privileges = self.check_privileges(self.custom_role, uri_ctx)
            self.hide_inaccessible_rows = self.hide_inaccessible_category(self.custom_role)
            self.delegated_admin = True

    def get_protocol_type(self, feed_url):
        """
        Returns the the protocol type based on the feed url.
        """
        return urlsplit(feed_url).scheme if feed_url else constants.HTTPS

    def format_last_updated_time(self, last_updated_time):
        """
        When the user language is Japanese these formatting is required.
        """
        split_date = last_updated_time.split()
        last_updated_day = split_date[0]
        last_updated_month = split_date[1]
        last_updated_year = split_date[2]
        last_updated_hours = split_date[3]
        last_updated_meridian = split_date[4]
        last_updated_time = last_updated_year + ' ' + \
                            last_updated_month + ' ' + \
                            last_updated_day + ' ' + \
                            last_updated_hours + ' ' + \
                            last_updated_meridian
        return last_updated_time

    def fetch_categories(self, uri_ctx, flag=False):
        """
        Prepares category data and returns it.
        """
        # Fetch all the custom categories instance and feed settings for external categories.
        cc_instances = self.url_categories.getCustomCategoriesList()
        external_feed_settings_inst = self.url_categories.getExternalFeedCategoriesList()
        feedsd_sock_path = uri_ctx.varstore.read_var(constants.CATEGORY_FEEDSD_SOCK_PATH)
        urls_to_exclude = uri_ctx.varstore.read_var(constants.CATEGORY_FEED_EXCLUSION_LIST)
        # Preparing external feed settings.
        external_feed_categories_settings = {}
        for external_category in external_feed_settings_inst:
            feed_dict = external_category.__dict__
            external_feed_categories_settings[feed_dict['customcat']] = feed_dict

        custom_url_categories = []
        # Iterate through the custom category instances and fetch details for each category.
        for idx, category in enumerate(cc_instances):
            category_data = category.__dict__
            # For local categories, parameters mentioned below are required.
            cat = {"category_type": category_data["cat_type"],
                   "category_name": category_data["cat_name"],
                   "list_order": idx + 1, "sites": category_data["server_list"],
                   "sites_regex": category_data["regex_list"],
                   "editable": self.is_category_editable(uri_ctx, category.code),
                   "comments": category_data["cat_comments"]
                  }
            # If category type is external then fetch additional parameters.
            if cat["category_type"] == constants.CATEGORY_EXTERNAL:
                # Fetch the excluded urls and regex for external category.
                exception_urls_list = []
                exception_regex_list = []
                for excluded_data in urls_to_exclude:
                    for key in excluded_data.keys():
                        if key == category.cat_name:
                            exception_urls_list = \
                                excluded_data[category.cat_name]['_exception_list']
                            exception_regex_list = \
                                excluded_data[category.cat_name]['_exception_regex']
                # Fetch feed settings for the current custom category.
                external_category = external_feed_categories_settings[category_data["code"]]

                # Check auto update and auto update frequency.
                update_freq = False
                if external_category['frequency']:
                    update_freq = True
                    cat['auto_update_freq'] = external_category['frequency']

                # Fetch feed location
                feed_url = external_category['feed_location']
                # If feed type is cisco i.e. 0 then
                # fetch protocol_type, username and password.
                # Password is returned only when this function invoked for internal use.
                if external_category['feed_type'] == 0:
                    # Strip http or https, if it exist in the feed location.
                    feed_url = self.get_stripped_url(external_category['feed_location'])
                    if external_category['username']:
                        cat['username'] = external_category['username']
                        if flag:
                            cat['password'] = \
                                config_util.decrypt(external_category['password'])
                    cat['protocol_type'] = self.get_protocol_type(
                        external_category['feed_location'])

                interface_type = constants.DATA \
                    if external_category['interface'] else constants.MANAGEMENT
                cat.update({
                    'feed_location': feed_url,
                    'auto_update': update_freq,
                    'feed_type': constants.FEED_TYPE_MAPPING[external_category['feed_type']],
                    'excluded_sites': exception_urls_list,
                    'excluded_regex': exception_regex_list,
                    'interface_option': interface_type,
                })

                # To get last updated time of external feed settings
                sandbox_environment = features.has_capability(
                    constants.CATEGORY_SANDBOX_ENV)
                cat['last_updated_time'] = constants.NEVER_UPDATED
                last_updated_time = category.getLastUpdatedTime(feedsd_sock_path)
                if not sandbox_environment and last_updated_time:
                    last_updated_time = category.getLastUpdatedTime(feedsd_sock_path)
                    if self.user_language == 'ja':
                        last_updated_time = self.format_last_updated_time(
                            last_updated_time)
                    date_diff = datetime.datetime.strptime(
                        last_updated_time, constants.CAT_TIME_FORMAT) - \
                                datetime.datetime(1970, 1, 1)
                    cat['last_updated_time'] = CategoriesValidation. \
                        convert_datetime_to_epoch(date_diff)
            # Do not include inaccessible rows.
            if self.hide_inaccessible_rows and not category['editable']:
                continue
            custom_url_categories.append(cat)
        return custom_url_categories

    @access_permit
    def get(self, uri_ctx):
        """
        Returns the list of existing URL Categories. Filtering options,
        category_type : Filter categories on category type parameter.
        category_name : Retrieve categories with category name parameter.
        current_page and page_size are pagination parameters.
        """
        category_type = str(uri_ctx.data_dict.get('category_type', ["all"])[0]).strip().lower()
        category_name = str(uri_ctx.data_dict.get('category_name', [""])[0]).strip()
        current_page = uri_ctx.data_dict.get('offset', [None])[0]
        page_size = uri_ctx.data_dict.get('limit', [None])[0]

        # Initialize and fetch categories.
        self.initialization(uri_ctx)
        categories = self.fetch_categories(uri_ctx)
        len_categories = len(categories)
        # If filtering is done on category name, return the specific categories.
        if category_name:
            find_success = []
            find_failure = []
            # Multiple names are seperated by , split them.
            category_name = set([cat_name.strip() for cat_name in str(category_name).split(",")
                                 if cat_name.strip()])
            if not category_name:
                del self.res['res_data']
                self.update_response(message=constants.NO_VALID_NAME_FOUND,
                                     code=constants.BAD_REQUEST)
                return self.res, 200

            # Fetch existing category names.
            cat_names = [category["category_name"] for category in categories]

            invalid_names = []
            for cat_name in category_name:
                if cat_name in cat_names:
                    indx = cat_names.index(cat_name)
                    find_success.append(categories[indx])
                else:
                    invalid_names.append(cat_name)

            len_invalid = CertificateValidation.append_failures(invalid_names, find_failure,
                                                                constants.CC_NOT_EXIST, 0)
            self.prepare_response("find", find_success, find_failure,
                                  len(find_success), len_invalid)
        else:
            if category_type not in [constants.CATEGORY_EXTERNAL,
                                     constants.CATEGORY_LOCAL, 'all']:
                del self.res['res_data']
                self.update_response(message=constants.INV_CATEGORY_TYPE,
                                     code=constants.BAD_REQUEST)
                return self.res, 200
            # Filter categories on category type value.
            if category_type != 'all':
                filtered_categories = [category for category in categories if
                                       category['category_type'] == category_type]
                if not filtered_categories:
                    del self.res['res_data']
                    self.update_response(message=constants.NO_CAT_TYPE_FOUND.format(
                        category_type))
                    return self.res, 200
                categories = filtered_categories
            len_categories = len(categories)
            is_pagination = False
            if current_page or page_size:
                # Validate pagination parameters(current_page, page_size) and return the
                # updated pagination parameters value. If invalid return with relevant error.
                current_page, page_size, error_msg = \
                    CertificateValidation.validate_pagination_params(current_page, page_size)

                if error_msg:
                    del self.res['res_data']
                    self.update_response(message=error_msg,
                                         code=constants.BAD_REQUEST)
                    return self.res, 200

                is_pagination = True

            if is_pagination:
                # The function returns paginated categories or
                # an error when pagination parameters are out of bound.
                categories, pagination_error = \
                    CertificateValidation.pagination(categories,
                                                     current_page, page_size)
                len_after_pagination = len(categories)
                self.res["pagination"] = {
                    "total_records": len_categories,
                    "total_pages": int(math.ceil(float(len_categories) / float(page_size))),
                    "limit": page_size,
                    "offset": current_page
                }
                if not len_after_pagination:
                    # When pagination is active and it has registered some error.
                    self.update_response(data=categories, message=pagination_error)
                    return self.res, 200

            self.update_response(data=categories)
        return self.res, 200

    def remove_url_tag(self, uri_ctx, cat_code):
        """
        Removes url tags from catgories.
        """
        cat_code_str = str(cat_code)
        url_tags = uri_ctx.varstore.read_var(constants.PROX_ACL_RULES_URL_TAGS)
        url_tags.pop(cat_code_str, None)
        uri_ctx.varstore.change_var(constants.PROX_ACL_RULES_URL_TAGS, url_tags)

    @access_permit
    @decorator_4xx('DELETE', ['category_name'])
    def delete(self, uri_ctx):
        """
        Delete category.
        Before delete a Custom Category we have to remove all references
        to this Category from ALL Policy Groups.
        """
        # Validate whether parsed data is application json or not.
        parsed_data = request_parser(uri_ctx)
        error_msg = CategoriesValidation.validate_parsed_data_type(parsed_data)
        if error_msg:
            del self.res['res_data']
            self.update_response(message=error_msg,
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        if not isinstance(parsed_data["body"], dict):
            del self.res["res_data"]
            self.update_response(message=constants.EXP_INPUT_BODY_DICT,
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        input_data = parsed_data["body"]["category_name"]

        # Check whether the inout data is in required format or not.
        error_msg = CategoriesValidation.validate_delete_data_type(input_data)
        if error_msg:
            del self.res["res_data"]
            self.update_response(message=error_msg,
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        # If the input is empty.
        if not input_data:
            del self.res["res_data"]
            self.update_response(message="Empty input.",
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        # Cannot optimize this operation due to python2.6 limitations.
        category_names = []
        if isinstance(input_data, str):
            category_names.append(input_data)
        else:
            category_names = input_data

        delete_success = []
        delete_failure = []

        self.initialization(uri_ctx)
        categories = self.url_categories.getCustomCategoriesList()

        # When there are no catgories to delete.
        if not categories:
            del self.res['res_data']
            self.update_response(message=constants.NO_CAT_TO_DELETE,
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        # Fetch existing existing categories' names and code.
        cat_names = []
        cat_codes = []
        for category in categories:
            cat_names.append(category.__dict__["cat_name"])
            cat_codes.append(category.__dict__["code"])

        # When delete_all is the input.
        if isinstance(category_names[0], str) and \
                category_names[0].strip().capitalize() == constants.DELETE_ALL:
            names = list(cat_names)
            codes = list(cat_codes)
        else:
            # If deleting specific catgories, fetch
            names = list(category_names)
            codes = [cat_codes[cat_names.index(name)] if name in cat_names else 0
                     for name in category_names]

        done = []
        for name, code in zip(names, codes):
            # If request is duplicate.
            if name in done:
                delete_failure.append({
                    "content": name,
                    "error_msg": constants.DUPLICATE_REQUEST
                })
                continue

            if not isinstance(name, str):
                delete_failure.append({
                    "content": name,
                    "error_msg": constants.DTYPE_STR_MSG.format("category name")
                })
                done.append(name)
                continue
            name = name.strip()

            # If request is duplicate.
            if name in done:
                delete_failure.append({
                    "content": name,
                    "error_msg": constants.DUPLICATE_REQUEST
                })
                continue
            done.append(name)
            # Check ehether the custom category exists or not.
            category = self.url_categories.getCategoryByAttr('custom', code=code)
            if not category:
                delete_failure.append({
                    "content": name,
                    "error_msg": constants.CC_NOT_EXIST
                })
                continue

            policies = self.policies.getAllGroups([PT_HTTP, PT_HTTPS, PT_ROUTING,
                                                   PT_DLP_ONBOX, PT_DLP_OFFBOX,
                                                   PT_IDENTITY, PT_OUT_AMW,
                                                   PT_SOCKS])
            # Remove references from all HTTP Policy Groups.
            # to remove the references in referer exemption
            category.removeCatReferencesInReferer(code, policies)

            references = category.removeCategoryReferences(policies)
            # We got list of modified policies, let's save them to the config.
            for policy, to_be_disabled in references:
                if to_be_disabled and policy.getType() == PT_IDENTITY:
                    # If we disable identity, we need to find policies depending on
                    # this identity and disable them too.
                    self.policies.disableIdentity(policy)

            # We need to save policies as some of them may become disabled because
            # they are dependent from disabled identity
            # (e.g.: identity was disabled by removing Custom URL Category).
            for policy in policies:
                self.policies.saveGroup(policy)

            # Delete the Category.
            self.url_categories.deleteCustomCategory(code)
            # Delete the external feed settings
            if category.getCatType() == constants.CATEGORY_EXTERNAL:
                try:
                    self.url_categories.deleteExternalFeedCategory(code)
                except ValueError:
                    pass

            # start from removing exception part of a category
            urls_to_exclude = uri_ctx.varstore.read_var(constants.CATEGORY_FEED_EXCLUSION_LIST)
            for excluded_data in urls_to_exclude:
                for key in excluded_data.keys():
                    if key == category.cat_name:
                        del excluded_data[category.cat_name]
            uri_ctx.varstore.change_var(constants.CATEGORY_FEED_EXCLUSION_LIST, urls_to_exclude)

            # Update URL tags.
            self.remove_url_tag(uri_ctx, code)

            # Update data.cfg file in trafmon.bypass
            custom_cat_dict = uri_ctx.varstore.read_var(constants.BYPASSLIST_CUSTCAT_CONFIG)
            if custom_cat_dict:
                for catname, catcode in custom_cat_dict.items():
                    if catcode == code:
                        del custom_cat_dict[catname]
                uri_ctx.varstore.change_var(constants.BYPASSLIST_CUSTCAT_CONFIG, custom_cat_dict)
            delete_success.append(name)
        self.commit_obj.commit_action(uri_ctx)
        self.prepare_response("delete", delete_success, delete_failure,
                              len(delete_success), len(delete_failure))
        return self.res, 200

    def validate_category_sites(self, values, key):
        """
        Check duplicate. Validates the list of sites.
        """
        error_msg = CategoriesValidation.check_str_duplicates_sites_and_regex(values, key)
        if error_msg:
            return error_msg
        try:
            # Validate each entry, if invalid entry found raises FilterError exception.
            if values[key]:
                values[key] = UrlCategoryUtils.filter_comma_or_newlines_list(
                    validateURL, allow_duplicates=False)(values[key])
        except ui_checker.FilterError as err:
            # Split the error string to extract the invalid entry.
            error_site = err.__dict__[constants.ERROR_STR].split("A")[0]
            return constants.INVALID_SITES.format(error_site)

    def validate_category_sites_regex(self, values, key, validate_escape=True):
        """
        Check duplicate. Validates the list of regex.
        """
        error_msg = CategoriesValidation.check_str_duplicates_sites_and_regex(values, key)
        if error_msg:
            return error_msg

        try:
            # Validate each entry, if invalid entry found raises FilterError exception.
            if values[key]:
                regex_func = validateRegex if validate_escape else validateRegexNoEscapeValidate
                values[key] = UrlCategoryUtils.filter_newlines_list(
                    regex_func, allow_duplicates=False)(values[key])
        except ui_checker.FilterError as err:
            # Split the error string to extract the invalid entry.
            error_regex = str(err.__dict__[constants.ERROR_STR].split(" is")[0])
            return constants.INVALID_REGEX.format(error_regex)

    def validate_category_data_local(self, values, existing_names, validate_escape=True):
        """
        Validate local category data.
        """
        error_msg = CategoriesValidation.validate_category_data_local(values, existing_names)
        if error_msg:
            return error_msg

        error_msg = self.validate_category_sites(values, "sites")
        if error_msg:
            return error_msg

        error_msg = self.validate_category_sites_regex(values, "sites_regex", validate_escape=validate_escape)
        if error_msg:
            return error_msg

    def validate_category_data_external(self, values, existing_names):
        """
        Validate external category data.
        """

        def validate_limit_restrictions(cat_code=0):
            """
            User can't create External feed category more than the limit.
            """
            external_feed_settings = []
            for cat in self.url_categories.getCustomCategoriesList():
                if cat['code'] != int(cat_code):
                    if cat.getCatType() == constants.CATEGORY_EXTERNAL:
                        external_feed_settings.append(cat)

            max_feeds_limit = self.url_categories.getExternalFeedsMaxLimit()
            if len(external_feed_settings) >= max_feeds_limit:
                return constants.CATEGORY_MAX_EXTERNAL_FEED.format(max_feeds_limit)

        def validate_o365_service_url(url):
            """
            Validate the 0365 url.
            """
            ui_checker.validate_http_url_with_params(url)
            url_obj = urlparse(url)
            if not url_obj.query:
                return url

            query_dictionary = parse_qs(url_obj.query)
            # If clientrequestid exists in the url, return error.
            if constants.CATEGORY_CLIENT_REQUEST_ID in query_dictionary:
                return constants.URL_WITHOUT_CLIENT_REQUEST_ID
            # Check the query dictionary is in JSON format.
            if 'format' in query_dictionary:
                if query_dictionary['format'] or query_dictionary['format'][0].lower() != 'json':
                    return constants.JSON_FORMAT_PARAMETER

            return url

        def validate_feed_url_protocol(values):
            """
            Validate the protocol type with the feed url.
            """
            feed_url = values.get('feed_location')
            if feed_url and (values.get('feed_type') == "cisco"):
                try:
                    ui_checker.validate_ext_feed_url(feed_url)
                except ui_checker.FilterError:
                    return ui_checker.validate_ext_feed_url_format.__dict__[constants.CC_ARGS][0]
                # Check if http(s) is present in the url and it matches the protocol type.
                if re.search('^[Hh][Tt][Tt][Pp]([Ss])?[://]', feed_url):
                    parsed_protocol_type = urlsplit(feed_url).scheme
                    if values.get('protocol_type') != parsed_protocol_type:
                        return constants.CATEGORY_PROTOCOL_NOT_MATCHING
            elif feed_url and (values.get('feed_type') == "office365"):
                # Check whether the feed url when feed type is office365 is valid or not.
                try:
                    ui_checker.validate_http_url(feed_url)
                except ui_checker.FilterError as err:
                    return str(err[1]).replace('\n', ' ')
            elif feed_url and (values.get('feed_type') == "office365_web"):
                # Check whether the feed url when feed type is office365_web is valid or not.
                try:
                    validate_o365_service_url(feed_url)
                except ui_checker.FilterError:
                    return ui_checker.validate_http_url_with_params_format.__dict__[
                        constants.CC_ARGS][0]
                except Exception as err:
                    return str(err)

        # Check required params present.
        required_params = set(["interface_option", "feed_type", "feed_location",
                               "auto_update"])
        error_msg = CategoriesValidation.required_param_present(required_params, values)
        if error_msg:
            return error_msg

        error_msg = CategoriesValidation.validate_category_data_external(values, existing_names,
                                                                         self.available_interfaces)
        if error_msg:
            return error_msg

        if values["feed_type"] == "cisco":
            # Validate parameters required when feed_type is cisco.
            error_msg = CategoriesValidation.validate_feed_type_cisco(values)
            if error_msg:
                return error_msg

        if values['auto_update']:
            # Validate parameters when auto update is true.
            error_msg = CategoriesValidation.validate_auto_update_param(values)
            if error_msg:
                return error_msg

        error_msg = validate_limit_restrictions()
        if error_msg:
            return error_msg

        error_msg = validate_feed_url_protocol(values)
        if error_msg:
            return error_msg

        if values.get("excluded_sites"):
            error_msg = self.validate_category_sites(values, "excluded_sites")
            if error_msg:
                return error_msg

        if values.get("excluded_regex"):
            error_msg = self.validate_category_sites_regex(values, "excluded_regex")
            if error_msg:
                return error_msg

    def format_url(self, protocol_type, feed_location):
        """
        Method to join protocol_type with the feed_url.
        """
        # If the protocol type in feed url doesn't match the protocol_type param
        # then remove and add protocol_type in feed url parameter.
        if re.search('^[Hh][Tt][Tt][Pp]([Ss])?[://]', feed_location):
            parsed_protocol_type = urlsplit(feed_location).scheme
            if protocol_type == parsed_protocol_type:
                result = feed_location
            else:
                result = "://".join([protocol_type, feed_location.split("://")[1]])
        else:
            result = "://".join([protocol_type, feed_location])

        return result

    def add_local_category(self, values):
        """
        Add local category.
        """
        category = CustomCategory(values["category_name"],
                                  values["comments"],
                                  values["sites"], values["sites_regex"],
                                  policy_use={
                                      PT_HTTP: 1,
                                      PT_HTTPS: 1,
                                      PT_DLP_ONBOX: 1,
                                      PT_WTT: 1,
                                  },
                                  cat_type=constants.CATEGORY_LOCAL)
        before_index = values["list_order"] - 1
        policy_use = [PT_HTTP, PT_HTTPS, PT_DLP_ONBOX, PT_WTT]
        self.url_categories.addCustomCategory(category, before_index,
                                              policy_use)

    def add_external_category(self, uri_ctx, values):
        """
        Add external category.
        """
        # Fetch the current urls to exclude.
        urls_to_exclude = uri_ctx.varstore.read_var(constants.CATEGORY_FEED_EXCLUSION_LIST)

        # Adding excluded_sites and excluded_regex for category.
        exception_list = values.get('excluded_sites', [])
        exception_regex = values.get('excluded_regex', [])

        if not urls_to_exclude:
            urls_to_exclude.append({values['category_name']: {"_exception_list": exception_list,
                                                              "_exception_regex": exception_regex}})
        else:
            urls_to_exclude[0][values['category_name']] = {"_exception_list": exception_list,
                                                           "_exception_regex": exception_regex}
        # Update urls_to_exclude based on the current exclusion details.
        uri_ctx.varstore.change_var('feedsd.feedsd.feed_exclusion_list', urls_to_exclude)
        # Create an external category.
        category_urls = []
        category_urls_regex = []
        category = CustomCategory(values["category_name"],
                                  values["comments"],
                                  category_urls,
                                  category_urls_regex,
                                  policy_use={
                                      PT_HTTP: 1,
                                      PT_HTTPS: 1,
                                      PT_DLP_ONBOX: 1,
                                      PT_WTT: 1,
                                  },
                                  cat_type=constants.CATEGORY_EXTERNAL)
        before_index = values['list_order'] - 1
        policy_use = [PT_HTTP, PT_HTTPS, PT_DLP_ONBOX, PT_WTT]
        self.url_categories.addCustomCategory(category, before_index,
                                              policy_use)
        # Prepare parameters for External Feed Settings.
        frequency = values['auto_update_freq'] if values['auto_update'] else 0

        encflag = 0
        user_name = ''
        password = ''
        feed_url = values.get('feed_location')
        if values['feed_type'] == "cisco":
            user_name = values.get('username', '')
            password = values.get('password', '')
            if password:
                password = config_util.encrypt(password)
                encflag = 1
            feed_url = self.format_url(values.get('protocol_type'),
                                       values.get('feed_location'))

        ext_category = ExternalFeedCategory(
            feed_url,
            user_name,
            password,
            encflag,
            frequency,
            category.getCode(),
            constants.FEED_TYPE_MAPPING_REVERSE[values['feed_type']],
            constants.INTERFACE_MAPPING[values['interface_option']]
        )
        self.url_categories.addExternalFeedCategory(ext_category)

    @access_permit
    def post(self, uri_ctx):
        """
        Append local or external category.
        """
        # Check if the input type is application json or not.
        parsed_data = request_parser(uri_ctx)
        error_msg = CategoriesValidation.validate_parsed_data_type(parsed_data)
        if error_msg:
            del self.res['res_data']
            self.update_response(message=error_msg,
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        # Validate if input is dict or list.
        body = parsed_data['body']
        if not isinstance(body, (dict, list)):
            del self.res['res_data']
            self.update_response(message=constants.EXP_CAT_POST_INPUT,
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        # categories = []
        # # Due to limitations of python2.7 it's not possible to optimize this operation.
        # if isinstance(body, dict):
        #     categories.append(body)
        # else:
        #     categories = body
        #     # Change
        #     categories = (item for item in body)
        categories = (item for item in body) if isinstance(body, list) else [body] if isinstance(body, dict) else []

        # If input is empty.
        if not categories:
            self.update_response(message=constants.EMPTY_INPUT,
                                 code=constants.BAD_REQUEST)
            return self.res, 200
        # Sort the input based on the list order value. Adding the non-sortable input at the end.
        to_sort = []
        not_to_sort = []
        for category in categories:
            if not isinstance(category, dict):
                not_to_sort.append(category)
                continue

            if 'list_order' not in category:
                not_to_sort.append(category)
                continue

            if not isinstance(category['list_order'], int):
                not_to_sort.append(category)
                continue

            to_sort.append(category)

        to_sort.sort(key=lambda k: k['list_order'])
        to_sort.extend(not_to_sort)
        categories = to_sort

        add_success = []
        add_failure = []

        invalid_input = []
        duplicate_names = []
        inv_cat_type_val = []
        current_names = []

        self.initialization(uri_ctx)
        existing_categories = self.fetch_categories(uri_ctx)
        existing_names = set(category["category_name"] for category in existing_categories)

        params = self.get_query_params(uri_ctx)
        # enable/disable velocityengine regex validation
        validate_escape = params.get('validate_escape') != 'false'

        # Iterate through the input and add category after validation is done.
        for category in categories:
            if not isinstance(category, dict):
                invalid_input.append(category)
                continue

            required_params = set(["category_type", "list_order", "category_name"])
            # required_params = {"category_type", "list_order", "category_name"}

            # Check whether the required params are present,
            # if not then return the missing params
            error_msg = CategoriesValidation.required_param_present(required_params, category)
            if error_msg:
                CategoriesValidation.remove_unnecessary_params(category)
                add_failure.append({
                    "content": category,
                    "error_msg": error_msg
                })
                continue

            category_type = str(category["category_type"]).lower().strip()
            if category_type not in \
                    [constants.CATEGORY_LOCAL, constants.CATEGORY_EXTERNAL]:
                CategoriesValidation.remove_unnecessary_params(category)
                inv_cat_type_val.append(category)
                continue

            category_name = str(category["category_name"]).strip()
            if category_name in current_names:
                CategoriesValidation.remove_unnecessary_params(category, category_type)
                duplicate_names.append(category)
                continue

            if category_type == constants.CATEGORY_LOCAL:
                # Validate parameters related to category type local.
                error_msg = self.validate_category_data_local(category, existing_names, validate_escape=validate_escape)
                if error_msg:
                    CategoriesValidation.remove_unnecessary_params(category,
                                                                   category["category_type"])
                    add_failure.append({
                        "content": category,
                        "error_msg": error_msg
                    })
                    continue
                self.add_local_category(category)
            else:
                # Validate parameters related to category type external
                error_msg = self.validate_category_data_external(category, existing_names)
                if error_msg:
                    CategoriesValidation.remove_unnecessary_params(category,
                                                                   category["category_type"])
                    add_failure.append({
                        "content": category,
                        "error_msg": error_msg
                    })
                    continue
                self.add_external_category(uri_ctx, category)
            CategoriesValidation.remove_unnecessary_params(category, category_type)
            current_names.append(category_name)
            add_success.append(category)
        # Append failures with relevant error.
        len_invalid = len(add_failure)
        len_invalid = CertificateValidation.append_failures(
            duplicate_names, add_failure, constants.CAT_DUPLICATE_NAME, len_invalid)

        len_invalid = CertificateValidation.append_failures(
            inv_cat_type_val, add_failure, constants.CATEGORY_TYPE_INVALID, len_invalid)

        len_invalid = CertificateValidation.append_failures(
            invalid_input, add_failure, constants.EXP_INPUT_AS_DICT, len_invalid)
        # Commit and prepare response.
        self.commit_obj.commit_action(uri_ctx)
        self.prepare_response("add", add_success, add_failure,
                              len(add_success), len_invalid)
        return self.res, 200

    def fetch_cat_names_codes(self):
        """
        Prepare category codes and names for existing categories.
        """
        categories = self.url_categories.getCustomCategoriesList()
        cat_names = []
        cat_codes = []
        for category in categories:
            category = category.__dict__
            cat_names.append(category["cat_name"])
            cat_codes.append(category["code"])
        return cat_names, cat_codes

    def get_query_params(self, uri_ctx):
        result = {}
        try:
            params = parse_qs(uri_ctx.parsed_uri.query)
            for name, values in params.items():
                if values:
                    result[name] = values[0]
        except:
            pass
        return result

    @access_permit
    def put(self, uri_ctx):
        """
        Modify category data.
        """
        # Check if the input type is application json or not.
        parsed_data = request_parser(uri_ctx)
        error_msg = CategoriesValidation.validate_parsed_data_type(parsed_data)
        if error_msg:
            del self.res['res_data']
            self.update_response(message=error_msg,
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        body = parsed_data.get('body')
        # Validate if input is dict or list.
        if not isinstance(body, (dict, list)):
            del self.res['res_data']
            self.update_response(message=constants.EXP_CAT_POST_INPUT,
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        # Due to limitations of python2.7 it's not possible to optimize this operation.
        categories_input = []
        if isinstance(body, dict):
            categories_input.append(body)
        else:
            categories_input = body
        # If input is empty.
        if not categories_input:
            del self.res['res_data']
            self.update_response(message=constants.EMPTY_INPUT,
                                 code=constants.BAD_REQUEST)
            return self.res, 200

        to_sort = []
        not_to_sort = []
        for category in categories_input:
            if not isinstance(category, dict):
                not_to_sort.append(category)
                continue

            if 'list_order' not in category:
                not_to_sort.append(category)
                continue

            if not isinstance(category['list_order'], int):
                not_to_sort.append(category)
                continue

            to_sort.append(category)

        to_sort.sort(key=lambda k: k['list_order'])
        to_sort.extend(not_to_sort)
        categories_input = to_sort

        modify_success = []
        modify_failure = []
        len_invalid = 0

        self.initialization(uri_ctx)
        cat_names, cat_codes = self.fetch_cat_names_codes()
        existing_categories = self.fetch_categories(uri_ctx, True)
        invalid_input = []
        name_not_exist = []
        processed_names = []
        duplicate_input = []
        existing_names = [category["category_name"] for category in existing_categories]
        params = self.get_query_params(uri_ctx)
        # enable/disable velocityengine regex validation
        validate_escape = params.get('validate_escape') != 'false'
        # Iterate through categories and validate them.
        for category_input in categories_input:
            # category_input should be a dict.
            used_names = list(existing_names)
            if not isinstance(category_input, dict):
                invalid_input.append(category_input)
                continue
            # Check whether the required parameters are present or not.
            required_params = set(['category_name'])
            error_msg = CategoriesValidation.required_param_present(required_params, category_input)
            if error_msg:
                CategoriesValidation.remove_unnecessary_params(category_input)
                modify_failure.append({"content": category_input, "err_message": error_msg})
                continue
            # If the category doesn't exist
            category_input['category_name'] = str(category_input['category_name']).strip()
            if category_input['category_name'] not in cat_names:
                CategoriesValidation.remove_unnecessary_params(category_input)
                name_not_exist.append(category_input)
                continue

            # Fetch the previously stored details if a category exists.
            cat_indx = cat_names.index(category_input['category_name'])
            old_category = existing_categories[cat_indx]
            # In bulk input if a request for a particular category name is already processed.
            # Skip the next inputs.
            if category_input['category_name'] in processed_names:
                CategoriesValidation.remove_unnecessary_params(category_input,
                                                               old_category["category_type"])
                duplicate_input.append(category_input)
                continue

            if old_category["category_type"] == constants.CATEGORY_LOCAL:
                CategoriesValidation.remove_unnecessary_params(category_input,
                                                               old_category["category_type"])
                # Check if atleast one of the listed params is present or not.
                required_params = ['new_category_name', 'list_order', 'sites', 'sites_regex',
                                   'comments']
                category_keys = category_input.keys()
                if not any(param in category_keys for param in required_params):
                    message = constants.ANY_PARAM_MISSING.format(
                        len(required_params), required_params)
                    modify_failure.append({"content": category_input, "err_message": message})
                    continue
                # Update the old category details with the new inputs.
                category_new = dict(old_category)
                category_new.update(category_input)

                if 'new_category_name' in category_new:
                    category_new['category_name'] = category_new.pop('new_category_name')
                # Remove current category name from used name list.
                del used_names[cat_indx]
                error_msg = self.validate_category_data_local(category_new, used_names, validate_escape=validate_escape)
                CategoriesValidation.update_input(category_input, category_new)
                if error_msg:
                    modify_failure.append({
                        "content": category_input,
                        "error_msg": error_msg
                    })
                    continue
            else:
                # Check if atleast one of the listed params is present or not.
                required_params = ['new_category_name', 'list_order', 'interface_option',
                                   'feed_type', 'feed_location', 'excluded_sites',
                                   'excluded_regex', 'auto_update', 'auto_update_freq',
                                   'protocol_type', 'username', 'password', 'comments']
                category_keys = category_input.keys()
                if not any(param in category_keys for param in required_params):
                    message = constants.ANY_PARAM_MISSING.format(
                        len(required_params), required_params)
                    CategoriesValidation.remove_unnecessary_params(category_input,
                                                                   old_category["category_type"])
                    modify_failure.append({"content": category_input, "err_message": message})
                    continue
                # Update the old category details with the new inputs.
                category_new = dict(old_category)
                category_new.update(category_input)

                if 'new_category_name' in category_new:
                    category_new['category_name'] = category_new.pop('new_category_name')
                # Remove current category name from used name list.
                del used_names[cat_indx]
                error_msg = self.validate_category_data_external(category_new, used_names)
                if error_msg:
                    CategoriesValidation.remove_unnecessary_params(category_input,
                                                                   old_category["category_type"])
                    modify_failure.append({
                        "content": category_input,
                        "error_msg": error_msg
                    })
                    continue
                CategoriesValidation.update_input(category_input, category_new)
                error_msg = CategoriesValidation.check_configurations(category_input, category_new)
                if error_msg:
                    CategoriesValidation.remove_unnecessary_params(category_input,
                                                                   old_category["category_type"])
                    modify_failure.append({
                        "content": category_input,
                        "error_msg": error_msg
                    })
                    continue
                # Remap input to required format
                category_new['interface_option'] = 1 \
                    if category_new['interface_option'] == 'data' else 0
                category_new['feed_type'] = constants.FEED_TYPE_MAPPING_REVERSE[
                    category_new['feed_type']]
            # Edit category and add in success list.
            self.edit_category(uri_ctx, category_new, cat_codes[cat_indx], cat_indx)
            CategoriesValidation.remove_unnecessary_params(category_input,
                                                           old_category["category_type"])
            modify_success.append(category_input)
            processed_names.append(category_input['category_name'])
            # Update the existing name list.
            if category_new['category_name'] not in existing_names:
                existing_names.append(category_new['category_name'])
        # Append failures with relevant error message.
        len_invalid = len(modify_failure)
        len_invalid = CertificateValidation.append_failures(
            duplicate_input, modify_failure, constants.MULTIPLE_REQUEST, len_invalid)

        len_invalid = CertificateValidation.append_failures(
            invalid_input, modify_failure, constants.EXP_INPUT_AS_DICT, len_invalid)

        len_invalid = CertificateValidation.append_failures(
            name_not_exist, modify_failure, constants.CC_NOT_EXIST, len_invalid)
        # Prepare response and commit changes.
        self.prepare_response("modify", modify_success, modify_failure,
                              len(modify_success), len_invalid)
        self.commit_obj.commit_action(uri_ctx)
        return self.res, 200

    def get_stripped_url(self, feed_url):
        """
        Formatting the url by removing the protocol type.
        """
        result = feed_url
        if re.search('^[Hh][Tt][Tt][Pp]([Ss])?[://]', feed_url):
            protocol_type = urlsplit(feed_url).scheme
            # to strip the protocol from the url
            index = len(protocol_type) + 3
            result = feed_url[index:]
        return result

    def edit_category(self, uri_ctx, values, code, old_order):
        """
        Edit category.
        """

        def check_url_equality(initial_urls_to_exclude, urls_to_exclude, category):
            """
            Checking if excluded list is changing or not.
            """
            equal_check = False
            ilist = initial_urls_to_exclude[0][category.cat_name].get('excluded_list', [])
            iregex = initial_urls_to_exclude[0][category.cat_name].get('excluded_regex', [])
            flist = urls_to_exclude[0][category.cat_name].get('excluded_list', [])
            fregex = urls_to_exclude[0][category.cat_name].get('excluded_regex', [])
            ilist.sort()
            iregex.sort()
            flist.sort()
            fregex.sort()

            if (ilist == flist) and (iregex == fregex):
                equal_check = True
            return equal_check

        def check_feed_equality(cat_dict_index, initial_custom_categories,
                                updated_custom_categories):
            """
            Checking if custom category data is changing or not.
            """
            if cat_dict_index == -1:
                return True
            equal_check = False
            isl = initial_custom_categories[cat_dict_index]['server_list']
            isl.sort()
            usl = updated_custom_categories[cat_dict_index]['server_list']
            usl.sort()
            irl = initial_custom_categories[cat_dict_index]['regex_list']
            irl.sort()
            uurl = updated_custom_categories[cat_dict_index]['regex_list']
            uurl.sort()

            if (isl == usl) and (irl == uurl):
                equal_check = True
            return equal_check

        def filter_cat_stream_sites(url_categories, category, urls_to_exclude, old_name,
                                    old_url, new_url, this_cat_val):
            """
            Filter out excluded sites from the sites in custom category.

            :Parameters:
                `url_categories` : url_categories object from shared module
                `category` : custom category object.
                `urls_to_exclude` : list holds excluded sites.
                `old_name` : old category name.
                `new_name` : new category name.
                `old_url` : old feed file url.
                `new_url` : new feed file url.
                `this_cat_val` : excluded value of current category.

            :Return:
                `category` : modified custom category object.
                `urls_to_exclude` : modified list holds excluded sites.
            """
            if category.server_list:
                excluded_list_temp = []
                if this_cat_val:
                    excluded_list_temp = urls_to_exclude[0][old_name].get('excluded_list', [])
                    if old_url == new_url:
                        category.server_list = list(set(category.server_list + excluded_list_temp))
                    _exception_list = urls_to_exclude[0][category.cat_name]['_exception_list']
                    parsed_before_filter = category.server_list
                    urls_to_exclude[0][category.cat_name]['excluded_list'] = list(
                        set(category.server_list).intersection(
                            urls_to_exclude[0][category.cat_name]['_exception_list']))

                    url_categories.getFilteredSites(_exception_list, parsed_before_filter,
                                                    category.server_list, urls_to_exclude,
                                                    category.cat_name)

                    urls_to_exclude[0][category.cat_name]['excluded_list'] = list(
                        set(urls_to_exclude[0][category.cat_name]['excluded_list']))
                    category.server_list = list(set(category.server_list) - set(urls_to_exclude[0]
                                                                                [category.cat_name]
                                                                                ['excluded_list']))
                    urls_to_exclude[0][category.cat_name]['excluded_list'] = list(
                        set(urls_to_exclude[0][category.cat_name]['excluded_list']))

            return category, urls_to_exclude

        def filter_cat_stream_regex(category, urls_to_exclude, old_name,
                                    old_url, new_url, this_cat_val):
            """filter out excluded regex from the regex in custom category.

            :Parameters:
                `category` : custom category object.
                `urls_to_exclude` : list holds excluded regex.
                `old_name` : old category name.
                `new_name` : new category name.
                `old_url` : old feed file url.
                `new_url` : new feed file url.
                `this_cat_val` : excluded value of current category.

            :Return:
                `category` : modified custom category object.
                `urls_to_exclude` : modified list holds excluded regex.
            """
            if category.regex_list:
                excluded_regex_temp = []
                if this_cat_val != {}:
                    excluded_regex_temp = urls_to_exclude[0][old_name].get('excluded_regex', [])

                    if old_url == new_url:
                        category.regex_list = list(set(category.regex_list + excluded_regex_temp))
                    urls_to_exclude[0][category.cat_name]['excluded_regex'] = list(
                        set(category.regex_list).intersection(
                            urls_to_exclude[0][category.cat_name]['_exception_regex']))
                    parsed_before_filter = category.regex_list
                    filter_set = set(urls_to_exclude[0][category.cat_name]['_exception_regex'])
                    parsed_after_filter = [x for x in parsed_before_filter if x not in filter_set]
                    category.regex_list = parsed_after_filter
                    urls_to_exclude[0][category.cat_name]['excluded_regex'] = list(
                        set(urls_to_exclude[0][category.cat_name]['excluded_regex']))
            return category, urls_to_exclude

        cat_names, cat_codes = self.fetch_cat_names_codes()
        categories = self.url_categories.getCustomCategoriesList()
        category = self.url_categories.getCategoryByAttr('custom', code=long(code))
        external_feed_categories = self.url_categories.getExternalFeedCategoriesList()
        ext_category = {}
        category_index = 0
        for cat_index, cat in enumerate(external_feed_categories):
            if cat['customcat'] == long(code):
                category_index = cat_index
                ext_category = cat
        old_name = category.cat_name
        custom_cat_dict = uri_ctx.varstore.read_var(constants.BYPASSLIST_CUSTCAT_CONFIG)
        # If the category name is changed.
        if category.cat_name != values['category_name']:
            if category.cat_name in custom_cat_dict:
                del custom_cat_dict[category.cat_name]
                custom_cat_dict[values['category_name']] = int(code)
                uri_ctx.varstore.change_var(constants.BYPASSLIST_CUSTCAT_CONFIG, custom_cat_dict)
            category.cat_name = values['category_name']
            # Updating category's abbreviation.
            category.setAbbreviation(self.url_categories.getUsedAbbreviations())

        if category.cat_comments != values['comments']:
            category.cat_comments = values['comments']

        category.policy_use[PT_HTTP] = 1
        if self.https.isFeatureKeyAvailable() and self.https.isEnabled():
            category.policy_use[PT_HTTPS] = 1
        if uri_ctx.varstore.read_var(constants.PROX_ACL_RULES_DLP_ENABLED) and \
                ui_checker.check_feature(capability='dlp'):
            category.policy_use[PT_DLP_ONBOX] = 1
        category.policy_use[PT_WTT] = 1
        # Update information category wise.
        if category.getCatType() == constants.CATEGORY_LOCAL:
            category.server_list = values['sites']
            category.regex_list = values['sites_regex']
        else:
            frequency = values['auto_update_freq'] if values['auto_update'] else 0
            # If feed type is cisco
            if values['feed_type'] == 0:
                user_name = values.get('username', '')
                password = values.get('password', '')
                password = config_util.encrypt(password)
                encflag = 1
                feed_url = self.format_url(values.get('protocol_type'),
                                           values.get('feed_location'))
            else:
                user_name = ''
                password = ''
                feed_url = values.get('feed_location')
            # Update external feed settings for the category.
            if ext_category:
                old_url = self.get_stripped_url(ext_category.feed_location)
                new_url = self.get_stripped_url(feed_url)
                if old_url != new_url:
                    category.server_list = []
                    category.regex_list = []
                ext_category.feed_location = feed_url
                ext_category.username = user_name
                ext_category.password = password
                ext_category.frequency = frequency
                ext_category.feed_type = values['feed_type']
                ext_category.interface = values['interface_option']
            external_feed_categories[category_index] = ext_category
            self.url_categories.setExternalFeedCategoriesList(external_feed_categories)
        # If the list order is changed
        from_index = cat_codes.index(code)
        before_index = values['list_order'] - 1

        policy_use = [PT_HTTP, PT_HTTPS, PT_DLP_ONBOX, PT_WTT]
        self.url_categories.assignCategoryToPolicyGroup(category,
                                                        policy_use)

        categories[from_index] = category
        # Save exception list changes
        # editing existing exception_list for category if any
        urls_to_exclude = uri_ctx.varstore.read_var(constants.CATEGORY_FEED_EXCLUSION_LIST)
        exception_list = values.get('excluded_sites', [])
        exception_regex = values.get('excluded_regex', [])
        found = False
        for excluded_data in urls_to_exclude:
            for key, value in excluded_data.iteritems():
                if key == category.cat_name:
                    found = True
                    excluded_data[category.cat_name]['_exception_list'] = exception_list
                    excluded_data[category.cat_name]['_exception_regex'] = exception_regex
        if (not found) and (category.getCatType() != constants.CATEGORY_LOCAL):
            urls_to_exclude[0][category.cat_name] = {'_exception_list': exception_list,
                                                     '_exception_regex': exception_regex}
        uri_ctx.varstore.change_var(constants.CATEGORY_FEED_EXCLUSION_LIST, urls_to_exclude)
        updated_custom_categories = uri_ctx.varstore.read_var(
            constants.PROX_ACL_RULES_CUSTOM_CATEGORIES)
        # start REPEAT update code
        this_cat_val = {}
        if urls_to_exclude[0].has_key(category.cat_name):
            initial_custom_categories = copy.deepcopy(updated_custom_categories)
            initial_urls_to_exclude = copy.deepcopy(urls_to_exclude)
            if urls_to_exclude:
                this_cat_val = urls_to_exclude[0].get(old_name, {})
            category, urls_to_exclude = filter_cat_stream_sites(
                self.url_categories, category, urls_to_exclude, old_name,
                old_url, new_url, this_cat_val)
            category, urls_to_exclude = filter_cat_stream_regex(
                category, urls_to_exclude, old_name, old_url, new_url, this_cat_val)

        if urls_to_exclude[0].has_key(old_name) and old_name != category.cat_name:
            del urls_to_exclude[0][old_name]
        if this_cat_val != {}:
            if not check_url_equality(initial_urls_to_exclude, urls_to_exclude, category):
                uri_ctx.varstore.change_var(constants.CATEGORY_FEED_EXCLUSION_LIST,
                                            urls_to_exclude)
        cat_dict_index = -1
        for ucategory in updated_custom_categories:
            for key, value in ucategory.iteritems():
                # if key == 'code' and value == int(values.get('cat_code')):
                if key == 'code' and value == int(code):
                    cat_dict_index = updated_custom_categories.index(ucategory)
                    ucategory['server_list'] = category.server_list
                    ucategory['regex_list'] = category.regex_list

        if this_cat_val:
            if not check_feed_equality(cat_dict_index, initial_custom_categories,
                                       updated_custom_categories):
                uri_ctx.varstore.change_var(constants.PROX_ACL_RULES_CUSTOM_CATEGORIES,
                                            updated_custom_categories)
            else:
                category.server_list = \
                    uri_ctx.varstore.read_var(
                        constants.PROX_ACL_RULES_CUSTOM_CATEGORIES)[cat_dict_index]['server_list']
                category.regex_list = \
                    uri_ctx.varstore.read_var(
                        constants.PROX_ACL_RULES_CUSTOM_CATEGORIES)[cat_dict_index]['regex_list']

        # Move category if list order changed
        if from_index == before_index:
            self.url_categories.setCustomCategoriesList(categories)
        else:
            # Moving and Saving edited category
            self.url_categories.moveCustomCategory(categories, from_index,
                                                   before_index)



