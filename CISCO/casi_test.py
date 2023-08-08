import json
import requests
from datetime import date, datetime as dt

SESSION_TOKEN = ""


def fetch_app_list():
    """
    This method will fetch the list of all apps
    from CASI server.
    """
    print('Fetching the list of all apps...')
    full_apps_list = []
    access_token = "r2426be0n9d44c2b82c89a1068f4895a"
    initial_token_url = "https://casi-tyk-gateway.us-east-1.prod.casi.umbrella.com/api/v1/session/token"
    credentials = {
        "user_email": "wsa@cisco.com",
        "password": "K8SKAnMP"
    }
    response = requests.post(initial_token_url,
                             headers={'Content-Type': 'application/json',
                                      'Authorization': 'Bearer {}'.format(access_token)}, json=credentials)
    global SESSION_TOKEN
    SESSION_TOKEN = (response.json())['token']

    batch_url = "https://casi-tyk-gateway.us-east-1.prod.casi.umbrella.com/api/v1/apps_list"
    param_data = {'batch': 1}
    response = requests.get(batch_url,
                            headers={'Authorization': 'Bearer {}'.format(SESSION_TOKEN)}, params=param_data)
    resp_data = response.json()
    total_batches = resp_data['total_batches']

    for batch in range(1, total_batches + 1):
        param_data = {'batch': batch}
        response = requests.get(batch_url,
                                headers={'Authorization': 'Bearer {}'.format(SESSION_TOKEN)}, params=param_data)
        resp_data = response.json()
        full_apps_list = full_apps_list + resp_data['apps']

    # import pdb;pdb.set_trace();
    # fetch_app_details([])
    with open('old_CASI_DB.json') as json_file:
        adc_dict = json.load(json_file)
    adc_apps_list = adc_dict.keys()

    apps_list = [app for app in full_apps_list if app['id'] in adc_apps_list]
    print(f'full_apps_list : {full_apps_list}')
    print(f'app_list : {apps_list}')
    return apps_list


def check_for_update(apps_list=None):
    """
    This method will check if update is required
    for ADC.
    """
    print('Checking if update is required...')
    update_required = False
    diff_apps = []
    with open('old_CASI_DB.json') as json_file:
        adc_dict_old = json.load(json_file)
    last_update_dt = adc_dict_old['update_info']['last_updated_date']
    last_update_dt_obj = dt.strptime(last_update_dt, "%Y-%m-%d")
    if len(adc_dict_old) - 1 > len(apps_list):
        adc_ids = adc_dict_old.keys()
        casi_ids = [app['id'] for app in apps_list]
        diff_app_ids = list(set(adc_ids).difference(casi_ids))
        diff_apps = [app['name'] for app in apps_list if app['id'] in diff_app_ids]
        print('Removed apps: ', str(diff_apps))
        return True
    for app in apps_list:
        activities_update_dt = app.get('activities_update_date', None)
        domain_update_dt = app.get('domains_updated_date', None)
        if activities_update_dt:
            if dt.strptime(activities_update_dt, "%m/%d/%Y") > last_update_dt_obj:
                update_required = True
                diff_apps.append(app['name'])
        if domain_update_dt:
            if dt.strptime(domain_update_dt, "%m/%d/%Y") > last_update_dt_obj:
                update_required = True
                diff_apps.append(app['name'])
    if update_required:
        print('Changed apps: ', str(diff_apps))
    return update_required


def fetch_app_details(apps_list=None):
    """
    This method will fetch all app details
    based on the app list.
    """
    print('Downloading all app data...')
    app_ids = []
    for app in apps_list:
        app_ids.append(app['id'])
    req_json = {"apps": app_ids}
    bulk_fetch_url = "https://casi-tyk-gateway.us-east-1.prod.casi.umbrella.com/api/v1/apps_bulk"
    response = requests.post(bulk_fetch_url,
                             headers={'Content-Type': 'application/json',
                                      'Authorization': 'Bearer {}'.format(SESSION_TOKEN)}, json=req_json)
    resp_data = response.json()
    return resp_data['apps']


def create_update_json(apps_dict=None):
    """
    This method will create the updated
    json file.
    """
    print('Creating the json file...')
    curr_date_str = str(date.today())
    apps_dict['update_info'] = {'last_updated_date': curr_date_str}
    with open("new_adc.json", "w") as outfile:
        json.dump(apps_dict, outfile)


def create_update():
    """
    The main method to check for update from CASI
    and create new adc.json if an update is determined
    """
    print('Starting update process...')
    apps_dict = {}

    apps_list = fetch_app_list()
    update_required = check_for_update(apps_list)
    if update_required:
        apps_dict = fetch_app_details(apps_list)
    if apps_dict:
        print("Update found...creating JSON")
        create_update_json(apps_dict)
    else:
        print("No Update Required")


if __name__ == "__main__":
    create_update()

twitter_value = {
    'apps': {
        '0JdbV4dy': {
            'activities': [
                {
                    'desc': 'Block File Uploads',
                    'id': 5000079,
                    'name': 'Uploads',
                    'regexes': [
                        'upload\\.twitter\\.com\\/i\\/media\\/upload.*\\.json'
                    ],
                    'regexes_request_methods': [
                        {
                            'regex': 'upload\\.twitter\\.com\\/i\\/media\\/upload.*\\.json',
                            'request_methods': [
                                'POST'
                            ]
                        }
                    ],
                    'supported': True,
                    'type': 'upload',
                    'urls': [
                        'https://upload.twitter.com/1.1/media/upload.json',
                        'https://upload.twitter.com/i/media/metadata/create.json'
                    ],
                    'urls_request_methods': [
                        {
                            'request_methods': [

                            ],
                            'url': 'https://upload.twitter.com/1.1/media/upload.json'
                        },
                        {
                            'request_methods': [
                                'POST'
                            ],
                            'url': 'https://help.twitter.com/en/upload.htcuploadcaseform.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'https://upload.twitter.com/i/media/metadata/create.json'
                        },
                        {
                            'request_methods': [
                                'POST',
                                'PUT'
                            ],
                            'url': 'https://help.twitter.com/en/forms/authenticity/impersonation/i-am-being-impersonated.media.upload.json'
                        },
                        {
                            'request_methods': [
                                'POST'
                            ],
                            'url': 'https://help.twitter.com/en/upload/thank-you.htcuploadcaseform.json'
                        },
                        {
                            'request_methods': [
                                'POST'
                            ],
                            'url': 'https://upload.twitter.com/i/media/studio/upload.json'
                        }
                    ]
                },
                {
                    'desc': 'Block Posts and Shares to Social Media',
                    'id': 5000007,
                    'name': 'Posts/Shares',
                    'regexes': [
                        'twitter\\.com\\/i\\/api\\/graphql\\/.*\\/createtweet',
                        'twitter\\.com\\/i\\/api\\/graphql\\/.*\\/createretweet',
                        'api\\.twitter\\.com\\/graphql\\/.*\\/CreateTweet',
                        'api\\.twitter\\.com\\/graphql\\/.*\\/CreateRetweet',
                        'api\\.twitter\\.com\\/graphql\\/.*\\/CreateScheduledTweet',
                        'twitter\\.com\\/i\\/api\\/graphql\\/.*\\/CreateScheduledTweet'
                    ],
                    'regexes_request_methods': [
                        {
                            'regex': 'twitter\\.com\\/i\\/api\\/graphql\\/.*\\/createtweet',
                            'request_methods': [

                            ]
                        },
                        {
                            'regex': 'twitter\\.com\\/i\\/api\\/graphql\\/.*\\/createretweet',
                            'request_methods': [

                            ]
                        },
                        {
                            'regex': 'api\\.twitter\\.com\\/graphql\\/.*\\/CreateTweet',
                            'request_methods': [
                                'POST'
                            ]
                        },
                        {
                            'regex': 'api\\.twitter\\.com\\/graphql\\/.*\\/CreateRetweet',
                            'request_methods': [
                                'POST'
                            ]
                        },
                        {
                            'regex': 'api\\.twitter\\.com\\/graphql\\/.*\\/CreateScheduledTweet',
                            'request_methods': [
                                'POST'
                            ]
                        },
                        {
                            'regex': 'twitter\\.com\\/i\\/api\\/graphql\\/.*\\/CreateScheduledTweet',
                            'request_methods': [
                                'POST'
                            ]
                        }
                    ],
                    'supported': True,
                    'type': 'post',
                    'urls': [
                        'twitter.com/i/jot',
                        'api.twitter.com/1.1/collections/create.json',
                        'api.twitter.com/1.1/collections/entries/add.json',
                        'api.twitter.com/1.1/collections/entries/curate.json',
                        'api.twitter.com/1.1/collections/update.json',
                        'api.twitter.com/1.1/favorites/create.json',
                        'twitter.com/intent/tweet',
                        'twitter.com/i/tweet/create',
                        'twitter.com/intent/tweet',
                        'api.twitter.com/1.1/statuses/retweet.json',
                        'api.twitter.com/1.1/statuses/update.json',
                        'https://twitter.com/i/api/1.1/statuses/update.json',
                        'https://twitter.com/i/api/1.1/statuses/unretweet.json',
                        'https://twitter.com/i/api/1.1/statuses/retweet.json',
                        'https://api.twitter.com/1.1/jot/client_event.json',
                        'https://api.twitter.com/1.1/live_pipeline/update_subscriptions'
                    ],
                    'urls_request_methods': [
                        {
                            'request_methods': [

                            ],
                            'url': 'twitter.com/i/jot'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'api.twitter.com/1.1/collections/create.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'api.twitter.com/1.1/collections/entries/add.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'api.twitter.com/1.1/collections/entries/curate.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'api.twitter.com/1.1/collections/update.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'api.twitter.com/1.1/favorites/create.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'twitter.com/intent/tweet'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'twitter.com/i/tweet/create'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'twitter.com/intent/tweet'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'api.twitter.com/1.1/statuses/retweet.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'api.twitter.com/1.1/statuses/update.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'https://twitter.com/i/api/1.1/statuses/update.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'https://twitter.com/i/api/1.1/statuses/unretweet.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'https://twitter.com/i/api/1.1/statuses/retweet.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'https://api.twitter.com/1.1/jot/client_event.json'
                        },
                        {
                            'request_methods': [

                            ],
                            'url': 'https://api.twitter.com/1.1/live_pipeline/update_subscriptions'
                        }
                    ]
                }
            ],
            'attributes': [
                {
                    'attribute_exist': True,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:29:58.204605',
                    'description': 'The SSL certificate key size refers to the length of the cryptographic key used to secure SSL/TLS (Transport Layer Security) encrypted communication between a web server and a web browser.The SSL certificate key size is measured in bits and typically ranges from 128 bits to 4096 bits. The larger the key size, the stronger the encryption and the more difficult it is to crack the encryption.',
                    'id': 17,
                    'is_certificate': False,
                    'name': 'SSL Cert Key Size',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:04.380393',
                    'values': [
                        {
                            'name': 'size',
                            'value': '2048'
                        }
                    ]
                },
                {
                    'attribute_exist': False,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:29:58.077511',
                    'description': "SSL pinning, also known as certificate pinning, is a security mechanism used to prevent man-in-the-middle (MitM) attacks by tying a web server's SSL certificate to a specific public key or set of public keys. With SSL pinning, a web application is designed to accept connections only from a web server whose SSL certificate contains a specific public key or set of public keys that have been pre-configured and 'pinned' to the application.",
                    'id': 16,
                    'is_certificate': False,
                    'name': 'SSL Pinned',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:01.982890',
                    'values': None
                },
                {
                    'attribute_exist': None,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:29:58.201344',
                    'description': "Screen sharing allows users to view the contents of another user's screen in real-time, allowing for easier collaboration and communication.While screen sharing can be a useful tool for collaboration and communication, it does pose a security risk and is important to use it in a secure manner to protect sensitive or confidential information.",
                    'id': 25,
                    'is_certificate': False,
                    'name': 'Screen Sharing',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:06.088871',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Access Control',
                    'created_date': '2023-04-23 08:29:58.078839',
                    'description': 'MFA requires users to provide two or more forms of authentication, such as a password and a biometric factor, to access SaaS applications, provides an extra layer of security to prevent unauthorized access.',
                    'id': 13,
                    'is_certificate': False,
                    'name': 'MFA',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:05.086170',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:29:58.290445',
                    'description': 'Heartbleed is a vulnerability that affected the OpenSSL cryptographic software library, which is used to implement SSL/TLS encryption on many websites and other online services. The vulnerability allowed an attacker to access sensitive information from the memory of affected systems, including passwords, cryptographic keys, and other private data.',
                    'id': 9,
                    'is_certificate': False,
                    'name': 'Heartbleed',
                    'parent_attr_md_id': 2,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:07.097211',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:29:58.585466',
                    'description': 'ROBOT is a vulnerability that affects certain implementations of RSA encryption in SSL/TLS protocols. The ROBOT attack works by exploiting the fact that some SSL/TLS servers still support RSA encryption using older, less secure encryption modes. By using specially crafted messages and timing attacks, an attacker can determine the private key used for RSA encryption and decrypt intercepted traffic.',
                    'id': 8,
                    'is_certificate': False,
                    'name': 'ROBOT',
                    'parent_attr_md_id': 2,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:07.185031',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:29:58.290445',
                    'description': 'Known vulnerabilities could potentially be exploited.',
                    'id': 2,
                    'is_certificate': False,
                    'name': 'Known Vulnerabilities',
                    'parent_attr_md_id': None,
                    'risk_level': 'HIGH',
                    'updated_date': '2023-04-23 09:18:02.792702',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:30:01.693798',
                    'description': 'DNS CAA (Certificate Authority Authorization) is a security mechanism that allows domain owners to specify which Certificate Authorities (CAs) are authorized to issue SSL/TLS certificates for their domain.',
                    'id': 23,
                    'is_certificate': False,
                    'name': 'DNS CAA',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:01.978272',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:30:00.120607',
                    'description': 'POODLE (Padding Oracle On Downgraded Legacy Encryption) is a security vulnerability that affects servers that use the SSLv3 protocol for encryption. POODLE works by exploiting a weakness in the way SSLv3 handles padding in encrypted communication streams. By forcing a server and client to use the weaker SSLv3 protocol instead of more secure protocols like TLS, an attacker can inject specially crafted packets into the communication stream and manipulate the padding to extract the encryption key.',
                    'id': 5,
                    'is_certificate': False,
                    'name': 'POODLE (SSLv3)',
                    'parent_attr_md_id': 2,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:04.084889',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:30:00.158891',
                    'description': 'A valid SSL (Secure Sockets Layer) certificate is a digital certificate that provides secure, encrypted communication between a web server and a web browser. It is important for website owners to ensure that their SSL certificate is valid and up to date, as expired or invalid SSL certificates can result in security warnings and reduced trust from users.',
                    'id': 15,
                    'is_certificate': False,
                    'name': 'Valid SSL Certificate',
                    'parent_attr_md_id': None,
                    'risk_level': 'HIGH',
                    'updated_date': '2023-04-23 09:18:06.691956',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:30:02.190788',
                    'description': 'Ability of a web server to include security-related HTTP headers in the response sent to a web browser or client. The Strict-Transport-Security (HSTS) header tells the web browser to only access a website over a secure HTTPS connection and helps to prevent man-in-the-middle (MITM) attacks by ensuring that all traffic is encrypted.',
                    'id': 20,
                    'is_certificate': False,
                    'name': 'HTTP Security Header Support',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:04.578087',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:30:03.118616',
                    'description': 'TLS 1.1 support refers to the ability of a web server or client to use the TLS 1.1 protocol for secure communication. Several organizations have stopped supporting TLS 1.1 due to known security vulnerabilities and the availability of more secure protocols.',
                    'id': 19,
                    'is_certificate': False,
                    'name': 'TLS 1.1 Support',
                    'parent_attr_md_id': None,
                    'risk_level': 'HIGH',
                    'updated_date': '2023-04-23 09:18:03.581788',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:29:58.782581',
                    'description': 'POODLE (Padding Oracle On Downgraded Legacy Encryption) is a security vulnerability that affects servers that use the TLS protocol for encryption. POODLE (TLS) is a variant of the original POODLE vulnerability that affects servers that support TLS version 1.2 or earlier and use block ciphers such as AES-CBC (Advanced Encryption Standard-Cipher Block Chaining) for encryption. Similar to the original POODLE attack on SSLv3, this variant allows an attacker to force a downgrade to an older, weaker version of TLS and manipulate the padding to extract the encryption key.',
                    'id': 6,
                    'is_certificate': False,
                    'name': 'POODLE (TLS)',
                    'parent_attr_md_id': 2,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:06.983174',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:30:02.599348',
                    'description': 'The renegotiation vulnerability is a security issue that affects SSL/TLS encrypted connections. This vulnerability allows an attacker to inject and modify data within an SSL/TLS session by exploiting the renegotiation process that occurs during an established connection.',
                    'id': 7,
                    'is_certificate': False,
                    'name': 'Renegotiation',
                    'parent_attr_md_id': 2,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:06.776175',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:30:02.786190',
                    'description': "The RC4 vulnerability refers to a weakness in the RC4 encryption algorithm that can be exploited by attackers to compromise the confidentiality of encrypted data. The vulnerability stems from statistical biases in the RC4 algorithm that can be used to predict some of the plaintext that corresponds to a given ciphertext. These biases can be exploited through a technique called 'plaintext recovery', which involves sending a large number of specially crafted plaintext messages to a target that uses RC4 encryption. By analyzing the corresponding ciphertext, an attacker can gradually build up knowledge of the plaintext, making it possible to decrypt the encrypted data.",
                    'id': 10,
                    'is_certificate': False,
                    'name': 'RC4',
                    'parent_attr_md_id': 2,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:07.088492',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Email Authenticity',
                    'created_date': '2023-04-23 08:30:00.679911',
                    'description': 'Domain-based Message Authentication, Reporting & Conformance (DMARC)\xa0 provides a framework for domain owners to specify their email authentication policies and receive reports on email activity for their domain.',
                    'id': 30,
                    'is_certificate': False,
                    'name': 'DMARC',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:03.679405',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:30:01.277661',
                    'description': 'File sharing can be used for a variety of purposes, including collaboration on projects, distributing software or media files, and sharing personal documents or photos. While file sharing can be a convenient and efficient way to distribute and access files, it can also pose security risks, particularly if sensitive or confidential information is being shared.',
                    'id': 24,
                    'is_certificate': False,
                    'name': 'File Sharing',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:05.776882',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Access Control',
                    'created_date': '2023-04-23 08:30:00.158012',
                    'description': 'SSO allows users to access multiple applications with a single set of credentials, simplifies the login process and reduces the risk of password reuse or weak passwords.',
                    'id': 12,
                    'is_certificate': False,
                    'name': 'SSO',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:05.390046',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Email Authenticity',
                    'created_date': '2023-04-23 08:30:01.878450',
                    'description': 'Sender Policy Framework (SPF) works by allowing the owner of a domain to specify which mail servers are authorized to send email messages from that domain.\xa0',
                    'id': 28,
                    'is_certificate': False,
                    'name': 'SPF',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:05.585233',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:30:00.489826',
                    'description': "Remote screen control allows users to view and control the contents of another user's screen in real-time, allowing for easier collaboration and troubleshooting. While remote screen control can be a useful tool for collaboration and technical support, it does pose a security risk and is important to use it in a secure manner to protect sensitive or confidential information.",
                    'id': 26,
                    'is_certificate': False,
                    'name': 'Remote Screen Control',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:02.094871',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:30:03.079266',
                    'description': "Extended Validation (EV) is a type of SSL (Secure Sockets Layer) certificate that provides the highest level of authentication for a website. An EV SSL certificate validates the domain name, organization, and legal existence of a website's owner before issuing the certificate.",
                    'id': 18,
                    'is_certificate': False,
                    'name': 'Extended Validation',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:04.186907',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Email Authenticity',
                    'created_date': '2023-04-23 08:30:00.199049',
                    'description': 'DomainKeys Identified Mail (DKIM) involves the use of digital signatures to verify the authenticity of an email message.',
                    'id': 29,
                    'is_certificate': False,
                    'name': 'DKIM',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:04.686911',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:29:59.380706',
                    'description': 'Forward secrecy is a cryptographic property that ensures that even if an attacker obtains the private key used to encrypt a session, they will not be able to decrypt past communications.',
                    'id': 22,
                    'is_certificate': False,
                    'name': 'Forward Secrecy',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:05.180223',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Data Security',
                    'created_date': '2023-04-23 08:30:03.182501',
                    'description': 'A weak cipher can be exploited by an attacker to intercept and decrypt sensitive information, such as passwords, credit card numbers, and other personal data transmitted between a web browser and a web server. Weak ciphers include DES (Data Encryption Standard), RC2 (Rivest Cipher 2), and MD5 (Message Digest 5)\xa0 and are considered weak because they have known vulnerabilities that can be exploited by attackers.',
                    'id': 21,
                    'is_certificate': False,
                    'name': 'Weak Cipher Supported',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:05.190378',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:30:01.124036',
                    'description': "DROWN (Decrypting RSA with Obsolete and Weakened eNcryption) is a security vulnerability that affects servers that support SSLv2 and use RSA encryption for key exchange. DROWN works by exploiting a weakness in SSLv2's implementation of the RSA key exchange algorithm.",
                    'id': 3,
                    'is_certificate': False,
                    'name': 'DROWN',
                    'parent_attr_md_id': 2,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:02.883667',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Auditability',
                    'created_date': '2023-04-23 08:30:02.695697',
                    'description': 'Records that capture the details of specific events or transactions that occur within a system, application, or network. These logs typically include information such as the date and time of the event, the user or entity that performed the action, and a description of the event or transaction that occurred.',
                    'id': 27,
                    'is_certificate': False,
                    'name': 'Audit Logs',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:01.778934',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:29:58.683844',
                    'description': 'BEAST (Browser Exploit Against SSL/TLS) is a security vulnerability that affects servers that use the SSLv3 and TLSv1 protocols. BEAST works by exploiting a weakness in the way SSLv3 and TLSv1 implement the cipher block chaining (CBC) encryption mode. By injecting specially crafted packets into the encrypted communication stream, an attacker can force the server to use weak encryption keys that can be decrypted using a technique called chosen plaintext attack.',
                    'id': 4,
                    'is_certificate': False,
                    'name': 'BEAST',
                    'parent_attr_md_id': 2,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:02.476645',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Compliance',
                    'created_date': '2023-04-23 08:30:02.578897',
                    'description': 'Discloses the ways in which personal data is collected, processed, stored, and used in compliance with the General Data Protection Regulation (GDPR).',
                    'id': 1,
                    'is_certificate': False,
                    'name': 'Provides GDPR information',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:01.776533',
                    'values': [
                        {
                            'name': 'Vendor GDPR Documentation',
                            'value': 'https://gdpr.twitter.com/en/faq.html,https://techcrunch.com/2022/11/14/is-elon-musks-twitter-about-to-fall-out-of-the-gdprs-one-stop-shop/'
                        }
                    ]
                },
                {
                    'attribute_exist': True,
                    'category': 'Access Control',
                    'created_date': '2023-04-23 08:29:59.583921',
                    'description': 'The process of using social media or other third-party credentials to authenticate and log in to websites or mobile applications. Social logins also have some potential drawbacks, such as the risk of privacy violations or data breaches if the third-party social media platform is compromised.',
                    'id': 14,
                    'is_certificate': False,
                    'name': 'Social Logins',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:02.083855',
                    'values': None
                },
                {
                    'attribute_exist': True,
                    'category': 'Vulnerabilities',
                    'created_date': '2023-04-23 08:29:59.979448',
                    'description': 'Incidents where unauthorized individuals or entities gained access to sensitive or confidential information belonging to individuals or organizations. The data breaches may involve theft, hacking, or accidental disclosure of sensitive data.',
                    'id': 11,
                    'is_certificate': False,
                    'name': 'Past Data Breaches',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2023-04-23 09:18:03.676281',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Compliance',
                    'created_date': '2016-08-12 00:00:00',
                    'description': 'PCI DSS',
                    'id': 1,
                    'is_certificate': True,
                    'name': 'PCI_DSS',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2022-08-07 22:17:31.443978',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Compliance',
                    'created_date': '2016-08-12 00:00:00',
                    'description': 'HIPAA',
                    'id': 2,
                    'is_certificate': True,
                    'name': 'HIPAA',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2022-08-07 22:17:31.438971',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Compliance',
                    'created_date': '2016-08-12 00:00:00',
                    'description': 'SSAE 16 / SAS 70',
                    'id': 3,
                    'is_certificate': True,
                    'name': 'FEDRAMP',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2022-08-07 22:17:31.433867',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Compliance',
                    'created_date': '2016-08-12 00:00:00',
                    'description': 'ISO 27001 / 27002',
                    'id': 4,
                    'is_certificate': True,
                    'name': 'ISO 27001 / 27002',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2022-08-07 22:17:31.427655',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Compliance',
                    'created_date': '2016-08-12 00:00:00',
                    'description': 'COBIT ',
                    'id': 5,
                    'is_certificate': True,
                    'name': 'COBIT',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2022-08-07 22:17:31.422502',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Compliance',
                    'created_date': '2016-08-12 00:00:00',
                    'description': 'SP800_53',
                    'id': 6,
                    'is_certificate': True,
                    'name': 'SP800_53',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2022-08-07 22:17:31.415138',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Compliance',
                    'created_date': '2016-08-12 00:00:00',
                    'description': 'BITS',
                    'id': 7,
                    'is_certificate': True,
                    'name': 'BITS',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2022-08-07 22:17:31.449322',
                    'values': None
                },
                {
                    'attribute_exist': False,
                    'category': 'Compliance',
                    'created_date': '2016-08-12 00:00:00',
                    'description': 'GAPP',
                    'id': 8,
                    'is_certificate': True,
                    'name': 'GAPP',
                    'parent_attr_md_id': None,
                    'risk_level': None,
                    'updated_date': '2022-08-07 22:17:31.454012',
                    'values': None
                }
            ],
            'category': 'Social Networking',
            'category_id': 33,
            'data_storage': 'Unstructured',
            'description': 'Online social networking service that enables users to send and read short messages called tweets.',
            'domains': [
                'api.twitter.com',
                'cdn.api.twitter.com',
                'cdn.cms-twdigitalassets.com',
                'image.e.twitter.com',
                'live.twitter.com',
                'pic.twitter.com',
                'platform2.twitter.com',
                'platform-eb.twitter.com',
                'platform.twitter.com',
                'prod.twitter.com',
                'publish.twitter.com',
                'sites.twitter.com',
                'static.twitter.com',
                'stories.twitter.com',
                'stream.twitter.com',
                's.twitter.com',
                'syndication.twitter.com',
                'tweet.twitter.com',
                'twitter.com',
                'twtrdns.net',
                'upload.twitter.com',
                'userstream.twitter.com',
                'wpad.local.twitter.com'
            ],
            'id': '0JdbV4dy',
            'logos': {
                'large': 'https://logo.prod.casi.umbrella.com/service/0JdbV4dy/b007648d8f7cebfe6a45971d53555de278985a69.svg',
                'small': 'https://logo.prod.casi.umbrella.com/service/0JdbV4dy/b007648d8f7cebfe6a45971d53555de278985a69.svg'
            },
            'name': 'Twitter',
            'numeric_id': 1929,
            'obsolete': None,
            'openappids': [
                {
                    'id': 882,
                    'name': 'Twitter'
                },
                {
                    'id': 1123,
                    'name': 'Tweet'
                }
            ],
            'reputation': {
                'web_reputation_updated_date': '07/16/2023',
                'web_reputation_worst_score': 33,
                'web_reputation_worst_score_domain': 'cdn.cms-twdigitalassets.com'
            },
            'risk': {
                'business': {
                    'level': 'Medium',
                    'value': 47
                },
                'country': {
                    'level': 'Heavy',
                    'value': 1
                },
                'csa': {
                    'level': 'Very High',
                    'value': 100
                },
                'total': {
                    'level': 'High',
                    'value': 68
                }
            },
            'support_domains': None,
            'type': 'SaaS',
            'url': 'https://twitter.com',
            'usage_type': 'Personal',
            'vendor': {
                'certifications': [
                    {
                        'description': 'The Payment Card Industry Data Security Standard (PCI DSS) is a widely accepted set of policies and procedures intended to optimize the security of credit, debit and cash card transactions and protect cardholders against misuse of their personal information.',
                        'id': 1,
                        'name': 'PCI_DSS',
                        'status': False
                    },
                    {
                        'description': 'HIPAA (Health Insurance Portability and Accountability Act of 1996) is United States legislation that provides data privacy and security provisions for safeguarding medical information.',
                        'id': 2,
                        'name': 'HIPAA',
                        'status': False
                    },
                    {
                        'description': 'The Federal Risk and Authorization Management Program (FedRAMP) is a government-wide program that provides a standardized approach to security assessment, authorization, and continuous monitoring for cloud products and services.',
                        'id': 3,
                        'name': 'FEDRAMP',
                        'status': False
                    },
                    {
                        'description': 'ISO 27001 is a specification for an information security management system (ISMS). An ISMS is a framework of policies and procedures that includes all legal, physical and technical controls involved in an organisations information risk management processes.',
                        'id': 4,
                        'name': 'ISO 27001 / 27002',
                        'status': False
                    },
                    {
                        'description': 'COBIT stands for Control Objectives for Information and Related Technology. It is a framework created by the ISACA (Information Systems Audit and Control Association) for IT governance and management.',
                        'id': 5,
                        'name': 'COBIT',
                        'status': False
                    },
                    {
                        'description': 'Security and Privacy Controls for Federal Information Systems and Organizations. National Institute of Standards and Technology (NIST)',
                        'id': 6,
                        'name': 'SP800_53',
                        'status': False
                    },
                    {
                        'description': 'NIST Special Publication 800-53 is part of the Special Publication 800-series that reports on the Information Technology Laboratory (ITL) research, guidelines, and outreach efforts in information system security, and on ITLs activity with industry, government, and academic organizations.',
                        'id': 7,
                        'name': 'BITS',
                        'status': False
                    },
                    {
                        'description': 'Generally Accepted Privacy Principles (GAPP) is a framework intended to assist Chartered Accountants and Certified Public Accountants in creating an effective privacy program for managing and preventing privacy risks.',
                        'id': 8,
                        'name': 'GAPP',
                        'status': False
                    }
                ],
                'duns_number': 4679305.0,
                'financial_viability': 'Medium',
                'id': 'baBJDdWO',
                'name': 'Twitter'
            },
            'web_reputation': 33
        }
    }
}

# CASI proj
#   DB - where the ll update CASI info
#   list api
#  twitter : {post, upload}


# OPS team

#   every 15 day
#     get all app_ids - [3300]
#     api to get [id1,id2]

#     create a json - 3200
#     twitter : {post}


# WSA:

# default adc_default.json - 3000
# update
# 3200

# twitter : {post}
